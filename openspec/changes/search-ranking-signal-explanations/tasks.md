## 1. Model and Compatibility

- [x] 1.1 Add a structured ranking signal model to `rst2md/rag/models.py`.
- [x] 1.2 Add default-empty ranking explanations to `SearchResult` without breaking existing construction.
- [x] 1.3 Extend model shape tests to cover ranking signal defaults and serialization-friendly fields.

## 2. Search Signal Recording

- [x] 2.1 Record symbol recall signals for exact, suffix, prefix, and alias-derived matches.
- [x] 2.2 Record hybrid/RRF and FTS scoring signals during candidate assembly.
- [x] 2.3 Record graph expansion signals including relation type and distance.
- [ ] 2.4 Preserve accumulated signals when later ranking stages improve an existing candidate.

## 3. Rerank Signal Recording

- [ ] 3.1 Update deterministic reranking to append named non-zero bonus signals.
- [ ] 3.2 Preserve existing rerank score math and final ordering behavior.

## 4. CLI and Diagnostics Output

- [ ] 4.1 Expose ranking signals in structured or debug search output.
- [ ] 4.2 Keep default human-readable search output concise and backward-compatible.

## 5. Verification

- [ ] 5.1 Add focused tests for symbol, FTS fallback, hybrid/RRF, graph expansion, and rerank explanations.
- [ ] 5.2 Run focused searcher, CLI, and search evaluation tests.
- [ ] 5.3 Run the broader pytest suite if focused tests pass and runtime is practical.
