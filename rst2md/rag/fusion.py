"""RRF fusion and rerank for search results.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""
from dataclasses import replace
from typing import List

from rag.models import RankingSignal, SearchResult
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


def _rerank_signals(plan: QueryPlan, result: SearchResult) -> list[RankingSignal]:
    """Named, non-zero rerank bonus signals.

    Mirrors the conditions and constants in :func:`_rerank_bonus` exactly so
    the bonus amounts stay in sync with the recorded signal weights.
    """
    signals: list[RankingSignal] = []
    if result.symbol in plan.alias_symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.alias_symbol",
            weight=5.0,
            value=result.symbol,
            details={"source": "alias_symbol_candidates"},
        ))
    elif result.symbol in plan.symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.direct_symbol",
            weight=2.0,
            value=result.symbol,
            details={"source": "symbol_candidates"},
        ))
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.doc_type_intent",
            weight=0.05,
            value=result.doc_type,
            details={"intent": plan.doc_type_intent},
        ))
    if plan.addon_intent and result.doc_type == "addon":
        signals.append(RankingSignal(
            name="rerank.addon_intent",
            weight=0.5,
            value=result.doc_type,
            details={"intent": plan.addon_intent},
        ))
    return signals


def rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]:
    boosted = []
    for result in results:
        bonus = _rerank_bonus(plan, result)
        # Copy the list (items are frozen dataclasses) before appending so the
        # original result's ranking_signals is not mutated across replace().
        signals = list(result.ranking_signals) + _rerank_signals(plan, result)
        boosted.append(replace(result, score=result.score + bonus, ranking_signals=signals))
    return sorted(boosted, key=lambda result: result.score, reverse=True)
