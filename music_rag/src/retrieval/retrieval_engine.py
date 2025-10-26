"""Dual-track retrieval engine for music RAG."""

from typing import List, Optional, Dict, Any
import numpy as np
from ..database.vector_db import MusicVectorDB
from ..embeddings.text_embedder import TextEmbedder
from ..embeddings.audio_embedder import AudioEmbedder
from ..models.music_item import RetrievalQuery, QueryResult, MusicItem


class RetrievalEngine:
    """Dual-track retrieval engine combining broad and targeted search."""

    def __init__(
        self,
        vector_db: MusicVectorDB,
        text_embedder: TextEmbedder,
        audio_embedder: AudioEmbedder
    ):
        """
        Initialize retrieval engine.

        Args:
            vector_db: Vector database instance
            text_embedder: Text embedding generator
            audio_embedder: Audio embedding generator
        """
        self.db = vector_db
        self.text_embedder = text_embedder
        self.audio_embedder = audio_embedder

    def retrieve(self, query: RetrievalQuery, music_items_cache: Dict[str, MusicItem]) -> List[QueryResult]:
        """
        Execute retrieval query with dual-track strategy.

        Args:
            query: Retrieval query parameters
            music_items_cache: Cache of full MusicItem objects by ID

        Returns:
            List of QueryResult objects sorted by relevance
        """
        results = []

        # Generate embeddings
        text_emb = None
        audio_emb = None

        if query.text_query:
            text_emb = self.text_embedder.embed(query.text_query)
            if len(text_emb.shape) > 1:
                text_emb = text_emb[0]

        if query.audio_path:
            audio_emb = self.audio_embedder.embed(query.audio_path)

        # Build metadata filter
        metadata_filter = self._build_metadata_filter(query)

        # Broad retrieval - cast wider net for general candidates
        if query.use_broad_retrieval:
            broad_results = self._broad_retrieval(
                text_emb,
                audio_emb,
                query.top_k * 2,  # Retrieve more candidates
                query.semantic_weight,
                None  # No metadata filtering in broad search
            )

            for result in broad_results:
                if result['id'] in music_items_cache:
                    results.append(QueryResult(
                        music_item=music_items_cache[result['id']],
                        score=result['combined_score'],
                        retrieval_type='broad'
                    ))

        # Targeted retrieval - refine with metadata constraints
        if query.use_targeted_retrieval and metadata_filter:
            targeted_results = self._targeted_retrieval(
                text_emb,
                audio_emb,
                query.top_k,
                query.semantic_weight,
                metadata_filter
            )

            # Boost scores for targeted results
            for result in targeted_results:
                if result['id'] in music_items_cache:
                    results.append(QueryResult(
                        music_item=music_items_cache[result['id']],
                        score=result['combined_score'] * 1.2,  # Boost targeted results
                        retrieval_type='targeted'
                    ))

        # Deduplicate and sort by score
        seen_ids = set()
        unique_results = []

        for result in sorted(results, key=lambda x: x.score, reverse=True):
            if result.music_item.id not in seen_ids:
                seen_ids.add(result.music_item.id)
                unique_results.append(result)

                if len(unique_results) >= query.top_k:
                    break

        return unique_results

    def _broad_retrieval(
        self,
        text_emb: Optional[np.ndarray],
        audio_emb: Optional[np.ndarray],
        top_k: int,
        semantic_weight: float,
        metadata_filter: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute broad retrieval without strict filtering."""
        return self.db.hybrid_search(
            text_embedding=text_emb,
            audio_embedding=audio_emb,
            top_k=top_k,
            text_weight=semantic_weight,
            metadata_filter=metadata_filter
        )

    def _targeted_retrieval(
        self,
        text_emb: Optional[np.ndarray],
        audio_emb: Optional[np.ndarray],
        top_k: int,
        semantic_weight: float,
        metadata_filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute targeted retrieval with metadata filtering."""
        return self.db.hybrid_search(
            text_embedding=text_emb,
            audio_embedding=audio_emb,
            top_k=top_k,
            text_weight=semantic_weight,
            metadata_filter=metadata_filter
        )

    def _build_metadata_filter(self, query: RetrievalQuery) -> Optional[Dict[str, Any]]:
        """Build metadata filter from query parameters."""
        filters = {}

        if query.genre_filter:
            filters['genre'] = query.genre_filter

        if query.mood_filter:
            # ChromaDB doesn't support list membership well, so we'll handle this differently
            # For now, we'll use the first mood in the filter
            if query.mood_filter:
                filters['mood'] = query.mood_filter[0]

        if query.cultural_origin_filter:
            filters['cultural_origin'] = query.cultural_origin_filter

        return filters if filters else None

    def search_by_text(self, text_query: str, top_k: int = 10) -> List[QueryResult]:
        """
        Simple text-based search.

        Args:
            text_query: Text query string
            top_k: Number of results

        Returns:
            List of QueryResult objects
        """
        query = RetrievalQuery(text_query=text_query, top_k=top_k)
        return self.retrieve(query, {})

    def search_by_audio(self, audio_path: str, top_k: int = 10) -> List[QueryResult]:
        """
        Simple audio-based search.

        Args:
            audio_path: Path to audio file
            top_k: Number of results

        Returns:
            List of QueryResult objects
        """
        query = RetrievalQuery(audio_path=audio_path, top_k=top_k)
        return self.retrieve(query, {})
