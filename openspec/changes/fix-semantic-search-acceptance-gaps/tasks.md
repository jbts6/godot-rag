# Tasks

- [ ] Replace `rst2md/tests/test_semantic_search.py` tests that depend on `godot_rag/docs-md` with deterministic `tmp_path` fixtures.
- [ ] Add a regression test showing ordinary pytest does not require ignored `godot_rag/` generated state.
- [ ] Make `--debug-search` metadata visible in text mode, or explicitly reject/redirect non-JSON debug usage.
- [ ] Add CLI coverage for `--debug-search` text output and JSON output.
- [ ] Update vector readiness/search metadata to detect empty or row-mismatched `vec_chunks`.
- [ ] Add regression coverage for empty `vec_chunks` and vector row-count mismatch search metadata.
- [ ] Run focused semantic/search tests.
- [ ] Run full test suite.
- [ ] Re-run release DB diagnostics when local release DB is available.
