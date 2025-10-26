# Music RAG - Complete Usage Guide

## 🚀 Getting Started

### Quick Start (30 seconds)

```bash
# 1. Setup
make dev
source venv/bin/activate

# 2. Run
python quickstart.py
```

## 📋 Usage Methods

### 1. Command Line Interface (CLI)

#### Initialize System

```bash
# Load sample data
python -m music_rag.cli init-sample-data

# Or use make command
make init-data
```

#### Search for Music

```bash
# Basic search
python -m music_rag.cli search "upbeat energetic music"

# Search with filters
python -m music_rag.cli search "meditative music" \
  --genre "Indian Classical" \
  --top-k 5

# Search with mood filter
python -m music_rag.cli search "relaxing piano" \
  --mood "calm"
```

#### View Statistics

```bash
python -m music_rag.cli stats
```

#### Interactive Demo

```bash
python -m music_rag.cli demo
```

### 2. Python API

#### Basic Usage

```python
from music_rag.cli import MusicRAGSystem
from music_rag.src.models.music_item import RetrievalQuery

# Initialize system
system = MusicRAGSystem()

# Load sample data
from music_rag.src.data.sample_data_generator import generate_sample_music_data
sample_items = generate_sample_music_data()
system.index_music_items(sample_items)

# Search
query = RetrievalQuery(
    text_query="energetic dance music",
    top_k=5
)
results = system.search(query)

# Display results
for result in results:
    print(f"{result.music_item.title} - {result.music_item.artist}")
    print(f"Score: {result.score:.3f}")
```

#### Advanced Queries

```python
# Query with metadata filters
query = RetrievalQuery(
    text_query="spiritual meditation",
    top_k=10,
    genre_filter=["Indian Classical", "Middle Eastern"],
    mood_filter=["meditative", "calm"],
    use_broad_retrieval=True,
    use_targeted_retrieval=True,
    semantic_weight=0.7
)

results = system.search(query)
```

#### Custom Music Items

```python
from music_rag.src.models.music_item import MusicItem, MusicMetadata

# Create custom item
my_song = MusicItem(
    id="my_song_1",
    title="Summer Breeze",
    artist="Jane Doe",
    description="A refreshing summer melody",
    metadata=MusicMetadata(
        genre="Pop",
        subgenre="Indie Pop",
        tempo=125.0,
        key="G major",
        instrumentation=["guitar", "piano", "drums"],
        mood=["happy", "uplifting", "light"],
        cultural_origin="American",
        duration=240.0
    )
)

# Index it
system.index_music_items([my_song])
```

### 3. REST API

#### Start API Server

```bash
# Development mode
make run-api

# Or directly
python -m uvicorn music_rag.api:app --reload

# Production mode
uvicorn music_rag.api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### API Endpoints

**1. Search for Music**

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "text_query": "upbeat jazz",
    "top_k": 5,
    "genre_filter": ["Jazz"],
    "semantic_weight": 0.7
  }'
```

**2. Index Single Item**

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "id": "song_123",
    "title": "My Song",
    "artist": "Artist Name",
    "description": "A beautiful melody",
    "metadata": {
      "genre": "Pop",
      "mood": ["happy", "uplifting"],
      "tempo": 120.0
    }
  }'
```

**3. Batch Index**

```bash
curl -X POST http://localhost:8000/index/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '[
    {
      "id": "song_1",
      "title": "Song 1",
      "artist": "Artist 1",
      "metadata": {"genre": "Rock"}
    },
    {
      "id": "song_2",
      "title": "Song 2",
      "artist": "Artist 2",
      "metadata": {"genre": "Jazz"}
    }
  ]'
```

**4. Get Item**

```bash
curl http://localhost:8000/item/song_123 \
  -H "X-API-Key: your-api-key"
```

**5. Get Statistics**

```bash
curl http://localhost:8000/stats \
  -H "X-API-Key: your-api-key"
```

**6. Health Check**

```bash
curl http://localhost:8000/health
```

#### API Documentation

Access interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. Docker Usage

#### Build and Run

```bash
# Build
docker build -t music-rag:latest .

# Run
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e API_KEY=your-secret-key \
  music-rag:latest
```

#### Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 5. Jupyter Notebook

```bash
# Start Jupyter
jupyter notebook

# Open
notebooks/demo_notebook.ipynb
```

## 🎯 Common Use Cases

### Use Case 1: Music Discovery

```python
# Find similar music
query = RetrievalQuery(
    text_query="music similar to Miles Davis",
    top_k=10,
    genre_filter=["Jazz"]
)
results = system.search(query)
```

### Use Case 2: Mood-Based Recommendation

```python
# Find music for specific mood
query = RetrievalQuery(
    text_query="relaxing background music for studying",
    mood_filter=["calm", "peaceful"],
    top_k=20
)
results = system.search(query)
```

### Use Case 3: Cultural Exploration

```python
# Explore music from specific cultures
query = RetrievalQuery(
    text_query="traditional percussion instruments",
    cultural_origin_filter=["West African", "Indian"],
    top_k=15
)
results = system.search(query)
```

### Use Case 4: Live Performance Search

```python
# Find live performances
query = RetrievalQuery(
    text_query="epic stadium performance",
    metadata_filter={"is_live_performance": True},
    top_k=10
)
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# Required
CHROMADB_PATH=./data/chromadb

# Optional
ENVIRONMENT=production
API_KEY=your-secret-api-key
LOG_LEVEL=INFO
DEFAULT_TOP_K=10
```

### Programmatic Configuration

```python
from music_rag.config import settings

# Access settings
print(settings.text_model)
print(settings.api_port)

# Check environment
if settings.is_production:
    # Production-specific logic
    pass
```

## 📊 Evaluation

### Built-in Metrics

```python
from music_rag.src.retrieval.evaluation import evaluate_retrieval

# Define ground truth
retrieved_ids = ['song_1', 'song_2', 'song_3']
relevant_ids = {'song_1', 'song_3', 'song_5'}

# Evaluate
metrics = evaluate_retrieval(
    retrieved_ids=retrieved_ids,
    relevant_ids=relevant_ids,
    k_values=[1, 5, 10]
)

print(f"Precision@5: {metrics['precision@5']}")
print(f"Recall@5: {metrics['recall@5']}")
print(f"MRR: {metrics['mrr']}")
```

## 🧪 Testing

### Run Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
./venv/bin/pytest tests/test_embeddings.py -v
```

### Write Custom Tests

```python
import pytest
from music_rag.src.embeddings.text_embedder import TextEmbedder

def test_custom_embedding():
    embedder = TextEmbedder()
    embedding = embedder.embed("test music")
    assert embedding.shape[1] == embedder.embedding_dim
```

## 🚀 Performance Tips

### 1. Batch Processing

```python
# Bad: One at a time
for item in items:
    system.index_music_items([item])

# Good: Batch processing
system.index_music_items(items)
```

### 2. Caching

```bash
# Enable caching
export CACHE_ENABLED=true
export CACHE_TTL=3600
```

### 3. Optimize Query

```python
# Use targeted retrieval for specific needs
query = RetrievalQuery(
    text_query="jazz",
    use_broad_retrieval=False,  # Skip broad search
    use_targeted_retrieval=True,
    genre_filter=["Jazz"]  # Direct filter
)
```

## 🐛 Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

### Check Database

```python
# Get stats
stats = system.db.get_stats()
print(f"Items indexed: {stats['text_embeddings_count']}")

# Check specific item
item = system.music_items_cache.get('song_id')
print(item)
```

## 📱 Integration Examples

### Web Application

```javascript
// Frontend (JavaScript)
async function searchMusic(query) {
  const response = await fetch('http://localhost:8000/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
      text_query: query,
      top_k: 10
    })
  });

  const results = await response.json();
  return results;
}
```

### Mobile App (React Native)

```javascript
import axios from 'axios';

const searchMusic = async (query) => {
  try {
    const response = await axios.post(
      'https://api.musicrag.com/search',
      {
        text_query: query,
        top_k: 5
      },
      {
        headers: {
          'X-API-Key': 'your-api-key'
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Search failed:', error);
  }
};
```

## 📖 Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [Development Guide](DEVELOPMENT.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Project Summary](PROJECT_SUMMARY.md)

## 💡 Tips and Best Practices

1. **Always use batch operations** for multiple items
2. **Enable caching** in production for better performance
3. **Use metadata filters** to narrow search scope
4. **Monitor database size** and clean up periodically
5. **Rotate API keys** regularly in production
6. **Use semantic_weight** to balance text vs audio relevance
7. **Test queries** with demo data before production
8. **Monitor logs** for error patterns
9. **Use health checks** in production deployments
10. **Keep embeddings model consistent** across environments

---

**Need Help?**
- GitHub Issues: Report bugs and request features
- Documentation: Read comprehensive guides
- Community: Join our discussions

**Happy Music Discovery! 🎵**
