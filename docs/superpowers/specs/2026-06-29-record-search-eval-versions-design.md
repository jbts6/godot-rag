---
comet_change: record-search-eval-versions
role: technical-design
canonical_spec: openspec
---

# Record Search Evaluation Versions - Technical Design

## Context

The previous search quality stabilization change made baselines self-describing for the canonical database and query suite, but missed the accepted requirement to record relevant evaluator/search versions. The current baseline metadata therefore proves which database and query definitions produced the metrics, but not which package version produced the evaluator and search behavior.

## Technical Approach

Add a small version metadata helper in `rst2md/rag/search_eval.py` and serialize its result under `metadata.versions`.

The helper will resolve the project package version using standard library facilities:

1. Try installed package metadata for `godot-rag`.
2. Fall back to parsing `pyproject.toml` in source-tree execution.
3. Fall back to `"unknown"` only if neither source is available.

Because the evaluator and searcher ship in the same package, the first version payload will be:

```json
{
  "evaluator": "4.7.0.post10",
  "search": "4.7.0.post10"
}
```

This keeps the format explicit while avoiding independent module constants that can drift from the packaged version.

## Data Flow

`evaluate_database()` already builds an `EvaluationReport` with the database fingerprint and query-suite hash. `report_to_dict()` is the single serialization boundary for JSON reports and baseline writes, so the version metadata should be added there. `apply_baseline(..., write_baseline=True)` writes `report_to_dict()`, so no separate baseline write path is needed.

## Testing Strategy

- Add a focused test asserting `report_to_dict()` includes `metadata.versions.evaluator` and `metadata.versions.search` as non-empty strings.
- Preserve existing tests for query-suite hash and database metadata.
- Refresh `docs/search-quality/baseline.json` through the real evaluator against `godot_rag.db`.
- Verify with focused search evaluation tests, full pytest, `uv build`, real baseline comparison, and OpenSpec validation.

## Risks

- Package metadata may be unavailable in editable/source execution. Mitigation: parse `pyproject.toml` as a fallback.
- The evaluator and search versions are initially identical. Mitigation: use distinct keys now so the JSON shape can support separate values later if these components version independently.
- Older local baselines may lack `metadata.versions`. Mitigation: do not make baseline comparison fail solely on missing version metadata; tests and checked-in artifacts enforce the current shape.
