"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

# Import and initialize app components
from music_rag import api
from music_rag.src.database.vector_db import MusicVectorDB
from music_rag.src.embeddings.text_embedder import TextEmbedder
from music_rag.src.embeddings.audio_embedder import AudioEmbedder
from music_rag.src.retrieval.retrieval_engine import RetrievalEngine


@pytest.fixture(scope="session")
def temp_db_dir():
    """Create temporary directory for test database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def initialized_app(temp_db_dir):
    """Initialize the FastAPI app with proper components for testing."""
    # Initialize components
    api.db = MusicVectorDB(temp_db_dir)
    api.text_embedder = TextEmbedder()
    api.audio_embedder = AudioEmbedder()
    api.retrieval_engine = RetrievalEngine(api.db, api.text_embedder, api.audio_embedder)
    api.music_items_cache = {}

    yield api.app

    # Cleanup
    api.db = None
    api.text_embedder = None
    api.audio_embedder = None
    api.retrieval_engine = None
    api.music_items_cache = {}


@pytest.fixture
def client(initialized_app):
    """Create test client with initialized app."""
    return TestClient(initialized_app)
