from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, replace
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
class DatabaseFingerprint:
    path: str
    size_bytes: int
    documents: int
    chunks: int
    symbols: int
    vectors: int | None


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


def validate_baseline_input(fingerprint: DatabaseFingerprint) -> list[str]:
    messages = []
    if fingerprint.documents == 0:
        messages.append("documents=0")
    if fingerprint.chunks == 0:
        messages.append("chunks=0")
    if fingerprint.symbols == 0:
        messages.append("symbols=0")
    return messages


@dataclass(frozen=True)
class FailureDiagnostics:
    expected_present: bool
    expected_rows: tuple[dict, ...]
    best_rank: int | None
    best_rank_no_graph: int | None
    diagnostic_window: int


@dataclass(frozen=True)
class QueryResult:
    query: GoldenQuery
    matched_rank: int | None
    passed: bool
    failure_classification: str
    observed: list[dict]
    graph_changed: bool = False
    diagnostics: FailureDiagnostics | None = None


def _as_tuple(data: dict, key: str) -> tuple[str, ...]:
    value = data.get(key) or []
    return tuple(str(item) for item in value)


def load_queries(path: Path) -> list[GoldenQuery]:
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
) -> FailureDiagnostics:
    expected_rows = _fetch_expected_rows(db_path, query)
    return FailureDiagnostics(
        expected_present=bool(expected_rows),
        expected_rows=expected_rows,
        best_rank=_find_matching_rank(query, expanded_results[:diagnostic_window]),
        best_rank_no_graph=_find_matching_rank(query, no_graph_results[:diagnostic_window]),
        diagnostic_window=diagnostic_window,
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


def _baseline_gating_ids(baseline: dict) -> set[str] | None:
    queries = baseline.get("query_results")
    if not isinstance(queries, list):
        return None
    return {
        str(query["id"])
        for query in queries
        if isinstance(query, dict) and "id" in query and not query.get("report_only", False)
    }


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


@dataclass(frozen=True)
class EvaluationReport:
    overall: dict
    categories: dict
    failures: list[QueryResult]
    query_results: list[QueryResult]
    graph_changes: list[QueryResult]
    regression_failed: bool = False
    regression_messages: tuple[str, ...] = ()
    baseline_written: bool = False
    baseline_compared: bool = False
    database: DatabaseFingerprint | None = None
    query_suite_hash: str = ""
    category_warnings: tuple[str, ...] = ()
    baseline_warnings: tuple[str, ...] = ()


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
    diagnostic_limit: int = 50,
) -> EvaluationReport:
    from rag.searcher import search_database

    query_results = []
    graph_changes = []
    required_window = max(10, limit)
    diagnostic_window = max(required_window, diagnostic_limit)
    for query in queries:
        results = search_database(db_path, query.query, limit=diagnostic_window, expand_graph=True)
        evaluated = evaluate_results(query, results, required_window=required_window)
        no_graph_results = []
        if compare_graph or not evaluated.passed:
            no_graph_results = search_database(db_path, query.query, limit=diagnostic_window, expand_graph=False)
        if compare_graph:
            no_graph = evaluate_results(query, no_graph_results, required_window=required_window)
            if no_graph.passed != evaluated.passed:
                evaluated = replace(evaluated, graph_changed=True)
                graph_changes.append(evaluated)
        if not evaluated.passed:
            evaluated = replace(
                evaluated,
                diagnostics=diagnose_failure(
                    db_path,
                    query,
                    results,
                    no_graph_results,
                    diagnostic_window=diagnostic_window,
                ),
            )
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
    )


def apply_baseline(
    report: EvaluationReport,
    baseline_path: Path | None,
    *,
    write_baseline: bool = False,
    hit5_drop_threshold: float = 0.05,
    mrr5_relative_drop_threshold: float = 0.10,
) -> EvaluationReport:
    if baseline_path is None:
        return report

    if write_baseline:
        if report.database:
            issues = validate_baseline_input(report.database)
            if issues:
                raise ValueError(f"Invalid database for baseline write: {', '.join(issues)}")
        baseline_report = EvaluationReport(
            overall=report.overall,
            categories=report.categories,
            failures=report.failures,
            query_results=report.query_results,
            graph_changes=report.graph_changes,
            regression_failed=False,
            regression_messages=(),
            baseline_written=True,
            baseline_compared=False,
            database=report.database,
            query_suite_hash=report.query_suite_hash,
            category_warnings=report.category_warnings,
            baseline_warnings=report.baseline_warnings,
        )
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(report_to_dict(baseline_report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return baseline_report

    if not baseline_path.exists():
        return report

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    comparison_overall = report.overall
    gating_ids = _baseline_gating_ids(baseline)
    if gating_ids is not None:
        comparison_results = [result for result in report.query_results if result.query.id in gating_ids]
        comparison_overall, _ = calculate_metrics(comparison_results)

    baseline_warnings = list(report.baseline_warnings)
    baseline_hash = (baseline.get("metadata") or {}).get("query_suite_hash", "")
    if baseline_hash and report.query_suite_hash and baseline_hash != report.query_suite_hash:
        baseline_warnings.append(
            f"query_suite_hash mismatch: baseline={baseline_hash[:12]} current={report.query_suite_hash[:12]}"
        )

    failed, messages = compare_with_baseline(
        comparison_overall,
        baseline.get("overall", {}),
        hit5_drop_threshold=hit5_drop_threshold,
        mrr5_relative_drop_threshold=mrr5_relative_drop_threshold,
    )
    return EvaluationReport(
        overall=report.overall,
        categories=report.categories,
        failures=report.failures,
        query_results=report.query_results,
        graph_changes=report.graph_changes,
        regression_failed=failed,
        regression_messages=tuple(messages),
        baseline_written=False,
        baseline_compared=True,
        database=report.database,
        query_suite_hash=report.query_suite_hash,
        category_warnings=report.category_warnings,
        baseline_warnings=tuple(baseline_warnings),
    )


def _format_expected(query: GoldenQuery) -> str:
    expected = {
        "paths": query.expected_paths,
        "symbols": query.expected_symbols,
        "doc_types": query.expected_doc_types,
        "addons": query.expected_addons,
    }
    parts = [f"{key}={list(values)}" for key, values in expected.items() if values]
    return " ".join(parts) if parts else "<none>"


def format_text_report(report: EvaluationReport) -> str:
    lines = ["=== Search Quality Evaluation ==="]
    lines.append(
        "overall: "
        f"count={report.overall['count']} "
        f"hit@1={report.overall['hit@1']:.3f} "
        f"hit@3={report.overall['hit@3']:.3f} "
        f"hit@5={report.overall['hit@5']:.3f} "
        f"mrr@5={report.overall['mrr@5']:.3f}"
    )
    for category, metrics in report.categories.items():
        lines.append(
            f"{category}: count={metrics['count']} "
            f"hit@5={metrics['hit@5']:.3f} mrr@5={metrics['mrr@5']:.3f}"
        )
    if report.baseline_written:
        lines.append("baseline: written")
    if report.baseline_compared:
        lines.append("baseline: compared")
    for message in report.regression_messages:
        lines.append(f"regression: {message}")
    for warning in report.category_warnings:
        lines.append(f"category_warning: missing gating queries for '{warning}'")
    for warning in report.baseline_warnings:
        lines.append(f"baseline_warning: {warning}")
    if report.failures:
        lines.append("failures:")
        for failure in report.failures:
            lines.append(f"- {failure.query.id}: {failure.failure_classification}")
            lines.append(f"  query: {failure.query.query}")
            lines.append(f"  category={failure.query.category} required_at={failure.query.required_at}")
            lines.append(f"  expected: {_format_expected(failure.query)}")
            if failure.diagnostics:
                lines.append("  diagnostics:")
                lines.append(
                    "  "
                    f"expected_present={failure.diagnostics.expected_present} "
                    f"best_rank={failure.diagnostics.best_rank} "
                    f"best_rank_no_graph={failure.diagnostics.best_rank_no_graph} "
                    f"diagnostic_window={failure.diagnostics.diagnostic_window}"
                )
            if failure.observed:
                lines.append("  observed:")
                for observed in failure.observed:
                    lines.append(
                        "  "
                        f"#{observed['rank']} path={observed['path']} "
                        f"symbol={observed['symbol']} doc_type={observed['doc_type']} addon={observed['addon']}"
                    )
            else:
                lines.append("  observed: <none>")
    return "\n".join(lines)


def _query_result_to_dict(result: QueryResult) -> dict:
    return {
        "id": result.query.id,
        "query": result.query.query,
        "category": result.query.category,
        "required_at": result.query.required_at,
        "matched_rank": result.matched_rank,
        "passed": result.passed,
        "failure_classification": result.failure_classification,
        "report_only": result.query.report_only,
        "graph_changed": result.graph_changed,
        "expected": {
            "paths": list(result.query.expected_paths),
            "symbols": list(result.query.expected_symbols),
            "doc_types": list(result.query.expected_doc_types),
            "addons": list(result.query.expected_addons),
        },
        "observed": result.observed,
        "diagnostics": (
            {
                "expected_present": result.diagnostics.expected_present,
                "expected_rows": result.diagnostics.expected_rows,
                "best_rank": result.diagnostics.best_rank,
                "best_rank_no_graph": result.diagnostics.best_rank_no_graph,
                "diagnostic_window": result.diagnostics.diagnostic_window,
            }
            if result.diagnostics
            else None
        ),
    }


def report_to_dict(report: EvaluationReport) -> dict:
    category_warnings = report.category_warnings
    if not category_warnings and report.query_results:
        category_warnings = _compute_category_warnings(
            [r.query for r in report.query_results],
            report.query_results,
        )
    result = {
        "overall": report.overall,
        "categories": report.categories,
        "failures": [_query_result_to_dict(result) for result in report.failures],
        "query_results": [_query_result_to_dict(result) for result in report.query_results],
        "graph_changes": [_query_result_to_dict(result) for result in report.graph_changes],
        "regression_failed": report.regression_failed,
        "regression_messages": list(report.regression_messages),
        "baseline_written": report.baseline_written,
        "baseline_compared": report.baseline_compared,
        "category_warnings": list(category_warnings),
        "baseline_warnings": list(report.baseline_warnings),
    }
    if report.database:
        result["metadata"] = {
            "query_suite_hash": report.query_suite_hash,
            "database": {
                "path": report.database.path,
                "size_bytes": report.database.size_bytes,
                "documents": report.database.documents,
                "chunks": report.database.chunks,
                "symbols": report.database.symbols,
                "vectors": report.database.vectors,
            },
        }
    return result
