---
comet_change: search-ranking-signal-explanations
role: technical-design
canonical_spec: openspec
---

# Search Ranking Signal Explanations - Technical Design

## Context

`rst2md/rag/searcher.py` currently combines several ranking signals into the final score, but callers only see the final order plus a small amount of relation metadata. The search pipeline already has enough structure to explain why a result ranked well: symbol recall tiers, hybrid FTS/vector fusion, FTS-only scoring, graph expansion, and deterministic reranking. What is missing is a per-result explanation payload that survives all of those stages.

This change adds structured ranking explanations without changing the ranking algorithm itself. The goal is diagnostic clarity: tests, debug output, and CLI JSON output should be able to say which signals affected a result and by how much.

## Goals / Non-Goals

**Goals:**
- Attach structured ranking signal explanations to each `SearchResult`.
- Preserve `search_database()` compatibility and keep existing `SearchResult` fields available.
- Cover the current signal families: symbol recall, FTS/BM25, hybrid/RRF fusion, graph expansion, and deterministic rerank.
- Make CLI debug and structured output able to display the signals.
- Keep ranking behavior stable unless a bug is uncovered by the added tests.

**Non-Goals:**
- Do not change ranking weights or introduce new retrieval channels.
- Do not change the database schema or persisted search data.
- Do not move explanations into `SearchMetadata` or a separate sidecar map.
- Do not require generated embeddings to be available for explanations.

## Design

### Data model

Add a frozen `RankingSignal` dataclass in `rst2md/rag/models.py` and extend `SearchResult` with an additive field:

```python
@dataclass(frozen=True)
class RankingSignal:
    name: str
    weight: float
    value: float | int | str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    ...
    snippet: str = ""
    ranking_signals: list[RankingSignal] = field(default_factory=list)
```

`ranking_signals` is appended after the existing fields so positional construction stays source-compatible. The default empty list keeps legacy callers and tests working.

Signal payloads must stay JSON-friendly. `details` carries stable context such as the normalized symbol, relation type, graph distance, or the source of a rerank bonus.

### Signal recording

Keep an internal mutable candidate map inside `_search_database_impl()` so each candidate can collect signals while its score is being assembled. Each stage appends a signal only when that stage materially contributes to the candidate:

- Symbol recall records exact, suffix, prefix, and alias-derived matches.
- Hybrid recall records RRF as its own signal when vector search is available.
- FTS-only fallback records the scaled BM25-derived score.
- Graph expansion records the relation type and distance, both for newly introduced results and for results that were already present.
- Rerank records named bonus signals for alias, direct symbol, doc-type intent, and addon intent logic.

When a later stage improves an existing candidate, the new score and the new signal are merged into the same candidate entry rather than replacing the explanation history. That keeps the explanation aligned with the final ranking path.

### Rerank safety

`rerank_results()` uses `dataclasses.replace()`, so signal lists must be copied before appending rerank explanations. A shallow copy is sufficient because the list items are frozen dataclasses, but the list object itself cannot be shared across result instances.

The rerank helper should preserve current score math and ordering, then append one or more non-zero rerank signals to the copied result before returning it.

### CLI output

`rst2md/rag/cli.py` should surface signals in the structured path that already serializes search results to JSON. The default human-readable search output should stay compact and should not print the full signal payload.

For `--debug-search`, the text path may print a concise summary line per result, such as a short list of signal names and their contributions. The JSON path should include the full `ranking_signals` array.

## Key Decisions

### Choose per-result explanations

Explanation data belongs on each `SearchResult`, not on `SearchMetadata`, because the signal set varies per result and must survive result reordering, trimming, and reranking.

### Keep the model additive

The existing `SearchResult` API stays intact. This avoids forcing all callers to learn a new response type or a sidecar explanation lookup.

### Record signals while assembling candidates

Signals are captured at the point where the score is created or improved. Reconstructing the explanation after the fact would lose information about which ranking family contributed.

### Keep rerank explainable

Deterministic rerank should expose its bonuses as explicit signals so tests and diagnostics can tell whether a result was boosted by alias, direct symbol, doc-type intent, or addon intent logic.

## Risks / Trade-offs

- Signal lists can become noisy if every intermediate candidate contributes a separate entry. The implementation should only record stable, material signals.
- `replace()` can accidentally share list state. Copying `ranking_signals` before mutation avoids that bug.
- CLI output can become too verbose if the debug path prints the entire payload. Keep the human summary compact and reserve the full payload for JSON.
- More structured data means more test surface. The benefit is that ranking assertions can now name the signal that drove a result instead of only checking final order.

## Testing Strategy

- Add model tests for `RankingSignal` defaults and `SearchResult` construction compatibility.
- Add search tests for symbol, FTS-only, hybrid/RRF, graph expansion, and rerank explanations.
- Add rerank tests that confirm score ordering is unchanged while signals are appended.
- Add CLI tests for JSON output and the `--debug-search` compact summary path.
- Keep existing search and evaluation tests passing to confirm behavior has not drifted.

## Implementation Boundaries

Primary files:
- `rst2md/rag/models.py`
- `rst2md/rag/searcher.py`
- `rst2md/rag/fusion.py`
- `rst2md/rag/cli.py`
- focused tests under `rst2md/tests/`

Files that should not need semantic changes:
- `rst2md/rag/query_plan.py`
- database schema and indexing modules
- `SearchMetadata`
- `search_database()` call sites

## Spec Alignment

No Spec Patch is required. The existing `intent-ranking` delta spec already requires per-result ranking signal explanations, additive API compatibility, and debug/structured output support.
