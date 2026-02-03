"""
Endee Vector Database Client
Handles all interactions with the Endee vector database API
"""

import requests
from typing import List, Dict, Optional, Any
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result from Endee"""
    id: str
    score: float
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None


class EndeeClient:
    """Client for interacting with Endee vector database"""
    
    def __init__(self, base_url: str = "http://localhost:8080", auth_token: Optional[str] = None):
        """
        Initialize Endee client
        
        Args:
            base_url: Endee server URL
            auth_token: Optional authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.headers = {}
        
        if auth_token:
            self.headers['Authorization'] = auth_token
        
        logger.info(f"Initialized Endee client for {self.base_url}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request to Endee API
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check if Endee server is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def create_index(
        self,
        index_name: str,
        vector_dim: int,
        metric_type: str = "cosine",
        index_type: str = "hnsw"
    ) -> Dict:
        """
        Create a new vector index
        
        Args:
            index_name: Name of the index
            vector_dim: Dimension of vectors
            metric_type: Distance metric (cosine, l2, ip)
            index_type: Index type (hnsw)
            
        Returns:
            Response data
        """
        payload = {
            "index_name": index_name,
            "vector_dim": vector_dim,
            "metric_type": metric_type,
            "index_type": index_type
        }
        
        logger.info(f"Creating index '{index_name}' with dim={vector_dim}")
        return self._make_request('POST', '/api/v1/index/create', json=payload)
    
    def list_indices(self) -> List[str]:
        """
        List all available indices
        
        Returns:
            List of index names
        """
        response = self._make_request('GET', '/api/v1/index/list')
        return response.get('indices', [])
    
    def delete_index(self, index_name: str) -> Dict:
        """
        Delete an index
        
        Args:
            index_name: Name of index to delete
            
        Returns:
            Response data
        """
        logger.warning(f"Deleting index '{index_name}'")
        return self._make_request('DELETE', f'/api/v1/index/{index_name}')
    
    def insert_vectors(
        self,
        index_name: str,
        vectors: List[List[float]],
        ids: List[str],
        metadata: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Insert vectors into index
        
        Args:
            index_name: Target index name
            vectors: List of vector embeddings
            ids: List of unique IDs
            metadata: Optional metadata for each vector
            
        Returns:
            Response data
        """
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have same length")
        
        if metadata and len(metadata) != len(vectors):
            raise ValueError("metadata must have same length as vectors")
        
        payload = {
            "vectors": vectors,
            "ids": ids
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        logger.info(f"Inserting {len(vectors)} vectors into '{index_name}'")
        return self._make_request(
            'POST',
            f'/api/v1/index/{index_name}/insert',
            json=payload
        )
    
    def search(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search for similar vectors
        
        Args:
            index_name: Index to search
            query_vector: Query embedding
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        payload = {
            "vector": query_vector,
            "top_k": top_k
        }
        
        if filters:
            payload["filters"] = filters
        
        logger.debug(f"Searching index '{index_name}' with top_k={top_k}")
        response = self._make_request(
            'POST',
            f'/api/v1/index/{index_name}/search',
            json=payload
        )
        
        # Parse results
        results = []
        for item in response.get('results', []):
            results.append(SearchResult(
                id=item['id'],
                score=item['score'],
                metadata=item.get('metadata', {}),
                vector=item.get('vector')
            ))
        
        return results
    
    def get_vector(self, index_name: str, vector_id: str) -> Optional[Dict]:
        """
        Retrieve a specific vector by ID
        
        Args:
            index_name: Index name
            vector_id: Vector ID
            
        Returns:
            Vector data or None if not found
        """
        try:
            return self._make_request(
                'GET',
                f'/api/v1/index/{index_name}/vector/{vector_id}'
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def delete_vectors(
        self,
        index_name: str,
        ids: List[str]
    ) -> Dict:
        """
        Delete vectors by IDs
        
        Args:
            index_name: Index name
            ids: List of vector IDs to delete
            
        Returns:
            Response data
        """
        payload = {"ids": ids}
        logger.info(f"Deleting {len(ids)} vectors from '{index_name}'")
        return self._make_request(
            'DELETE',
            f'/api/v1/index/{index_name}/delete',
            json=payload
        )
    
    def get_index_stats(self, index_name: str) -> Dict:
        """
        Get statistics about an index
        
        Args:
            index_name: Index name
            
        Returns:
            Index statistics
        """
        return self._make_request('GET', f'/api/v1/index/{index_name}/stats')


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = EndeeClient()
    
    # Health check
    if client.health_check():
        print("✓ Endee is healthy")
    
    # Create index
    client.create_index(
        index_name="test_index",
        vector_dim=384,
        metric_type="cosine"
    )
    
    # Insert sample vectors
    import numpy as np
    vectors = np.random.rand(10, 384).tolist()
    ids = [f"vec_{i}" for i in range(10)]
    metadata = [{"text": f"Sample text {i}"} for i in range(10)]
    
    client.insert_vectors("test_index", vectors, ids, metadata)
    
    # Search
    query_vector = np.random.rand(384).tolist()
    results = client.search("test_index", query_vector, top_k=5)
    
    for result in results:
        print(f"ID: {result.id}, Score: {result.score:.4f}")
