# Comet Design Handoff

- Change: search-quality-optimization-loop-2
- Phase: design
- Mode: compact
- Context hash: 001cd70dad3a8f769e5ba05ee88947ead1e75f088f63cfa0ddb9befd978d2bc6

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/search-quality-optimization-loop-2/proposal.md

- Source: openspec/changes/search-quality-optimization-loop-2/proposal.md
- Lines: 1-31
- SHA256: da63225131a545024bbb2137b1bd2be730139dcae61118898dd2c2ed9fc5dd02

```md
## Why

`docs/search-quality/baseline.json` 记录 38 个查询中 6 个失败（Hit@5 89.5%，MRR@5 80.5%）。剩余失败分三类，各自阻塞不同的搜索质量维度：符号查询归一化（2 个 `query_normalization` 失败）、tutorial 排序（2 个 `low_ranking` + 最弱类 hit@5 仅 71%）、继承关系召回（1 个 `missing_recall`）。这三类已分别定位到具体代码位置，可在本轮一次性收回，把整体 Hit@5 推到 94%+。

**不拆分为三个独立 change 的原因**：三项共享同一验证机制（`eval-search` + `baseline.json`），按 A→B→C 串行实施并在每段后跑 eval 锁定增量，可在单 change 内保留归因；而三次 Comet 仪式的固定开销大于共享验证带来的合并风险。

## What Changes

- **A. 符号查询归一化**：`expand_query_variants`（`rst2md/rag/query_rewrite.py`）增加对 `Class.method` / `Class.method()` 形式的识别，把点号查询归一化为符号候选；FTS5/符号查询路径使用该候选，使 `ResourceLoader.load`、`Node.connect` 能命中索引中的 `Class.method` chunk 符号。
- **B. Tutorial 排序加权**：`doc_type_boost`（`rst2md/rag/query_rewrite.py`）和 `fusion._rerank_bonus` 的 tutorial 权重从 0.05 上调至可压过 class 文档 bm25 优势的水平；具体数值由 `eval-search` 二分确定，最终值写入 spec 作为下界。
- **C. 继承图扩展**：`rst2md/rag/relations.py` 暴露类继承边（如已由 indexer 写入则仅补查询路径），`searcher` 图扩展把父类文档拉入候选，使 `Node inherits Object` 命中 `Object` 类文档。

非目标：不动向量嵌入模型与权重；不改 RRF k 值；不引入 LLM reranker；不重构 searcher 主流程；不改 chunker/indexer 数据 schema（除非 C 证明继承边根本未写入）。

## Capabilities

### New Capabilities

无。三类修改均落在既有 capability 上。

### Modified Capabilities

- `query-rewrite`：扩展符号归一化要求，覆盖 `Class.method` 与 `Class.method()` 形式，使其进入 `symbol_candidates` 并能驱动符号召回。
- `intent-ranking`：tutorial intent 的 rerank 权重不再固定为 0.05；改为按"足以压过 class 文档 bm25 优势"的可调值，并在 spec 中固化下界。同时增加继承关系图扩展的召回要求，使 `Class inherits Parent` 形式查询能命中父类文档。

## Impact

- **代码**：`rst2md/rag/{query_rewrite,query_plan,fusion,relations,searcher}.py`；可能涉及 `retrieval.py` 视 FTS5 查询构造方式而定（design 阶段确认）。
- **数据**：若 C 证明继承边当前未由 indexer 写入，则需补 `rst2md/rst.py` 解析与 `indexer.py` 写入；此分支在 design 阶段判定，本 proposal 暂不承诺。
- **测试**：`rst2md/tests/test_searcher_module.py`、`test_rag_search.py`、`test_search_eval.py` 增量；`search_eval_queries.json` 不新增查询（保留 38 条基线对比）。
- **回归风险**：tutorial 加权上调可能压低 class 查询的 hit@1；用 eval 在每段后验证 32 个通过查询不回归（hit@5 不低于 89.5%）。
```

## openspec/changes/search-quality-optimization-loop-2/design.md

- Source: openspec/changes/search-quality-optimization-loop-2/design.md
- Lines: 1-117
- SHA256: 0ed18301c6bb3377cafb750a0de8b6c4d728ed720376813d2815fad988dbe8e0

[TRUNCATED]

```md
## Context

`docs/search-quality/baseline.json` 当前 38 查询 6 失败（Hit@5 89.5%，MRR@5 80.5%）。三类失败已通过 codegraph 定位到具体代码路径：

- **A. 符号查询归一化**：`ResourceLoader.load`、`Node.connect` 返回 `matched_rank: null`。
  - 已确认 `expand_query_variants`（`query_rewrite.py:32`）仅基于 `_ALIAS_RULES` 派生变体，对 `Class.method` 形式不拆分。
  - 已确认 `_canonical_form`（`symbols.py:17`）保留 `.`，所以 `Node.connect` → `node.connect`。
  - 已确认 searcher `_search_database_impl`（`searcher.py:182-247`）对 `symbol_candidates` 走 exact → suffix → prefix 三段查询。Suffix 查询用 `LIKE '%.{normalized}'`，对 `Node.connect`（normalized=`node.connect`）产生 pattern `%.node.connect`，**匹配不到 `Object.connect`**（normalized=`object.connect`，不以 `.node.connect` 结尾）。
  - 真实根因：`Node` 类自身没有 `connect` 方法（继承自 `Object`），所以索引中没有 `Node.connect` 符号。用户查 `Node.connect` 实际想要"Node 上可用的 connect 方法"，应当匹配到祖先类 `Object.connect`。
- **B. Tutorial 排序**：`scene tree tutorial`（rank 8）、`how to use scene tree nodes`（rank 10）。
  - 已确认 `_doc_type_intent`（`query_plan.py:9`）正确识别这两个查询为 tutorial intent。
  - 已确认 `doc_type_boost`（`query_rewrite.py:17`）与 `_rerank_bonus`（`fusion.py:49-59`）的 tutorial 权重都是 0.05（additive）。
  - 已确认失败案例中 class 文档 FTS5 scaled 得分 9.91~39.66，tutorial 文档得分 0.66；+0.05 完全无效。
- **C. 继承图扩展**：`Node inherits Object` 返回 `matched_rank: null`（`missing_recall`）。
  - 已确认 `relations.py:39-48` **已经**从 `**Inherits:**` 行提取继承边并写入 `chunk_relations`（weight=0.8），但 `build_chunk_relations` 无覆盖测试（codegraph 标记）。
  - 已确认 `searcher.py:310-352` 图扩展从 top-K（K=3）结果出发，按 weight DESC 取前 5 条关系，**不区分 relation 类型**。
  - 推测根因：top-K 通常包含 `Node` 的成员方法 chunk（如 `Node.add_child`），从这些 chunk 出发的图查询命中 `parent` 边（weight 1.0）→ `Node` class_summary，**`inherits` 边只在从 `Node` class_summary 出发时才被遍历**，而 class_summary chunk 本身可能不在 top-K。
  - 待验证：实际 `class_node.md` 的 `**Inherits:**` 行格式是否匹配 `INHERITS_RE`，以及 `Node` class_summary chunk 是否被 FTS5 召回。

## Goals / Non-Goals

**Goals**：
- A：`ResourceLoader.load`、`Node.connect` 命中 rank ≤3；symbol 类 hit@5 80%→90%+。
- B：`scene tree tutorial`、`how to use scene tree nodes` 命中 rank ≤5；tutorial 类 hit@5 71%→100%。
- C：`Node inherits Object` 命中 rank ≤5；class 类 hit@5 保持 100%。
- 整体：Hit@5 89.5%→94%+，MRR@5 80.5%→85%+，32 个现有通过查询不回归（hit@5 不低于 89.5%）。
- 每段 task 后跑 `eval-search` 锁定增量基线，归因清晰。

**Non-Goals**：
- 不动向量嵌入模型、不重训、不改嵌入维度。
- 不改 RRF k 值（60）。
- 不引入 LLM reranker。
- 不重构 searcher 主流程结构（仅加分支与权重）。
- 不改 chunker 数据 schema（C 的修复在 relations/searcher 层，不动 chunker）。
- 不新增 eval 查询（保留 38 条基线对比）。

## Decisions

### A1. 在 `expand_query_variants` 拆分点号查询

修改 `rst2md/rag/query_rewrite.py` 的 `expand_query_variants`：当 query 匹配 `^[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\(?\s*$` 时，追加一个变体 = 方法后缀（最后一个 `.` 之后的部分，去掉末尾 `()`）。

例：`Node.connect` → 变体 `["Node.connect", "connect"]`；`ResourceLoader.load()` → `["ResourceLoader.load()", "load"]`。

`_symbol_candidates`（`query_plan.py:30`）会把这两个变体都 normalize 后加入 `symbol_candidates`。searcher 现有 suffix 查询 `LIKE '%.{normalized}'` 对 `connect`（normalized=`connect`）产生 pattern `%.connect`，**匹配 `Object.connect`**。

`Class.method()` 形式已被 `_canonical_form` 的 `rstrip("()")` 处理，无需额外逻辑。

**替代方案**（已否决）：
- 在 searcher 里直接拆分 query：违反"query_rewrite 是变体生成的唯一入口"约定。
- 拆出所有部分（Class + method）：Class 单独太泛，会引入噪音。

### A2. 防止 over-split 误伤

仅当点号两侧符合"大写开头类名 + 小写开头方法名"模式时拆分。`scene_tree.tutorial` 这种不会触发拆分（前段非大写开头）。同时保留原 query 作为第一个变体，exact 查询仍会尝试 `Node.connect` 整体匹配。

### B1. Tutorial 改 additive 为 multiplicative

修改 `rst2md/rag/fusion.py` 的 `_rerank_bonus` 和 `_rerank_signals`：当 `plan.doc_type_intent` 非空且 `result.doc_type == plan.doc_type_intent` 且 `not plan.symbol_candidates` 时，bonus 从 `+0.05` 改为 `result.score * (TUTORIAL_BOOST_FACTOR - 1)`（即把原 score 放大 `TUTORIAL_BOOST_FACTOR` 倍）。

`TUTORIAL_BOOST_FACTOR` 初始值 5.0（让 score 0.66 → 3.3，仍低于 9.91，所以可能需要 15.0+，由 eval 二分确定）。最终值在 spec 中固化为下界。

`doc_type_boost`（`query_rewrite.py:17`）保留函数签名但返回 0.0（避免破坏 3 个 caller 与现有测试），所有 tutorial 加权改走 rerank 的 multiplicative 路径。更新对应单元测试。

**替代方案**（已否决）：
- 大 additive boost（+10）：bm25 scaled 得分绝对值在不同查询间差异大，固定 additive 难以泛化。
- 硬过滤（intent 命中时只返回 tutorial）：会压制 "how to use Node" 这类既含 tutorial intent 又需要 Node 类信息的查询。

### B2. 防止 class 查询被 tutorial intent 误伤

`_doc_type_intent` 已有 `"." in query or "_" in query` 短路（line 11-12），符号查询不会触发 tutorial intent。保留此守卫。同时 multiplicative bonus 条件包含 `not plan.symbol_candidates`，双重保护。

### C1. 继承 intent 检测 + 定向 inherits 遍历

修改 `rst2md/rag/query_plan.py` 加 `_inheritance_intent(query)`：检测 `inherits`、`extends`、`subclass of`、`parent class`、`derived from` 等关键词，返回 bool。在 `QueryPlan` 加 `inheritance_intent: bool` 字段。

修改 `rst2md/rag/searcher.py` `_search_database_impl` 图扩展段：当 `plan.inheritance_intent` 为 True 时，对 top-K 结果中每个 `chunk_type == "class_summary"` 的 chunk，**额外**跑一次定向查询：

```sql
SELECT c.*, r.relation, r.weight FROM chunk_relations r
```

Full source: openspec/changes/search-quality-optimization-loop-2/design.md

## openspec/changes/search-quality-optimization-loop-2/tasks.md

- Source: openspec/changes/search-quality-optimization-loop-2/tasks.md
- Lines: 1-46
- SHA256: 103d883ffade29ee9e1d158ef61e171ed62b147dd96dcf0ed60d36298fa2c404

```md
## 0. 前置基线锁定

- [ ] 0.1 跑 `uv run godot-rag eval-search` 在当前代码上跑 38 查询，把输出存为 `docs/search-quality/loop-2-stage-0-baseline.json`（即当前 baseline.json 的副本，作为三段对比的起点）
- [ ] 0.2 确认 32 个通过查询的 hit@5 / hit@1 / mrr@5 数值与 `baseline.json` 一致；6 个失败查询的 `failure_classification` 与 `matched_rank` 一致

## 1. A 段：符号查询归一化（dot-notation 拆分）

- [ ] 1.1 在 `rst2md/rag/query_rewrite.py` 的 `expand_query_variants` 增加点号拆分逻辑：query 匹配 `^[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\(?\s*$` 时，追加方法后缀变体（最后一个 `.` 之后的部分，去掉末尾 `()`）。保留原 query 作为第一个变体
- [ ] 1.2 在 `rst2md/tests/test_searcher_module.py` 加单元测试：`Node.connect` → `["Node.connect", "connect"]`；`ResourceLoader.load()` → `["ResourceLoader.load()", "load"]`；`scene_tree.tutorial` → 单元素（不拆分）；`v2.1` → 单元素（不拆分）
- [ ] 1.3 验证 `_symbol_candidates`（`query_plan.py:30`）对 `["Node.connect", "connect"]` 输出两个去重候选 `("Node.connect", "connect")`
- [ ] 1.4 跑 `uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py` 确认 A 段单元测试通过且无回归
- [ ] 1.5 跑 `uv run godot-rag eval-search`，把输出存为 `docs/search-quality/loop-2-stage-A.json`
- [ ] 1.6 验证 `ResourceLoader.load` 与 `Node.connect` 命中 rank ≤3；symbol 类 hit@5 80%→90%+；32 个原通过查询 hit@5 不低于 89.5%。若有回归，记录是哪个查询、分析是否需要给方法后缀加最小长度守卫

## 2. B 段：Tutorial 排序改 multiplicative

- [ ] 2.1 在 `rst2md/rag/fusion.py` 加模块常量 `TUTORIAL_BOOST_FACTOR = 5.0`（初始值，待 eval 二分上调）
- [ ] 2.2 修改 `_rerank_bonus`（`fusion.py:49`）：当 `plan.doc_type_intent` 非空且 `result.doc_type == plan.doc_type_intent` 且 `not plan.symbol_candidates` 时，bonus 从 `+0.05` 改为 `result.score * (TUTORIAL_BOOST_FACTOR - 1)`
- [ ] 2.3 同步修改 `_rerank_signals`（`fusion.py:62`）记录 `rerank.doc_type_intent` 信号的 weight 为新的 bonus 值（保持信号名不变，weight 跟随 bonus）
- [ ] 2.4 修改 `rst2md/rag/query_rewrite.py` 的 `doc_type_boost`：tutorial intent 分支返回 0.0（保留函数签名与守卫逻辑，避免破坏 3 个 caller 与现有测试）
- [ ] 2.5 更新 `rst2md/tests/test_searcher_module.py` 中 `doc_type_boost_prefers_tutorial_for_how_to_query` 测试，断言新返回值为 0.0；新增测试断言 `_rerank_bonus` 对 tutorial 命中返回 `result.score * (TUTORIAL_BOOST_FACTOR - 1)`
- [ ] 2.6 跑 `uv run pytest -q rst2md/tests/` 全套不回归
- [ ] 2.7 跑 `uv run godot-rag eval-search`，factor=5.0 时若两个 tutorial 查询未达 rank ≤5，把 factor 上调到 10.0 重跑；仍未达则上调到 20.0；找到最小可行值后向下微调（如 15.0、12.0）。把最终值写入 `fusion.py` 常量与 spec 注释
- [ ] 2.8 把 eval 输出存为 `docs/search-quality/loop-2-stage-B.json`
- [ ] 2.9 验证 `scene tree tutorial` 与 `how to use scene tree nodes` 命中 rank ≤5；tutorial 类 hit@5 71%→100%；A 段通过的查询不回归

## 3. C 段：继承图扩展（inherits 边定向遍历）

- [ ] 3.1 读一份真实 `class_node.md` chunk 文本（用 `sqlite3` 查 chunks 表，path=`classes/class_node.md` 且 chunk_type=`class_summary`），确认 `**Inherits:**` 行格式匹配 `INHERITS_RE`（`rst2md/rag/relations.py:6`）。若不匹配，暂停 C 段，回到 design 补" indexer 阶段解析"决策
- [ ] 3.2 在 `rst2md/tests/test_rag_search.py` 加 `build_chunk_relations` 覆盖测试：构造 `Node` class_summary chunk（含 `**Inherits:** \`Object\``）+ `Object` class_summary chunk，调用 `build_chunk_relations`，断言 `chunk_relations` 表存在 `(source=Node_id, target=Object_id, relation='inherits', weight=0.8)` 行
- [ ] 3.3 在 `rst2md/rag/query_plan.py` 加 `_inheritance_intent(query: str) -> bool`：检测 `inherits`、`extends`、`subclass of`、`parent class`、`derived from` 关键词（大小写不敏感，整词匹配）
- [ ] 3.4 在 `QueryPlan` dataclass 加 `inheritance_intent: bool` 字段；`build_query_plan` 调用 `_inheritance_intent` 填充
- [ ] 3.5 在 `rst2md/tests/test_searcher_module.py` 加测试：`Node inherits Object` → `plan.inheritance_intent == True`；`Node connect` → False；`tutorial scene tree` → False
- [ ] 3.6 在 `rst2md/rag/searcher.py` `_search_database_impl` 图扩展段（line 310-352 之后）加定向 inherits 遍历分支：当 `plan.inheritance_intent` 为 True 时，对 top-K 中每个 `chunk_type == "class_summary"` 的结果，跑 `SELECT c.*, r.relation, r.weight FROM chunk_relations r JOIN chunks c ON c.id = r.target_id WHERE r.source_id = ? AND r.relation = 'inherits'`，把命中 chunk 加入 results，score = `result.score * 0.7`，记录 `graph.inherits` 信号
- [ ] 3.7 在 `rst2md/tests/test_rag_search.py` 加端到端测试：建小型 fixture DB（含 Node class_summary + Object class_summary + 继承边），搜索 `Node inherits Object`，断言 Object class_summary 出现在结果中且 rank ≤5
- [ ] 3.8 跑 `uv run pytest -q rst2md/tests/` 全套不回归
- [ ] 3.9 跑 `uv run godot-rag eval-search`，把输出存为 `docs/search-quality/loop-2-stage-C.json`
- [ ] 3.10 验证 `Node inherits Object` 命中 rank ≤5；class 类 hit@5 保持 100%；A/B 段通过的查询不回归

## 4. 收尾验证

- [ ] 4.1 跑完整 `uv run pytest -q` 全套测试通过
- [ ] 4.2 跑 `uv run godot-rag eval-search`，把最终输出存为 `docs/search-quality/loop-2-final.json`
- [ ] 4.3 对比 `loop-2-stage-0-baseline.json` 与 `loop-2-final.json`：6 个原失败查询至少 5 个进入 rank ≤5（最后一个允许仍失败但需记录原因）；整体 Hit@5 ≥ 94%；MRR@5 ≥ 85%
- [ ] 4.4 更新 `docs/search-quality/baseline.json` 为 loop-2-final 的内容（成为新基线）
- [ ] 4.5 准备 verify 阶段所需材料：design.md 中三个 Open Questions 的答案（factor 最终值、Inherits 行格式确认、A 段回归检查结果）
```

## openspec/changes/search-quality-optimization-loop-2/specs/intent-ranking/spec.md

- Source: openspec/changes/search-quality-optimization-loop-2/specs/intent-ranking/spec.md
- Lines: 1-102
- SHA256: c051c2d2f55f818af2a903254844b25dcfb9c6f3c593d4a624a33c28fdc42160

[TRUNCATED]

```md
## MODIFIED Requirements

### Requirement: Tutorial intent detection
The system SHALL detect tutorial intent from query patterns. The legacy fixed additive boost (`doc_type_boost` returning 0.05 for tutorial doc_type) SHALL be replaced by a floor-plus-multiplicative rerank boost applied in `_rerank_bonus`. The `doc_type_boost` function SHALL return 0.0 for all inputs (retained for backward compatibility with existing callers and tests) and the substantive tutorial weighting SHALL move to the rerank stage.

The boost SHALL use two tunable constants: `TUTORIAL_SCORE_FLOOR` (minimum pre-rerank score eligible for multiplicative treatment, default ≥ 3.0) and `TUTORIAL_BOOST_FACTOR` (multiplicative factor, default ≥ 5.0). Both SHALL be set to the smallest combination that lifts both `scene tree tutorial` and `how to use scene tree nodes` queries into rank ≤5 on the canonical baseline, with spec-fixed lower bounds.

The rerank bonus formula SHALL be `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`, yielding a reranked score of `result.score + max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`. When `result.score >= TUTORIAL_SCORE_FLOOR`, this reduces to `result.score * TUTORIAL_BOOST_FACTOR`. When `result.score < TUTORIAL_SCORE_FLOOR`, the floor lifts the effective base so that low-bm25 tutorial results can still overtake high-bm25 class results.

#### Scenario: How-to query triggers tutorial intent
- **WHEN** a query starts with "how to " or contains " tutorial", " guide", or "learn "
- **THEN** `_doc_type_intent` SHALL return "tutorial"
- **AND** `doc_type_boost` SHALL return 0.0 for all doc types (legacy function retained but neutralized)
- **AND** `_rerank_bonus` SHALL apply a floor-plus-multiplicative boost to tutorial doc_type results when no symbol candidates exist in the plan

#### Scenario: Symbol query does not trigger intent boost
- **WHEN** a query contains "." or "_" (symbol-like pattern)
- **THEN** `_doc_type_intent` SHALL return None
- **AND** `_rerank_bonus` SHALL NOT apply the tutorial boost to any result

#### Scenario: Tutorial boost is floored multiplicative on result score
- **WHEN** `_rerank_bonus` is called for a result whose `doc_type == "tutorial"` and the plan has tutorial intent and no symbol candidates
- **THEN** the bonus SHALL equal `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- **AND** the reranked score SHALL equal `result.score + max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- **AND** the bonus SHALL be recorded as a named ranking signal `rerank.doc_type_intent` with weight equal to the bonus amount

#### Scenario: Low tutorial score is floored before boost
- **WHEN** `_rerank_bonus` is called for a tutorial result whose `result.score < TUTORIAL_SCORE_FLOOR` (e.g., score=0.66, FLOOR=3.0, FACTOR=5.0)
- **THEN** the reranked score SHALL equal `result.score + TUTORIAL_SCORE_FLOOR * (TUTORIAL_BOOST_FACTOR - 1)` (e.g., 0.66 + 3*4 = 12.66)
- **AND** the reranked score MUST be able to overtake class-doc results with bm25-scaled scores up to `TUTORIAL_SCORE_FLOOR * (TUTORIAL_BOOST_FACTOR - 1)` (e.g., 12.0)

#### Scenario: High tutorial score is not overshooting
- **WHEN** `_rerank_bonus` is called for a tutorial result whose `result.score >= TUTORIAL_SCORE_FLOOR` (e.g., score=5.0, FLOOR=3.0, FACTOR=5.0)
- **THEN** the reranked score SHALL equal `result.score * TUTORIAL_BOOST_FACTOR` (e.g., 25.0)
- **AND** the reranked score MUST remain below the symbol exact-match score (100.0) so that symbol candidates, when present, are not suppressed

### Requirement: Deterministic reranking uses query-plan signals
Search SHALL apply deterministic reranking signals after candidate assembly and before returning final results. For tutorial intent, the reranking SHALL be floor-plus-multiplicative rather than purely additive so that tutorial results with low lexical scores can overtake class results with high bm25 scores when the user expresses tutorial intent.

#### Scenario: alias symbol match is promoted
- **WHEN** a candidate result symbol exactly matches a query-plan alias-derived symbol candidate
- **THEN** reranking MUST increase that candidate's final rank relative to candidates without symbol, path, heading, or intent matches

#### Scenario: tutorial intent floored-multiplicative promotes tutorial results
- **WHEN** a query expresses tutorial intent (e.g., "scene tree tutorial") and a candidate result has `doc_type == "tutorial"`
- **THEN** reranking MUST apply bonus `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)` (defaults FLOOR ≥ 3.0, FACTOR ≥ 5.0)
- **AND** the candidate MUST be able to overtake class-doc results whose bm25-scaled scores would otherwise dominate under additive-only boosting

#### Scenario: doc-type intent remains constrained
- **WHEN** a query expresses tutorial intent
- **THEN** reranking MUST prefer tutorial results without suppressing exact symbol matches for symbol-like queries

#### Scenario: addon intent can be represented without gating unstable data
- **WHEN** a query expresses addon intent
- **THEN** reranking MUST expose addon intent as a ranking signal
- **AND** evaluation MUST keep addon queries report-only unless expected addon rows exist in the canonical database

## ADDED Requirements

### Requirement: Inheritance intent detection
The system SHALL detect inheritance intent from query patterns and surface it on the query plan so that the searcher can apply targeted `inherits`-relation traversal. Inheritance intent SHALL be triggered by the keywords `inherits`, `subclass of`, `parent class`, and `derived from` (case-insensitive, whole-word/whole-phrase matching). The bare verb `extends` SHALL NOT trigger inheritance intent to avoid false positives on queries like "how to extend Node functionality".

#### Scenario: inherits keyword triggers inheritance intent
- **WHEN** a query contains the token "inherits" (case-insensitive) as a whole word (e.g., "Node inherits Object")
- **THEN** `_inheritance_intent` SHALL return True
- **AND** the query plan SHALL set `inheritance_intent = True`

#### Scenario: synonym phrases trigger inheritance intent
- **WHEN** a query contains any of the phrases "subclass of", "parent class", or "derived from" (case-insensitive)
- **THEN** `_inheritance_intent` SHALL return True
- **AND** the query plan SHALL set `inheritance_intent = True`

#### Scenario: bare verb extends does not trigger inheritance intent
- **WHEN** a query contains the word "extends" or "extend" but NOT in the `Class extends Class` form (e.g., "how to extend Node functionality")
- **THEN** `_inheritance_intent` SHALL return False
- **AND** the query plan SHALL set `inheritance_intent = False`

#### Scenario: non-inheritance query does not trigger
- **WHEN** a query does not contain any inheritance keyword (e.g., "Node connect", "tutorial scene tree")
- **THEN** `_inheritance_intent` SHALL return False
```

Full source: openspec/changes/search-quality-optimization-loop-2/specs/intent-ranking/spec.md

## openspec/changes/search-quality-optimization-loop-2/specs/query-rewrite/spec.md

- Source: openspec/changes/search-quality-optimization-loop-2/specs/query-rewrite/spec.md
- Lines: 1-45
- SHA256: 4432235d7f230cec95760795cf386bb1124af89249c2e44ea55a2a6d4549eab5

```md
## MODIFIED Requirements

### Requirement: Conservative query alias expansion
The system SHALL expand natural-language queries into structured query-plan variants that include the original query plus any matching symbol aliases. For dot-notation symbol queries (`Class.method` or `Class.method()`), the system SHALL additionally append a method-suffix variant (the substring after the last `.` with trailing `()` stripped) so that suffix symbol recall can match inherited methods on ancestor classes.

The method-suffix variant SHALL only be appended when the segment before the `.` starts with an uppercase letter (class-like) and the segment after the `.` starts with a lowercase letter or underscore (method-like). This prevents over-splitting on non-symbol queries that happen to contain a dot.

#### Scenario: Known alias pattern matches
- **WHEN** a query contains tokens matching an alias rule (e.g., "attach node to scene tree")
- **THEN** `expand_query_variants` SHALL return the original query followed by the matching symbol alias (e.g., "Node.add_child")
- **AND** the query plan SHALL expose the matching symbol alias as a symbol candidate

#### Scenario: No alias matches
- **WHEN** a query does not match any alias rule
- **THEN** `expand_query_variants` SHALL return a single-element list containing only the original query
- **AND** the query plan SHALL expose no alias-derived symbol candidate

#### Scenario: Dot-notation symbol query produces method-suffix variant
- **WHEN** a query is a dot-notation symbol form matching `^[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\(?\s*$` (e.g., "Node.connect", "ResourceLoader.load()")
- **THEN** `expand_query_variants` SHALL return the original query followed by the method-suffix variant (e.g., "Node.connect" → ["Node.connect", "connect"]; "ResourceLoader.load()" → ["ResourceLoader.load()", "load"])
- **AND** the query plan SHALL expose both the full dot-notation form and the method-suffix form as symbol candidates

#### Scenario: Non-symbol dot query is not split
- **WHEN** a query contains a dot but does not match the Class.method pattern (e.g., "scene_tree.tutorial" where the prefix is not uppercase, or "v2.1" where the suffix is numeric)
- **THEN** `expand_query_variants` SHALL NOT append a method-suffix variant
- **AND** the query plan SHALL expose only the original query

### Requirement: Query plan exposes structured search intent
The system SHALL build a structured query plan for each search query before recall and ranking. For dot-notation symbol queries, the query plan SHALL expose both the full dot-notation form and the method-suffix form so that exact and suffix symbol lookup can each evaluate both candidates.

#### Scenario: alias query creates symbol candidates
- **WHEN** a query contains tokens matching an alias rule such as "attach node to scene tree"
- **THEN** the query plan MUST include the original query
- **AND** it MUST include `Node.add_child` as an alias-derived symbol candidate

#### Scenario: exact dot-notation symbol query produces full and suffix candidates
- **WHEN** a query is a dot-notation symbol such as "Node.connect"
- **THEN** the query plan MUST include the original query
- **AND** it MUST include `Node.connect` as a symbol candidate (for exact symbol lookup)
- **AND** it MUST include `connect` as a symbol candidate (for suffix symbol lookup against inherited methods like `Object.connect`)

#### Scenario: unknown query keeps original text
- **WHEN** a query does not match any alias or symbol rule
- **THEN** the query plan MUST preserve the original query text
- **AND** it MUST expose no alias-derived symbol candidates
```

