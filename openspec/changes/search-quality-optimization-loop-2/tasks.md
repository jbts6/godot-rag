## 0. 前置基线锁定

- [x] 0.1 跑 `uv run godot-rag eval-search` 在当前代码上跑 38 查询，把输出存为 `docs/search-quality/loop-2-stage-0-baseline.json`（即当前 baseline.json 的副本，作为三段对比的起点）
- [x] 0.2 确认 32 个通过查询的 hit@5 / hit@1 / mrr@5 数值与 `baseline.json` 一致；6 个失败查询的 `failure_classification` 与 `matched_rank` 一致

## 1. A 段：符号查询归一化（dot-notation 拆分）

- [ ] 1.1 在 `rst2md/rag/query_rewrite.py` 的 `expand_query_variants` 增加点号拆分逻辑：query 匹配 `^[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\(?\s*$` 时，追加方法后缀变体（最后一个 `.` 之后的部分，去掉末尾 `()`）。保留原 query 作为第一个变体
- [x] 1.2 在 `rst2md/tests/test_searcher_module.py` 加单元测试：`Node.connect` → `["Node.connect", "connect"]`；`ResourceLoader.load()` → `["ResourceLoader.load()", "load"]`；`scene_tree.tutorial` → 单元素（不拆分）；`v2.1` → 单元素（不拆分）
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
