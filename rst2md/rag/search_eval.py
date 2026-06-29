from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from rag.models import SearchResult


@dataclass(frozen=True)
class GoldenQuery:
    id: str
    query: str
    category: str
    required_at: int = 5
    expected_paths: tuple[str, ...] = ()
    expected_symbols: tuple[str, ...] = ()
    expected_doc_types: tuple[str, ...] = ()
    expected_addons: tuple[str, ...] = ()
    report_only: bool = False
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryResult:
    query: GoldenQuery
    matched_rank: int | None
    passed: bool
    failure_classification: str
    observed: list[dict]
    graph_changed: bool = False


def _as_tuple(data: dict, key: str) -> tuple[str, ...]:
    value = data.get(key) or []
    return tuple(str(item) for item in value)


def load_queries(path: Path) -> list[GoldenQuery]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    queries = []
    for item in raw:
        queries.append(
            GoldenQuery(
                id=str(item["id"]),
                query=str(item["query"]),
                category=str(item["category"]),
                required_at=int(item.get("required_at", 5)),
                expected_paths=_as_tuple(item, "expected_paths"),
                expected_symbols=_as_tuple(item, "expected_symbols"),
                expected_doc_types=_as_tuple(item, "expected_doc_types"),
                expected_addons=_as_tuple(item, "expected_addons"),
                report_only=bool(item.get("report_only", False)),
                tags=_as_tuple(item, "tags"),
            )
        )
    return queries


def _result_to_observed(result: SearchResult, rank: int) -> dict:
    return {
        "rank": rank,
        "score": result.score,
        "path": result.path,
        "symbol": result.symbol,
        "doc_type": result.doc_type,
        "addon": result.addon,
        "heading": result.heading,
    }


def _matches_any(value: str, expected: tuple[str, ...]) -> bool:
    return not expected or value in expected


def result_matches(query: GoldenQuery, result: SearchResult) -> bool:
    return (
        _matches_any(result.path, query.expected_paths)
        and _matches_any(result.symbol, query.expected_symbols)
        and _matches_any(result.doc_type, query.expected_doc_types)
        and _matches_any(result.addon, query.expected_addons)
    )


def _classify_failure(query: GoldenQuery, results: Sequence[SearchResult], matched_rank: int | None) -> str:
    if matched_rank is not None and matched_rank > query.required_at:
        return "low_ranking"
    if query.expected_doc_types and any(r.doc_type not in query.expected_doc_types for r in results[: query.required_at]):
        return "filter_mismatch"
    if query.expected_addons and any(r.addon not in query.expected_addons for r in results[: query.required_at]):
        return "filter_mismatch"
    if "normalization" in query.tags or "symbol_variant" in query.tags:
        return "query_normalization"
    return "missing_recall"


def evaluate_results(query: GoldenQuery, results: Sequence[SearchResult], *, required_window: int = 10) -> QueryResult:
    matched_rank = None
    for rank, result in enumerate(results[:required_window], start=1):
        if result_matches(query, result):
            matched_rank = rank
            break
    passed = matched_rank is not None and matched_rank <= query.required_at
    observed = [_result_to_observed(result, rank) for rank, result in enumerate(results[:required_window], start=1)]
    return QueryResult(
        query=query,
        matched_rank=matched_rank,
        passed=passed,
        failure_classification="" if passed else _classify_failure(query, results, matched_rank),
        observed=observed,
    )


def _metric_summary(results: Sequence[QueryResult]) -> dict:
    gating = [result for result in results if not result.query.report_only]
    if not gating:
        return {"count": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0}

    def hit_at(k: int) -> float:
        return sum(1 for result in gating if result.matched_rank is not None and result.matched_rank <= k) / len(gating)

    mrr_total = 0.0
    for result in gating:
        if result.matched_rank is not None and result.matched_rank <= 5:
            mrr_total += 1.0 / result.matched_rank

    return {
        "count": len(gating),
        "hit@1": hit_at(1),
        "hit@3": hit_at(3),
        "hit@5": hit_at(5),
        "mrr@5": mrr_total / len(gating),
    }


def calculate_metrics(query_results: Sequence[QueryResult]) -> tuple[dict, dict]:
    overall = _metric_summary(query_results)
    categories = {}
    for result in query_results:
        categories.setdefault(result.query.category, []).append(result)
    return overall, {category: _metric_summary(results) for category, results in sorted(categories.items())}


def compare_with_baseline(
    current: dict,
    baseline: dict,
    *,
    hit5_drop_threshold: float = 0.05,
    mrr5_relative_drop_threshold: float = 0.10,
) -> tuple[bool, list[str]]:
    messages = []
    baseline_hit5 = float(baseline.get("hit@5", 0.0))
    current_hit5 = float(current.get("hit@5", 0.0))
    hit5_drop = baseline_hit5 - current_hit5
    if hit5_drop > hit5_drop_threshold:
        messages.append(
            f"hit@5 regressed from {baseline_hit5:.4f} to {current_hit5:.4f}; "
            f"drop {hit5_drop:.4f} exceeds threshold {hit5_drop_threshold:.4f}"
        )

    baseline_mrr = float(baseline.get("mrr@5", 0.0))
    current_mrr = float(current.get("mrr@5", 0.0))
    if baseline_mrr > 0:
        relative_drop = (baseline_mrr - current_mrr) / baseline_mrr
        if relative_drop > mrr5_relative_drop_threshold:
            messages.append(
                f"mrr@5 regressed from {baseline_mrr:.4f} to {current_mrr:.4f}; "
                f"relative drop {relative_drop:.4f} exceeds threshold {mrr5_relative_drop_threshold:.4f}"
            )

    return bool(messages), messages
