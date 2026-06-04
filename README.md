# Financial RAG — Learning Project

A complete Retrieval-Augmented Generation (RAG) pipeline for financial PDFs.
Built for learning — every design decision is explained in comments.

## Project Structure

```
financial_rag/
├── data/
│   └── novatech_earnings_report.pdf   ← generated fake earnings report
├── src/
│   ├── generate_pdf.py     ← Step 0: Creates the dummy financial PDF
│   ├── pdf_parser.py       ← Step 1: Smart PDF → Chunks (handles tables properly)
│   ├── hybrid_search.py    ← Step 2: BM25 + Vector + RRF + Re-ranker
│   └── rag_pipeline.py     ← Step 3: Full pipeline + demo queries
└── README.md
```

## What This Covers

| Concept              | Where                         | Key Idea                                      |
|----------------------|-------------------------------|-----------------------------------------------|
| Smart PDF parsing    | `pdf_parser.py`               | Tables extracted separately, not as raw text  |
| Chunking with overlap| `pdf_parser.py`               | 150-char overlap prevents cutting mid-context |
| Number metadata      | `pdf_parser.py:extract_numbers` | Dollar amounts stored separately for fallback |
| BM25 keyword search  | `hybrid_search.py:BM25Index`  | Exact match — critical for "$4,820.5M"        |
| Vector/semantic search| `hybrid_search.py:VectorIndex`| TF-IDF cosine sim (swap for embeddings)       |
| RRF fusion           | `hybrid_search.py:reciprocal_rank_fusion` | Scale-invariant rank merging   |
| Re-ranking           | `hybrid_search.py:CrossEncoderReranker`  | Final scoring pass on top-N    |
| Grounded answers     | `rag_pipeline.py:mock_llm_answer`        | Context → LLM prompt structure|

## How to Run

```bash
# 1. Install dependencies
pip install reportlab pdfplumber rank-bm25 scikit-learn numpy

# 2. Generate the fake PDF
python src/generate_pdf.py

# 3. Run the full RAG pipeline with demo queries
python src/rag_pipeline.py
```

## Upgrading to a Real LLM

In `rag_pipeline.py`, replace `mock_llm_answer` with:

```python
from anthropic import Anthropic
client = Anthropic()

def real_llm_answer(query: str, context_chunks):
    context = "\n\n---\n\n".join(
        f"[page {c.page}]\n{c.text}" for c, _ in context_chunks
    )
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        system=(
            "You are a financial analyst assistant. "
            "Answer ONLY using the provided context. "
            "If a specific number is not in the context, say 'Not found in retrieved context'. "
            "Always cite the page number."
        ),
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}"
        }]
    )
    return response.content[0].text
```

## Upgrading Vector Search (Production)

Replace `VectorIndex` in `hybrid_search.py` with:

```python
from sentence_transformers import SentenceTransformer

class VectorIndex:
    def __init__(self, chunks):
        self.chunks = chunks
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [c.text for c in chunks]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True)

    def search(self, query, top_k=10):
        qvec = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.embeddings @ qvec
        idx = scores.argsort()[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in idx]
```

## Key Financial RAG Lessons

1. **Never split tables across chunks** — a revenue table cut in half returns wrong numbers
2. **BM25 is non-negotiable** for financial docs — vector search alone misses exact figures
3. **RRF over score-averaging** — BM25 and cosine scores are on different scales; ranks aren't
4. **Always cite page + chunk type** in the prompt — forces LLM to stay grounded
5. **Extract numbers as metadata** — enables an exact-match fallback layer
6. **The dangerous query**: "What was EPS in Q2?" — if chunking split the table, you get a confident wrong answer. Test this explicitly.

## Sample Queries to Try

```python
# Simple retrieval
"What was total revenue for FY2023?"
"What is the diluted EPS?"

# Table-heavy
"List all debt instruments with their maturity dates and interest rates"
"Break down revenue by segment for FY2023"

# Multi-concept
"How did EBITDA margin change year over year?"
"What is free cash flow and how was it calculated?"

# Forward-looking
"What is the FY2024 revenue guidance range?"
"What does management expect for AI Solutions revenue?"
```
