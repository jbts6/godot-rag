---
comet_change: search-quality-optimization-loop-2
role: technical-design
canonical_spec: openspec
archived-with: 2026-07-02-search-quality-optimization-loop-2
status: final
---

# Design Doc: Search Quality Optimization Loop 2

**Date**: 2026-07-01
**OpenSpec change**: `openspec/changes/search-quality-optimization-loop-2/`
**Canonical spec**: `openspec/changes/search-quality-optimization-loop-2/design.md` + `specs/{query-rewrite,intent-ranking}/spec.md`

## 范围

本 Design Doc 是 comet-design 阶段 brainstorming 验证后的技术设计快照。OpenSpec `design.md` 是事实源；本文档记录 brainstorming 对 `design.md` 的三处修订与决策依据，并标注需回写的 Spec Patch。

完整背景（基线数据、根因定位、原 5 项决策 A1/A2/B1/B2/C1/C2）见 OpenSpec `design.md`。本文档仅记录 brainstorming 阶段的**修订点**。

## 修订 1：B 段 tutorial boost 改"地板 + multiplicative"

### 原决策（OpenSpec design.md）

`_rerank_bonus` 对 tutorial 命中：`bonus = result.score * (FACTOR - 1)`，即 `reranked = result.score * FACTOR`（纯 multiplicative）。

### 问题识别

失败案例数据显示 tutorial doc pre-rerank score 极低（0.66），class doc score 9.91~39.66：

| 结果 | doc_type | score | ×5 | ×15 | ×20 |
|------|----------|-------|----|----|-----|
| StringName | class | 39.66 | 39.66（不 boost）| 39.66 | 39.66 |
| scene tree tutorial | tutorial | 0.66 | 3.3 | 9.9 | 13.2 |

纯 multiplicative 需 FACTOR=20 才能让 tutorial 0.66 压过 class 9.91。但 FACTOR=20 应用到 score=5 的 tutorial 命中变 100，撞 symbol exact 阈值；应用到 score=10 的 tutorial 命中变 200，overshoot。

### 修订决策

**公式**：`reranked = result.score + max(result.score, FLOOR) * (FACTOR - 1)`

- 当 `score >= FLOOR`：`reranked = score * FACTOR`（与原设计一致）
- 当 `score < FLOOR`：`reranked = score + FLOOR * (FACTOR - 1)`（地板救起低分）

**常量**：`TUTORIAL_SCORE_FLOOR = 3.0`，`TUTORIAL_BOOST_FACTOR = 5.0`（初始值，eval 二分确定）

**失败案例验证**：tutorial score=0.66 → reranked = 0.66 + 3*4 = 12.66 > class 9.91 ✓

### 取舍

- **优点**：低分救起、高分不 overshoot、保留 tutorial 间 bm25 排序信号
- **代价**：FLOOR + FACTOR 二维 eval 二维调参（候选 FLOOR ∈ {2, 3, 5}，FACTOR ∈ {3, 5, 7, 10}）

### Spec Patch

`specs/intent-ranking/spec.md` MODIFIED "Tutorial intent detection" + "Deterministic reranking uses query-plan signals"：
- 场景 "Tutorial boost is multiplicative on result score" 修订：bonus 公式改为 `max(result.score, FLOOR) * (FACTOR - 1)`
- 新增场景 "Low tutorial score is floored before boost"
- 常量从单一 `TUTORIAL_BOOST_FACTOR` 改为 `TUTORIAL_BOOST_FACTOR` + `TUTORIAL_SCORE_FLOOR`

## 修订 2：A 段短方法名不加守卫

### 决策

`expand_query_variants` 拆分 dot-notation 时不加最小长度守卫。`Node.get` 拆出 `get`，suffix `%.get` 命中多个类的 `get` 方法，依赖 bm25 在 +80 平分中排序。

### 取舍

- **优点**：实现最简；`Node.get` 合法查询不被误伤
- **风险**：短方法名 suffix 噪音大；eval 回归时若 `*.get`/`*.set` 类查询受影响再补守卫
- **依据**：YAGNI — 不提前优化未确认问题

### Spec Patch

`specs/query-rewrite/spec.md`：**不变**。A 段决策与 OpenSpec design.md 一致。

## 修订 3：C 段 inheritance intent 去掉 `extends` 关键词

### 原决策（OpenSpec design.md）

`_inheritance_intent` 检测 5 个关键词：`inherits` / `extends` / `subclass of` / `parent class` / `derived from`。

### 问题识别

`extends` 是常见英文词：
- "Node extends Object" → 真继承查询，应触发
- "how to extend Node functionality" → 非继承，但词根匹配会误触发

虽然实际无 `inherits` 边时 traversal 是 no-op，但语义不对，且会让 `_inheritance_intent` 字段在 tutorial intent 查询上误亮。

### 修订决策

**关键词集**：4 个无歧义词 `inherits` / `subclass of` / `parent class` / `derived from`，去掉 `extends`。

**失败查询覆盖**：唯一 eval 失败 `Node inherits Object` 用 `inherits`，不受影响。

### 取舍

- **优点**：零误判；spec 验收场景明确
- **代价**：真 "Class extends Class" 查询不触发（罕见；出现时再加模式约束 `Class 关键词 Class`）

### Spec Patch

`specs/intent-ranking/spec.md` ADDED "Inheritance intent detection"：
- 关键词列表从 5 词改为 4 词
- 场景 "synonym keywords trigger inheritance intent" 修订：去掉 "extends"
- 新增场景 "bare verb 'extends' does not trigger inheritance intent"

## 测试策略

### A 段
- 单元：`test_searcher_module.py` 加 `expand_query_variants` 4 场景（Class.method / Class.method() / 非符号 dot / 数字 dot）
- 集成：32 查询 eval 不回归；`ResourceLoader.load` / `Node.connect` 命中 rank ≤3

### B 段
- 单元：`test_searcher_module.py` 改 `doc_type_boost` 测试为返回 0.0；新增 `_rerank_bonus` 3 场景（低分救起 / 高分不 overshoot / symbol 候选存在时不触发）
- 集成：tutorial 类 hit@5 71%→100%；`scene tree tutorial` / `how to use scene tree nodes` 命中 rank ≤5

### C 段
- 单元：`test_rag_search.py` 加 `build_chunk_relations` 覆盖测试（首次，codegraph 标记无覆盖）；`_inheritance_intent` 5 场景（4 关键词 + 1 `extends` 误判）
- 集成：`Node inherits Object` 命中 rank ≤5；class 类 hit@5 保持 100%

### 段间增量
- 每段后 `uv run godot-rag eval-search` 输出存 `docs/search-quality/loop-2-stage-{A|B|C}.json`
- 最终 `loop-2-final.json` 替换 `baseline.json`

## 边界条件

- A 段正则要求前段大写开头、后段小写或下划线开头，避免 `scene_tree.tutorial` 误拆
- B 段 multiplicative 仍受 `not plan.symbol_candidates` 守卫保护，符号查询不触发
- C 段 `inherits` 整词匹配（`\b` 边界），避免 `non-inherits` 等误匹配
- C 段 traversal 只过滤 `r.relation = 'inherits'`，不混入 `parent` / `references` / `see_also`

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| B 段 FLOOR + FACTOR 组合不收敛 | 候选集小（3×4=12 组），eval 二分可在 6 次运行内确定 |
| A 段短方法名噪音 | eval 跑 32 查询，`*.get` 类回归立刻暴露 |
| C 段 `**Inherits:**` 格式不匹配 `INHERITS_RE` | C 段 task 3.1 先读真实 chunk 文本确认；不匹配则回 design 补 indexer 决策 |
| 三段串行依赖基线 | tasks.md 明确顺序，每段后写 delta 基线文件 |

## Open Questions（保留到 build 阶段实测确认）

1. `TUTORIAL_SCORE_FLOOR` 与 `TUTORIAL_BOOST_FACTOR` 最终值（候选 FLOOR ∈ {2,3,5}，FACTOR ∈ {3,5,7,10}）
2. `class_node.md` 实际 `**Inherits:**` 行格式（C 段 task 3.1 确认）
3. A 段拆分后 32 个原通过查询中 `*.get`/`*.set` 类是否回归（A 段 task 1.6 检查）
