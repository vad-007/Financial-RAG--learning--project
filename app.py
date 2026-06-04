import streamlit as st
import os
from rag_pipeline import FinancialRAGPipeline

st.set_page_config(page_title="Financial RAG", layout="wide")

st.title("Financial RAG — NovaTech Earnings")
st.markdown("Ask questions about NovaTech's FY2023 Earnings Report.")

@st.cache_resource
def load_pipeline():
    pdf_path = "novatech_earnings_report.pdf"
    if not os.path.exists(pdf_path):
        return None
    # Initialize pipeline
    return FinancialRAGPipeline(pdf_path=pdf_path, use_reranker=False)

pipeline = load_pipeline()

if pipeline is None:
    st.error("Could not find `novatech_earnings_report.pdf`. Make sure it's in the same directory as this script.")
else:
    st.sidebar.header("Search Settings")
    st.sidebar.markdown(
        "Use these settings to demonstrate the difference between a Naive RAG (Vector Only) "
        "and an Advanced RAG (Hybrid Search). Notice how Vector Only might miss the exact number!"
    )
    search_mode = st.sidebar.radio(
        "Search Mode",
        options=["Hybrid Search (Recommended)", "Vector Search Only (Naive RAG)", "Keyword Search Only (BM25)"]
    )
    
    mode_map = {
        "Hybrid Search (Recommended)": "hybrid",
        "Vector Search Only (Naive RAG)": "vector_only",
        "Keyword Search Only (BM25)": "bm25_only"
    }
    selected_mode = mode_map[search_mode]

    query = st.text_input("Enter your question:", "What was the total revenue for Q3 2023?")
    
    if st.button("Search"):
        if query:
            with st.spinner(f"Searching using {search_mode}..."):
                result = pipeline.query(query, search_mode=selected_mode)
                
            st.subheader("Answer")
            st.write(result["answer"])
            
            st.subheader("Sources")
            for i, source in enumerate(result["sources"]):
                with st.expander(f"Source {i+1}: Page {source['page']} - {source['type']} (Score: {source['score']})"):
                    # Find the chunk text from result["chunks"]
                    chunk_text = ""
                    for chunk, score in result["chunks"]:
                        if chunk.chunk_id == source['chunk_id']:
                            chunk_text = chunk.text
                            break
                    st.text(chunk_text)
                    st.write(f"**Section:** {source['section']}")
                    if source['numbers']:
                        st.write(f"**Numbers found:** {', '.join(source['numbers'])}")
