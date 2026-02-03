"""
Configuration Management
Centralized configuration for the RAG system
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class EndeeConfig:
    """Endee database configuration"""
    url: str = "http://localhost:8080"
    auth_token: Optional[str] = None
    index_name: str = "documents"
    
    @classmethod
    def from_env(cls):
        return cls(
            url=os.getenv("ENDEE_URL", "http://localhost:8080"),
            auth_token=os.getenv("ENDEE_AUTH_TOKEN"),
            index_name=os.getenv("INDEX_NAME", "documents")
        )


@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    @classmethod
    def from_env(cls):
        return cls(
            model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "512")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50"))
        )


@dataclass
class RAGConfig:
    """RAG system configuration"""
    top_k: int = 5
    use_llm: bool = False
    llm_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        return cls(
            top_k=int(os.getenv("TOP_K", "5")),
            use_llm=os.getenv("USE_LLM", "false").lower() == "true",
            llm_api_key=os.getenv("OPENAI_API_KEY")
        )


@dataclass
class AppConfig:
    """Application configuration"""
    documents_dir: str = "./data/documents"
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls):
        return cls(
            documents_dir=os.getenv("DOCUMENTS_DIR", "./data/documents"),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )


# Global configuration instances
endee_config = EndeeConfig.from_env()
embedding_config = EmbeddingConfig.from_env()
rag_config = RAGConfig.from_env()
app_config = AppConfig.from_env()
