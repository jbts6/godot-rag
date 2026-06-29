## 1. Fix CLI Entry Point

- [x] 1.1 Write failing packaging test in `test_search_eval_cli.py`
- [x] 1.2 Run failing test to confirm it fails
- [x] 1.3 Fix `pyproject.toml` script target and wheel packages
- [x] 1.4 Verify test passes and `godot-rag eval-search --help` works
- [x] 1.5 Commit: "fix: make eval-search CLI entrypoint importable"

## 2. Add Failure Diagnostics

- [x] 2.1 Write failing diagnostics tests in `test_search_eval.py`
- [x] 2.2 Run failing tests to confirm they fail
- [x] 2.3 Add `FailureDiagnostics` dataclass and update `QueryResult` in `search_eval.py`
- [x] 2.4 Add diagnostic helpers (`_query_constraints`, `_fetch_expected_rows`, `_find_matching_rank`)
- [x] 2.5 Integrate diagnostics into `evaluate_database` with `diagnostic_limit` parameter
- [x] 2.6 Add diagnostics to `report_to_dict` and `format_text_report`
- [x] 2.7 Verify diagnostics tests pass
- [x] 2.8 Commit: "feat: add failure diagnostics to search evaluation"

## 3. Expand Golden Query Suite

- [x] 3.1 Write failing query-suite shape test in `test_search_eval.py`
- [x] 3.2 Run failing test to confirm it fails
- [x] 3.3 Replace `search_eval_queries.json` with 30+ tiered queries
- [x] 3.4 Verify query loading and shape tests pass
- [x] 3.5 Commit: "test: expand tiered search quality queries"

## 4. Add Query Rewriting

- [x] 4.1 Write failing unit tests for `expand_query_variants` in `test_searcher_module.py`
- [x] 4.2 Write failing search integration test in `test_rag_search.py`
- [x] 4.3 Run failing tests to confirm they fail
- [x] 4.4 Create `rst2md/rag/query_rewrite.py` with alias rules
- [x] 4.5 Integrate query variants into `searcher.py` FTS path
- [x] 4.6 Promote fixed alias queries out of `report_only` in query JSON
- [x] 4.7 Verify rewrite tests pass
- [x] 4.8 Commit: "feat: add conservative query rewrite aliases"

## 5. Add Intent-Aware Ranking

- [x] 5.1 Write failing unit tests for `doc_type_boost` in `test_searcher_module.py`
- [x] 5.2 Write failing integration test in `test_rag_search.py`
- [x] 5.3 Run failing tests to confirm they fail
- [x] 5.4 Add `doc_type_boost` to `query_rewrite.py`
- [x] 5.5 Apply intent boost in `searcher.py` post-ranking
- [x] 5.6 Promote tutorial intent query out of `report_only`
- [x] 5.7 Verify intent tests pass
- [x] 5.8 Commit: "feat: boost tutorial intent in search ranking"

## 6. Document and Baseline

- [x] 6.1 Update README with working `eval-search` commands
- [x] 6.2 Run full focused test suite
- [x] 6.3 Run manual evaluation and verify output
- [x] 6.4 Create baseline JSON at `docs/search-quality/baseline.json`
- [x] 6.5 Verify baseline comparison works
- [x] 6.6 Commit: "docs: document search quality optimization loop"
