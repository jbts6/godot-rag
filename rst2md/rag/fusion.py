"""RRF fusion and rerank for search results.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""
from dataclasses import replace
from typing import List

from rag.models import SearchResult
from rag.query_plan import QueryPlan


def rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]:
    """Fuse FTS5 and vector search results using Reciprocal Rank Fusion.

    Args:
        fts_results: FTS5 results with 'id' key.
        vec_results: Vector results with 'id' and 'distance' keys.
        k: RRF parameter (default 60).

    Returns:
        Fused results sorted by RRF score, with 'rrf_score' key added.
    """
    scores = {}

    for rank, result in enumerate(fts_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    for rank, result in enumerate(vec_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    results = []
    for chunk_id in sorted_ids:
        result = next((r for r in fts_results if r['id'] == chunk_id), None)
        if result is None:
            result = next((r for r in vec_results if r['id'] == chunk_id), None)
        if result:
            result = dict(result)
            result['rrf_score'] = scores[chunk_id]
            results.append(result)

    return results


def _rerank_bonus(plan: QueryPlan, result: SearchResult) -> float:
    bonus = 0.0
    if result.symbol in plan.alias_symbol_candidates:
        bonus += 5.0
    elif result.symbol in plan.symbol_candidates:
        bonus += 2.0
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        bonus += 0.05
    if plan.addon_intent and result.doc_type == "addon":
        bonus += 0.5
    return bonus


def rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]:
    boosted = [
        replace(result, score=result.score + _rerank_bonus(plan, result))
        for result in results
    ]
    return sorted(boosted, key=lambda result: result.score, reverse=True)
