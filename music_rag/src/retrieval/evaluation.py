"""Evaluation metrics for retrieval performance."""

from typing import List, Set
import numpy as np
from sklearn.metrics import ndcg_score


def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Precision@K.

    Args:
        retrieved_ids: List of retrieved item IDs (in order)
        relevant_ids: Set of relevant item IDs
        k: Number of top results to consider

    Returns:
        Precision@K score (0-1)
    """
    if k <= 0 or not retrieved_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for id in top_k if id in relevant_ids)

    return relevant_count / k


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Recall@K.

    Args:
        retrieved_ids: List of retrieved item IDs (in order)
        relevant_ids: Set of relevant item IDs
        k: Number of top results to consider

    Returns:
        Recall@K score (0-1)
    """
    if not relevant_ids or not retrieved_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for id in top_k if id in relevant_ids)

    return relevant_count / len(relevant_ids)


def mean_reciprocal_rank(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).

    Args:
        retrieved_ids: List of retrieved item IDs (in order)
        relevant_ids: Set of relevant item IDs

    Returns:
        MRR score
    """
    for i, id in enumerate(retrieved_ids, 1):
        if id in relevant_ids:
            return 1.0 / i

    return 0.0


def ndcg_at_k(retrieved_ids: List[str], relevance_scores: dict, k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.

    Args:
        retrieved_ids: List of retrieved item IDs (in order)
        relevance_scores: Dict mapping item IDs to relevance scores
        k: Number of top results to consider

    Returns:
        nDCG@K score (0-1)
    """
    if not retrieved_ids or not relevance_scores:
        return 0.0

    # Get relevance scores for retrieved items
    top_k = retrieved_ids[:k]
    y_true = [[relevance_scores.get(id, 0) for id in top_k]]
    y_pred = [[i for i in range(len(top_k), 0, -1)]]  # Position-based scores

    try:
        return ndcg_score(y_true, y_pred)
    except:
        return 0.0


def evaluate_retrieval(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    relevance_scores: dict = None,
    k_values: List[int] = [1, 5, 10]
) -> dict:
    """
    Comprehensive retrieval evaluation.

    Args:
        retrieved_ids: List of retrieved item IDs (in order)
        relevant_ids: Set of relevant item IDs
        relevance_scores: Optional dict mapping item IDs to relevance scores
        k_values: List of K values to evaluate

    Returns:
        Dictionary with evaluation metrics
    """
    results = {}

    for k in k_values:
        results[f'precision@{k}'] = precision_at_k(retrieved_ids, relevant_ids, k)
        results[f'recall@{k}'] = recall_at_k(retrieved_ids, relevant_ids, k)

        if relevance_scores:
            results[f'ndcg@{k}'] = ndcg_at_k(retrieved_ids, relevance_scores, k)

    results['mrr'] = mean_reciprocal_rank(retrieved_ids, relevant_ids)

    return results
