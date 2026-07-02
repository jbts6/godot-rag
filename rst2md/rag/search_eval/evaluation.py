from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from rag.models import SearchMetadata, SearchResult

from .models import (
    DatabaseFingerprint,
    EvaluationReport,
    FailureDiagnostics,
    GoldenQuery,
    PromotionStatus,
    QueryResult,
    ReportOnlyTriage,
)
from .metrics import calculate_metrics, latency_summary, query_suite_hash


def database_fingerprint(db_path: str) -> DatabaseFingerprint:
    conn = sqlite3.connect(db_path)
    try:
        documents = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        symbols = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        try:
            vectors = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
        except sqlite3.OperationalError:
            vectors = None
    finally:
        conn.close()
    size_bytes = os.path.getsize(db_path)
    return DatabaseFingerprint(
        path=db_path,
        size_bytes=size_bytes,
        documents=documents,
        chunks=chunks,
        symbols=symbols,
        vectors=vectors,
    )


def _as_tuple(data: dict, key: str) -> tuple[str, ...]:
    value = data.get(key) or []
    return tuple(str(item) for item in value)


def load_queries(path: Path) -> list[GoldenQuery]:
    import json

    raw = json.loads(path.read_text(encoding="utf-8"))
    queries = []
    for idx, item in enumerate(raw):
        try:
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
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Malformed query entry at index {idx} in {path}: {exc}") from exc
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


def _query_constraints(query: GoldenQuery) -> tuple[list[str], list[str]]:
    clauses = []
    params = []
    if query.expected_paths:
        clauses.append("path IN ({})".format(",".join("?" for _ in query.expected_paths)))
        params.extend(query.expected_paths)
    if query.expected_symbols:
        clauses.append("symbol IN ({})".format(",".join("?" for _ in query.expected_symbols)))
        params.extend(query.expected_symbols)
    if query.expected_doc_types:
        clauses.append("doc_type IN ({})".format(",".join("?" for _ in query.expected_doc_types)))
        params.extend(query.expected_doc_types)
    if query.expected_addons:
        clauses.append("addon IN ({})".format(",".join("?" for _ in query.expected_addons)))
        params.extend(query.expected_addons)
    return clauses, params


def _fetch_expected_rows(db_path: Path, query: GoldenQuery, *, limit: int = 10) -> list[dict]:
    import sqlite3

    clauses, params = _query_constraints(query)
    if not clauses:
        return []

    sql = (
        "SELECT path, symbol, doc_type, addon, heading "
        "FROM chunks WHERE " + " AND ".join(clauses) + " "
        "ORDER BY path, symbol LIMIT ?"
    )
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, [*params, limit]).fetchall()
    return tuple(dict(row) for row in rows)


def _find_matching_rank(query: GoldenQuery, results: Sequence[SearchResult]) -> int | None:
    for rank, result in enumerate(results, start=1):
        if result_matches(query, result):
            return rank
    return None


def diagnose_failure(
    db_path: Path,
    query: GoldenQuery,
    expanded_results: Sequence[SearchResult],
    no_graph_results: Sequence[SearchResult],
    *,
    diagnostic_window: int,
    metadata: SearchMetadata | None = None,
) -> FailureDiagnostics:
    expected_rows = _fetch_expected_rows(db_path, query)
    return FailureDiagnostics(
        expected_present=bool(expected_rows),
        expected_rows=expected_rows,
        best_rank=_find_matching_rank(query, expanded_results[:diagnostic_window]),
        best_rank_no_graph=_find_matching_rank(query, no_graph_results[:diagnostic_window]),
        diagnostic_window=diagnostic_window,
        search_mode=metadata.mode if metadata else "",
        fallback_reason=metadata.fallback_reason if metadata else "",
    )


def promotion_eligibility(
    *,
    passed: bool,
    report_only: bool,
    expected_present: bool,
    matched_rank: int | None,
    required_at: int,
    category: str,
) -> PromotionStatus:
    """Determine whether a report-only query is eligible for promotion to gating.

    This is a library helper for programmatic use (e.g. CLI ``promote``
    sub-commands).  It is intentionally **not** called automatically inside
    the evaluation pipeline so that callers can apply their own promotion
    policies.
    """
    if not report_only:
        return PromotionStatus(eligible=False, reason="not_report_only")
    if not expected_present:
        return PromotionStatus(eligible=False, reason="expected_not_present")
    if not passed:
        if matched_rank is not None and matched_rank > required_at:
            return PromotionStatus(eligible=False, reason="rank_too_low")
        return PromotionStatus(eligible=False, reason="not_passing")
    if category == "addon":
        return PromotionStatus(eligible=False, reason="addon_data_unstable")
    return PromotionStatus(eligible=True, reason="eligible")


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


def _triage_evidence(result: QueryResult) -> dict:
    diagnostics = result.diagnostics
    return {
        "expected_present": diagnostics.expected_present if diagnostics else None,
        "matched_rank": result.matched_rank,
        "best_rank": diagnostics.best_rank if diagnostics else result.matched_rank,
        "best_rank_no_graph": diagnostics.best_rank_no_graph if diagnostics else None,
        "required_at": result.query.required_at,
        "search_mode": diagnostics.search_mode if diagnostics else "",
        "fallback_reason": diagnostics.fallback_reason if diagnostics else "",
        "observed": result.observed,
    }


def _report_only_triage_result(
    result: QueryResult,
    classification: str,
    recommended_followup: str,
    *,
    promotion_candidate: bool = False,
) -> ReportOnlyTriage:
    return ReportOnlyTriage(
        query_id=result.query.id,
        classification=classification,
        promotion_candidate=promotion_candidate,
        recommended_followup=recommended_followup,
        evidence=_triage_evidence(result),
    )


def _classify_report_only_triage(result: QueryResult) -> ReportOnlyTriage | None:
    if not result.query.report_only:
        return None

    evidence = _triage_evidence(result)
    if evidence["fallback_reason"]:
        return _report_only_triage_result(result, "degraded_search", "degraded_search")
    if result.passed and result.matched_rank is not None and result.matched_rank <= result.query.required_at:
        return _report_only_triage_result(
            result,
            "promotion_ready",
            "promotion",
            promotion_candidate=True,
        )
    if evidence["expected_present"] is False:
        return _report_only_triage_result(result, "missing_expected_data", "data")
    if result.failure_classification == "filter_mismatch":
        return _report_only_triage_result(result, "filter_mismatch", "filter")
    best_rank = evidence["best_rank"]
    if best_rank is not None and best_rank > result.query.required_at:
        return _report_only_triage_result(result, "low_ranking", "ranking")
    return _report_only_triage_result(result, "missing_recall", "recall")


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


_REQUIRED_CATEGORIES = {"class", "symbol", "tutorial", "engine", "addon"}


def _compute_category_warnings(
    queries: Sequence[GoldenQuery],
    query_results: Sequence[QueryResult],
) -> tuple[str, ...]:
    gating_categories = {
        result.query.category
        for result in query_results
        if not result.query.report_only
    }
    return tuple(sorted(_REQUIRED_CATEGORIES - gating_categories))


def evaluate_database(
    db_path: Path,
    queries: Sequence[GoldenQuery],
    *,
    limit: int = 5,
    compare_graph: bool = False,
    diagnostic_limit: int | None = None,
) -> EvaluationReport:
    from rag.searcher import search_database, search_database_with_metadata

    query_results = []
    graph_changes = []
    report_only_triage = []
    elapsed_seconds = []
    required_window = max(10, limit)
    diagnostic_window = max(required_window, diagnostic_limit or 0)
    for query in queries:
        started = time.perf_counter()
        is_addon_query = query.category == "addon"
        response = search_database_with_metadata(
            db_path, query.query, limit=diagnostic_window, expand_graph=True,
            exclude_addons=not is_addon_query,
        )
        results = response.results
        elapsed_seconds.append(time.perf_counter() - started)
        evaluated = evaluate_results(query, results, required_window=required_window)
        no_graph_results = []
        diagnostics_enabled = diagnostic_limit is not None
        needs_diagnostics = diagnostics_enabled and (not evaluated.passed or query.report_only)
        if compare_graph or needs_diagnostics:
            no_graph_results = search_database(db_path, query.query, limit=diagnostic_window, expand_graph=False)
        if compare_graph:
            no_graph = evaluate_results(query, no_graph_results, required_window=required_window)
            if no_graph.passed != evaluated.passed:
                evaluated = replace(evaluated, graph_changed=True)
                graph_changes.append(evaluated)
        if needs_diagnostics:
            evaluated = replace(
                evaluated,
                diagnostics=diagnose_failure(
                    db_path,
                    query,
                    results,
                    no_graph_results,
                    diagnostic_window=diagnostic_window,
                    metadata=response.metadata,
                ),
            )
        if diagnostics_enabled and query.report_only:
            triage = _classify_report_only_triage(evaluated)
            if triage:
                report_only_triage.append(triage)
        query_results.append(evaluated)

    overall, categories = calculate_metrics(query_results)
    failures = [result for result in query_results if not result.passed]

    fp = database_fingerprint(str(db_path))
    suite_hash = query_suite_hash(queries)
    category_warnings = _compute_category_warnings(queries, query_results)

    return EvaluationReport(
        overall=overall,
        categories=categories,
        failures=failures,
        query_results=query_results,
        graph_changes=graph_changes,
        database=fp,
        query_suite_hash=suite_hash,
        category_warnings=category_warnings,
        latency=latency_summary(elapsed_seconds),
        report_only_triage=tuple(report_only_triage),
    )