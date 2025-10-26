"""Vector database implementation using ChromaDB."""

from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
import numpy as np
import json
from pathlib import Path


class MusicVectorDB:
    """Vector database for music embeddings and metadata."""

    def __init__(self, persist_dir: str = "./data/chromadb"):
        """
        Initialize vector database.

        Args:
            persist_dir: Directory to persist the database
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create collections for text and audio embeddings
        self.text_collection = self.client.get_or_create_collection(
            name="music_text_embeddings",
            metadata={"description": "Text embeddings for music items"}
        )

        self.audio_collection = self.client.get_or_create_collection(
            name="music_audio_embeddings",
            metadata={"description": "Audio embeddings for music items"}
        )

    def add_music_item(
        self,
        id: str,
        text_embedding: Optional[np.ndarray] = None,
        audio_embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a music item to the database.

        Args:
            id: Unique identifier for the music item
            text_embedding: Text embedding vector
            audio_embedding: Audio embedding vector
            metadata: Metadata dictionary
        """
        # Convert metadata lists to JSON strings for ChromaDB
        chroma_metadata = self._prepare_metadata(metadata) if metadata else {}

        # Add text embedding
        if text_embedding is not None:
            self.text_collection.add(
                ids=[id],
                embeddings=[text_embedding.tolist()],
                metadatas=[chroma_metadata]
            )

        # Add audio embedding
        if audio_embedding is not None:
            self.audio_collection.add(
                ids=[id],
                embeddings=[audio_embedding.tolist()],
                metadatas=[chroma_metadata]
            )

    def add_batch(
        self,
        ids: List[str],
        text_embeddings: Optional[List[np.ndarray]] = None,
        audio_embeddings: Optional[List[np.ndarray]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Add multiple music items in batch.

        Args:
            ids: List of unique identifiers
            text_embeddings: List of text embedding vectors
            audio_embeddings: List of audio embedding vectors
            metadatas: List of metadata dictionaries
        """
        chroma_metadatas = [self._prepare_metadata(m) for m in metadatas] if metadatas else None

        if text_embeddings is not None:
            self.text_collection.add(
                ids=ids,
                embeddings=[emb.tolist() for emb in text_embeddings],
                metadatas=chroma_metadatas
            )

        if audio_embeddings is not None:
            self.audio_collection.add(
                ids=ids,
                embeddings=[emb.tolist() for emb in audio_embeddings],
                metadatas=chroma_metadatas
            )

    def search_by_text(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search using text embedding.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filters

        Returns:
            Search results with ids, distances, and metadatas
        """
        where = self._build_where_clause(metadata_filter) if metadata_filter else None

        results = self.text_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where
        )

        return results

    def search_by_audio(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search using audio embedding.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filters

        Returns:
            Search results with ids, distances, and metadatas
        """
        where = self._build_where_clause(metadata_filter) if metadata_filter else None

        results = self.audio_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where
        )

        return results

    def hybrid_search(
        self,
        text_embedding: Optional[np.ndarray] = None,
        audio_embedding: Optional[np.ndarray] = None,
        top_k: int = 10,
        text_weight: float = 0.5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining text and audio embeddings.

        Args:
            text_embedding: Text query embedding
            audio_embedding: Audio query embedding
            top_k: Number of results to return
            text_weight: Weight for text results (0-1), audio gets (1-weight)
            metadata_filter: Optional metadata filters

        Returns:
            Combined and reranked search results
        """
        results = {}

        # Search with text embedding
        if text_embedding is not None:
            text_results = self.search_by_text(text_embedding, top_k * 2, metadata_filter)
            for i, id in enumerate(text_results['ids'][0]):
                score = 1.0 / (1.0 + text_results['distances'][0][i])  # Convert distance to similarity
                results[id] = {
                    'id': id,
                    'text_score': score,
                    'audio_score': 0.0,
                    'metadata': text_results['metadatas'][0][i]
                }

        # Search with audio embedding
        if audio_embedding is not None:
            audio_results = self.search_by_audio(audio_embedding, top_k * 2, metadata_filter)
            for i, id in enumerate(audio_results['ids'][0]):
                score = 1.0 / (1.0 + audio_results['distances'][0][i])
                if id in results:
                    results[id]['audio_score'] = score
                else:
                    results[id] = {
                        'id': id,
                        'text_score': 0.0,
                        'audio_score': score,
                        'metadata': audio_results['metadatas'][0][i]
                    }

        # Combine scores
        for id in results:
            results[id]['combined_score'] = (
                text_weight * results[id]['text_score'] +
                (1 - text_weight) * results[id]['audio_score']
            )

        # Sort by combined score and return top_k
        sorted_results = sorted(
            results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:top_k]

        return sorted_results

    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata to ChromaDB-compatible format."""
        chroma_metadata = {}

        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                # Convert complex types to JSON strings
                chroma_metadata[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                chroma_metadata[key] = value
            elif value is not None:
                chroma_metadata[key] = str(value)

        return chroma_metadata

    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        where_conditions = []

        for key, value in filters.items():
            if isinstance(value, list):
                # OR condition for lists
                where_conditions.append({key: {"$in": value}})
            else:
                where_conditions.append({key: value})

        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {"$and": where_conditions}
        else:
            return {}

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        return {
            "text_embeddings_count": self.text_collection.count(),
            "audio_embeddings_count": self.audio_collection.count()
        }
