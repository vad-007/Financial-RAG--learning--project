# Financial RAG — Learning Project

This project explores the challenges of building Retrieval-Augmented Generation (RAG) systems for highly numerical, complex documents like financial earnings reports. 

The core thesis of this project is: **"In financial RAG, missing one number can be expensive."**

When querying financial documents, Naive RAG (Vector-only search) often fails because it looks for semantic meaning rather than exact keywords or numbers. It might retrieve a chunk from Q2 when you asked for Q3 because the sentences are semantically similar, leading to expensive hallucinations.

This project solves that by implementing an **Advanced Hybrid RAG** pipeline.

## Features

- **Hybrid Search Engine:** Combines `BM25` (Keyword Search) and `TF-IDF / Vector Search` (Semantic Search) to capture both exact numbers/dates and contextual meaning.
- **Reciprocal Rank Fusion (RRF):** Merges the results of BM25 and Vector search to find the absolute best chunks.
- **Custom PDF Parsing:** Extracts and chunks complex layouts, including tables and dense financial text.
- **Strict Number Grounding:** Forces the mock LLM to extract and ground its answers using the exact numbers found in the retrieved context to prevent hallucinations.
- **Interactive Streamlit UI:** A clean web interface to test queries and visualize the retrieved chunks, page numbers, and exact scores.

## Interactive "Before & After" Demo

The Streamlit UI includes a **Search Settings** toggle to let you visually compare standard RAG vs. Hybrid RAG:

1. **Vector Search Only (Naive RAG):** Simulates the problem. Try asking for Q3 revenue and watch it retrieve chunks from Q4 and give the wrong number.
2. **Hybrid Search (Recommended):** Simulates the solution. Run the same query and watch the BM25 algorithm perfectly catch the Q3 keywords, retrieve the right chunk, and output the correct number!

## Getting Started

### 1. Setup Virtual Environment
```powershell
uv venv Fin_venv
.\Fin_venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
uv pip install -r requirements.txt
# Alternatively, manually install the required packages:
# pip install streamlit sentence-transformers rank_bm25 scikit-learn numpy pypdf
```

### 3. Run the Streamlit App
```powershell
streamlit run app.py
```
This will launch the web interface where you can interact with the RAG pipeline!

## Project Structure

- `app.py`: The Streamlit web interface.
- `rag_pipeline.py`: The core RAG pipeline connecting the search engine and mock LLM.
- `hybrid_search.py`: Implements BM25, Vector Search, and RRF fusion.
- `pdf_parser.py`: Custom chunking and parsing logic for the financial PDF.
- `generate_pdf.py`: Script to generate the dummy `novatech_earnings_report.pdf` used for testing.
- `LINKEDIN_POST.md`: A draft for sharing this learning project on LinkedIn.

## Why this matters
Building this project demonstrates that when dealing with financial data, your RAG pipeline is only as good as your retrieval and chunking strategy. Relying solely on vector embeddings for highly numerical data is a recipe for hallucinations. Hybrid search is a strict necessity.
