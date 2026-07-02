from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .models import DatabaseFingerprint, EvaluationReport, QueryResult
from .metrics import calculate_metrics, latency_summary, query_suite_hash
from .reports import report_to_dict


def validate_baseline_input(fingerprint: DatabaseFingerprint) -> list[str]:
    messages = []
    if fingerprint.documents == 0:
        messages.append("documents=0")
    if fingerprint.chunks == 0:
        messages.append("chunks=0")
    if fingerprint.symbols == 0:
        messages.append("symbols=0")
    return messages


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


def compare_latency_with_baseline(
    current: dict | None,
    baseline: dict | None,
    *,
    p95_latency_threshold_ms: float | None = None,
) -> tuple[bool, list[str]]:
    if p95_latency_threshold_ms is None or not current or not baseline:
        return False, []

    current_p95 = float(current.get("p95_ms", 0.0))
    baseline_p95 = float(baseline.get("p95_ms", 0.0))
    latency_increase = current_p95 - baseline_p95
    if latency_increase <= p95_latency_threshold_ms:
        return False, []

    return True, [
        f"p95 latency regressed from {baseline_p95:.3f}ms to {current_p95:.3f}ms; "
        f"increase {latency_increase:.3f}ms exceeds threshold {p95_latency_threshold_ms:.3f}ms"
    ]


def apply_baseline(
    report: EvaluationReport,
    baseline_path: Path | None,
    *,
    write_baseline: bool = False,
    hit5_drop_threshold: float = 0.05,
    mrr5_relative_drop_threshold: float = 0.10,
    p95_latency_threshold_ms: float | None = None,
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
            latency=report.latency,
            report_only_triage=report.report_only_triage,
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
    latency_failed, latency_messages = compare_latency_with_baseline(
        report.latency,
        baseline.get("latency"),
        p95_latency_threshold_ms=p95_latency_threshold_ms,
    )
    messages = [*messages, *latency_messages]
    return EvaluationReport(
        overall=report.overall,
        categories=report.categories,
        failures=report.failures,
        query_results=report.query_results,
        graph_changes=report.graph_changes,
        regression_failed=failed or latency_failed,
        regression_messages=tuple(messages),
        baseline_written=False,
        baseline_compared=True,
        database=report.database,
        query_suite_hash=report.query_suite_hash,
        category_warnings=report.category_warnings,
        baseline_warnings=tuple(baseline_warnings),
        latency=report.latency,
        report_only_triage=report.report_only_triage,
    )