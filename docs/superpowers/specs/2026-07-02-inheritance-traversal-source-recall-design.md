---
comet_change: inheritance-traversal-source-recall
role: technical-design
canonical_spec: openspec
archived-with: 2026-07-02-inheritance-traversal-source-recall
status: final
---

# Design Doc: Inheritance Traversal Source Recall

## 范围

修复 `Node inherits Object` 查询的生产 gap：C 段 inherits 遍历代码正确但生产静默，因 Node class_summary 不在 top_k=3 候选集，遍历无源可遍历。本设计只动**召回**（让源 chunk 进入候选集），不动遍历代码、不动排序数学。

## 根因（实测确认）

`Node inherits Object` 是糟糕的 FTS 查询：匹配**数百个** class_summary chunk（每个继承链含 `... < Node < Object` 的类都命中三 token）。

- **FTS 分数 cap 在 40.0**：`fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))`，bm25 为负（所有真实匹配）时结果 >40，被 min 截断。所有匹配 chunk 同分 40.0。
- **Vector/RRF 无法区分**：Node class_summary（id=5710，文本含 `**Inherits:** \`Object\``，bm25=-6.169 比 top 结果 -10.484 更好）不在 top-15。实测 top-15 全是 ScrollBar/Slider/PopupPanel 等其他 class_summary（分数 ~36.7-36.96）。
- **top_k=3 窗口**（`searcher.py:312`）只看前 3 → Node 永远进不去 → `searcher.py:384-386` 的 `if result.get("chunk_type") != "class_summary": continue` 跳过所有源 → inherits 遍历不触发 → Object 不被召回 → rank=None。

## 决策

### D1. 类名提取用 PascalCase + DB 验证，不做关键词位置解析

**决策**：按空白分词 → 筛 `^[A-Z][a-zA-Z0-9_]+$`（Godot 类名 PascalCase 约定）→ 对每个候选查 `chunks WHERE symbol=? AND chunk_type='class_summary'` 验证存在 → 召回所有验证通过的。

**理由**：
- 4 种关键词模式（inherits / subclass of / parent class of / derived from）主语位置不同（"X inherits Y" 主语在前，"subclass of X" 主语在后），位置解析需 4 套 regex，脆弱。
- PascalCase + DB 验证不依赖关键词模式，且 DB 验证自动过滤非类名 PascalCase 词（如 "Inherits" 不是 class_summary symbol）。
- "Node inherits Object" → 提取 ["Node","Object"]，两者都验证通过 → 都召回。

**取舍**：
- 召回所有 PascalCase 类名（不只主语）。对 "derived from Object"（语义要找子类，但 inherits 遍历方向是 child→parent），召回 Object 后遍历到 root 无害，且 Object class_summary 本身是有用结果。
- 查询成本：每个 PascalCase token 一次 SQLite 查询，量小（一句话通常 1-2 个），可接受。

### D2. 在 symbol recall 之后、FTS 之前插入 step 3.5

**决策**：插入位置在 `searcher.py` symbol recall（step 1-3，~line 247）之后、FTS（step 4，~line 249）之前。

**理由**：
- 在 sort（line 308）和 graph expansion（line 310+）之前，保证召回的 chunk 进入候选集并参与 top_k。
- 与 symbol recall 同属 intent-gated recall，位置相邻，逻辑连贯。
- 在 FTS 之前：若召回的 chunk 已被 vector/RRF 收入，高分更新 + 追加信号（与 symbol recall 同模式）；FTS 的 `fused_exclude` 不影响（step 3.5 不走 FTS 路径）。

### D3. 分数 90.0，信号 inheritance_recall.class_summary

**决策**：召回的 class_summary 给分 **90.0**，信号名 `inheritance_recall.class_summary`（weight=90.0, value=类名, details={"source":"inheritance_intent_recall"}）。

**理由**：
- 低于 symbol_recall.exact=100（精确符号匹配仍最高优先级）。
- 高于 FTS cap=40 和 RRF~36.8 → 保证进 top_k=3。
- Node class_summary 以 90 分进 rank 1-2 → 进 top_k=3 → inherits 遍历触发 → Object 被 `graph.inherits`（weight=源分*0.7=63）拉入 → 两者 rank ≤ 5。
- 90 是安全初始值；若 eval 显示过度压制其他结果可下调，但当前 top 分 ~36.8，90 有充足余量。

### D4. 门控：仅 plan.inheritance_intent 时触发

**决策**：step 3.5 整体由 `if plan.inheritance_intent:` 门控，与现有 inherits 遍历（line 384）同条件。

**理由**：非继承查询不受任何影响，保证 32 个通过查询零回归。PascalCase 提取只在 inheritance intent 时跑，无副作用。

## 边界条件

| 条件 | 行为 |
|------|------|
| 类名不在 DB | 查询返回空，不召回，不崩溃（与 "no inherits edge does not crash" 同精神） |
| 无 PascalCase token | 不召回，回退正常搜索 |
| 多个类名 | 全召回（Node + Object 都进候选集） |
| chunk 已在结果集 | 高分更新 + 追加信号（与 symbol recall 同模式） |
| 非 inheritance 查询 | `plan.inheritance_intent` 门控，不触发 |

## 测试策略

### TDD Red（复现生产 gap）

构造测试 DB：含 Node、Object class_summary + 若干其他 class_summary（如 ScrollBar，文本含 `Inherits: ... < Node < Object`）。Node class_summary 的 FTS 分被其他 chunk 淹没（不在默认 top-3）。

```python
def test_inheritance_recall_pulls_class_summary_into_top_k():
    # Node class_summary 不在默认 FTS top-3（被 ScrollBar 等淹没）
    # 不实现 step 3.5 时：Node rank > 3 → 遍历不触发 → Object 不在结果 → Red
    results = search_database(db, "Node inherits Object", limit=5, expand_graph=True)
    symbols = [r.symbol for r in results]
    assert "Node" in symbols          # 召回进 top-5
    assert "Object" in symbols        # 遍历拉入
    # 信号存在
    node = next(r for r in results if r.symbol == "Node")
    assert any(s.name == "inheritance_recall.class_summary" for s in node.ranking_signals)
```

当前代码 Red：Node 不在 top-3 → 遍历不触发 → Object 不在结果。

### TDD Green

实现 step 3.5，断言通过。

### 回归

- `uv run pytest -q`：290/0 全套不回归
- `uv run godot-rag eval-search`：Hit@5 ≥ 97.37%、MRR@5 ≥ 87.50%、32 通过查询不回归
- `Node inherits Object`：rank=None → rank ≤ 5

## 不改的部分（binding constraints）

- 不动 inherits 遍历代码（`searcher.py:384-442`，正确）
- 不动排序数学 / RRF k=60 / 嵌入模型 / chunker schema
- 不引入 LLM reranker
- 不新增 eval 查询（保留 38 条基线）
