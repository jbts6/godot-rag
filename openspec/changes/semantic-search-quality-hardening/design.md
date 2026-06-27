## Context

The previous `semantic-search` change added vector storage, query embeddings, and RRF fusion. Review found that the code path could pass tests while the generated CLI default database lacked vectors, and that failures in the vector path were hard to observe. A small follow-up already prevents embedding generation when `vec_chunks` is missing and removes a generated root database from git tracking.

## Goals / Non-Goals

**Goals:**

- Make the default CLI database generation path explicit and verifiable.
- Add relevance-oriented tests with golden queries.
- Reuse the embedding model within a process and guard warm-query latency.
- Expose vector fallback state for diagnostics without noisy normal output.

**Non-Goals:**

- Change the embedding model.
- Redesign the full RAG ranking architecture.
- Change the generated `README_PYPI.md` strategy.
- Commit generated database binaries.

## Decisions

1. **Use a release asset validation command rather than committed DB files.**
   Generated DBs remain ignored. The workflow should validate row parity and table presence after generation so release readiness is reproducible without adding binaries to git.

2. **Use deterministic golden-query tests.**
   Relevance gates should assert expected path or symbol families within top-K results. This avoids brittle exact ranking while still detecting semantic-quality regressions.

3. **Cache the model in `rag.embeddings`.**
   A process-local cache keeps the public API small and avoids threading model state through every search call. Tests can monkeypatch the loader to verify reuse.

4. **Expose fallback through diagnostics/debug metadata.**
   Normal CLI output should stay clean, but tests and diagnostics need a way to detect whether vector search ran or FTS fallback was used.

## Risks / Trade-offs

- Golden queries can become brittle as the corpus changes -> prefer top-K family assertions and document the corpus fixture.
- Performance tests can be noisy -> use a warm-query threshold and avoid asserting cold-start latency.
- Diagnostics can leak into user output -> keep fallback visibility behind debug/status paths unless explicitly requested.
- Release generation can be slow -> separate fast fixture tests from full release validation.

## Migration Plan

1. Add fixture-level tests for model reuse, fallback observability, and golden-query behavior.
2. Add or update release asset generation/validation commands.
3. Wire generated DB validation into the documented verification flow.
4. Run full tests and a local release DB validation pass.

## Open Questions

- What warm-query latency threshold should be used for local CI on this machine?
- Should fallback visibility be a CLI flag, JSON metadata field, or separate diagnostics command?
