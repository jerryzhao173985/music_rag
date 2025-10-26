"""Text embedding generation using sentence transformers."""

from typing import List, Union
from sentence_transformers import SentenceTransformer
import numpy as np


class TextEmbedder:
    """Generate text embeddings for music descriptions and queries."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize text embedder.

        Args:
            model_name: HuggingFace model name for sentence embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text string or list of text strings

        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        return embeddings

    def embed_music_item(self, title: str, artist: str, description: str = "", metadata: dict = None) -> np.ndarray:
        """
        Generate embedding for a music item by combining its attributes.

        Args:
            title: Track title
            artist: Artist name
            description: Track description
            metadata: Additional metadata dict

        Returns:
            Single embedding vector
        """
        # Combine textual information
        parts = [f"Title: {title}", f"Artist: {artist}"]

        if description:
            parts.append(f"Description: {description}")

        if metadata:
            if metadata.get("genre"):
                parts.append(f"Genre: {metadata['genre']}")
            if metadata.get("mood"):
                moods = ", ".join(metadata["mood"]) if isinstance(metadata["mood"], list) else metadata["mood"]
                parts.append(f"Mood: {moods}")
            if metadata.get("cultural_origin"):
                parts.append(f"Cultural Origin: {metadata['cultural_origin']}")
            if metadata.get("instrumentation"):
                instruments = ", ".join(metadata["instrumentation"]) if isinstance(metadata["instrumentation"], list) else metadata["instrumentation"]
                parts.append(f"Instruments: {instruments}")

        combined_text = " | ".join(parts)
        embedding = self.embed(combined_text)

        return embedding[0]  # Return single vector
