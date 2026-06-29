## Context

The search quality evaluator already computes deterministic metadata for the evaluation database and loaded query definitions. The previous change's design also required relevant evaluator/search versions, but the implementation only serializes `metadata.query_suite_hash` and `metadata.database`. This fix closes that traceability gap without changing ranking, query loading, baseline comparison thresholds, or database structure.

## Goals / Non-Goals

**Goals:**

- Include stable evaluator/search version fields in every evaluation report dictionary and written baseline.
- Refresh the checked-in baseline so future comparisons carry the same identity metadata.
- Add focused tests that prove version metadata is serialized.
- Make the OpenSpec requirement explicit so future verification checks this behavior directly.

**Non-Goals:**

- Do not change query evaluation metrics, ranking, graph comparison, or report-only promotion behavior.
- Do not add new CLI options or external dependencies.
- Do not rewrite existing baseline comparison semantics beyond preserving the new metadata in reports.

## Decisions

1. Add an explicit version payload under `metadata.versions`.

   The report dictionary should contain a nested `versions` object instead of scattering fields at the metadata top level. This keeps metadata grouped by concern: `database`, `query_suite_hash`, and `versions`.

   Alternatives considered:
   - Top-level `evaluation_version` and `search_version`: simpler, but less extensible if more version identifiers are added later.
   - Hash source files dynamically: stronger provenance, but brittle and unnecessary for this follow-up because the design asked for relevant versions, not source digests.

2. Use the project package version for both evaluator and search version initially.

   The evaluator and searcher ship in the same package and version together through `pyproject.toml`. Recording the package version as both `evaluator` and `search` gives stable provenance without introducing module-level version constants.

   Alternatives considered:
   - Add separate module constants: more explicit but creates independent version values that could drift from packaging.
   - Use importlib package metadata only: good for installed packages, but less reliable in editable/source-tree test contexts without a fallback.

3. Keep baseline comparison tolerant of older baselines.

   This change refreshes the checked-in baseline, but comparison should not fail solely because an older local baseline lacks version metadata. Query-suite hash mismatch remains the compatibility guard. The new tests and checked-in baseline enforce the desired artifact shape.

## Risks / Trade-offs

- Package version lookup can fail in source-tree contexts -> use a `pyproject.toml` fallback and a final `"unknown"` fallback.
- Recording the same package version for evaluator and search is coarse -> acceptable because both components are released together today.
- Older local baselines may lack `metadata.versions` -> keep comparison tolerant to avoid breaking developer workflows unrelated to this fix.

## Migration Plan

1. Add serialization and tests for `metadata.versions`.
2. Refresh `docs/search-quality/baseline.json` with the canonical `godot_rag.db`.
3. Run focused tests, full tests, search quality baseline comparison, build, and OpenSpec validation.

Rollback is a normal git revert of this change plus restoring the previous baseline JSON.

## Open Questions

None.
