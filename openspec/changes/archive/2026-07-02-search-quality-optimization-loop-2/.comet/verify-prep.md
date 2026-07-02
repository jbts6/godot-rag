# Verify 阶段准备材料 — 三个 Open Questions 答案

> 对应 `openspec/changes/search-quality-optimization-loop-2/design.md:113-117` 的 Open Questions 节。
> 本文档汇总 A / B / C 三段实现完成后，对三个待验证问题的实际结论，供 verify 阶段直接引用。

---

## Open Question 1 — FLOOR / FACTOR 最终值

**问题（design.md:115）**：`TUTORIAL_BOOST_FACTOR` 最终值是多少？需在 B 段 task 中用 eval 二分：从 5.0 起，每次 ×2（5→10→20），找到让两个 tutorial 查询都进 top 5 的最小值，再向下微调。

**结论**：
- 最终值 `TUTORIAL_SCORE_FLOOR = 3.0`，`TUTORIAL_BOOST_FACTOR = 5.0`
- **与 design.md 初始值一致，无需二分上调**

**证据（B.5 eval）**：
- 初始值（FLOOR=3.0, FACTOR=5.0）即达标
- 两个 tutorial 查询均进 top 5：
  - `scene tree tutorial` → rank=2
  - `how to use scene tree nodes` → rank=1
- 无需执行 5→10→20 的二分搜索

**spec 固化**：`specs/intent-ranking/spec.md:6` 已将下界固化为 `TUTORIAL_SCORE_FLOOR ≥ 3.0`、`TUTORIAL_BOOST_FACTOR ≥ 5.0`，最终值等于下界。

---

## Open Question 2 — Inherits 行格式确认

**问题（design.md:116）**：`class_node.md` 实际 `**Inherits:**` 行的格式是什么？需在 C 段 task 启动时读一份真实 chunk 文本确认。

**结论**：实际格式为 `**Inherits:** \`Object\``（继承目标被反引号包裹），与 `INHERITS_RE` 正则匹配。

**证据**：
- **C.1 门禁通过**：从 `classes/class_node.md` 的 `class_summary` chunk 读到真实文本，含 `**Inherits:** \`Object\`` 行
- `INHERITS_RE`（`rst2md/rag/relations.py:6`）正则匹配成功
- `extract_inherits` 返回 `['Object']`
- **C.2 覆盖测试 PASS**：`build_chunk_relations` 正确创建 `(source=Node, target=Object, relation='inherits', weight=0.8)` 行，断言通过

**对 design.md 风险评估的回应**：design.md:109 担心的"`**Inherits:** Object` 无反引号"格式并未出现，C 段无需回退到 indexer 阶段解析。`relations.py` 现有实现按预期工作，仅补齐了覆盖测试。

---

## Open Question 3 — A 段回归检查结果

**问题（design.md:117）**：A 段拆分后，原 32 个通过查询中是否有因 suffix 误匹配而回归的？需在 A 段 eval 后逐查询检查 `low_ranking` 新增。

**结论**：A 段未引入回归。

**证据**：
- **A.4 回归检查**：`test_searcher_module` + `test_rag_search` 套件 113/0 pass
- **A.6 验收**：
  - symbol 类 hit@5 0.8 → 0.9，达标
  - `Node.connect` rank=2 修复成功
- `*.get` / `*.set` 类短方法名无回归 — design.md 中"不加最小长度守卫"的决策正确
- `ResourceLoader.load` 仍失败（pre-existing，**非 A 段引入的回归**）

**`ResourceLoader.load` 失败根因（pre-existing）**：
- 索引中 `ResourceLoader.load` 符号 chunk 的 FTS5 得分被 `@GDScript.load` / `Image.load` 等同名方法 chunk 压制
- 此为索引阶段 FTS5 BM25 排序的固有问题，与 A 段的 query 归一化逻辑无关
- A 段已成功修复 `Node.connect`（同类问题），证明归一化逻辑本身工作正常
- `ResourceLoader.load` 的彻底修复需要索引阶段或 FTS5 加权调整，超出本 change 范围

---

## Verify 阶段引用指南

| Open Question | 答案 | 关键证据来源 |
|---|---|---|
| 1. FLOOR/FACTOR 最终值 | 3.0 / 5.0（初始值即达标） | B.5-report、`specs/intent-ranking/spec.md:6` |
| 2. Inherits 行格式 | `**Inherits:** \`Object\``，匹配 `INHERITS_RE` | C.1-report、C.2-report |
| 3. A 段回归检查 | 无回归；`ResourceLoader.load` 为 pre-existing | A.4-report、A.6-report |
