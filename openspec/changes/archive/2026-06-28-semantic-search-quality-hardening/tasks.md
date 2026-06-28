## 1. Relevance Gates

- [x] 1.1 Define a small set of semantic-search golden queries with expected top-K path or symbol families.
- [x] 1.2 Add deterministic relevance tests that do not depend on untracked local-only database state.

## 2. Release Database Validation

- [x] 2.1 Add or update the release database generation flow for the CLI default database path.
- [x] 2.2 Add validation that `vec_chunks` exists and has the same row count as `chunks`.
- [x] 2.3 Verify generated database files remain ignored and are not committed.

## 3. Model Reuse And Performance

- [x] 3.1 Cache the model2vec model inside the embedding layer.
- [x] 3.2 Add a test proving repeated searches load the model at most once per process.
- [x] 3.3 Add a warm-query latency guard with a documented threshold.

## 4. Fallback Observability

- [x] 4.1 Add a debug or diagnostics path that reports vector search availability and fallback reason.
- [x] 4.2 Add tests for missing table, missing extension, and vector query failure fallback behavior.

## 5. Verification

- [x] 5.1 Run the focused semantic-search test suite.
- [x] 5.2 Run the full test suite.
- [x] 5.3 Run the release database validation flow and record the result.
