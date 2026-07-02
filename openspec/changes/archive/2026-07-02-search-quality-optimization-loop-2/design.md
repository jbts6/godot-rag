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
JOIN chunks c ON c.id = r.target_id
WHERE r.source_id = ? AND r.relation = 'inherits'
```

把命中的父类 class_summary 加入 results，score = `result.score * 0.7`（高于通用图扩展的 `* 0.5`，确保进入 top results）。

**替代方案**（已否决）：
- 全局 2-hop 图扩展：噪音大，会把 see_also/references 间接边也拉进来。
- 在 indexer 阶段把 parent_class 作为 chunk 字段：数据 schema 变更，违反非目标。

### C2. 补 `build_chunk_relations` 覆盖测试

codegraph 标记 `build_chunk_relations` 无覆盖测试。在 `rst2md/tests/test_rag_search.py` 或新建 `test_relations.py` 加测试：构造含 `**Inherits:** \`Object\`` 的 class_summary chunk + `Object` class_summary chunk，调用 `build_chunk_relations`，断言 `chunk_relations` 表有 `(source=Node_class_summary, target=Object_class_summary, relation='inherits', weight=0.8)` 行。

这是 C1 的前置：先证明边已写入，再证明 searcher 能遍历到。

### 验证策略（三段共享）

每段 task 完成后：
1. `uv run pytest -q rst2md/tests/` 全套不回归。
2. `uv run godot-rag eval-search` 跑 38 查询，对比 baseline.json。
3. 记录 delta 到 `docs/search-quality/<loop-2-stage-A|B|C>.json`（新增文件，不覆盖 baseline.json）。
4. 任何一段导致 32 个原通过查询回归 ≥1 个，立即回滚该段权重或拆分逻辑，重新二分。

## Risks / Trade-offs

- **[A 风险] 方法后缀过短引发误匹配**：如 `Node.get` 拆出 `get`，suffix `%.get` 可能匹配大量 `*.get` 方法。 → 缓解：suffix 查询本身已有 +80 分阈值，且最终排序仍受 RRF/bm25 调节；eval 验证 32 个原通过查询不回归。
- **[B 风险] multiplicative factor 过大压垮 class hit@1**：tutorial intent 查询若也命中了相关 class 文档（如 "how to use Node"），class 结果可能被压到 tutorial 之后。 → 缓解：`not plan.symbol_candidates` 守卫 + factor 由 eval 二分，目标是"刚好让 tutorial 进 top 5"而非最大化。
- **[C 风险] `**Inherits:**` 实际格式不匹配 `INHERITS_RE`**：如果 Godot RST 转换后用了不同的标记（如 `**Inherits:** Object` 无反引号），`extract_inherits` 返回空列表，边根本未写入。 → 缓解：C2 测试用真实格式样本；若发现格式不一致，C1 改为在 indexer 阶段直接解析（届时需修改非目标，回到 design 重新决策）。
- **[全局风险] 三段串行依赖基线**：B 依赖 A 完成后的基线（否则 B 的回归无法区分是 B 自身还是 A 残留），C 依赖 B 完成后的基线。 → 缓解：tasks.md 明确三段顺序，每段后写 delta 基线文件。
- **[范围风险] C 可能需要补 indexer**：若 C2 测试发现 inherits 边根本未写入，需要回退到 indexer/rst.py 改解析。届时本 change 范围扩大，需在 design 补充决策。

## Open Questions

1. `TUTORIAL_BOOST_FACTOR` 最终值是多少？需在 B 段 task 中用 eval 二分：从 5.0 起，每次 ×2（5→10→20），找到让两个 tutorial 查询都进 top 5 的最小值，再向下微调。
2. `class_node.md` 实际 `**Inherits:**` 行的格式是什么？需在 C 段 task 启动时读一份真实 chunk 文本确认。
3. A 段拆分后，原 32 个通过查询中是否有因 suffix 误匹配而回归的？需在 A 段 eval 后逐查询检查 `low_ranking` 新增。
