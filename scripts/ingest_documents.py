"""
Document Ingestion Script
Process and index documents into Endee
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

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


def ingest_directory(
    directory: str,
    endee_client: EndeeClient,
    processor: DocumentProcessor,
    index_name: str
):
    """
    Ingest all documents from a directory
    
    Args:
        directory: Path to documents directory
        endee_client: Endee client
        processor: Document processor
        index_name: Target index name
    """
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory}")
        return
    
    # Find all supported documents
    supported_extensions = {'.pdf', '.txt', '.docx', '.md'}
    files = []
    
    for ext in supported_extensions:
        files.extend(directory_path.rglob(f'*{ext}'))
    
    if not files:
        logger.warning(f"No documents found in {directory}")
        return
    
    logger.info(f"Found {len(files)} documents to process")
    
    total_chunks = 0
    successful_files = 0
    failed_files = 0
    
    # Process each file
    for file_path in tqdm(files, desc="Processing documents"):
        try:
            logger.info(f"Processing: {file_path.name}")
            
            # Process document
            chunks = processor.process_document(str(file_path))
            
            if not chunks:
                logger.warning(f"No chunks generated for {file_path.name}")
                continue
            
            # Prepare data for insertion
            vectors = [chunk.embedding for chunk in chunks]
            ids = [chunk.id for chunk in chunks]
            metadata = [chunk.metadata for chunk in chunks]
            
            # Insert into Endee in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_vectors = vectors[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                batch_metadata = metadata[i:i+batch_size]
                
                endee_client.insert_vectors(
                    index_name=index_name,
                    vectors=batch_vectors,
                    ids=batch_ids,
                    metadata=batch_metadata
                )
            
            total_chunks += len(chunks)
            successful_files += 1
            logger.info(f"✓ Indexed {len(chunks)} chunks from {file_path.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
            failed_files += 1
            continue
    
    # Summary
    logger.info("=" * 60)
    logger.info("Ingestion Summary")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {successful_files}/{len(files)}")
    logger.info(f"Total chunks indexed: {total_chunks}")
    logger.info(f"Failed files: {failed_files}")
    logger.info("=" * 60)


def main():
    """Main ingestion function"""
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    endee_url = os.getenv("ENDEE_URL", "http://localhost:8080")
    auth_token = os.getenv("ENDEE_AUTH_TOKEN", None)
    index_name = os.getenv("INDEX_NAME", "documents")
    documents_dir = os.getenv("DOCUMENTS_DIR", "./data/documents")
    
    logger.info("=" * 60)
    logger.info("Endee RAG System - Document Ingestion")
    logger.info("=" * 60)
    logger.info(f"Documents directory: {documents_dir}")
    logger.info(f"Target index: {index_name}")
    
    # Initialize clients
    logger.info("Initializing clients...")
    endee_client = EndeeClient(base_url=endee_url, auth_token=auth_token)
    processor = DocumentProcessor()
    
    # Health check
    if not endee_client.health_check():
        logger.error("❌ Cannot connect to Endee!")
        sys.exit(1)
    
    logger.info("✓ Connected to Endee")
    
    # Check if index exists
    indices = endee_client.list_indices()
    if index_name not in indices:
        logger.error(f"❌ Index '{index_name}' does not exist!")
        logger.error("Please run: python scripts/setup_index.py")
        sys.exit(1)
    
    logger.info(f"✓ Index '{index_name}' found")
    
    # Ingest documents
    ingest_directory(documents_dir, endee_client, processor, index_name)
    
    # Final statistics
    try:
        stats = endee_client.get_index_stats(index_name)
        logger.info("\nFinal Index Statistics:")
        logger.info(f"  Total vectors: {stats.get('total_vectors', 'N/A')}")
    except Exception as e:
        logger.warning(f"Could not retrieve final stats: {e}")
    
    logger.info("\n✅ Ingestion complete!")
    logger.info("\nNext step:")
    logger.info("  Run the web app: streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    main()
