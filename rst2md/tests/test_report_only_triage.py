import pytest

from rag.search_eval import _classify_report_only_triage


def _query_result(query, *, matched_rank=None, passed=False, failure_classification="", observed=None, diagnostics=None):
    from rag.search_eval import QueryResult
    return QueryResult(
        query=query,
        matched_rank=matched_rank,
        passed=passed,
        failure_classification=failure_classification,
        observed=observed or [],
        diagnostics=diagnostics,
    )


def _report_only_query(*, required_at=5, expected_doc_types=(), expected_addons=()):
    from rag.search_eval import GoldenQuery
    return GoldenQuery(
        id="report-only",
        query="test query",
        category="class",
        required_at=required_at,
        expected_paths=("classes/class_node.md",),
        expected_doc_types=expected_doc_types,
        expected_addons=expected_addons,
        report_only=True,
    )


def _diagnostics(*, expected_present=True, expected_rows=None, best_rank=None, best_rank_no_graph=None, fallback_reason=""):
    from rag.search_eval import FailureDiagnostics
    return FailureDiagnostics(
        expected_present=expected_present,
        expected_rows=expected_rows if expected_rows is not None else (),
        best_rank=best_rank,
        best_rank_no_graph=best_rank_no_graph,
        diagnostic_window=10,
        fallback_reason=fallback_reason,
    )


@pytest.mark.parametrize("result_kwargs,expected_classification,expected_candidate,expected_followup,expected_evidence", [
    # promotion_ready
    (
        {"matched_rank": 3, "passed": True},
        "promotion_ready", True, "promotion", {"matched_rank": 3}
    ),
    # missing_expected_data
    (
        {"failure_classification": "missing_recall", "diagnostics_kwargs": {"expected_present": False, "expected_rows": (), "best_rank": None}},
        "missing_expected_data", False, "data", {"expected_present": False}
    ),
    # low_ranking
    (
        {"matched_rank": None, "failure_classification": "low_ranking", "diagnostics_kwargs": {"best_rank": 12}},
        "low_ranking", False, "ranking", {"best_rank": 12, "required_at": 5}
    ),
    # filter_mismatch
    (
        {"failure_classification": "filter_mismatch", "observed": [{"rank": 1, "path": "tutorials/nodes.md", "symbol": "", "doc_type": "tutorial", "addon": "", "heading": "Nodes"}], "diagnostics_kwargs": {"best_rank": None}},
        "filter_mismatch", False, "filter", {"observed_doc_type": "tutorial"}
    ),
    # degraded_search
    (
        {"matched_rank": 1, "passed": True, "failure_classification": "missing_recall", "diagnostics_kwargs": {"best_rank": 1, "fallback_reason": "vector_query_failed"}},
        "degraded_search", False, "degraded_search", {"fallback_reason": "vector_query_failed"}
    ),
    # missing_recall
    (
        {"failure_classification": "missing_recall", "diagnostics_kwargs": {"expected_present": True, "best_rank": None}},
        "missing_recall", False, "recall", {}
    ),
])
def test_report_only_triage_classifications(result_kwargs, expected_classification, expected_candidate, expected_followup, expected_evidence):
    # Extract diagnostics_kwargs if present
    diagnostics_kwargs = result_kwargs.pop("diagnostics_kwargs", {})
    if diagnostics_kwargs:
        result_kwargs["diagnostics"] = _diagnostics(**diagnostics_kwargs)
    
    result = _query_result(_report_only_query(), **result_kwargs)
    triage = _classify_report_only_triage(result)
    
    assert triage.classification == expected_classification
    assert triage.promotion_candidate == expected_candidate
    assert triage.recommended_followup == expected_followup
    
    for key, value in expected_evidence.items():
        if key == "observed_doc_type":
            assert triage.evidence["observed"][0]["doc_type"] == value
        else:
            assert triage.evidence[key] == value