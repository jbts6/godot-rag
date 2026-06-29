## Why

Search quality has moved past the obvious missing-capability phase: the current pipeline already combines symbol matching, FTS5, semantic vectors, RRF fusion, graph expansion, snippets, and fallback metadata. Further tuning without a stronger evaluation harness has low signal and can trade one set of queries for another without proving net improvement.

This change adds a two-layer search quality evaluation flow so future ranking, chunking, graph, and embedding changes are driven by repeatable quality evidence rather than ad hoc spot checks.

## What Changes

- Add a small deterministic golden-query evaluation layer suitable for tests and CI.
- Add a real release-database evaluation command or equivalent manual workflow for full-corpus quality checks.
- Report `hit@1`, `hit@3`, `hit@5`, and `MRR@5` overall and by query category.
- Support regression comparison against a stored baseline for real-database evaluation.
- Fail only on clear quality regressions, not on first-run baseline creation or immature newly-added queries.
- Classify failed queries into actionable buckets such as missing recall, low ranking, graph expansion noise, filter mismatch, chunk noise, and query normalization issues.
- Do not change the search ranking algorithm, embedding model, database schema, or default CLI search output as part of this change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `semantic-search-quality`: Adds explicit quality evaluation, category-level metrics, and regression-gate behavior for hybrid search relevance.

## Impact

- Affected RAG areas: search quality fixtures, evaluation metrics, CLI/manual evaluation entry point, semantic search tests, and release verification documentation.
- Public search behavior remains unchanged; this change adds observability and gates around search quality.
- No new runtime dependency is expected for the first version.
- Generated release database artifacts remain untracked; baselines and golden-query fixtures should be small text artifacts.
