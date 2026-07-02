# Comet Design Handoff

- Change: inheritance-traversal-source-recall
- Phase: design
- Mode: compact
- Context hash: 99da9570f1faddbccc38c4a574f4fcfa474e9634462f94bde80a91a7605848df

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/inheritance-traversal-source-recall/proposal.md

- Source: openspec/changes/inheritance-traversal-source-recall/proposal.md
- Lines: 1-30
- SHA256: ae9650869c5d6b40e154695688fbdf00eee32e765b1cdbdbc201be03bb207338

```md
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
```

## openspec/changes/inheritance-traversal-source-recall/design.md

- Source: openspec/changes/inheritance-traversal-source-recall/design.md
- Lines: 1-70
- SHA256: 8b639ef5323b75c4a7e5c9ba328e8ffaaf3a28aa2b9a2c1fe828913675a1fb78

```md
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
```

## openspec/changes/inheritance-traversal-source-recall/tasks.md

- Source: openspec/changes/inheritance-traversal-source-recall/tasks.md
- Lines: 1-23
- SHA256: 75abd5bc881ed35755af2fb07acdb6172cc5f524c6c07ca0b343bf365e324f2c

```md
# Tasks

## 0. 前置基线锁定

- [ ] 0.1 跑 `uv run godot-rag eval-search`，确认 `Node inherits Object` 当前 rank=None；锁定 stage-0 基线到 `docs/search-quality/inheritance-recall-stage-0.json`
- [ ] 0.2 确认 Node / Object `class_summary` chunk 在索引库中的 `symbol` / `heading` / `chunk_type` 字段值（为设计召回查询提供依据）

## 1. 实现召回修复（方案待 design brainstorming 确认）

- [ ] 1.1 设计 brainstorming 确认召回方案（候选 1-4 中选一个或组合）
- [ ] 1.2 实现召回逻辑：inheritance-intent 查询时确保目标 `class_summary` 进入候选集（TDD：Red 测试复现生产 gap — class_summary 不在默认 top-K 时仍被召回）
- [ ] 1.3 跑 `uv run pytest -q` 全套不回归

## 2. 评估验证

- [ ] 2.1 跑 `uv run godot-rag eval-search`，`Node inherits Object` rank ≤ 5；Hit@5 ≥ 97.37%；MRR@5 ≥ 87.50%
- [ ] 2.2 对比 stage-0 基线：32 个原通过查询无回归
- [ ] 2.3 锁定 final 基线到 `docs/search-quality/inheritance-recall-final.json`，更新 `baseline.json`

## 3. 收尾验证

- [ ] 3.1 跑完整 `uv run pytest -q` 全套通过
- [ ] 3.2 准备 verify 阶段材料
```

## openspec/changes/inheritance-traversal-source-recall/specs/intent-ranking/spec.md

- Source: openspec/changes/inheritance-traversal-source-recall/specs/intent-ranking/spec.md
- Lines: 1-33
- SHA256: ba5d787a66acb57c9dbc3aebcfa601c302d892f609ecac38f46242af67efd41c

```md
## MODIFIED Requirements

### Requirement: Inheritance relation traversal in search

When the query plan expresses inheritance intent, search SHALL first ensure that the relevant `class_summary` chunks are present in the candidate set — the query's named classes SHALL be recalled even when their FTS/vector score falls below the default top-K threshold — and SHALL then traverse `inherits` relations from each `class_summary` chunk in the candidate set, adding parent `class_summary` chunks to the result set with a score boost higher than the generic graph-expansion weight.

The recall precondition exists because the directed `inherits` traversal can only fire on source chunks already in the candidate set. Without the precondition, the traversal is vacuously satisfied (no source chunks → no traversal) and the feature delivers no value for inheritance queries whose target `class_summary` is not in the default top-K — which is the observed production gap for `Node inherits Object` (Node `class_summary` absent from top-K → `inherits` traversal never fires → Object `class_summary` never recalled → `rank=None`).

#### Scenario: inheritance query recalls target class_summary into candidate set

- **WHEN** the query "Node inherits Object" is searched with inheritance intent
- **AND** the Node `class_summary` chunk's default FTS/vector score falls below the top-K threshold
- **THEN** the search SHALL still include the Node `class_summary` chunk in the candidate set passed to `inherits` traversal
- **AND** this recall SHALL be scoped to inheritance-intent queries (non-inheritance queries MUST NOT receive this boost)

#### Scenario: inheritance query recalls parent class_summary

- **WHEN** the query "Node inherits Object" is searched with inheritance intent
- **AND** the Node `class_summary` chunk is in the candidate set (per the recall precondition above)
- **THEN** the result set SHALL include the Object `class_summary` chunk
- **AND** the Object chunk SHALL carry a `graph.inherits` ranking signal

#### Scenario: inheritance traversal is scoped to inherits relation

- **WHEN** inheritance intent traversal runs
- **THEN** the SQL query MUST filter `r.relation = 'inherits'` (not generic graph expansion)
- **AND** traversal MUST NOT pull `references`, `see_also`, or `parent` edges via this code path (those remain on the generic graph expansion path)

#### Scenario: no inherits edge does not crash

- **WHEN** inheritance intent is detected but no `inherits` edge exists in the relations table
- **THEN** traversal SHALL return no additional chunks
- **AND** the search SHALL NOT raise an error
```

