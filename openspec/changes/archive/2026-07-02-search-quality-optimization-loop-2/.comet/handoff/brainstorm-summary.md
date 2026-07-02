# Brainstorm Summary

- Change: search-quality-optimization-loop-2
- Date: 2026-07-01

## 确认的技术方案

基于 OpenSpec open 阶段 design.md 的三处 brainstorming 修订（已用户确认）：

### A 段：符号查询归一化（不变）
- `expand_query_variants` 加 dot-notation 拆分：`Class.method` / `Class.method()` → 追加方法后缀变体
- 正则：`^[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\(?\s*$`
- 无最小长度守卫（YAGNI；eval 回归时再补）
- 例：`Node.connect` → `["Node.connect", "connect"]`；`ResourceLoader.load()` → `["ResourceLoader.load()", "load"]`

### B 段：Tutorial boost 改地板 + multiplicative（修订）
- 原设计：`new_score = score * FACTOR`（纯 multiplicative）
- **修订为**：`new_score = max(score, FLOOR) * FACTOR`，FLOOR≈3.0、FACTOR≈5.0
- 公式拆解：bonus = `max(score, FLOOR) * (FACTOR - 1)`，reranked_score = `score + bonus` = `score + max(score, FLOOR) * (FACTOR - 1)`
  - 当 `score >= FLOOR`：reranked = `score * FACTOR`（与原设计一致）
  - 当 `score < FLOOR`：reranked = `score + FLOOR * (FACTOR - 1)`（地板救起低分）
- 失败案例验证：tutorial score=0.66，FLOOR=3, FACTOR=5 → reranked = 0.66 + 3*4 = 12.66 > class 9.91 ✓
- `doc_type_boost` 函数保留但返回 0.0；移除 `not plan.symbol_candidates` 守卫外的所有 tutorial 加权路径
- eval 二分：FLOOR 候选 [2, 3, 5]；FACTOR 候选 [3, 5, 7, 10]；目标两 tutorial 查询进 rank ≤5 且 32 原通过查询不回归

### C 段：继承图扩展（修订关键词集）
- `_inheritance_intent(query)` 关键词：**4 个** `inherits` / `subclass of` / `parent class` / `derived from`（去掉 `extends`）
- 整词、大小写不敏感匹配
- `QueryPlan` 加 `inheritance_intent: bool` 字段
- searcher 加定向 `inherits` 关系遍历：`WHERE r.relation = 'inherits'`，score = `child_result.score * 0.7`
- 前置：补 `build_chunk_relations` 覆盖测试（codegraph 标记无覆盖）

## 关键取舍与风险

- **B 地板方案**：低分 tutorial 救得起、高分不 overshoot；代价是 FLOOR + FACTOR 二维 eval 二维调参。
- **A 无守卫**：依赖 bm25 在多个 +80 命中之间排序；`Node.get` 类短方法名查询有噪音风险，eval 暴露后再加守卫。
- **C 去 `extends`**：唯一 eval 失败查询用 `inherits`，不影响验收；真 "Class extends Class" 查询不触发（罕见）。
- **全局**：三段串行依赖基线，每段后跑 eval 锁定增量；任何段导致 32 原通过查询回归 ≥1 立即回滚。

## 测试策略

- **A**：`test_searcher_module.py` 加 `expand_query_variants` 拆分单元测试（4 场景：Class.method / Class.method() / 非符号 dot / 数字 dot）；32 查询 eval 不回归。
- **B**：`test_searcher_module.py` 改 `doc_type_boost` 测试为返回 0.0；新增 `_rerank_bonus` 地板公式测试（3 场景：低分救起 / 高分不 overshoot / symbol 候选存在时不触发）；tutorial 类 hit@5 71%→100%。
- **C**：`test_rag_search.py` 加 `build_chunk_relations` 覆盖测试（首次）；加 `_inheritance_intent` 单元测试（4 关键词 + 1 误判场景）；加 `Node inherits Object` 端到端测试。
- **集成**：每段后 `uv run godot-rag eval-search` 输出存 `docs/search-quality/loop-2-stage-{A|B|C}.json`；最终存 `loop-2-final.json` 替换 `baseline.json`。

## Spec Patch

将回写的 delta spec 变更：

1. **`specs/intent-ranking/spec.md`** MODIFIED "Tutorial intent detection"：
   - 场景 "Tutorial boost is multiplicative on result score" 修订：bonus 公式从 `result.score * (FACTOR-1)` 改为 `max(result.score, FLOOR) * (FACTOR-1)`，reranked_score = `result.score + max(result.score, FLOOR) * (FACTOR-1)`
   - 新增场景 "Low tutorial score is floored before boost"：当 `result.score < FLOOR` 时，reranked = `result.score + FLOOR * (FACTOR-1)`
   - 常量 `TUTORIAL_BOOST_FACTOR` 改为 `TUTORIAL_BOOST_FACTOR` (≥5.0) + `TUTORIAL_SCORE_FLOOR` (≥3.0) 双常量

2. **`specs/intent-ranking/spec.md`** ADDED "Inheritance intent detection"：
   - 关键词列表从 5 词改为 4 词：`inherits` / `subclass of` / `parent class` / `derived from`
   - 场景 "synonym keywords trigger inheritance intent" 修订：去掉 "extends"
   - 新增场景 "bare verb 'extends' does not trigger inheritance intent"：query "how to extend Node functionality" → `inheritance_intent == False`

3. **`specs/query-rewrite/spec.md`**：不变（A 段决策无修订）
