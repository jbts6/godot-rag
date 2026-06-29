---
comet_change: search-quality-evaluation-expansion
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-29-search-quality-evaluation-expansion
status: final
---

# Search Quality Evaluation Expansion Design

## Context

The search quality loop already has deterministic fixture tests, real-database `eval-search`, baseline regression, failure classification, query-suite identity, database fingerprints, and evaluator/search version metadata. The current reviewed baseline is still too narrow for the next phase: it gates a small set of queries and currently scores perfectly, so it will not reliably expose regressions from ranking changes, searcher restructuring, fallback behavior, or latency changes.

The core implementation risk is that future work will touch `rst2md/rag/searcher.py`, `rst2md/rag/search_eval.py`, query fixtures, CLI reporting, and documentation at the same time. This design makes the evaluation surface stronger before ranking or architecture changes become the main work.

## Design Goals

- Expand stable quality coverage before changing ranking behavior.
- Add performance and stability signals to the same evaluation report used for quality gates.
- Keep existing CLI/search result behavior backward compatible by adding fields rather than replacing fields.
- Define a safety boundary for any searcher restructuring: equivalent refactors must preserve ranking, result metadata, diagnostics, and baseline metrics.

## Non-Goals

- Do not make broad ranking-weight changes in this change.
- Do not change the embedding model.
- Do not modify the database schema.
- Do not implement the full future alias/ranking strategy from `WIP.md`.

## Technical Approach

### 1. Query Suite Expansion

Start by auditing `rst2md/rag/search_eval_queries.json` against the required categories and tags. Add stable queries until the suite has at least 40 unique IDs, at least 25 gating queries, and at least 10 report-only queries.

Gating queries should cover:

- `class`, `symbol`, `tutorial`, `engine`, and `addon` categories.
- Symbol format variants such as dotted, snake_case, camelCase, and natural-language alias forms.
- Graph expansion behavior where the expected target is present and stable.
- Addon and doc-type filter precision, especially cases where returning the wrong type would be misleading.

Queries whose expected target is absent from the canonical database, unstable under graph expansion, or not yet ranked consistently should remain report-only. The evaluator should keep reporting them so future promotion has evidence, but they should not fail the gate.

### 2. Evaluation Metrics And Diagnostics

`evaluate_database` should measure elapsed time per query around the existing `search_database` call. The evaluation report should compute latency summaries such as p50 and p95 and expose them in both JSON and text output.

Search execution metadata should flow into diagnostics where available:

- search mode: hybrid vs FTS-only
- vector availability
- fallback or degraded reason
- graph-enabled and no-graph comparison ranks

These fields should be additive. Existing report fields, baseline fields, failure classifications, and query result shapes should remain stable unless the OpenSpec delta explicitly requires a new field.

### 3. Routine Validation

Document two validation levels:

- Deterministic local validation: focused tests for search evaluation fixtures, metrics, diagnostics, and CLI output.
- Real-database validation: `eval-search` with the checked-in baseline when the release database is available.

The first level should be suitable for routine development. The second level should be explicit and repeatable, but it may remain conditional on local availability of the release database.

### 4. Searcher Refactor Safety Boundary

This change may identify a narrow searcher extraction boundary, but any extraction must be equivalent:

- no intended ranking change
- no output shape removal
- no diagnostic metadata loss
- no baseline regression

Candidate extraction boundaries are candidate retrieval, fusion/rerank, graph expansion, and result formatting. If implementation starts to require ranking changes, query rewrite strategy changes, or embedding-model changes, that work should be split into a later change.

## Risks And Mitigations

- Risk: New gating queries are flaky.
  Mitigation: keep unstable or data-dependent cases report-only until expected targets are present and ranks are stable.

- Risk: latency metrics are noisy across machines.
  Mitigation: first make latency visible and JSON-readable; use broad or configurable thresholds rather than hard narrow defaults.

- Risk: output changes break downstream consumers.
  Mitigation: add fields without removing existing fields.

- Risk: searcher refactor scope grows.
  Mitigation: enforce behavior-equivalence tests and defer ranking/alias/embedding changes.

## Testing Strategy

- Update `rst2md/tests/test_search_eval.py` for query-suite counts, category coverage, required tags, filter precision checks, latency summaries, and fallback/degraded diagnostics.
- Update CLI/evaluator tests for JSON and text output additions.
- Run focused tests:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

- Run the full suite:

```bash
rtk uv run pytest -q
```

- When the real database is available, run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```
