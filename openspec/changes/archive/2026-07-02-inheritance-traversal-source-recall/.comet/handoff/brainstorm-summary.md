# Brainstorm Summary

- Change: inheritance-traversal-source-recall
- Date: 2026-07-02

## 确认的技术方案

**类名提取 + 定向 class_summary 召回**（用户确认）

在 `_search_database_impl` 的 symbol recall（step 1-3）之后、FTS（step 4）之前，插入 **step 3.5: inheritance-intent class_summary recall**（仅 `plan.inheritance_intent` 时触发）。

- **类名提取**：按空白分词 → 筛 `^[A-Z][a-zA-Z0-9_]+$`（PascalCase）→ 对每个候选查 `chunks WHERE symbol=? AND chunk_type='class_summary'` 验证存在 → 召回所有验证通过的。绕过 4 种关键词模式的主语位置差异；非类名 PascalCase 词被 DB 验证过滤。
- **召回机制**：`SELECT * FROM chunks WHERE symbol=? AND chunk_type='class_summary'`，分数 **90.0**（低于 symbol_recall.exact=100，高于 FTS cap=40 / RRF~36.8），信号 `inheritance_recall.class_summary`。已在结果集的 chunk：高分更新 + 追加信号（与 symbol recall 同模式）。
- **效果**：Node class_summary 以 90 分进 top_k=3 → inherits 遍历触发 → Object 被 `graph.inherits` 拉入 → 两者 rank ≤ 5。

## 关键取舍与风险

- **分数 90 的选择**：保证进 top_k=3（当前 top 分 ~36.8）又不过度压过精确符号匹配（100）。可调，但 90 是安全初始值。
- **PascalCase 提取 vs 关键词位置解析**：PascalCase + DB 验证更鲁棒（不依赖关键词模式），但召回所有 PascalCase 类名（如 "Node inherits Object" 召回 Node + Object 两者），对"derived from Object"这类要找子类而非父类的语义不完全匹配——但 inherits 遍历方向是 child→parent，召回 Object 后遍历到 root 无害，且把 Object class_summary 召回本身就是有用结果。
- **不污染非继承查询**：`plan.inheritance_intent` 门控，PascalCase 提取只在 inheritance intent 时跑。
- **DB 验证的成本**：每个 PascalCase token 一次 SQLite 查询。查询量小（一句话通常 1-2 个 PascalCase 词），可接受。

## 测试策略

- **Red**：构造 DB，Node class_summary 的 FTS 分被其他 chunk 淹没（不在默认 top-3），断言 `search_database(db, "Node inherits Object")` 含 Node 且 rank ≤ 3。当前代码 Red。
- **Green**：实现 step 3.5，断言通过；新信号 `inheritance_recall.class_summary` 存在。
- **回归**：`uv run pytest -q` 290/0；`eval-search` Hit@5 ≥ 97.37%、MRR@5 ≥ 87.50%、32 通过查询不回归。
- **边界**：类名不在 DB → 不召回不崩溃；无 PascalCase token → 回退正常搜索。

## Spec Patch

无。delta spec 已有 "recall target class_summary into candidate set" 场景覆盖本方案；实现细节（PascalCase 提取、分数 90、信号名）属实现层不入 spec。
