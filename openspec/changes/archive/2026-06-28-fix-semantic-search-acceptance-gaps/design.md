# Design

## Approach

This is a focused hotfix for acceptance gaps left after `semantic-search-quality-hardening`.

### Deterministic Semantic Fixtures

Replace the top-level `test_db` fixture in `rst2md/tests/test_semantic_search.py` that reads `Path("godot_rag/docs-md")`.

Recommended approach:

- Build a small docs tree under `tmp_path`.
- Include enough class/tutorial content to exercise:
  - `see_also` relation extraction, with deterministic expected count.
  - vector row parity/population on a small DB.
  - golden query expected path families.
- Keep large release DB validation in `build.sh` diagnostics, not ordinary pytest.

### Debug Metadata Visibility

`--debug-search` should visibly alter output when requested.

Recommended approach:

- In JSON mode, keep the existing envelope:
  - `metadata`
  - `results`
- In text mode, print a short metadata header before results, for example:
  - `search_mode: fts_only`
  - `vector_available: false`
  - `fallback_reason: missing_vec_chunks`
- Add CLI tests for `--debug-search` with and without `--json`.

### Vector Availability Semantics

Current `_vector_availability()` only checks whether `vec_chunks` can be queried. That misses degraded states where the table exists but is empty or inconsistent.

Recommended approach:

- Extend vector readiness checks to compare:
  - `chunks` row count
  - `vec_chunks` row count
  - extension/table queryability
- Treat row mismatch or empty vector rows as degraded/unavailable for search metadata, using explicit reasons such as:
  - `missing_vec_chunks`
  - `empty_vec_chunks`
  - `vector_row_count_mismatch`
  - `vector_query_failed`
- If vector query returns no rows while FTS returns rows, avoid reporting pure `hybrid` unless that is an intentional “vector path attempted” state. Prefer a metadata field or mode that distinguishes attempted vector search from useful vector contribution.

## Risks

- Small deterministic fixtures should not accidentally assert full release-db scale properties such as `>= 28000` rows.
- Changing metadata names may affect consumers. Prefer adding explicit reasons while keeping existing JSON keys unless a spec update says otherwise.
- Text debug output should not alter normal output when `--debug-search` is absent.

## Verification

- `PYTHONPATH=rst2md uv run pytest -q rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_search.py`
- `PYTHONPATH=rst2md uv run pytest -q`
- `PYTHONPATH=rst2md uv run python -m rag.cli diagnostics --db godot_rag/rag/godot_docs.sqlite --no-model --json` when a local release DB exists.
- A fresh clone/tracked-only check should not require `godot_rag/docs-md`.
