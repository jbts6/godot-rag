---
comet_change: search-ranking-report-only-triage
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-30-search-ranking-report-only-triage
status: final
---

# Search Ranking Report-Only Triage - Technical Design

## Context

The search quality loop has 45 evaluation queries: 25 gating queries and 20 `report_only` queries. The evaluator already records pass/fail status, observed top results, optional failure diagnostics, latency metadata, graph comparison changes, category warnings, and baseline regression state. The remaining workflow gap is decision support for `report_only` queries: the current report can show that a non-gating query failed, but it does not summarize whether the query is ready for promotion, blocked by fixture data, or best handled by recall, ranking, filter, or degraded-search follow-up work.

This change belongs in the search evaluation and diagnostics layer. It should not alter search ranking, vector recall, query planning, database schema, or the runtime `search_database` API. Its purpose is to convert already available evaluation evidence into a deterministic triage summary for humans reviewing search-quality work.

## Goals / Non-Goals

**Goals:**
- Classify every report-only query when diagnostics are requested.
- Reuse existing evidence from `QueryResult`, `FailureDiagnostics`, `SearchMetadata`, and observed top results.
- Include the triage summary in JSON evaluation output and a concise version in text output.
- Make promotion-ready report-only queries explicit without changing the query suite.
- Preserve current gating metrics, baseline comparison behavior, CLI exit behavior, and search runtime behavior.

**Non-Goals:**
- Do not change ranking weights, RRF fusion, vector recall, query rewrite, aliases, or graph expansion.
- Do not automatically edit `rst2md/rag/search_eval_queries.json` to promote queries.
- Do not add database columns, tables, or migrations.
- Do not put evaluation workflow fields into `SearchMetadata` or `SearchResult`.
- Do not introduce free-form or model-generated explanations.

## Architecture

### Component Overview

```text
eval-search CLI
  load_queries()
    -> evaluate_database()
      -> search_database_with_metadata()
      -> evaluate_results()
      -> diagnose_failure() when diagnostics are requested
      -> classify_report_only_triage()
    -> apply_baseline()
    -> report_to_dict() / format_text_report()
```

The new triage model lives in `rst2md/rag/search_eval.py` beside the existing evaluation dataclasses. `evaluate_database()` remains the orchestration point because it has access to the query definition, evaluated result, optional diagnostics, search metadata, and observed top results. Reporting stays at the existing serialization boundaries: `report_to_dict()` for JSON and `format_text_report()` for text.

## Data Model

Add a frozen dataclass:

```python
@dataclass(frozen=True)
class ReportOnlyTriage:
    query_id: str
    classification: str
    promotion_candidate: bool
    recommended_followup: str
    evidence: dict
```

Add a field to `EvaluationReport`:

```python
report_only_triage: tuple[ReportOnlyTriage, ...] = ()
```

The JSON shape should be stable and machine-readable:

```json
{
  "report_only_triage": [
    {
      "query_id": "addon-dialogue-manager",
      "classification": "low_ranking",
      "promotion_candidate": false,
      "recommended_followup": "ranking",
      "evidence": {
        "expected_present": true,
        "matched_rank": 12,
        "best_rank": 12,
        "best_rank_no_graph": null,
        "required_at": 5,
        "search_mode": "hybrid",
        "fallback_reason": "",
        "observed": []
      }
    }
  ]
}
```

The `observed` evidence should reuse the same observed dictionaries already emitted by `_query_result_to_dict()`. Keep the top-result evidence compact by reusing the evaluator's `observed` window; do not run additional search queries just for triage.

## Classification Rules

Use a deterministic priority order. The priority matters because some failures can have multiple symptoms.

1. `degraded_search`: search metadata has a non-empty `fallback_reason` or reports degraded vector execution. Follow-up: `degraded_search`.
2. `promotion_ready`: query is report-only, passed within `required_at`, and search execution is not degraded. Follow-up: `promotion`.
3. `missing_expected_data`: diagnostics show the expected target is absent from the database. Follow-up: `data`.
4. `filter_mismatch`: existing failure classification is `filter_mismatch`, or expected doc-type/addon constraints are contradicted by observed top results. Follow-up: `filter`.
5. `low_ranking`: a matching expected target exists in the diagnostic window but ranks after `required_at`. Follow-up: `ranking`.
6. `missing_recall`: expected data is present, but no matching result appears in the diagnostic window. Follow-up: `recall`.

If diagnostics are requested but a report-only query lacks diagnostics because it passed, classify it from `QueryResult.passed`, `matched_rank`, and search metadata. If diagnostics are not requested, do not emit triage; this keeps the requirement scoped to diagnostic evaluation and avoids extra database work in default runs.

## Reporting

### JSON

`report_to_dict()` should include a top-level `report_only_triage` array. This keeps triage discoverable without forcing consumers to scan `query_results`. Existing fields should remain unchanged for compatibility.

Baseline writes use `report_to_dict()`, so baseline JSON may include the triage array when diagnostics are requested during a baseline write. Baseline comparison must not gate on triage content and must not treat missing triage in older baselines as a regression.

### Text

`format_text_report()` should append a concise section only when triage entries exist:

```text
report_only_triage:
- addon-dialogue-manager: low_ranking followup=ranking promotion_candidate=False
  evidence: expected_present=True best_rank=12 required_at=5 search_mode=hybrid fallback_reason=
```

The text report should be brief enough for terminal use. Detailed top-result evidence remains available in JSON.

## Testing Strategy

- Add focused tests in `rst2md/tests/test_search_eval.py` for each classification branch:
  - promotion-ready passed report-only query
  - missing expected data
  - missing recall
  - low ranking
  - filter mismatch
  - degraded search execution
- Add JSON shape tests for `report_to_dict()` including `classification`, `promotion_candidate`, `recommended_followup`, and evidence fields.
- Add text report tests for the concise `report_only_triage` section.
- Add CLI tests in `rst2md/tests/test_search_eval_cli.py` to ensure JSON and text output expose the triage summary.
- Preserve regression tests proving gating evaluation and baseline comparison behavior remain unchanged.

## Risks / Trade-offs

- Some report-only failures may have more than one plausible cause. The deterministic priority order makes output testable and conservative; evidence remains available for human review.
- Triage output can become noisy if it repeats full observed results in text mode. JSON should remain authoritative, while text stays compact.
- Promotion recommendations could be mistaken for policy changes. The field name and documentation should make promotion advisory, and implementation must not edit query definitions.
- Existing baseline artifacts may not contain triage. Baseline comparison should continue to rely on the existing gating metrics, query-suite metadata, and latency thresholds.

## Implementation Boundaries

Primary files:
- `rst2md/rag/search_eval.py`: dataclass, classification helper, evaluator integration, JSON/text serialization.
- `rst2md/tests/test_search_eval.py`: model and report coverage.
- `rst2md/tests/test_search_eval_cli.py`: CLI output coverage.

Files that should not change for this capability:
- `rst2md/rag/searcher.py`
- `rst2md/rag/query_plan.py`
- database schema/indexing modules
- `rst2md/rag/search_eval_queries.json`, except for a separate explicit promotion decision outside this change.
