"""
Utility Functions
Helper functions used across the project
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def ensure_directory(path: str) -> Path:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of file
    
    Args:
        file_path: Path to file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def load_json(file_path: str) -> Dict:
    """
    Load JSON file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: Dict, file_path: str, indent: int = 2):
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
    """
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)


def get_supported_files(directory: str, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Get all supported files from directory
    
    Args:
        directory: Directory to search
        extensions: List of file extensions (e.g., ['.pdf', '.txt'])
        
    Returns:
        List of file paths
    """
    if extensions is None:
        extensions = ['.pdf', '.txt', '.docx', '.md']
    
    directory_path = Path(directory)
    files = []
    
    for ext in extensions:
        files.extend(directory_path.rglob(f'*{ext}'))
    
    return files


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    # Remove multiple newlines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text


def create_timestamp() -> str:
    """
    Create ISO format timestamp
    
    Returns:
        Timestamp string
    """
    return datetime.now().isoformat()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
):
    """
    Setup logging configuration
    
    Args:
        level: Logging level
        log_file: Optional file to log to
        format_string: Custom format string
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=handlers
    )


def batch_items(items: List, batch_size: int = 100):
    """
    Generate batches from list
    
    Args:
        items: List of items
        batch_size: Size of each batch
        
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    import numpy as np
    
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"Starting {self.name}...")
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"Completed {self.name} in {duration:.2f}s")
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


def validate_environment():
    """
    Validate required environment variables
    
    Raises:
        ValueError if required variables are missing
    """
    required = ['ENDEE_URL', 'INDEX_NAME']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def get_project_root() -> Path:
    """
    Get project root directory
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent


# Example usage
if __name__ == "__main__":
    setup_logging()
    
    # Test utilities
    print(f"Project root: {get_project_root()}")
    print(f"Timestamp: {create_timestamp()}")
    print(f"File size: {format_file_size(1024 * 1024 * 2.5)}")
    
    # Test timer
    with Timer("Test operation") as timer:
        import time
        time.sleep(1)
    
    print(f"Elapsed: {timer.elapsed:.2f}s")
