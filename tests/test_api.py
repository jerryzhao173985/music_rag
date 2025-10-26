"""Tests for FastAPI endpoints."""

import pytest
from music_rag.src.models.music_item import MusicItem, MusicMetadata

# client fixture is now provided by conftest.py


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Music RAG"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_stats_endpoint(client):
    """Test stats endpoint."""
    response = client.get("/stats")
    # Should return 200 since we initialized properly
    assert response.status_code == 200
    data = response.json()
    assert "text_embeddings_count" in data
    assert "audio_embeddings_count" in data


def test_search_endpoint(client):
    """Test search endpoint."""
    query_data = {
        "text_query": "upbeat energetic music",
        "top_k": 5
    }
    response = client.post("/search", json=query_data)

    # Should return 200 with results (may be empty if no data indexed)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_index_endpoint(client):
    """Test index endpoint."""
    music_item = {
        "id": "test_1",
        "title": "Test Song",
        "artist": "Test Artist",
        "description": "A test song",
        "metadata": {
            "genre": "Pop",
            "mood": ["happy"],
            "tempo": 120.0
        }
    }

    response = client.post("/index", json=music_item)
    # Should return 200 since we initialized properly
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["id"] == "test_1"


def test_batch_index_endpoint(client):
    """Test batch index endpoint."""
    items = [
        {
            "id": f"test_{i}",
            "title": f"Test Song {i}",
            "artist": "Test Artist",
            "metadata": {
                "genre": "Pop",
                "mood": ["happy"]
            }
        }
        for i in range(3)
    ]

    response = client.post("/index/batch", json=items)
    # Should return 200 with success count
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 3
