---
comet_change: semantic-search-quality-hardening
role: technical-design
canonical_spec: openspec
---

# Semantic Search Quality Hardening Design

## Context

`semantic-search` already has vector storage, query embeddings, and RRF fusion, but the earlier completion quality was mostly structural: tests proved tables and functions existed, while release readiness, relevance quality, performance, and fallback visibility were not hard gates. This change turns those concerns into explicit implementation and verification paths.

## Technical Approach

Use a quality-gate approach rather than another ranking rewrite.

1. **Release database validation**
   Add a release asset validation command or script that checks the CLI default database path, loads `sqlite-vec`, verifies `vec_chunks` exists, and asserts `vec_chunks` row count equals `chunks` row count. Generated DB files remain ignored artifacts and must not be committed.

2. **Golden-query relevance gates**
   Add deterministic golden-query tests with top-K path or symbol-family expectations. These tests should avoid exact ranking assertions so they catch semantic regressions without becoming brittle when the corpus shifts.

3. **Embedding model reuse**
   Cache the model2vec model inside `rag.embeddings`. The public `generate_embeddings(texts, batch_size=...)` API can stay stable while the implementation reuses a process-local model instance. Tests should monkeypatch the loader and prove repeated searches load the model at most once.

4. **Fallback observability**
   Keep normal text output clean. Add lightweight search metadata for JSON/debug paths indicating `hybrid` vs `fts_only` and any fallback reason. Add a `diagnostics` command that checks DB path, extension loading, vector row parity, and model availability.

## Data Flow

Release flow:

1. Generate or refresh documentation Markdown.
2. Build the default CLI database with docs and addons.
3. Generate vectors during `build_database`.
4. Run release DB validation against the default DB path.
5. Keep the generated database local and ignored.

Search flow:

1. Open the selected database.
2. Check vector availability before generating a query embedding.
3. If vector search is usable, generate the query embedding with the cached model and run hybrid/RRF search.
4. If vector search is unavailable, record a fallback reason and run FTS-only search.
5. Return existing `SearchResult` data plus metadata for JSON/debug consumers.

## Key Trade-offs

- Golden-query tests use top-K family assertions, not exact rank, to balance signal and stability.
- The 1 second threshold applies only to warm queries after the model is loaded; cold start and first model download are out of scope for this performance gate.
- Diagnostics are explicit instead of always printed, so ordinary CLI output remains predictable.
- Full release DB validation may be slower than unit tests, so it should be separate from fast fixture-based test runs.

## Testing Strategy

- Unit or fixture tests for model cache reuse.
- Fixture tests for missing `vec_chunks`, missing/unloadable vector search, and vector query failure fallback metadata.
- CLI tests for `diagnostics` and JSON/debug metadata.
- Golden-query tests using deterministic fixture data or a generated test database that does not rely on untracked local state.
- Release validation command that checks default DB vector parity and ignored generated artifacts.

## Spec Patch

The OpenSpec delta spec is updated to make two previously open design choices explicit:

- Warm-query latency must stay below 1 second after model load.
- Fallback observability requires both JSON/debug search metadata and a diagnostics command.
