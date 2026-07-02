# Design: inheritance-traversal-source-recall

## Context

The directed `inherits` traversal shipped in `search-quality-optimization-loop-2` (C段) works in unit tests but is **silent in production** for its target query `Node inherits Object` (still `rank=None`).

Root cause is in `rst2md/rag/searcher.py:384-386`:

```python
if plan.inheritance_intent:
    for result in sorted_results[:top_k]:      # top_k = min(3, len)
        if result.get("chunk_type") != "class_summary":
            continue
        # traverse 'inherits' edges from this class_summary
```

The traversal only fires on `class_summary` chunks already in the **top 3** of the sorted candidate set. For `Node inherits Object`, the Node `class_summary` chunk does not rank in the top 3 (and may not be in the returned set at all), so the `continue` skips every source and no `inherits` edge is traversed → Object `class_summary` is never recalled → `rank=None`.

The traversal code itself is correct. The gap is purely **source recall**: getting the Node `class_summary` into the candidate set before traversal runs.

Recall paths today for `Node inherits Object`:
- **Symbol recall** (`searcher.py:182-247`): `expand_query_variants` produces no symbol for this natural-language query → no exact/suffix/prefix symbol match.
- **Vector search** (if available): semantic similarity — may or may not surface the Node `class_summary`.
- **FTS5 bm25** (`searcher.py:249-305`): tokenizes to `Node AND inherits AND Object` → the Node `class_summary` text (`# Node ... **Inherits:** \`Object\``) matches but is outranked by other chunks.

## Goals / Non-Goals

**Goals**:
- `Node inherits Object` query returns the Node `class_summary` (and via traversal, the Object `class_summary`) within rank ≤ 5.
- No regression on the 32 passing queries (Hit@5 ≥ 97.37%, MRR@5 ≥ 87.50%).
- Recall boost is scoped to inheritance-intent queries only (non-inheritance queries unaffected).

**Non-Goals**:
- Do not change the directed `inherits` traversal code (it is correct).
- Do not change ranking math, RRF k (60), embeddings, or chunker schema.
- Do not introduce LLM reranker.
- Do not add new eval queries (keep 38-query baseline).

## Candidate Approaches (to be decided in design brainstorming)

1. **Class-name extraction + targeted class_summary recall**: parse the class name(s) from the inheritance query (e.g., "Node" from "Node inherits Object"), then query `chunks WHERE chunk_type='class_summary' AND symbol/heading MATCH 'Node'` to force-recall the Node `class_summary` into the candidate set before traversal.
2. **Lower top-K threshold / widen top-K for inheritance intent**: increase `top_k` (currently 3) for inheritance-intent queries so more `class_summary` chunks are eligible as traversal sources.
3. **Pre-traversal class_summary boost**: re-rank `class_summary` chunks higher when `inheritance_intent` is set, so they enter top-K.
4. **Hybrid**: extract class names AND boost — targeted recall guarantees presence, boost ensures top-K position.

## Constraints

- `top_k = min(3, ...)` is shared with generic graph expansion; widening it affects all queries unless gated.
- Class-name extraction must handle natural-language forms: "X inherits Y", "subclass of X", "parent class of X", "derived from X" — the class name position varies.
- The Node `class_summary` chunk's `symbol` and `heading` fields are the lookup keys; need to confirm their values in the indexed DB.

## Risks / Trade-offs

- **Over-recall**: force-recalling class_summary chunks for inheritance queries could push out more relevant chunks for the 32 passing queries.
- **Class-name extraction fragility**: natural-language parsing may misidentify the class name (e.g., "what is the parent class of Timer" → "Timer" not "parent class").
- **Scope creep**: the generic graph-expansion path also failed to pull Node in; fixing only the inheritance path may leave a parallel gap.

## Open Questions (deferred to brainstorming)

1. Which candidate approach (or combination) best balances recall guarantee vs. regression risk?
2. How to robustly extract the subject class name from the 4 inheritance keyword patterns?
3. Should the generic graph-expansion top-K (3) be widened, or only the inheritance-traversal source set?
4. What are the actual `symbol`/`heading`/`chunk_type` values of the Node and Object `class_summary` chunks in the indexed DB?

## Verification Strategy

- Lock a stage-0 baseline confirming `Node inherits Object` rank=None (and the 32 passing queries' current ranks).
- After implementation: `Node inherits Object` rank ≤ 5; Hit@5 ≥ 97.37%; MRR@5 ≥ 87.50%.
- Unit test: inheritance-intent query with a class_summary NOT in default top-K still recalls it (the production gap scenario, not just the unit test where Node is force-included).
- Full `uv run pytest -q` suite: 290/0 no regression.
