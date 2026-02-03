# Quick Start Guide

Get your Endee RAG system running in 5 minutes!

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- 4GB+ RAM

## Step-by-Step Setup

### 1. Start Endee Database (1 minute)

```bash
# Start Endee using Docker Compose
docker-compose up -d

# Verify it's running
curl http://localhost:8080/health
# Expected: {"status":"healthy"}
```

### 2. Set Up Python Environment (2 minutes)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment (30 seconds)

```bash
# Copy environment template
cp .env.example .env

# Edit if needed (defaults work fine)
nano .env
```

### 4. Initialize Index (30 seconds)

```bash
# Create vector index in Endee
python scripts/setup_index.py
```

### 5. Load Sample Documents (1 minute)

```bash
# Process and index sample documents
python scripts/ingest_documents.py
```

### 6. Run the Application! (30 seconds)

```bash
# Start web interface
streamlit run app/streamlit_app.py
```

🎉 **Done!** Open http://localhost:8501 in your browser

## Quick Test

Try asking these questions:

- "What is machine learning?"
- "Explain neural networks"
- "What are the types of AI?"
- "How does deep learning work?"

## Next Steps

### Add Your Own Documents

1. Place your documents in `data/documents/`
   - Supported formats: PDF, DOCX, TXT, MD

2. Run ingestion:
   ```bash
   python scripts/ingest_documents.py
   ```

3. Query your documents in the web interface!

### Use Python API

```python
from src.endee_client import EndeeClient
from src.document_processor import DocumentProcessor
from src.rag_engine import RAGEngine

# Initialize
client = EndeeClient()
processor = DocumentProcessor()
rag = RAGEngine(client, processor)

# Query
response = rag.query("Your question here")
print(response.answer)
```

## Troubleshooting

### Endee won't start
```bash
# Check if port 8080 is in use
lsof -i :8080

# Restart Docker
docker-compose down
docker-compose up -d
```

### Installation errors
```bash
# Update pip
pip install --upgrade pip

# Install with no cache
pip install --no-cache-dir -r requirements.txt
```

### Model download slow
The first run downloads the embedding model (~80MB). Be patient!

## Common Commands

```bash
# Check Endee health
curl http://localhost:8080/health

# List indices
curl http://localhost:8080/api/v1/index/list

# Stop Endee
docker-compose down

# View logs
docker-compose logs -f

# Run tests
pytest tests/ -v
```

## Architecture Overview

```
User Question
     ↓
[Embedding Model] → Query Vector
     ↓
[Endee Search] → Top-K Documents
     ↓
[Context Assembly]
     ↓
[Answer Generation] → Final Answer
```

## Performance Tips

1. **Chunk Size**: Adjust in `.env` for better retrieval
   ```
   CHUNK_SIZE=512
   CHUNK_OVERLAP=50
   ```

2. **Top-K**: Increase for more context
   ```python
   response = rag.query("question", top_k=10)
   ```

3. **Index Type**: HNSW is fast, tune for your use case

## Project Structure

```
endee-rag-project/
├── app/              # Web interface
├── src/              # Core code
├── scripts/          # Setup scripts
├── data/             # Documents
├── tests/            # Test suite
└── docker-compose.yml
```

## Support

- 📚 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/yourusername/endee-rag-project/issues)
- 💬 [Discussions](https://github.com/yourusername/endee-rag-project/discussions)

---

**Built with ❤️ for Endee.io Campus Placement**
