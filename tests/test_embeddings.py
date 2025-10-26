"""Tests for embedding modules."""

import pytest
import numpy as np
from music_rag.src.embeddings.text_embedder import TextEmbedder
from music_rag.src.embeddings.audio_embedder import AudioEmbedder


class TestTextEmbedder:
    """Tests for TextEmbedder."""

    @pytest.fixture
    def embedder(self):
        """Create text embedder instance."""
        return TextEmbedder()

    def test_initialization(self, embedder):
        """Test embedder initialization."""
        assert embedder is not None
        assert embedder.embedding_dim > 0

    def test_embed_single_text(self, embedder):
        """Test embedding a single text."""
        text = "This is a test song about happiness"
        embedding = embedder.embed(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == 1
        assert embedding.shape[1] == embedder.embedding_dim

    def test_embed_multiple_texts(self, embedder):
        """Test embedding multiple texts."""
        texts = ["Song 1", "Song 2", "Song 3"]
        embeddings = embedder.embed(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(texts)
        assert embeddings.shape[1] == embedder.embedding_dim

    def test_embed_music_item(self, embedder):
        """Test embedding a music item."""
        embedding = embedder.embed_music_item(
            title="Test Song",
            artist="Test Artist",
            description="A beautiful melody",
            metadata={"genre": "Pop", "mood": ["happy", "upbeat"]}
        )

        assert isinstance(embedding, np.ndarray)
        assert len(embedding.shape) == 1
        assert embedding.shape[0] == embedder.embedding_dim

    def test_deterministic_embeddings(self, embedder):
        """Test that same input produces same embedding."""
        text = "Consistent test"
        emb1 = embedder.embed(text)
        emb2 = embedder.embed(text)

        np.testing.assert_array_almost_equal(emb1, emb2)


class TestAudioEmbedder:
    """Tests for AudioEmbedder."""

    @pytest.fixture
    def embedder(self):
        """Create audio embedder instance."""
        return AudioEmbedder()

    def test_initialization(self, embedder):
        """Test embedder initialization."""
        assert embedder is not None
        assert embedder.embedding_dim > 0
        assert embedder.sr == 22050
        assert embedder.n_mfcc == 40

    def test_embedding_dimension(self, embedder):
        """Test expected embedding dimension."""
        expected_dim = embedder.n_mfcc * 3  # MFCCs + chroma + spectral
        assert embedder.embedding_dim == expected_dim
