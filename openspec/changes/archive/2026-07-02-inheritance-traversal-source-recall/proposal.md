## Why

The inheritance traversal feature shipped in `search-quality-optimization-loop-2` (C段) works in unit tests but is **silent in production for its target query**. `Node inherits Object` still returns `rank=None` because the Node `class_summary` chunk does not enter the top-K candidate set, so the directed `inherits` traversal has no source chunk to traverse from. The feature is "done" per spec and green in tests, but delivers zero value for the query it was built to fix. This was documented as WARNING 2 in the loop-2 verification report and deferred to a future loop; this change tracks that gap.

## What Changes

- Ensure inheritance-intent queries recall the relevant `class_summary` chunks into the candidate set so the existing `inherits` traversal can fire.
- The directed traversal code itself is correct and unchanged — the gap is purely in **source recall** (getting the class_summary chunk into top-K before traversal runs).
- No change to ranking math, RRF k, embeddings, or chunker schema (same binding constraints as loop-2).

## Capabilities

### New Capabilities

_(None.)_

### Modified Capabilities

- `intent-ranking`: the "Inheritance relation traversal in search" requirement currently says traversal runs "from each class_summary chunk in the top-K candidate set" — which is vacuously satisfied when no class_summary is in top-K. Add a recall precondition: inheritance-intent queries SHALL ensure relevant `class_summary` chunks are present in the candidate set before traversal runs.

## Impact

- **Affected code**: `rst2md/rag/searcher.py` (candidate assembly / recall path for inheritance intent), possibly `rst2md/rag/query_plan.py` (expose class names parsed from the query).
- **Affected specs**: `openspec/specs/intent-ranking/spec.md` (Inheritance relation traversal requirement gains a recall precondition).
- **Evaluation**: `Node inherits Object` query must move from `rank=None` to `rank ≤ 5` (loop-2 original C段 goal, unmet). No regression on the 32 passing queries (Hit@5 ≥ 97.37%).
- **Dependencies**: None new. Builds on the `_inheritance_intent` detector and directed `inherits` SQL already in place from loop-2.
- **Open design questions** (deferred to design phase):
  1. Recall approach: lower FTS threshold for class_summary on inheritance intent? Add a class_summary-specific recall path? Re-rank class_summary into top-K pre-traversal? Widen top-K for inheritance-intent queries?
  2. How to extract the class name(s) from the query (e.g., "Node" from "Node inherits Object") to target recall.
  3. Whether the generic graph-expansion path (which also failed to pull Node in) needs the same treatment.
