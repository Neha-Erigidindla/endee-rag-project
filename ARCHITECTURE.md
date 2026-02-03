# System Architecture

## Overview

The Endee RAG System is designed as a modular, scalable architecture for semantic document search and question answering. This document details the technical design, data flow, and implementation decisions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Streamlit  │  │  REST API    │  │  Jupyter Labs    │  │
│  │  Web UI     │  │  (Future)    │  │  (Analysis)      │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              RAG Engine (rag_engine.py)             │   │
│  │  • Query Processing                                 │   │
│  │  • Context Assembly                                 │   │
│  │  • Answer Generation                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌──────────────────────┐            ┌─────────────────────────┐
│  Document Processor  │            │    Endee Client         │
│  • Text Extraction   │            │  • Index Management     │
│  • Chunking          │            │  • Vector Operations    │
│  • Embedding Gen.    │            │  • Search              │
└──────────────────────┘            └─────────────────────────┘
        │                                       │
        ▼                                       ▼
┌──────────────────────┐            ┌─────────────────────────┐
│  Sentence Transformer│            │   Endee Vector DB       │
│  • all-MiniLM-L6-v2  │            │  • HNSW Index          │
│  • 384-dim vectors   │            │  • Cosine Similarity   │
└──────────────────────┘            └─────────────────────────┘
```

## Component Details

### 1. Document Processor (`document_processor.py`)

**Purpose**: Convert raw documents into vector embeddings

**Responsibilities**:
- Load documents (PDF, DOCX, TXT, MD)
- Split text into semantically meaningful chunks
- Generate embeddings using Sentence Transformers
- Manage metadata

**Key Algorithms**:

```python
# Chunking Algorithm
def chunk_text(text, chunk_size=512, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            for delimiter in ['. ', '.\n', '! ', '? ']:
                last_delim = chunk.rfind(delimiter)
                if last_delim > chunk_size * 0.5:
                    chunk = chunk[:last_delim + 1]
                    break
        
        chunks.append(chunk.strip())
        start = start + chunk_size - overlap
    
    return chunks
```

**Design Decisions**:
- **Chunk Size**: 512 characters balances context vs. precision
- **Overlap**: 50 characters prevents information loss at boundaries
- **Sentence Boundary**: Improves semantic coherence

### 2. Endee Client (`endee_client.py`)

**Purpose**: Interface with Endee vector database

**Responsibilities**:
- Manage index lifecycle (create, delete, list)
- Insert/delete vectors
- Perform similarity search
- Handle API communication

**API Endpoints Used**:
```
POST   /api/v1/index/create        - Create new index
GET    /api/v1/index/list          - List all indices
DELETE /api/v1/index/{name}        - Delete index
POST   /api/v1/index/{name}/insert - Insert vectors
POST   /api/v1/index/{name}/search - Search vectors
GET    /api/v1/index/{name}/stats  - Get statistics
```

**Error Handling**:
- Retry logic for transient failures
- Graceful degradation when service unavailable
- Detailed error logging

### 3. RAG Engine (`rag_engine.py`)

**Purpose**: Orchestrate retrieval and generation

**Workflow**:

```
User Query
    │
    ▼
Embed Query (384-dim vector)
    │
    ▼
Search Endee (Top-K retrieval)
    │
    ▼
Assemble Context
    │
    ▼
Generate Answer (Extractive or LLM)
    │
    ▼
Return Response + Sources
```

**Retrieval Strategy**:
- **Semantic Search**: Cosine similarity in vector space
- **Top-K**: Configurable (default 5)
- **Re-ranking**: Future enhancement

**Generation Strategy**:
- **Default**: Extractive summarization
- **Optional**: LLM-based generation (GPT/Claude)

### 4. Streamlit UI (`streamlit_app.py`)

**Purpose**: User-friendly web interface

**Features**:
- Interactive question answering
- Document upload and processing
- Source visualization
- System statistics
- Performance metrics

**Caching Strategy**:
```python
@st.cache_resource
def initialize_rag_system():
    # Cached to avoid re-initialization
    return RAGEngine(...)
```

## Data Flow

### Document Ingestion Flow

```
1. Upload Document (PDF/DOCX/TXT/MD)
   │
   ▼
2. Extract Text
   │ (PyPDF2, python-docx)
   ▼
3. Chunk Text
   │ (512 chars, 50 overlap)
   ▼
4. Generate Embeddings
   │ (Sentence Transformer)
   ▼
5. Store in Endee
   │ (Vector + Metadata)
   ▼
6. Ready for Search
```

### Query Processing Flow

```
1. User Question
   │
   ▼
2. Generate Query Embedding
   │ (Same model as documents)
   ▼
3. Search Endee
   │ (Cosine similarity)
   ▼
4. Retrieve Top-K Documents
   │
   ▼
5. Assemble Context
   │ (Concatenate relevant chunks)
   ▼
6. Generate Answer
   │ (Extractive or LLM)
   ▼
7. Return with Sources
```

## Database Schema

### Endee Index Structure

```
Index Name: documents
Vector Dimension: 384
Metric: cosine
Type: HNSW

Vector Entry:
{
  "id": "doc1_chunk0_a3f2b8",
  "vector": [0.1, 0.2, ..., 0.384],  // 384 dimensions
  "metadata": {
    "text": "Original chunk text...",
    "source": "document.pdf",
    "source_path": "/path/to/document.pdf",
    "chunk_index": 0,
    "total_chunks": 15,
    "char_count": 487
  }
}
```

### Metadata Design

**Why we store the text in metadata**:
- Enables context assembly without re-reading files
- Supports filtering and display
- Trade-off: Increased storage for better performance

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**
   ```python
   # Insert in batches of 100
   for i in range(0, len(vectors), 100):
       batch = vectors[i:i+100]
       client.insert_vectors(batch)
   ```

2. **Caching**
   - Model loaded once and cached
   - RAG engine singleton
   - Streamlit resource caching

3. **Vector Search**
   - HNSW index: O(log n) search time
   - Pre-filtering with metadata
   - Configurable top-k

### Expected Performance

**Hardware**: 4-core CPU, 8GB RAM, SSD

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Document Embedding | 3-5ms/doc | 200-300 docs/sec |
| Vector Insert | 0.5-1ms | 1000-2000 vectors/sec |
| Semantic Search (k=5) | 2-5ms | 200-500 queries/sec |
| End-to-End RAG | 1-2s | 0.5-1 queries/sec |

*Note: End-to-end includes optional LLM inference*

## Scalability

### Horizontal Scaling

```
┌─────────────┐     ┌─────────────┐
│  App Server │     │  App Server │
│   (RAG)     │     │   (RAG)     │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
         ┌───────▼────────┐
         │  Load Balancer │
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │   Endee Cluster│
         │  (Distributed) │
         └────────────────┘
```

### Vertical Scaling

- Increase Endee resources (CPU, RAM)
- Add more application instances
- Use GPU for embedding generation

## Security

### Authentication
- Optional token-based auth for Endee
- Environment variable management
- No hardcoded credentials

### Data Privacy
- Local deployment option
- No external API calls (except optional LLM)
- User data stays in Endee

### Input Validation
- File type checking
- Size limits
- Sanitization of queries

## Monitoring & Logging

### Logging Strategy

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Logged Events**:
- API requests/responses
- Vector operations
- Search queries
- Errors and exceptions

### Metrics (Future)

- Query latency (p50, p95, p99)
- Search accuracy
- Index size and growth
- Cache hit rates

## Testing Strategy

### Unit Tests
```
tests/
├── test_endee_client.py
├── test_document_processor.py
└── test_rag_engine.py
```

### Integration Tests
- End-to-end RAG queries
- Document ingestion pipeline
- API error handling

### Load Testing
```bash
# Simulate concurrent queries
locust -f tests/load_test.py
```

## Deployment Options

### 1. Local Development
```bash
docker-compose up
streamlit run app/streamlit_app.py
```

### 2. Cloud Deployment (AWS)
```
- EC2: Application server
- ECS: Containerized Endee
- S3: Document storage
- CloudWatch: Logging
```

### 3. Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: endee-rag
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: endee
        image: endeeio/endee-server:latest
      - name: rag-app
        image: rag-system:latest
```

## Future Enhancements

### Short-term
- [ ] REST API with FastAPI
- [ ] Advanced re-ranking
- [ ] Hybrid search (semantic + keyword)
- [ ] Better error messages

### Medium-term
- [ ] Multi-language support
- [ ] Real-time document updates
- [ ] User authentication
- [ ] Analytics dashboard

### Long-term
- [ ] Distributed indexing
- [ ] Multi-modal search (text + images)
- [ ] Federated learning
- [ ] Custom embedding fine-tuning

## Technology Decisions

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Vector DB | Pinecone, Weaviate, Endee | **Endee** | Open-source, high performance, simple API |
| Embedding | OpenAI, Cohere, ST | **Sentence Transformers** | Free, local, good quality |
| Framework | LangChain, LlamaIndex, Custom | **Custom** | Full control, learning opportunity |
| UI | Gradio, Streamlit, Flask | **Streamlit** | Rapid development, interactive |
| Language | Python, TypeScript | **Python** | ML ecosystem, team expertise |

## Conclusion

This architecture provides:
- ✅ Modular design for easy maintenance
- ✅ Scalable components
- ✅ Clear separation of concerns
- ✅ Performance optimization
- ✅ Extensibility for future features

The system demonstrates production-ready practices while remaining accessible for learning and experimentation.
