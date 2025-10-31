"""
Streamlit UI for EideticRAG
"""

import streamlit as st
import requests
import json
from typing import Dict, List


# API configuration
API_URL = "http://localhost:8000"


def query_api(query: str, k: int = 5) -> Dict:
    """Send query to API"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query, "k": k}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None


def display_chunk(chunk: Dict, index: int):
    """Display a retrieved chunk"""
    with st.expander(f"Source {index + 1} (Score: {chunk['score']:.3f})"):
        st.text(f"Chunk ID: {chunk['chunk_id'][:16]}...")
        st.text(f"Document ID: {chunk['metadata']['doc_id'][:16]}...")
        st.write(chunk['text'])


def main():
    st.set_page_config(
        page_title="EideticRAG",
        page_icon="🧠",
        layout="wide"
    )
    
    # Header
    st.title("🧠 EideticRAG - Intelligent Question Answering")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        num_chunks = st.slider(
            "Number of chunks to retrieve",
            min_value=1,
            max_value=10,
            value=5
        )
        
        st.markdown("---")
        st.header("About")
        st.markdown("""
        **EideticRAG** is a retrieval-augmented generation system that:
        - 📚 Retrieves relevant context
        - 🎯 Generates accurate answers
        - 📍 Provides clear provenance
        - 💭 Remembers past interactions
        """)
        
        # Stats
        st.markdown("---")
        if st.button("🔄 Refresh Stats"):
            try:
                response = requests.get(f"{API_URL}/stats")
                if response.status_code == 200:
                    stats = response.json()["stats"]
                    st.metric("Total Chunks", stats["total_chunks"])
            except:
                st.error("Failed to load stats")
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("💬 Ask a Question")
        
        # Query input
        query = st.text_area(
            "Enter your question:",
            placeholder="e.g., When was AI research founded?",
            height=100
        )
        
        if st.button("🔍 Search", type="primary"):
            if query:
                with st.spinner("Searching..."):
                    result = query_api(query, k=num_chunks)
                
                if result:
                    # Store in session state
                    st.session_state['last_result'] = result
            else:
                st.warning("Please enter a question")
    
    with col2:
        st.header("📝 Answer")
        
        if 'last_result' in st.session_state:
            result = st.session_state['last_result']
            
            # Display answer
            st.markdown("### Response")
            st.write(result['answer'])
            
            # Display metadata
            with st.expander("📊 Metadata"):
                st.json({
                    'model': result['metadata']['model'],
                    'chunks_retrieved': result['metadata']['num_chunks_retrieved'],
                    'chunks_cited': result['metadata']['num_chunks_cited']
                })
    
    # Retrieved chunks section
    if 'last_result' in st.session_state:
        result = st.session_state['last_result']
        
        st.markdown("---")
        st.header("📚 Retrieved Sources")
        
        # Display provenance
        if result['provenance']:
            st.markdown("### 🔗 Citations")
            for prov in result['provenance']:
                st.write(f"- Chunk `{prov['chunk_id'][:16]}...` (Score: {prov['score']:.3f})")
        
        # Display chunks
        st.markdown("### 📄 Full Retrieved Chunks")
        for i, chunk in enumerate(result['chunks']):
            display_chunk(chunk, i)
    
    # File upload section
    st.markdown("---")
    st.header("📤 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file to ingest",
        type=['txt', 'pdf']
    )
    
    if uploaded_file is not None:
        if st.button("📥 Ingest Document"):
            with st.spinner("Ingesting document..."):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(
                        f"{API_URL}/ingest",
                        files=files
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.success(result['message'])
                        st.json(result)
                    else:
                        st.error(f"Failed to ingest: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
