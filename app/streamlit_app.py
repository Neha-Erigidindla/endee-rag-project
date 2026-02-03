"""
Streamlit Web Interface for RAG System
Interactive UI for document search and question answering
"""

import streamlit as st
import logging
from typing import List
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RAG components
from src.endee_client import EndeeClient
from src.document_processor import DocumentProcessor
from src.rag_engine import RAGEngine

# Page config
st.set_page_config(
    page_title="Endee RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .source-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_rag_system():
    """Initialize RAG system components (cached)"""
    try:
        # Get configuration from environment or use defaults
        endee_url = os.getenv("ENDEE_URL", "http://localhost:8080")
        auth_token = os.getenv("ENDEE_AUTH_TOKEN", None)
        index_name = os.getenv("INDEX_NAME", "documents")
        
        # Initialize components
        endee_client = EndeeClient(base_url=endee_url, auth_token=auth_token)
        processor = DocumentProcessor()
        
        # Check if Endee is healthy
        if not endee_client.health_check():
            st.error("⚠️ Cannot connect to Endee. Please ensure it's running.")
            return None
        
        # Initialize RAG engine
        rag_engine = RAGEngine(
            endee_client=endee_client,
            document_processor=processor,
            index_name=index_name,
            top_k=5,
            use_llm=False
        )
        
        return rag_engine
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        st.error(f"Error initializing system: {e}")
        return None


def display_source_card(source, index: int):
    """Display a source document card"""
    text = source.metadata.get('text', '')
    source_file = source.metadata.get('source', 'Unknown')
    score = source.score
    
    st.markdown(f"""
    <div class="source-card">
        <h4>📄 Source {index}: {source_file}</h4>
        <p><strong>Relevance Score:</strong> {score:.3f}</p>
        <p>{text[:300]}{'...' if len(text) > 300 else ''}</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔍 Intelligent Document Search & RAG</h1>', unsafe_allow_html=True)
    st.markdown("### Powered by Endee Vector Database")
    
    # Initialize RAG system
    rag = initialize_rag_system()
    
    if rag is None:
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Search parameters
        top_k = st.slider(
            "Number of results",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of relevant documents to retrieve"
        )
        
        st.divider()
        
        # Statistics
        st.header("📊 Statistics")
        try:
            indices = rag.endee.list_indices()
            st.metric("Available Indices", len(indices))
            
            if indices:
                stats = rag.endee.get_index_stats(rag.index_name)
                st.metric("Total Vectors", stats.get('total_vectors', 'N/A'))
        except:
            st.warning("Could not fetch statistics")
        
        st.divider()
        
        # About
        st.header("ℹ️ About")
        st.info("""
        This RAG system uses:
        - **Endee** for vector storage
        - **Sentence Transformers** for embeddings
        - **Semantic Search** for retrieval
        - **LLM** for answer generation
        """)
        
        st.markdown("---")
        st.markdown("Built with ❤️ for Endee.io")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🔍 Search", "📚 Documents", "📊 Analytics"])
    
    with tab1:
        st.header("Ask a Question")
        
        # Query input
        query = st.text_input(
            "Enter your question:",
            placeholder="E.g., What is machine learning?",
            key="query_input"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            search_button = st.button("🔍 Search", type="primary", use_container_width=True)
        
        if search_button and query:
            with st.spinner("Searching knowledge base..."):
                try:
                    # Perform RAG query
                    response = rag.query(query, top_k=top_k)
                    
                    # Display answer
                    st.success("✅ Answer Generated")
                    
                    # Answer section
                    st.markdown("### 💡 Answer")
                    st.markdown(f"""
                    <div style="background-color: #e8f4f8; padding: 1.5rem; border-radius: 0.5rem; border-left: 5px solid #1f77b4;">
                        {response.answer}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Sources section
                    st.markdown("### 📚 Retrieved Sources")
                    
                    if response.sources:
                        for i, source in enumerate(response.sources, 1):
                            display_source_card(source, i)
                    else:
                        st.info("No sources found.")
                    
                    # Show context (expandable)
                    with st.expander("🔍 View Full Context"):
                        st.text(response.context_used)
                        
                except Exception as e:
                    st.error(f"Error processing query: {e}")
                    logger.error(f"Query error: {e}")
        
        elif search_button:
            st.warning("Please enter a question.")
        
        # Example queries
        st.divider()
        st.markdown("#### 💡 Example Questions")
        
        examples = [
            "What is machine learning?",
            "Explain neural networks",
            "What are the applications of AI?",
            "How does deep learning work?"
        ]
        
        cols = st.columns(2)
        for i, example in enumerate(examples):
            with cols[i % 2]:
                if st.button(example, key=f"example_{i}", use_container_width=True):
                    st.session_state.query_input = example
                    st.rerun()
    
    with tab2:
        st.header("Document Management")
        
        # Upload section
        st.subheader("📤 Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Upload documents to add to knowledge base",
            type=['pdf', 'txt', 'docx', 'md'],
            accept_multiple_files=True,
            help="Supported formats: PDF, TXT, DOCX, MD"
        )
        
        if uploaded_files:
            if st.button("Process Uploaded Documents", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        status_text.text(f"Processing {uploaded_file.name}...")
                        
                        # Save temporarily
                        temp_path = f"/tmp/{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.read())
                        
                        # Process document
                        chunks = rag.processor.process_document(temp_path)
                        
                        # Insert into Endee
                        vectors = [chunk.embedding for chunk in chunks]
                        ids = [chunk.id for chunk in chunks]
                        metadata = [chunk.metadata for chunk in chunks]
                        
                        rag.endee.insert_vectors(
                            index_name=rag.index_name,
                            vectors=vectors,
                            ids=ids,
                            metadata=metadata
                        )
                        
                        # Clean up
                        os.remove(temp_path)
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
                
                status_text.text("✅ All documents processed!")
                st.success(f"Successfully processed {len(uploaded_files)} documents")
        
        st.divider()
        
        # Document list
        st.subheader("📋 Indexed Documents")
        
        try:
            stats = rag.endee.get_index_stats(rag.index_name)
            total_vectors = stats.get('total_vectors', 0)
            
            st.info(f"Total document chunks indexed: **{total_vectors}**")
            
        except Exception as e:
            st.warning("Could not retrieve document statistics")
    
    with tab3:
        st.header("Analytics & Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h2>⚡</h2>
                <h3>Fast Search</h3>
                <p>Sub-millisecond retrieval</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h2>🎯</h2>
                <h3>High Accuracy</h3>
                <p>Semantic understanding</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h2>📈</h2>
                <h3>Scalable</h3>
                <p>Millions of vectors</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # System info
        st.subheader("🖥️ System Information")
        
        system_info = {
            "Endee URL": os.getenv("ENDEE_URL", "http://localhost:8080"),
            "Index Name": rag.index_name,
            "Embedding Model": "all-MiniLM-L6-v2",
            "Embedding Dimension": rag.processor.embedding_dim,
            "Top-K Results": top_k
        }
        
        for key, value in system_info.items():
            st.text(f"{key}: {value}")


if __name__ == "__main__":
    main()
