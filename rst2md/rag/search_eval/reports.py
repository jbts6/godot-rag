from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .models import EvaluationReport, GoldenQuery, QueryResult, ReportOnlyTriage
from .evaluation import _compute_category_warnings


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
    if report.latency is not None:
        lat = report.latency
        lines.append(f"latency: count={lat['count']} p50={lat['p50_ms']}ms p95={lat['p95_ms']}ms")
    if report.report_only_triage:
        lines.append("report_only_triage:")
        for triage in report.report_only_triage:
            evidence = triage.evidence
            lines.append(
                f"- {triage.query_id}: {triage.classification} "
                f"followup={triage.recommended_followup} "
                f"promotion_candidate={triage.promotion_candidate}"
            )
            lines.append(
                "  evidence: "
                f"expected_present={evidence.get('expected_present')} "
                f"best_rank={evidence.get('best_rank')} "
                f"required_at={evidence.get('required_at')} "
                f"search_mode={evidence.get('search_mode')} "
                f"fallback_reason={evidence.get('fallback_reason')}"
            )
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
                if failure.diagnostics.search_mode:
                    lines.append(
                        "  "
                        f"search_mode={failure.diagnostics.search_mode} "
                        f"fallback_reason={failure.diagnostics.fallback_reason}"
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
                "search_mode": result.diagnostics.search_mode,
                "fallback_reason": result.diagnostics.fallback_reason,
            }
            if result.diagnostics
            else None
        ),
    }


def _report_only_triage_to_dict(triage: ReportOnlyTriage) -> dict:
    return {
        "query_id": triage.query_id,
        "classification": triage.classification,
        "promotion_candidate": triage.promotion_candidate,
        "recommended_followup": triage.recommended_followup,
        "evidence": triage.evidence,
    }


def _package_version() -> str:
    """Resolve the godot-rag package version, falling back to pyproject.toml then 'unknown'."""
    try:
        from importlib.metadata import version as _dist_version

        return _dist_version("godot-rag")
    except Exception:
        pass
    try:
        import tomllib

        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
        return str(data["project"]["version"])
    except Exception:
        return "unknown"


def _evaluation_versions() -> dict[str, str]:
    version = _package_version()
    return {"evaluator": version, "search": version}


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
        "report_only_triage": [_report_only_triage_to_dict(triage) for triage in report.report_only_triage],
    }
    if report.latency is not None:
        result["latency"] = report.latency
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
            "versions": _evaluation_versions(),
        }
    return result