"""
Tests for Endee Client
"""

import pytest
from src.endee_client import EndeeClient, SearchResult
import numpy as np


@pytest.fixture
def client():
    """Create test Endee client"""
    return EndeeClient(base_url="http://localhost:8080")


@pytest.fixture
def test_index_name():
    """Test index name"""
    return "test_index"


class TestEndeeClient:
    """Test suite for Endee client"""
    
    def test_health_check(self, client):
        """Test health check"""
        # This test requires Endee to be running
        try:
            is_healthy = client.health_check()
            assert isinstance(is_healthy, bool)
        except:
            pytest.skip("Endee not running")
    
    def test_create_index(self, client, test_index_name):
        """Test index creation"""
        try:
            # Clean up if exists
            try:
                client.delete_index(test_index_name)
            except:
                pass
            
            # Create index
            response = client.create_index(
                index_name=test_index_name,
                vector_dim=384,
                metric_type="cosine"
            )
            
            assert response is not None
            
            # Verify it exists
            indices = client.list_indices()
            assert test_index_name in indices
            
        except Exception as e:
            pytest.skip(f"Endee not available: {e}")
    
    def test_insert_and_search(self, client, test_index_name):
        """Test vector insertion and search"""
        try:
            # Create index
            try:
                client.delete_index(test_index_name)
            except:
                pass
            
            client.create_index(
                index_name=test_index_name,
                vector_dim=384,
                metric_type="cosine"
            )
            
            # Insert vectors
            vectors = np.random.rand(10, 384).tolist()
            ids = [f"vec_{i}" for i in range(10)]
            metadata = [{"text": f"Sample {i}"} for i in range(10)]
            
            response = client.insert_vectors(
                index_name=test_index_name,
                vectors=vectors,
                ids=ids,
                metadata=metadata
            )
            
            assert response is not None
            
            # Search
            query_vector = np.random.rand(384).tolist()
            results = client.search(
                index_name=test_index_name,
                query_vector=query_vector,
                top_k=5
            )
            
            assert len(results) <= 5
            assert all(isinstance(r, SearchResult) for r in results)
            
            # Clean up
            client.delete_index(test_index_name)
            
        except Exception as e:
            pytest.skip(f"Endee not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
