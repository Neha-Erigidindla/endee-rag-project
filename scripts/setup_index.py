"""
Setup Script - Initialize Endee Index
Run this script once to create the vector index in Endee
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.endee_client import EndeeClient
from src.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize Endee index"""
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    endee_url = os.getenv("ENDEE_URL", "http://localhost:8080")
    auth_token = os.getenv("ENDEE_AUTH_TOKEN", None)
    index_name = os.getenv("INDEX_NAME", "documents")
    
    logger.info("=" * 60)
    logger.info("Endee RAG System - Index Setup")
    logger.info("=" * 60)
    
    # Initialize clients
    logger.info(f"Connecting to Endee at {endee_url}...")
    endee_client = EndeeClient(base_url=endee_url, auth_token=auth_token)
    
    # Health check
    if not endee_client.health_check():
        logger.error("❌ Failed to connect to Endee!")
        logger.error("Please ensure Endee is running:")
        logger.error("  docker-compose up -d")
        sys.exit(1)
    
    logger.info("✓ Connected to Endee successfully")
    
    # Initialize document processor to get embedding dimension
    logger.info("Loading embedding model...")
    processor = DocumentProcessor()
    embedding_dim = processor.embedding_dim
    logger.info(f"✓ Embedding dimension: {embedding_dim}")
    
    # Check if index already exists
    existing_indices = endee_client.list_indices()
    logger.info(f"Existing indices: {existing_indices}")
    
    if index_name in existing_indices:
        response = input(f"\n⚠️  Index '{index_name}' already exists. Delete and recreate? (y/N): ")
        if response.lower() == 'y':
            logger.info(f"Deleting existing index '{index_name}'...")
            endee_client.delete_index(index_name)
            logger.info("✓ Index deleted")
        else:
            logger.info("Keeping existing index")
            logger.info("✓ Setup complete!")
            return
    
    # Create index
    logger.info(f"Creating index '{index_name}'...")
    logger.info(f"  Vector dimension: {embedding_dim}")
    logger.info(f"  Metric: cosine")
    logger.info(f"  Type: hnsw")
    
    try:
        endee_client.create_index(
            index_name=index_name,
            vector_dim=embedding_dim,
            metric_type="cosine",
            index_type="hnsw"
        )
        logger.info("✓ Index created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to create index: {e}")
        sys.exit(1)
    
    # Verify index creation
    indices = endee_client.list_indices()
    if index_name in indices:
        logger.info("✓ Index verified")
        
        # Get index stats
        stats = endee_client.get_index_stats(index_name)
        logger.info(f"Index stats: {stats}")
        
    else:
        logger.error("❌ Index verification failed")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✅ Setup completed successfully!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Add documents: python scripts/ingest_documents.py")
    logger.info("  2. Run web app: streamlit run app/streamlit_app.py")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
