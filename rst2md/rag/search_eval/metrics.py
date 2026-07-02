from __future__ import annotations

import hashlib
import json
from typing import Sequence

from .models import GoldenQuery, QueryResult


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    if n == 1:
        return ordered[0]
    # Median of even-length sequences requires averaging the two middle
    # elements.  The plan's round((n-1)*p) formula picks only one index,
    # which gives the wrong result (e.g. p50 of [0.01,0.02,0.03,0.04]
    # would be 0.03 instead of the correct 0.025).
    if percentile == 0.50 and n % 2 == 0:
        return (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    index = min(n - 1, max(0, int((n - 1) * percentile + 0.5)))
    return ordered[index]


def latency_summary(elapsed_seconds: Sequence[float]) -> dict:
    return {
        "count": len(elapsed_seconds),
        "p50_ms": round(_percentile(elapsed_seconds, 0.50) * 1000, 3),
        "p95_ms": round(_percentile(elapsed_seconds, 0.95) * 1000, 3),
    }


def query_suite_hash(queries: Sequence[GoldenQuery]) -> str:
    payload = [
        {
            "id": query.id,
            "query": query.query,
            "category": query.category,
            "required_at": query.required_at,
            "expected_symbols": list(query.expected_symbols),
            "expected_paths": list(query.expected_paths),
            "expected_doc_types": list(query.expected_doc_types),
            "expected_addons": list(query.expected_addons),
            "tags": list(query.tags),
            "report_only": query.report_only,
        }
        for query in sorted(queries, key=lambda item: item.id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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