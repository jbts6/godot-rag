## Why

The current search quality gate is now guarded against empty-baseline mistakes, but it still does not make real search quality improvements repeatable. Report-only failures show that natural-language symbol aliases, category/filter coverage, and ranking stability need a tighter loop before more queries can safely become gating.

## What Changes

- Harden real-database baseline handling with DB/query-suite metadata and guards that reject empty or incomplete evaluation databases.
- Introduce a query-planning layer that makes aliases, symbol intent, doc-type intent, and addon intent available to all relevant search stages.
- Apply deterministic reranking so alias/symbol matches and intent-consistent results can be promoted without adding external reranker dependencies.
- Add promotion rules and tests for moving stable report-only queries back into the gating set.
- Preserve report-only visibility for unstable queries while making failures actionable by classification and category.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `semantic-search-quality`: baseline metadata, canonical database safeguards, category coverage checks, and report-only promotion rules.
- `query-rewrite`: query aliases expand into a structured query plan used beyond FTS-only recall.
- `intent-ranking`: intent signals participate in deterministic reranking, not only a small post-ranking doc-type boost.
- `search-quality-diagnostics`: evaluation failures expose enough metadata to distinguish empty/incomplete data, missing recall, low ranking, and filter/category issues.

## Impact

- Affected code: `rst2md/rag/search_eval.py`, `rst2md/rag/searcher.py`, query expansion helpers, search quality query fixtures, and related tests.
- Affected artifacts: `rst2md/rag/search_eval_queries.json`, `docs/search-quality/baseline.json`, and OpenSpec delta specs for modified capabilities.
- No new runtime service, external model, learned reranker, or database schema migration is planned.
