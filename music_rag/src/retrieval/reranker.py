"""Cross-encoder reranking for improving retrieval precision.

Reranking uses a cross-encoder model that jointly encodes the query and each
retrieved document to compute a more accurate relevance score. This typically
improves precision@k by 20-30% compared to bi-encoder retrieval alone.

Reference: https://www.sbert.net/examples/applications/cross-encoder/README.html
"""

from typing import List, Tuple, Optional, Union
import numpy as np
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)


class MusicReranker:
    """Rerank retrieved music items using cross-encoder models."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize reranker.

        Args:
            model_name: HuggingFace cross-encoder model name
            device: Device to run model on ('cuda', 'cpu', or None for auto)
            batch_size: Batch size for reranking
        """
        logger.info(f"Loading cross-encoder model: {model_name}")

        self.model = CrossEncoder(model_name, device=device)
        self.batch_size = batch_size

        logger.info(f"Reranker model loaded on device: {self.model.device}")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        return_scores: bool = True
    ) -> Union[List[int], List[Tuple[int, float]]]:
        """
        Rerank documents based on query relevance.

        Args:
            query: Search query
            documents: List of document texts to rerank
            top_k: Return only top-k results (None = return all)
            return_scores: If True, return (index, score) tuples

        Returns:
            List of document indices (if return_scores=False) or
            List of (index, score) tuples sorted by relevance
        """
        if not documents:
            return []

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get relevance scores
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False
        )

        # Create (index, score) tuples
        results = [(idx, float(score)) for idx, score in enumerate(scores)]

        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        # Filter to top-k
        if top_k is not None:
            results = results[:top_k]

        if return_scores:
            return results
        else:
            return [idx for idx, _ in results]

    def rerank_with_items(
        self,
        query: str,
        items: List[dict],
        text_key: str = "text",
        top_k: Optional[int] = None
    ) -> List[dict]:
        """
        Rerank items (dicts) based on query relevance.

        Args:
            query: Search query
            items: List of item dicts to rerank
            text_key: Key in item dict containing text to rank
            top_k: Return only top-k results (None = return all)

        Returns:
            List of reranked items with added 'rerank_score' field
        """
        if not items:
            return []

        # Extract texts
        documents = []
        for item in items:
            if text_key in item:
                documents.append(item[text_key])
            else:
                # Fallback: stringify the item
                documents.append(str(item))

        # Rerank
        ranked_results = self.rerank(
            query=query,
            documents=documents,
            top_k=top_k,
            return_scores=True
        )

        # Reconstruct items with rerank scores
        reranked_items = []
        for idx, score in ranked_results:
            item = items[idx].copy()
            item['rerank_score'] = score
            reranked_items.append(item)

        return reranked_items


class MusicCrossEncoderReranker(MusicReranker):
    """
    Music-specific reranker that constructs better text representations
    for music items before reranking.
    """

    def create_music_text(self, item: dict) -> str:
        """
        Create rich text representation of music item for reranking.

        Args:
            item: Music item dict with title, artist, description, metadata

        Returns:
            Formatted text string
        """
        parts = []

        # Core fields
        if 'title' in item:
            parts.append(f"Title: {item['title']}")
        if 'artist' in item:
            parts.append(f"Artist: {item['artist']}")
        if 'description' in item and item['description']:
            parts.append(f"Description: {item['description']}")

        # Metadata
        metadata = item.get('metadata', {})
        if metadata:
            if metadata.get('genre'):
                parts.append(f"Genre: {metadata['genre']}")
            if metadata.get('subgenre'):
                parts.append(f"Subgenre: {metadata['subgenre']}")
            if metadata.get('mood'):
                moods = metadata['mood'] if isinstance(metadata['mood'], str) else ', '.join(metadata['mood'])
                parts.append(f"Mood: {moods}")
            if metadata.get('cultural_origin'):
                parts.append(f"Cultural Origin: {metadata['cultural_origin']}")
            if metadata.get('tempo'):
                parts.append(f"Tempo: {metadata['tempo']} BPM")
            if metadata.get('instrumentation'):
                instruments = metadata['instrumentation'] if isinstance(metadata['instrumentation'], str) else ', '.join(metadata['instrumentation'])
                parts.append(f"Instruments: {instruments}")
            if metadata.get('era'):
                parts.append(f"Era: {metadata['era']}")
            if metadata.get('key'):
                parts.append(f"Key: {metadata['key']}")

        return " | ".join(parts)

    def rerank_music_items(
        self,
        query: str,
        music_items: List[dict],
        top_k: Optional[int] = None
    ) -> List[dict]:
        """
        Rerank music items based on query relevance.

        Args:
            query: Search query
            music_items: List of music item dicts
            top_k: Return only top-k results (None = return all)

        Returns:
            List of reranked music items with 'rerank_score' field
        """
        if not music_items:
            return []

        # Create rich text representations
        documents = [self.create_music_text(item) for item in music_items]

        # Rerank
        ranked_results = self.rerank(
            query=query,
            documents=documents,
            top_k=top_k,
            return_scores=True
        )

        # Reconstruct items with rerank scores
        reranked_items = []
        for idx, score in ranked_results:
            item = music_items[idx].copy()
            item['rerank_score'] = score
            reranked_items.append(item)

        return reranked_items


class HybridScoreReranker:
    """
    Combines original retrieval scores with reranking scores for hybrid ranking.
    """

    def __init__(
        self,
        reranker: MusicReranker,
        retrieval_weight: float = 0.5,
        rerank_weight: float = 0.5
    ):
        """
        Initialize hybrid reranker.

        Args:
            reranker: Base reranker instance
            retrieval_weight: Weight for original retrieval score
            rerank_weight: Weight for reranking score
        """
        self.reranker = reranker
        self.retrieval_weight = retrieval_weight
        self.rerank_weight = rerank_weight

        # Validate weights
        if not np.isclose(retrieval_weight + rerank_weight, 1.0):
            logger.warning(
                f"Weights don't sum to 1.0: {retrieval_weight} + {rerank_weight} = "
                f"{retrieval_weight + rerank_weight}. Normalizing..."
            )
            total = retrieval_weight + rerank_weight
            self.retrieval_weight = retrieval_weight / total
            self.rerank_weight = rerank_weight / total

    def rerank_with_hybrid_scores(
        self,
        query: str,
        items: List[dict],
        text_key: str = "text",
        score_key: str = "score",
        top_k: Optional[int] = None
    ) -> List[dict]:
        """
        Rerank items using hybrid scoring (retrieval + rerank scores).

        Args:
            query: Search query
            items: List of items with original retrieval scores
            text_key: Key for text in item dict
            score_key: Key for original retrieval score
            top_k: Return only top-k results

        Returns:
            List of reranked items with 'hybrid_score' field
        """
        if not items:
            return []

        # Get rerank scores
        reranked_items = self.reranker.rerank_with_items(
            query=query,
            items=items,
            text_key=text_key,
            top_k=None  # Don't filter yet
        )

        # Normalize scores to [0, 1] range
        retrieval_scores = [item.get(score_key, 0.0) for item in reranked_items]
        rerank_scores = [item.get('rerank_score', 0.0) for item in reranked_items]

        # Min-max normalization
        def normalize(scores):
            if len(scores) == 0:
                return scores
            min_score = min(scores)
            max_score = max(scores)
            if max_score == min_score:
                return [1.0] * len(scores)
            return [(s - min_score) / (max_score - min_score) for s in scores]

        norm_retrieval = normalize(retrieval_scores)
        norm_rerank = normalize(rerank_scores)

        # Compute hybrid scores
        for i, item in enumerate(reranked_items):
            hybrid_score = (
                self.retrieval_weight * norm_retrieval[i] +
                self.rerank_weight * norm_rerank[i]
            )
            item['hybrid_score'] = hybrid_score

        # Sort by hybrid score
        reranked_items.sort(key=lambda x: x['hybrid_score'], reverse=True)

        # Filter to top-k
        if top_k is not None:
            reranked_items = reranked_items[:top_k]

        return reranked_items
