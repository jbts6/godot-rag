from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


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


@dataclass(frozen=True)
class FailureDiagnostics:
    expected_present: bool
    expected_rows: tuple[dict, ...]
    best_rank: int | None
    best_rank_no_graph: int | None
    diagnostic_window: int
    search_mode: str = ""
    fallback_reason: str = ""


@dataclass(frozen=True)
class QueryResult:
    query: GoldenQuery
    matched_rank: int | None
    passed: bool
    failure_classification: str
    observed: list[dict]
    graph_changed: bool = False
    diagnostics: FailureDiagnostics | None = None


@dataclass(frozen=True)
class ReportOnlyTriage:
    query_id: str
    classification: str
    promotion_candidate: bool
    recommended_followup: str
    evidence: dict


@dataclass(frozen=True)
class PromotionStatus:
    eligible: bool
    reason: str


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
    latency: dict | None = None
    report_only_triage: tuple[ReportOnlyTriage, ...] = ()