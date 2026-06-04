"""
rag_pipeline.py
Full RAG pipeline: parse PDF → index → retrieve → answer with a mock LLM.

For learning purposes the "LLM" is a simple template-based answer generator
so you can run this without any API keys. The comments show exactly where
you'd plug in a real model (OpenAI, Anthropic, etc.).
"""

import sys
import re
import os

from pdf_parser import parse_pdf, Chunk
from hybrid_search import HybridSearchEngine


# ── Mock LLM (no API key needed) ───────────────────────────────────────────────

def mock_llm_answer(query: str, context_chunks: list[tuple[Chunk, float]]) -> str:
    """
    In a real system, this function would call:
        from anthropic import Anthropic
        client = Anthropic()
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            system="You are a financial analyst. Answer ONLY from the provided context. "
                   "If a number is not explicitly stated, say so.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    For learning, we simulate the grounding step instead.
    """
    context_text = "\n\n---\n\n".join(
        f"[Source: page {c.page}, type={c.chunk_type}, section='{c.section}']\n{c.text}"
        for c, _ in context_chunks
    )
    prompt = (
        f"Context from NovaTech Corp FY2023 Earnings Report:\n\n"
        f"{context_text}\n\n"
        f"Question: {query}\n\n"
        f"Answer (grounded in context above):"
    )

    # ── Simulated grounding: scan context for numbers that answer the query ──
    query_lower = query.lower()
    all_numbers = []
    for chunk, score in context_chunks:
        all_numbers.extend(chunk.numbers)

    # Try to pull the most relevant number from context
    answer_lines = [f"Based on the retrieved context (top chunk: page {context_chunks[0][0].page}):"]

    # Look for direct mentions in top chunk text
    top_text = context_chunks[0][0].text
    sentences = [s.strip() for s in re.split(r'[.\n]', top_text) if len(s.strip()) > 20]

    relevant = []
    for kw in query_lower.split():
        if len(kw) < 4:
            continue
        for sent in sentences:
            if kw in sent.lower() and any(c.isdigit() for c in sent):
                relevant.append(sent)

    if relevant:
        answer_lines.append("")
        for r in relevant[:3]:
            answer_lines.append(f"  • {r.strip()}")
    else:
        answer_lines.append("")
        answer_lines.append(f"  Relevant excerpt: \"{top_text[:200].strip()}...\"")

    answer_lines += [
        "",
        f"Numbers found in top context: {', '.join(all_numbers[:8])}",
        "",
        "[In production: replace this function with a real LLM call using the prompt above]"
    ]
    return "\n".join(answer_lines)


# ── RAG Pipeline ───────────────────────────────────────────────────────────────

class FinancialRAGPipeline:
    """
    End-to-end pipeline:
      1. Load & parse PDF into chunks
      2. Build hybrid search index (BM25 + Vector + optional re-ranker)
      3. For each query: retrieve → format context → generate answer
    """

    def __init__(self, pdf_path: str, use_reranker: bool = False):
        print("=" * 55)
        print("  NovaTech Financial RAG — Initialising")
        print("=" * 55)

        # Step 1: Parse PDF
        self.chunks = parse_pdf(pdf_path)

        # Step 2: Build search engine
        # use_reranker=False by default to avoid downloading another model;
        # set True to enable the cross-encoder re-ranking layer
        self.engine = HybridSearchEngine(self.chunks, use_reranker=use_reranker)
        print("\nRAG pipeline ready.\n")

    def query(self, question: str, top_k: int = 5, verbose: bool = False, search_mode: str = "hybrid") -> dict:
        """
        Run a single question through the pipeline.
        Returns a dict with: question, answer, sources, retrieved_chunks
        """
        print(f"\n{'─'*55}")
        print(f"  QUERY: {question}")
        print(f"{'─'*55}")

        # Retrieve relevant chunks
        results = self.engine.search(question, top_k_final=top_k, verbose=verbose, search_mode=search_mode)

        # Generate answer (swap mock_llm_answer with real LLM call here)
        answer = mock_llm_answer(question, results)

        # Format source citations
        sources = [
            {
                "chunk_id": c.chunk_id,
                "page": c.page,
                "type": c.chunk_type,
                "section": c.section,
                "score": round(score, 4),
                "numbers": c.numbers[:5],
            }
            for c, score in results
        ]

        print(f"\nANSWER:\n{answer}")
        print(f"\nSOURCES ({len(sources)} chunks retrieved):")
        for s in sources:
            print(f"  • {s['chunk_id']} | page {s['page']} | {s['type']} | score={s['score']}")

        return {"question": question, "answer": answer, "sources": sources, "chunks": results}


# ── Run demo queries ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pipeline = FinancialRAGPipeline(
        pdf_path="novatech_earnings_report.pdf",
        use_reranker=False,
    )

    # These queries cover the different difficulty levels we discussed:
    demo_queries = [
        # Simple fact retrieval
        "What was the total revenue for Q3 2023?",
        # Exact number from a table
        "What was the diluted EPS for fiscal year 2023?",
        # Multi-concept
        "What is the EBITDA margin and how did it change year over year?",
        # Debt / table query
        "What are the interest rates and maturity dates of NovaTech's debt instruments?",
        # Guidance / forward-looking
        "What is the FY2024 revenue guidance?",
    ]

    for q in demo_queries:
        pipeline.query(q)
        print()
