"""
hybrid_search.py
Implements the three-layer search strategy for financial RAG:

  Layer 1 — BM25 (keyword)  : exact term matching, great for numbers & codes
  Layer 2 — Vector (semantic): meaning-based, great for paraphrases & context
  Layer 3 — RRF Fusion      : merges both ranked lists into one final ranking

Why this combo?
  - BM25 alone misses "third-quarter earnings" when query says "Q3 revenue"
  - Vector alone may hallucinate/confuse similar-looking numbers ($4.8B vs $4.2B)
  - Together they cover each other's blind spots
"""

import math
import re
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from pdf_parser import Chunk


# ── Tokenizer ──────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """
    Simple whitespace + lowercase tokenizer for BM25.
    For financial text, we intentionally keep tokens like "$4,820.5" intact
    so BM25 can match exact figures.
    """
    # Keep dollar amounts, percentages, and alphanumeric tokens
    tokens = re.findall(r'\$[\d,\.]+[MB]?|[\+\-]?\d+\.?\d*%|\w+', text.lower())
    return tokens


# ── BM25 Index ─────────────────────────────────────────────────────────────────

class BM25Index:
    """Wraps rank-bm25's BM25Okapi with our Chunk objects."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        tokenized_corpus = [tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"BM25 index built: {len(chunks)} documents")

    def search(self, query: str, top_k: int = 10) -> list[tuple[Chunk, float]]:
        """Returns (chunk, score) pairs sorted by BM25 score descending."""
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        # Get indices sorted by score
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in ranked_indices]


# ── Vector Index ───────────────────────────────────────────────────────────────

class VectorIndex:
    """
    Semantic similarity search using TF-IDF vectors with cosine similarity.

    In production you'd replace this with a real embedding model:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, normalize_embeddings=True)

    TF-IDF is a good stand-in for learning because:
      - It captures "meaning" through term co-occurrence (not just exact matches like BM25)
      - It down-weights common words automatically (IDF component)
      - No model download required
    The key difference from BM25: TF-IDF represents docs as dense vectors enabling
    cosine similarity, while BM25 scores each query term independently.
    """

    def __init__(self, chunks: list[Chunk]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.chunks = chunks
        texts = [c.text for c in chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),   # unigrams + bigrams capture phrases like "net income"
            max_features=8000,
            sublinear_tf=True,    # log-scale TF to dampen very frequent terms
        )
        self.embeddings = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)
        # L2-normalize rows so dot product = cosine similarity
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        self.embeddings /= norms
        print(f"TF-IDF vector index built: {self.embeddings.shape} (swap for SentenceTransformer in production)")

    def search(self, query: str, top_k: int = 10) -> list[tuple[Chunk, float]]:
        """Returns (chunk, score) pairs sorted by cosine similarity descending."""
        qvec = self.vectorizer.transform([query]).toarray().astype(np.float32)[0]
        norm = np.linalg.norm(qvec)
        if norm > 0:
            qvec /= norm
        scores = self.embeddings @ qvec
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in ranked_indices]


# ── RRF Fusion ─────────────────────────────────────────────────────────────────

def reciprocal_rank_fusion(
    bm25_results: list[tuple[Chunk, float]],
    vector_results: list[tuple[Chunk, float]],
    k: int = 60,           # RRF constant — 60 is the standard default
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5,
) -> list[tuple[Chunk, float]]:
    """
    Reciprocal Rank Fusion: combines two ranked lists into one.

    RRF score for a document d:
        RRF(d) = Σ  weight_i / (k + rank_i(d))

    Why RRF over simple score averaging?
      - BM25 scores (0 to ~15) and cosine scores (0 to 1) are on completely
        different scales. You can't just add them.
      - RRF only cares about RANK, not the raw score — scale-invariant by design.
      - k=60 is a smoothing constant: it stops rank-1 from dominating too much.
    """
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, Chunk] = {}

    # BM25 contribution
    for rank, (chunk, _) in enumerate(bm25_results, start=1):
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0)
        rrf_scores[chunk.chunk_id] += bm25_weight / (k + rank)
        chunk_map[chunk.chunk_id] = chunk

    # Vector contribution
    for rank, (chunk, _) in enumerate(vector_results, start=1):
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0)
        rrf_scores[chunk.chunk_id] += vector_weight / (k + rank)
        chunk_map[chunk.chunk_id] = chunk

    # Sort by final RRF score
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
    return [(chunk_map[cid], rrf_scores[cid]) for cid in sorted_ids]


# ── Re-ranker (Cross-encoder simulation) ──────────────────────────────────────

class CrossEncoderReranker:
    """
    Production cross-encoder usage:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        scores = model.predict([(query, chunk.text) for chunk in candidates])

    A cross-encoder scores (query, chunk) pairs jointly — unlike bi-encoders which
    encode query and document independently. Slower but more accurate because the
    model attends to both texts simultaneously.

    This offline version approximates re-ranking by combining:
      - Keyword overlap density (precision)
      - Exact number match bonus (critical for financial queries)
      - Chunk type bonus (tables get a boost for number queries)
    """

    def rerank(self, query: str, candidates: list[tuple[Chunk, float]], top_k: int = 5) -> list[tuple[Chunk, float]]:
        query_tokens = set(tokenize(query))
        query_has_numbers = bool(re.search(r'\d', query))

        scored = []
        for chunk, rrf_score in candidates:
            chunk_tokens = set(tokenize(chunk.text))

            # Overlap precision: what fraction of query tokens appear in chunk
            overlap = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)

            # Exact number match bonus: does the chunk contain numbers from query?
            query_numbers = set(re.findall(r'\d[\d,\.]*', query))
            chunk_numbers = set(re.findall(r'\d[\d,\.]*', chunk.text))
            number_bonus = 0.3 if (query_numbers & chunk_numbers) else 0.0

            # Table bonus: tables are better sources for precise financial figures
            table_bonus = 0.2 if (chunk.chunk_type == "table" and query_has_numbers) else 0.0

            # Combine: base RRF score + local signals
            final_score = rrf_score + 0.4 * overlap + number_bonus + table_bonus
            scored.append((chunk, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


# ── HybridSearchEngine (puts it all together) ─────────────────────────────────

class HybridSearchEngine:
    """
    The main search class. Usage:
        engine = HybridSearchEngine(chunks)
        results = engine.search("What was Q3 2023 revenue?")
    """

    def __init__(self, chunks: list[Chunk], use_reranker: bool = True):
        self.chunks = chunks
        self.bm25_index = BM25Index(chunks)
        self.vector_index = VectorIndex(chunks)
        self.reranker = CrossEncoderReranker() if use_reranker else None

    def search(
        self,
        query: str,
        top_k_retrieval: int = 15,   # how many from each method before fusion
        top_k_final: int = 5,        # final top chunks returned to LLM
        verbose: bool = False,
        search_mode: str = "hybrid"  # "hybrid", "vector_only", "bm25_only"
    ) -> list[tuple[Chunk, float]]:
        """
        Full pipeline:
          1. BM25 retrieval
          2. Vector retrieval
          3. RRF fusion
          4. Cross-encoder re-rank (if enabled)
        """
        # Step 1 & 2: Retrieve candidates from both methods
        bm25_hits  = self.bm25_index.search(query, top_k=top_k_retrieval)
        vector_hits = self.vector_index.search(query, top_k=top_k_retrieval)

        if verbose:
            print(f"\n-- BM25 top-3 --")
            for c, s in bm25_hits[:3]:
                print(f"  [{s:.3f}] {c.chunk_id} (p{c.page}) - {c.text[:60].replace(chr(10),' ')}...")
            print(f"\n-- Vector top-3 --")
            for c, s in vector_hits[:3]:
                print(f"  [{s:.3f}] {c.chunk_id} (p{c.page}) - {c.text[:60].replace(chr(10),' ')}...")

        # Step 3: Fusion or selection based on mode
        if search_mode == "vector_only":
            fused = vector_hits
        elif search_mode == "bm25_only":
            fused = bm25_hits
        else:
            fused = reciprocal_rank_fusion(bm25_hits, vector_hits)

        if verbose:
            print(f"\n-- After RRF fusion (top-5) --")
            for c, s in fused[:5]:
                print(f"  [{s:.4f}] {c.chunk_id} (p{c.page}, {c.chunk_type}) - {c.text[:60].replace(chr(10),' ')}...")

        # Step 4: Re-rank the top candidates with cross-encoder
        if self.reranker:
            # Only pass top-N to re-ranker (it's slower, O(n) model calls)
            candidates = fused[:top_k_retrieval]
            final = self.reranker.rerank(query, candidates, top_k=top_k_final)
        else:
            final = fused[:top_k_final]

        return final


if __name__ == "__main__":
    import os
    from pdf_parser import parse_pdf

    # Resolve the PDF path relative to this script's directory
    _here = os.path.dirname(os.path.abspath(__file__))
    _pdf  = os.path.join(_here, "novatech_earnings_report.pdf")

    chunks = parse_pdf(_pdf)
    engine = HybridSearchEngine(chunks, use_reranker=False)  # enable reranker for better results

    query = "What was the total revenue for Q3 2023?"
    print(f"\nQuery: {query}")
    results = engine.search(query, verbose=True)
    print("\n-- Final top results --")
    for chunk, score in results:
        print(f"\n[score={score:.4f}] {chunk.chunk_id} | page {chunk.page} | {chunk.chunk_type}")
        print(chunk.text[:300])
