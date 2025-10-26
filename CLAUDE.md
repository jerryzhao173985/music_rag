# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Music RAG is a music-domain Retrieval-Augmented Generation system that enhances music discovery through dual-track retrieval, multimodal embeddings (text + audio), and diverse vector databases. The system addresses limitations of general LLMs in music-specific knowledge.

## Development Commands

### Environment Setup
```bash
# Create venv and install dependencies
make install
# OR manually:
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
./venv/bin/pytest tests/test_embeddings.py -v

# Run single test
./venv/bin/pytest tests/test_api.py::test_search_endpoint -v

# Run tests by marker
./venv/bin/pytest -m unit          # Unit tests only
./venv/bin/pytest -m "not slow"    # Skip slow tests
```

### Running the Application
```bash
# Initialize sample data
make init-data

# Run quickstart demo
make run-demo

# Run FastAPI server (port 8000)
make run-api
# OR directly:
./venv/bin/python -m uvicorn music_rag.api:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality
```bash
# Lint code
make lint

# Format code (black + isort)
make format
```

### Docker
```bash
# Build Docker image
make docker-build

# Run with docker-compose
make docker-run

# View logs
make docker-logs

# Stop containers
make docker-stop
```

## Architecture

### High-Level Flow
```
User Query → Embeddings → Vector DB → Retrieval Engine → Results
                ↓              ↓            ↓
           Text/Audio     ChromaDB    Dual-Track
```

### Core Components

**1. Dual-Track Retrieval Strategy** (`src/retrieval/retrieval_engine.py`)
- **Broad Retrieval**: Casts wide net without metadata filtering
  - Retrieves `top_k * 2` candidates
  - Uses pure semantic similarity
  - Returns results marked as `retrieval_type='broad'`
- **Targeted Retrieval**: Applies metadata constraints
  - Uses metadata filters (genre, mood, cultural_origin, tempo_range)
  - Scores are boosted by 20% (`score * 1.2`)
  - Returns results marked as `retrieval_type='targeted'`
- **Hybrid Combination**: Merges and deduplicates results from both tracks

**2. Multimodal Embeddings**
- **Text**: `src/embeddings/text_embedder.py` uses Sentence Transformers (`all-MiniLM-L6-v2`, 384-dim)
  - Combines title, artist, description, and metadata into rich text
- **Audio**: `src/embeddings/audio_embedder.py` uses librosa for basic features
  - Extracts MFCCs, chroma features, spectral characteristics
  - **Extension Point**: Replace with CLAP or MuLan for production

**3. Vector Database** (`src/database/vector_db.py`)
- ChromaDB with separate collections for text and audio embeddings
- Supports hybrid search combining both modalities with configurable weights
- Metadata filtering via ChromaDB's `where` clause

**4. Data Models** (`src/models/music_item.py`)
- `MusicItem`: Main data structure with embeddings and metadata
- `MusicMetadata`: Genre, mood, tempo, instrumentation, cultural_origin, live performance info
- `RetrievalQuery`: Query parameters with filters and strategy flags
- `QueryResult`: Result wrapper with score and retrieval_type

**5. API Layer** (`api.py`)
- FastAPI with lifespan management for resource initialization
- Endpoints: `/search`, `/index`, `/index/batch`, `/stats`, `/item/{item_id}`, `/health`
- Optional API key authentication via `X-API-Key` header
- CORS enabled (configurable per environment)

### Key Design Patterns

**Batch Operations for Performance**
```python
# Always prefer batch operations when indexing multiple items
db.add_batch(ids, text_embeddings, audio_embeddings, metadatas)
# NOT: for item in items: db.add_music_item(...)
```

**Music Item Cache**
The API maintains an in-memory `music_items_cache: Dict[str, MusicItem]` for fast lookups. This cache must be populated when indexing items, as the vector DB only stores embeddings and metadata, not the full MusicItem objects.

**Metadata Filter Construction**
Metadata filters are built from query parameters and applied to targeted retrieval:
```python
filters = {
    'genre': query.genre_filter,      # List of genres
    'mood': query.mood_filter[0],     # First mood (ChromaDB limitation)
    'cultural_origin': query.cultural_origin_filter
}
```

## Configuration

The system uses `music_rag/config.py` with settings loaded from environment variables:

```bash
# Key environment variables (create .env file):
CHROMADB_PATH=./data/chromadb        # Vector DB storage path
TEXT_MODEL=all-MiniLM-L6-v2          # Sentence transformer model
AUDIO_SAMPLE_RATE=22050              # Audio processing sample rate
API_KEY=your-secret-key              # Optional API authentication
API_PORT=8000                        # FastAPI server port
LOG_LEVEL=INFO                       # Logging level
```

## Testing Strategy

Tests are organized by component:
- `test_embeddings.py`: Text and audio embedding generation
- `test_database.py`: Vector DB operations and queries
- `test_api.py`: FastAPI endpoint integration tests
- `conftest.py`: Shared fixtures for test setup

**Markers**:
- `@pytest.mark.unit`: Unit tests (fast, no external dependencies)
- `@pytest.mark.integration`: Integration tests (slower, may use disk/network)
- `@pytest.mark.slow`: Long-running tests

## Extension Points

### Adding New Embedding Models
Replace the embedders in `src/embeddings/`:
- For CLAP: Use `transformers` library with `laion/clap-htsat-unfused`
- For MuLan: Integrate Google's joint audio-text embedding model
- Interface: `embed(text) -> np.ndarray` or `embed(audio_path) -> np.ndarray`

### Switching Vector Databases
The system is designed for easy DB swapping:
- ChromaDB (current): Local, embedded, good for prototyping
- Qdrant: Better scalability, HNSW indexing, production-ready
- Milvus: Large-scale deployments, GPU support
- Interface: Implement same methods as `MusicVectorDB` (`add_music_item`, `add_batch`, `hybrid_search`)

### Adding Retrieval Strategies
Extend `RetrievalEngine` with new methods:
- Cross-encoder reranking for improved precision
- Fusion-based retrieval combining multiple strategies
- Query expansion using LLMs
- Personalized retrieval with user preferences

## Common Development Tasks

### Adding a New Music Genre
1. Add sample data to `src/data/sample_data_generator.py`
2. Update metadata schema if needed in `src/models/music_item.py`
3. Test retrieval with new genre filter

### Implementing Audio File Upload
1. Add file upload endpoint in `api.py` using `UploadFile`
2. Save audio to `data/sample_music/` directory
3. Generate audio embedding via `audio_embedder.embed(audio_path)`
4. Index the new item with both text and audio embeddings

### Debugging Retrieval Results
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('music_rag')
```
Check ChromaDB query results, embedding shapes, and metadata filters.

## Performance Considerations

- **Batch indexing**: Use `/index/batch` endpoint for multiple items (max batch size configurable)
- **Embedding caching**: Consider Redis cache for frequently embedded texts
- **HNSW parameters**: ChromaDB uses HNSW by default; tune `m` and `ef_construct` for large datasets
- **Query optimization**: Broad retrieval uses 2x `top_k`; adjust multiplier based on dataset size

## Research Foundation

Based on recent research:
- **MuSTRAG** (Kwon et al., 2025): Music-specialized vector database
- **VMB** (Wang et al., 2024): Dual-track retrieval strategy
- **MuLan** (Huang et al., 2022): Audio-text joint embeddings
- **CLAP**: Contrastive Language-Audio Pretraining
