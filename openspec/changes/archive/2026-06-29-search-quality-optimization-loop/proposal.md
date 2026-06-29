## Why

The `eval-search` CLI command is documented but not importable due to a packaging misconfiguration. The packaged golden-query suite is too small (5 entries) to catch regressions. Failed queries lack diagnostics, making it hard to diagnose whether failures are recall issues or ranking issues. There is no repeatable optimization loop for improving search quality.

## What Changes

- Fix `pyproject.toml` so `godot-rag` CLI points to the importable `rag.cli:main` module and includes `rst2md/rag` in wheel packaging.
- Add `FailureDiagnostics` dataclass and attach diagnostic metadata to failed evaluation queries (expected-present, best-rank, diagnostic window).
- Expand the packaged golden-query suite from 5 to 30+ entries with tiered gating (`report_only`) and coverage for `class`, `symbol`, `tutorial`, `engine`, and `addon` categories.
- Add conservative query rewriting (`expand_query_variants`) for natural-language aliases that map to known symbols.
- Add intent-aware ranking (`doc_type_boost`) that boosts tutorial results for "how to" queries.
- Update README with working `eval-search` commands and generate a reviewable baseline JSON.

## Capabilities

### New Capabilities
- `search-quality-diagnostics`: Failure diagnostics for evaluation queries — whether expected targets exist in DB, best rank in diagnostic window.
- `query-rewrite`: Conservative natural-language-to-symbol alias expansion for lexical recall.
- `intent-ranking`: Doc-type-aware ranking boost for tutorial-intent queries.

### Modified Capabilities
- `semantic-search-quality`: Expanded golden-query suite with tiered gating and broader category coverage.

## Impact

- `pyproject.toml`: CLI entry point and wheel packaging.
- `rst2md/rag/search_eval.py`: New dataclass, diagnostic helpers, JSON/text report fields.
- `rst2md/rag/query_rewrite.py`: New module for alias expansion and intent boost.
- `rst2md/rag/searcher.py`: FTS query variant merging and intent boost integration.
- `rst2md/rag/search_eval_queries.json`: Expanded from 5 to 30+ queries.
- Tests: `test_search_eval.py`, `test_search_eval_cli.py`, `test_searcher_module.py`, `test_rag_search.py`.
- `README.md`: Updated evaluation documentation.
- `docs/search-quality/baseline.json`: New baseline file.
