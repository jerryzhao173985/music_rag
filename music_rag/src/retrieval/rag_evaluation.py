"""RAG-specific evaluation metrics for Music RAG system.

Implements comprehensive evaluation metrics beyond traditional IR metrics,
including context relevance, faithfulness, and answer quality.
"""

from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Comprehensive RAG evaluation metrics."""

    def __init__(self, embedder=None):
        """
        Initialize evaluator.

        Args:
            embedder: Optional embedder for semantic similarity calculations
        """
        self.embedder = embedder

    def context_precision(
        self,
        retrieved_items: List[Dict],
        ground_truth_relevant: List[str],
        k: int = 10
    ) -> float:
        """
        Compute Context Precision@K: % of retrieved items that are relevant.

        Args:
            retrieved_items: List of retrieved items (with 'id' field)
            ground_truth_relevant: List of IDs that are known to be relevant
            k: Number of top results to consider

        Returns:
            Context precision score (0-1)
        """
        if not retrieved_items or not ground_truth_relevant:
            return 0.0

        retrieved_ids = [item.get('id') for item in retrieved_items[:k]]
        relevant_retrieved = sum(1 for rid in retrieved_ids if rid in ground_truth_relevant)

        return relevant_retrieved / min(k, len(retrieved_items))

    def context_recall(
        self,
        retrieved_items: List[Dict],
        ground_truth_relevant: List[str],
        k: int = 10
    ) -> float:
        """
        Compute Context Recall@K: % of relevant items that were retrieved.

        Args:
            retrieved_items: List of retrieved items (with 'id' field)
            ground_truth_relevant: List of IDs that are known to be relevant
            k: Number of top results to consider

        Returns:
            Context recall score (0-1)
        """
        if not ground_truth_relevant:
            return 0.0

        retrieved_ids = [item.get('id') for item in retrieved_items[:k]]
        relevant_retrieved = sum(1 for gt_id in ground_truth_relevant if gt_id in retrieved_ids)

        return relevant_retrieved / len(ground_truth_relevant)

    def context_f1(
        self,
        retrieved_items: List[Dict],
        ground_truth_relevant: List[str],
        k: int = 10
    ) -> float:
        """
        Compute Context F1 score (harmonic mean of precision and recall).

        Args:
            retrieved_items: List of retrieved items
            ground_truth_relevant: List of relevant item IDs
            k: Number of top results to consider

        Returns:
            F1 score (0-1)
        """
        precision = self.context_precision(retrieved_items, ground_truth_relevant, k)
        recall = self.context_recall(retrieved_items, ground_truth_relevant, k)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def semantic_similarity_score(
        self,
        query: str,
        retrieved_items: List[Dict],
        text_key: str = 'text',
        k: int = 10
    ) -> float:
        """
        Compute average semantic similarity between query and retrieved items.

        Args:
            query: Search query
            retrieved_items: List of retrieved items
            text_key: Key in item dict containing text
            k: Number of top results to consider

        Returns:
            Average similarity score (0-1)
        """
        if not self.embedder or not retrieved_items:
            return 0.0

        try:
            # Get query embedding
            query_emb = self.embedder.embed([query])[0]

            # Get item embeddings
            item_texts = [item.get(text_key, str(item)) for item in retrieved_items[:k]]
            item_embs = self.embedder.embed(item_texts)

            # Compute similarities
            similarities = cosine_similarity([query_emb], item_embs)[0]

            return float(np.mean(similarities))

        except Exception as e:
            logger.exception("Error computing semantic similarity")
            return 0.0

    def ranking_quality_score(
        self,
        retrieved_items: List[Dict],
        ground_truth_relevant: List[str]
    ) -> float:
        """
        Compute ranking quality using normalized discounted cumulative gain.

        Rewards systems that put relevant items higher in the ranking.

        Args:
            retrieved_items: List of retrieved items (ordered by relevance)
            ground_truth_relevant: List of relevant item IDs

        Returns:
            nDCG score (0-1)
        """
        if not retrieved_items or not ground_truth_relevant:
            return 0.0

        # Binary relevance: 1 if relevant, 0 otherwise
        retrieved_ids = [item.get('id') for item in retrieved_items]
        relevances = [1 if rid in ground_truth_relevant else 0 for rid in retrieved_ids]

        # Discounted cumulative gain
        dcg = sum(rel / np.log2(idx + 2) for idx, rel in enumerate(relevances))

        # Ideal DCG (all relevant items at the top)
        ideal_relevances = sorted(relevances, reverse=True)
        idcg = sum(rel / np.log2(idx + 2) for idx, rel in enumerate(ideal_relevances))

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def diversity_score(
        self,
        retrieved_items: List[Dict],
        diversity_key: str = 'genre'
    ) -> float:
        """
        Measure diversity of retrieved results.

        Rewards systems that retrieve diverse items rather than very similar ones.

        Args:
            retrieved_items: List of retrieved items
            diversity_key: Key in item metadata to measure diversity

        Returns:
            Diversity score (0-1, higher = more diverse)
        """
        if not retrieved_items:
            return 0.0

        # Extract diversity attribute
        attributes = []
        for item in retrieved_items:
            metadata = item.get('metadata', {})
            attr = metadata.get(diversity_key)
            if attr:
                attributes.append(attr)

        if not attributes:
            return 0.0

        # Compute diversity as ratio of unique values
        unique_attrs = len(set(attributes))
        total_attrs = len(attributes)

        return unique_attrs / total_attrs

    def coverage_score(
        self,
        all_queries: List[str],
        retrieval_results: Dict[str, List[Dict]],
        min_results: int = 1
    ) -> float:
        """
        Measure what proportion of queries returned results.

        Args:
            all_queries: List of all test queries
            retrieval_results: Dict mapping queries to their results
            min_results: Minimum number of results to count as success

        Returns:
            Coverage score (0-1)
        """
        if not all_queries:
            return 0.0

        successful_queries = sum(
            1 for query in all_queries
            if retrieval_results.get(query) and len(retrieval_results[query]) >= min_results
        )

        return successful_queries / len(all_queries)

    def latency_score(
        self,
        latencies: List[float],
        target_latency: float = 0.5
    ) -> float:
        """
        Compute latency performance score.

        Args:
            latencies: List of query latencies in seconds
            target_latency: Target latency threshold

        Returns:
            Score (0-1, higher = better performance)
        """
        if not latencies:
            return 0.0

        # Compute p95 latency
        p95_latency = np.percentile(latencies, 95)

        # Score based on how close to target
        if p95_latency <= target_latency:
            return 1.0
        else:
            # Decay score linearly
            return max(0.0, 1.0 - (p95_latency - target_latency) / target_latency)

    def comprehensive_eval(
        self,
        queries: List[str],
        retrieval_results: Dict[str, List[Dict]],
        ground_truth: Dict[str, List[str]],
        latencies: Optional[List[float]] = None,
        k: int = 10
    ) -> Dict[str, float]:
        """
        Run comprehensive evaluation across all metrics.

        Args:
            queries: List of test queries
            retrieval_results: Dict mapping queries to their retrieved items
            ground_truth: Dict mapping queries to relevant item IDs
            latencies: Optional list of query latencies
            k: Number of top results to consider

        Returns:
            Dict of metric names to scores
        """
        results = {}

        # Per-query metrics
        precisions = []
        recalls = []
        f1_scores = []
        ndcg_scores = []
        diversity_scores = []

        for query in queries:
            retrieved = retrieval_results.get(query, [])
            relevant = ground_truth.get(query, [])

            if retrieved and relevant:
                precisions.append(self.context_precision(retrieved, relevant, k))
                recalls.append(self.context_recall(retrieved, relevant, k))
                f1_scores.append(self.context_f1(retrieved, relevant, k))
                ndcg_scores.append(self.ranking_quality_score(retrieved, relevant))
                diversity_scores.append(self.diversity_score(retrieved))

        # Aggregate metrics
        results['precision@k'] = np.mean(precisions) if precisions else 0.0
        results['recall@k'] = np.mean(recalls) if recalls else 0.0
        results['f1@k'] = np.mean(f1_scores) if f1_scores else 0.0
        results['ndcg'] = np.mean(ndcg_scores) if ndcg_scores else 0.0
        results['diversity'] = np.mean(diversity_scores) if diversity_scores else 0.0

        # System-level metrics
        results['coverage'] = self.coverage_score(queries, retrieval_results)

        if latencies:
            results['latency_score'] = self.latency_score(latencies)
            results['p95_latency'] = np.percentile(latencies, 95)
            results['mean_latency'] = np.mean(latencies)

        return results


def compute_mrr(
    retrieval_results: Dict[str, List[Dict]],
    ground_truth: Dict[str, List[str]]
) -> float:
    """
    Compute Mean Reciprocal Rank.

    MRR measures the rank of the first relevant item averaged across queries.

    Args:
        retrieval_results: Dict mapping queries to retrieved items
        ground_truth: Dict mapping queries to relevant item IDs

    Returns:
        MRR score (0-1)
    """
    reciprocal_ranks = []

    for query, retrieved in retrieval_results.items():
        relevant = ground_truth.get(query, [])

        if not relevant:
            continue

        # Find rank of first relevant item
        for rank, item in enumerate(retrieved, start=1):
            if item.get('id') in relevant:
                reciprocal_ranks.append(1.0 / rank)
                break
        else:
            # No relevant item found
            reciprocal_ranks.append(0.0)

    return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0


def compute_map(
    retrieval_results: Dict[str, List[Dict]],
    ground_truth: Dict[str, List[str]],
    k: int = 10
) -> float:
    """
    Compute Mean Average Precision@K.

    MAP measures precision at each relevant item position, averaged across queries.

    Args:
        retrieval_results: Dict mapping queries to retrieved items
        ground_truth: Dict mapping queries to relevant item IDs
        k: Number of top results to consider

    Returns:
        MAP@K score (0-1)
    """
    average_precisions = []

    for query, retrieved in retrieval_results.items():
        relevant = ground_truth.get(query, [])

        if not relevant:
            continue

        retrieved = retrieved[:k]
        retrieved_ids = [item.get('id') for item in retrieved]

        # Compute precision at each relevant position
        precisions = []
        num_relevant = 0

        for i, item_id in enumerate(retrieved_ids, start=1):
            if item_id in relevant:
                num_relevant += 1
                precision_at_i = num_relevant / i
                precisions.append(precision_at_i)

        if precisions:
            average_precisions.append(np.mean(precisions))
        else:
            average_precisions.append(0.0)

    return np.mean(average_precisions) if average_precisions else 0.0


class MusicRAGBenchmark:
    """Benchmark suite for Music RAG system."""

    def __init__(self, evaluator: RAGEvaluator):
        """
        Initialize benchmark.

        Args:
            evaluator: RAGEvaluator instance
        """
        self.evaluator = evaluator

    def run_benchmark(
        self,
        rag_system,
        test_queries: List[Dict[str, Any]],
        ground_truth: Dict[str, List[str]],
        k: int = 10
    ) -> Dict[str, Any]:
        """
        Run complete benchmark on RAG system.

        Args:
            rag_system: Music RAG system to evaluate
            test_queries: List of test query dicts with 'query' and optional filters
            ground_truth: Dict mapping queries to relevant item IDs
            k: Number of top results to consider

        Returns:
            Dict with benchmark results
        """
        logger.info(f"Running benchmark with {len(test_queries)} queries")

        import time
        retrieval_results = {}
        latencies = []

        # Run all queries
        for query_dict in test_queries:
            query_text = query_dict['query']

            try:
                start = time.time()

                # Build retrieval query
                from music_rag.src.models.music_item import RetrievalQuery
                query = RetrievalQuery(
                    text_query=query_text,
                    top_k=k,
                    **{k: v for k, v in query_dict.items() if k != 'query'}
                )

                # Retrieve
                results = rag_system.search(query)

                latency = time.time() - start
                latencies.append(latency)

                # Convert to dicts
                retrieval_results[query_text] = [
                    {
                        'id': r.music_item.id,
                        'title': r.music_item.title,
                        'artist': r.music_item.artist,
                        'metadata': r.music_item.metadata.model_dump() if hasattr(r.music_item.metadata, 'model_dump') else r.music_item.metadata,
                        'score': r.score
                    }
                    for r in results
                ]

            except Exception as e:
                logger.exception(f"Error processing query '{query_text}'")
                retrieval_results[query_text] = []
                latencies.append(0.0)

        # Compute metrics
        queries = [q['query'] for q in test_queries]
        metrics = self.evaluator.comprehensive_eval(
            queries=queries,
            retrieval_results=retrieval_results,
            ground_truth=ground_truth,
            latencies=latencies,
            k=k
        )

        # Add additional metrics
        metrics['mrr'] = compute_mrr(retrieval_results, ground_truth)
        metrics['map@k'] = compute_map(retrieval_results, ground_truth, k)

        logger.info("Benchmark complete")
        logger.info(f"Precision@{k}: {metrics['precision@k']:.3f}")
        logger.info(f"Recall@{k}: {metrics['recall@k']:.3f}")
        logger.info(f"nDCG: {metrics['ndcg']:.3f}")
        logger.info(f"MRR: {metrics['mrr']:.3f}")

        return {
            'metrics': metrics,
            'retrieval_results': retrieval_results,
            'latencies': latencies,
            'summary': {
                'total_queries': len(queries),
                'successful_queries': sum(1 for r in retrieval_results.values() if r),
                'avg_latency': np.mean(latencies),
                'p95_latency': np.percentile(latencies, 95)
            }
        }
