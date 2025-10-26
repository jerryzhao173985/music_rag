# Development Guide

## Architecture Overview

The Music RAG system is built with modularity and extensibility in mind. Here's how the components work together:

```
User Query → Embeddings → Vector DB → Retrieval Engine → Results
                ↓              ↓            ↓
           Text/Audio     ChromaDB    Dual-Track
```

## Core Components

### 1. Embeddings (`src/embeddings/`)

**TextEmbedder** (`text_embedder.py`)
- Uses Sentence Transformers for text embeddings
- Default model: `all-MiniLM-L6-v2` (384-dim embeddings)
- Combines title, artist, description, and metadata into rich text representations

**AudioEmbedder** (`audio_embedder.py`)
- Currently uses librosa for basic audio features
- Extracts MFCCs, chroma features, and spectral characteristics
- **Extension Point**: Replace with CLAP or MuLan for production

### 2. Vector Database (`src/database/`)

**MusicVectorDB** (`vector_db.py`)
- Wraps ChromaDB for persistent vector storage
- Maintains separate collections for text and audio embeddings
- Supports hybrid search combining both modalities
- Metadata filtering via ChromaDB's where clause

**Key Methods**:
- `add_music_item()`: Index a single item
- `add_batch()`: Batch indexing for efficiency
- `hybrid_search()`: Combine text and audio embeddings with configurable weights

### 3. Retrieval (`src/retrieval/`)

**RetrievalEngine** (`retrieval_engine.py`)
- Implements dual-track retrieval strategy
- **Broad Retrieval**: Casts wide net without filters
- **Targeted Retrieval**: Applies metadata constraints
- Combines and deduplicates results with score boosting

**Evaluation** (`evaluation.py`)
- Precision@K, Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (nDCG)

### 4. Data Models (`src/models/`)

**MusicItem** (`music_item.py`)
- Main data structure for music tracks
- Includes metadata, embeddings, and descriptive information
- Pydantic models for validation and serialization

**MusicMetadata**
- Genre, mood, tempo, instrumentation
- Cultural origin, live performance info
- Extensible for additional attributes

## Extension Points

### Adding New Embedding Models

```python
# Example: Integrate CLAP embeddings
from transformers import ClapModel, ClapProcessor

class CLAPEmbedder:
    def __init__(self):
        self.model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
        self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")

    def embed_text(self, text: str):
        inputs = self.processor(text=text, return_tensors="pt")
        return self.model.get_text_features(**inputs)

    def embed_audio(self, audio_path: str):
        # Load audio and process
        inputs = self.processor(audio=audio, return_tensors="pt", sampling_rate=48000)
        return self.model.get_audio_features(**inputs)
```

### Switching Vector Databases

The system is designed to easily swap ChromaDB for Qdrant or Milvus:

```python
# src/database/qdrant_db.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantMusicDB:
    def __init__(self, url: str = "localhost:6333"):
        self.client = QdrantClient(url=url)
        self.client.create_collection(
            collection_name="music_embeddings",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    # Implement same interface as MusicVectorDB
    def add_music_item(self, ...):
        pass
```

### Adding New Retrieval Strategies

Extend `RetrievalEngine` with custom strategies:

```python
def _reranking_retrieval(self, initial_results, query_embedding):
    """Rerank results using cross-encoder."""
    from sentence_transformers import CrossEncoder

    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    scores = reranker.predict([(query, item.description) for item in initial_results])

    # Sort by reranker scores
    reranked = sorted(zip(initial_results, scores), key=lambda x: x[1], reverse=True)
    return reranked
```

## Performance Optimization

### Batch Processing

Always use batch operations for indexing:

```python
# Good - Batch indexing
ids = [item.id for item in items]
text_embeddings = [embed(item) for item in items]
db.add_batch(ids, text_embeddings)

# Bad - Individual inserts
for item in items:
    db.add_music_item(item.id, embed(item))
```

### Caching

Add Redis for embedding cache:

```python
import redis
import pickle

class CachedEmbedder:
    def __init__(self, embedder):
        self.embedder = embedder
        self.cache = redis.Redis(host='localhost', port=6379)

    def embed(self, text):
        key = f"emb:{hash(text)}"
        cached = self.cache.get(key)

        if cached:
            return pickle.loads(cached)

        embedding = self.embedder.embed(text)
        self.cache.set(key, pickle.dumps(embedding), ex=3600)
        return embedding
```

### Approximate Nearest Neighbors

For large-scale deployments, use HNSW or IVF-PQ:

```python
# ChromaDB uses HNSW by default
# For Qdrant, configure HNSW parameters:
from qdrant_client.models import HnswConfigDiff

self.client.update_collection(
    collection_name="music",
    hnsw_config=HnswConfigDiff(
        m=16,  # Number of edges per node
        ef_construct=100  # Construction time accuracy
    )
)
```

## Testing

### Unit Tests

```bash
pytest tests/test_embeddings.py -v
pytest tests/test_retrieval.py -v
```

### Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Evaluation on Custom Dataset

```python
from music_rag.src.retrieval.evaluation import evaluate_retrieval

# Your ground truth
ground_truth = {
    "query1": {"relevant_ids": {"1", "3", "5"}, "scores": {"1": 1.0, "3": 0.8}},
    # ...
}

# Run evaluation
for query_id, truth in ground_truth.items():
    results = system.search(query)
    metrics = evaluate_retrieval(
        retrieved_ids=[r.music_item.id for r in results],
        relevant_ids=truth["relevant_ids"],
        relevance_scores=truth["scores"]
    )
    print(f"{query_id}: {metrics}")
```

## API Development

To create a REST API with FastAPI:

```python
# api.py
from fastapi import FastAPI, HTTPException
from music_rag.cli import MusicRAGSystem
from music_rag.src.models.music_item import RetrievalQuery

app = FastAPI(title="Music RAG API")
system = MusicRAGSystem()

@app.post("/search")
async def search(query: RetrievalQuery):
    try:
        results = system.search(query)
        return {
            "results": [
                {
                    "id": r.music_item.id,
                    "title": r.music_item.title,
                    "artist": r.music_item.artist,
                    "score": r.score
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn api:app --reload
```

## Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY music_rag/ ./music_rag/
COPY data/ ./data/

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Create `.env` file:

```bash
# Vector DB
CHROMADB_PATH=./data/chromadb
QDRANT_URL=localhost:6333

# Embeddings
TEXT_MODEL=all-MiniLM-L6-v2
AUDIO_MODEL=clap-htsat-unfused

# API
API_KEY=your-secret-key
RATE_LIMIT=100
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions small and focused

## Debugging

Enable verbose logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('music_rag')
```

## Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Librosa Documentation](https://librosa.org/doc/latest/)
- [CLAP Model](https://huggingface.co/laion/clap-htsat-unfused)
- [MuLan Paper](https://arxiv.org/abs/2208.12415)
