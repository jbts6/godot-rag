# Comet Design Handoff

- Change: record-search-eval-versions
- Phase: design
- Mode: compact
- Context hash: 33af56f901d014f940afa404bafa88b026ee143c144b4bf23ae19640a058627c

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/record-search-eval-versions/proposal.md

- Source: openspec/changes/record-search-eval-versions/proposal.md
- Lines: 1-28
- SHA256: 89a2afe0f04c90ff65049abf92d717bfc66f67bd4d2270ec54119db56e4ea03c

```md
## Why

`stabilize-search-quality-loop` was archived with a verification gap: the baseline metadata records the database counts and query-suite hash, but it does not record the evaluator/search versions required by the accepted technical design and task list. Without those version fields, a baseline can still be compared across evaluator or search-code changes without making the producing code identity explicit.

## What Changes

- Add version metadata to search quality evaluation reports and written baselines.
- Keep the existing database fingerprint and query-suite hash behavior unchanged.
- Refresh `docs/search-quality/baseline.json` so the checked-in baseline includes the new version metadata.
- Add regression tests that fail when version metadata is omitted.
- Tighten the `semantic-search-quality` spec so version metadata is an explicit acceptance scenario for baseline identity.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `semantic-search-quality`: Baseline identity metadata must include evaluator/search version fields in addition to database fingerprint and query-suite hash.

## Impact

- Affected code: `rst2md/rag/search_eval.py`.
- Affected tests: `rst2md/tests/test_search_eval.py`.
- Affected artifacts: `docs/search-quality/baseline.json`, `openspec/specs/semantic-search-quality/spec.md` through the delta spec.
- No CLI flag, external dependency, database schema, or runtime search behavior change is planned.
```

## openspec/changes/record-search-eval-versions/design.md

- Source: openspec/changes/record-search-eval-versions/design.md
- Lines: 1-58
- SHA256: a14f0fb11121e1dc1e4f13741234921f8cc9edcd2812ba92720a4350ef77f68b

```md
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
```

## openspec/changes/record-search-eval-versions/tasks.md

- Source: openspec/changes/record-search-eval-versions/tasks.md
- Lines: 1-10
- SHA256: 2ed5b7a88ae772d6ad8cdeb4e36771ab4ae4297de87a55cccb15cd6b1c0efd05

```md
## 1. Baseline Version Metadata

- [ ] 1.1 Add focused failing tests for serialized evaluator/search version metadata.
- [ ] 1.2 Implement version metadata serialization in search quality reports and baseline writes.
- [ ] 1.3 Refresh the checked-in real-database baseline with version metadata.

## 2. Verification

- [ ] 2.1 Run focused search evaluation tests.
- [ ] 2.2 Run full tests, build, search quality baseline comparison, and OpenSpec validation.
```

## openspec/changes/record-search-eval-versions/specs/semantic-search-quality/spec.md

- Source: openspec/changes/record-search-eval-versions/specs/semantic-search-quality/spec.md
- Lines: 1-20
- SHA256: 272091d07723f3742b4242c96ce84a181e1fa23dcb7e54d15f9bb4d43c0b22e0

```md
## MODIFIED Requirements

### Requirement: Baseline artifacts identify their evaluation inputs
Search quality baselines SHALL record enough metadata to prove which database, query suite, and evaluator/search version produced the metrics.

#### Scenario: baseline includes database fingerprint
- **WHEN** a baseline is written from a populated evaluation database
- **THEN** the baseline JSON MUST include document, chunk, symbol, and vector row counts
- **AND** it MUST include a deterministic database fingerprint derived from those counts and available file metadata

#### Scenario: baseline includes query suite identity
- **WHEN** a baseline is written
- **THEN** the baseline JSON MUST include a deterministic hash of the loaded query definitions
- **AND** a later comparison MUST report when the current query-suite hash differs from the baseline hash

#### Scenario: baseline includes evaluator and search versions
- **WHEN** a baseline is written
- **THEN** the baseline JSON MUST include evaluator version metadata
- **AND** it MUST include search version metadata
- **AND** those values MUST be non-empty strings
```

