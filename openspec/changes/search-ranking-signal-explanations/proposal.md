## Why

Search ranking now combines symbol recall, FTS/BM25, vector/RRF fusion, graph expansion, and deterministic reranking, but callers only receive final scores and sparse relation metadata. This makes it hard to diagnose why a result ranked highly, why expected results were demoted, or which existing ranking signal should be adjusted.

## What Changes

- Add structured ranking signal explanations to search results so each returned result can describe the major signals that affected its final rank.
- Preserve the existing `search_database()` compatibility surface while exposing explanations through metadata-bearing search responses and CLI/debug output.
- Ensure explanations cover existing signal families: symbol matches, hybrid retrieval/RRF, FTS scoring, graph expansion, and deterministic reranking.
- Extend tests so ranking assertions can validate named signals instead of depending only on final order.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `intent-ranking`: Search results expose named ranking signals and explanation metadata for deterministic ranking and reranking behavior.

## Impact

- Affected code: `rst2md/rag/models.py`, `rst2md/rag/searcher.py`, `rst2md/rag/fusion.py` or reranking helpers if needed, `rst2md/rag/cli.py`, and focused tests under `rst2md/tests/`.
- APIs: `search_database_with_metadata()` may return richer result metadata; `search_database()` should remain source-compatible for existing callers.
- Dependencies: no new runtime dependencies expected.
- Systems: search quality diagnostics and CLI/debug output can consume the explanations, but the ranking algorithm itself should remain behaviorally stable unless tests reveal existing unexplained signal gaps.
