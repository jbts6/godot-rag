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
