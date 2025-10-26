"""Tests for vector database."""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
from music_rag.src.database.vector_db import MusicVectorDB


class TestMusicVectorDB:
    """Tests for MusicVectorDB."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def db(self, temp_db_path):
        """Create database instance."""
        return MusicVectorDB(temp_db_path)

    def test_initialization(self, db):
        """Test database initialization."""
        assert db is not None
        assert db.text_collection is not None
        assert db.audio_collection is not None

    def test_add_single_item(self, db):
        """Test adding a single music item."""
        text_emb = np.random.rand(384)
        db.add_music_item(
            id="test_1",
            text_embedding=text_emb,
            metadata={"genre": "Jazz", "mood": "relaxed"}
        )

        stats = db.get_stats()
        assert stats["text_embeddings_count"] == 1

    def test_add_batch(self, db):
        """Test batch adding items."""
        n_items = 5
        ids = [f"item_{i}" for i in range(n_items)]
        text_embs = [np.random.rand(384) for _ in range(n_items)]
        metadatas = [{"genre": f"Genre_{i}"} for i in range(n_items)]

        db.add_batch(
            ids=ids,
            text_embeddings=text_embs,
            metadatas=metadatas
        )

        stats = db.get_stats()
        assert stats["text_embeddings_count"] == n_items

    def test_search_by_text(self, db):
        """Test text-based search."""
        # Add some items
        for i in range(3):
            text_emb = np.random.rand(384)
            db.add_music_item(
                id=f"item_{i}",
                text_embedding=text_emb,
                metadata={"genre": "Rock"}
            )

        # Search
        query_emb = np.random.rand(384)
        results = db.search_by_text(query_emb, top_k=2)

        assert "ids" in results
        assert len(results["ids"][0]) == 2

    def test_hybrid_search(self, db):
        """Test hybrid search with text and audio."""
        # Add items with both text and audio embeddings
        for i in range(3):
            text_emb = np.random.rand(384)
            audio_emb = np.random.rand(120)  # 40*3
            db.add_music_item(
                id=f"item_{i}",
                text_embedding=text_emb,
                audio_embedding=audio_emb,
                metadata={"genre": "Pop"}
            )

        # Hybrid search
        text_query = np.random.rand(384)
        audio_query = np.random.rand(120)
        results = db.hybrid_search(
            text_embedding=text_query,
            audio_embedding=audio_query,
            top_k=2,
            text_weight=0.7
        )

        assert len(results) == 2
        assert "combined_score" in results[0]

    def test_metadata_filtering(self, db):
        """Test search with metadata filters."""
        # Add items with different genres
        for i, genre in enumerate(["Jazz", "Rock", "Pop"]):
            text_emb = np.random.rand(384)
            db.add_music_item(
                id=f"item_{i}",
                text_embedding=text_emb,
                metadata={"genre": genre}
            )

        # Search with filter
        query_emb = np.random.rand(384)
        results = db.search_by_text(
            query_emb,
            top_k=10,
            metadata_filter={"genre": "Jazz"}
        )

        # Should only return Jazz items
        assert len(results["ids"][0]) <= 1
