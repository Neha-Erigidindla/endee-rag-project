"""
RAG Engine
Combines retrieval from Endee with LLM generation
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from src.endee_client import EndeeClient, SearchResult
from src.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG system"""
    answer: str
    sources: List[SearchResult]
    query: str
    context_used: str


class RAGEngine:
    """Retrieval-Augmented Generation Engine"""
    
    def __init__(
        self,
        endee_client: EndeeClient,
        document_processor: DocumentProcessor,
        index_name: str = "documents",
        top_k: int = 5,
        use_llm: bool = False,
        llm_api_key: Optional[str] = None
    ):
        """
        Initialize RAG engine
        
        Args:
            endee_client: Endee database client
            document_processor: Document processor for embeddings
            index_name: Name of vector index to use
            top_k: Number of documents to retrieve
            use_llm: Whether to use LLM for generation
            llm_api_key: API key for LLM (OpenAI/Anthropic)
        """
        self.endee = endee_client
        self.processor = document_processor
        self.index_name = index_name
        self.top_k = top_k
        self.use_llm = use_llm
        self.llm_api_key = llm_api_key
        
        if use_llm and llm_api_key:
            self._initialize_llm()
        
        logger.info(f"Initialized RAG engine with index '{index_name}'")
    
    def _initialize_llm(self):
        """Initialize LLM client (OpenAI or Anthropic)"""
        try:
            import openai
            self.llm_client = openai.OpenAI(api_key=self.llm_api_key)
            self.llm_type = "openai"
            logger.info("Initialized OpenAI LLM")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}")
            self.use_llm = False
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Retrieve relevant documents for query
        
        Args:
            query: Search query
            top_k: Number of results (uses default if None)
            filters: Optional metadata filters
            
        Returns:
            List of relevant documents
        """
        k = top_k or self.top_k
        
        # Generate query embedding
        logger.info(f"Retrieving top-{k} documents for query: {query[:100]}...")
        query_embedding = self.processor.embed_query(query)
        
        # Search in Endee
        results = self.endee.search(
            index_name=self.index_name,
            query_vector=query_embedding,
            top_k=k,
            filters=filters
        )
        
        logger.info(f"Retrieved {len(results)} documents")
        return results
    
    def _format_context(self, results: List[SearchResult]) -> str:
        """
        Format retrieved documents into context string
        
        Args:
            results: Search results
            
        Returns:
            Formatted context
        """
        context_parts = []
        
        for i, result in enumerate(results, 1):
            text = result.metadata.get('text', '')
            source = result.metadata.get('source', 'Unknown')
            
            context_parts.append(
                f"[Document {i}] (Source: {source}, Relevance: {result.score:.3f})\n{text}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _generate_with_llm(self, query: str, context: str) -> str:
        """
        Generate answer using LLM
        
        Args:
            query: User query
            context: Retrieved context
            
        Returns:
            Generated answer
        """
        if not self.use_llm:
            return self._generate_extractive_answer(context, query)
        
        # Create prompt
        prompt = f"""You are a helpful AI assistant. Answer the question based ONLY on the provided context.
If the context doesn't contain relevant information, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            if self.llm_type == "openai":
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_extractive_answer(context, query)
    
    def _generate_extractive_answer(self, context: str, query: str) -> str:
        """
        Generate answer by extracting from context (fallback method)
        
        Args:
            context: Retrieved context
            query: User query
            
        Returns:
            Extracted answer
        """
        # Simple extractive approach: return most relevant chunks
        lines = context.split('\n')
        
        # Filter out section markers
        content_lines = [line for line in lines if line.strip() and not line.startswith('[Document')]
        
        if not content_lines:
            return "I couldn't find relevant information to answer your question."
        
        # Return first few relevant sentences
        answer = ' '.join(content_lines[:5])
        
        # Truncate if too long
        if len(answer) > 500:
            answer = answer[:500] + "..."
        
        return answer
    
    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None,
        return_sources: bool = True
    ) -> RAGResponse:
        """
        Main RAG query method
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
            filters: Optional metadata filters
            return_sources: Whether to include source documents
            
        Returns:
            RAG response with answer and sources
        """
        logger.info(f"Processing RAG query: {query[:100]}...")
        
        # Retrieve relevant documents
        results = self.retrieve(query, top_k, filters)
        
        if not results:
            return RAGResponse(
                answer="I couldn't find any relevant information in the knowledge base.",
                sources=[],
                query=query,
                context_used=""
            )
        
        # Format context
        context = self._format_context(results)
        
        # Generate answer
        answer = self._generate_with_llm(query, context)
        
        # Prepare response
        response = RAGResponse(
            answer=answer,
            sources=results if return_sources else [],
            query=query,
            context_used=context
        )
        
        logger.info(f"✓ Generated answer ({len(answer)} chars)")
        return response
    
    def batch_query(self, queries: List[str]) -> List[RAGResponse]:
        """
        Process multiple queries
        
        Args:
            queries: List of questions
            
        Returns:
            List of RAG responses
        """
        logger.info(f"Processing {len(queries)} queries in batch")
        
        responses = []
        for query in queries:
            try:
                response = self.query(query)
                responses.append(response)
            except Exception as e:
                logger.error(f"Failed to process query '{query}': {e}")
                responses.append(RAGResponse(
                    answer=f"Error processing query: {str(e)}",
                    sources=[],
                    query=query,
                    context_used=""
                ))
        
        return responses
    
    def get_similar_documents(
        self,
        document_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Find documents similar to a given document
        
        Args:
            document_id: ID of reference document
            top_k: Number of similar documents to return
            
        Returns:
            List of similar documents
        """
        # Get the reference document's vector
        doc = self.endee.get_vector(self.index_name, document_id)
        
        if not doc:
            logger.warning(f"Document {document_id} not found")
            return []
        
        # Search using its vector
        results = self.endee.search(
            index_name=self.index_name,
            query_vector=doc['vector'],
            top_k=top_k + 1  # +1 to exclude self
        )
        
        # Remove the document itself from results
        results = [r for r in results if r.id != document_id][:top_k]
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        keyword_filter: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query
            keyword_filter: Optional keyword to filter by
            top_k: Number of results
            
        Returns:
            Hybrid search results
        """
        # Get semantic results
        semantic_results = self.retrieve(query, top_k=top_k or self.top_k * 2)
        
        if not keyword_filter:
            return semantic_results[:top_k or self.top_k]
        
        # Filter by keyword in metadata
        filtered_results = []
        keyword_lower = keyword_filter.lower()
        
        for result in semantic_results:
            text = result.metadata.get('text', '').lower()
            if keyword_lower in text:
                filtered_results.append(result)
        
        return filtered_results[:top_k or self.top_k]


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    
    # Initialize components
    endee_client = EndeeClient()
    processor = DocumentProcessor()
    
    # Initialize RAG engine
    rag = RAGEngine(
        endee_client=endee_client,
        document_processor=processor,
        index_name="documents",
        top_k=5,
        use_llm=False  # Set to True if you have API key
    )
    
    # Query
    response = rag.query("What is machine learning?")
    
    print(f"Query: {response.query}")
    print(f"\nAnswer: {response.answer}")
    print(f"\nSources ({len(response.sources)}):")
    
    for i, source in enumerate(response.sources, 1):
        print(f"\n{i}. {source.metadata.get('source')} (score: {source.score:.3f})")
        print(f"   {source.metadata.get('text', '')[:100]}...")
