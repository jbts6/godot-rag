## Why

当前搜索质量闭环已经有 45 条评估查询、延迟指标、搜索执行元数据和拆分后的 searcher 边界，但 20 条 `report_only` 查询仍只是“观察项”。在继续调整 ranking、alias 或 intent scoring 前，需要先把这些观察项按数据缺口、召回、低排名、过滤和 degraded search mode 分类，避免把数据问题误判为 ranking 问题。

## What Changes

- 为 `eval-search` 增加面向 `report_only` 查询的 triage 输出或可复用分类结构。
- 对每个 `report_only` 查询给出明确状态：可考虑晋升 gating、需要数据/fixture、需要 recall/ranking 改进、需要 filter 修正，或受 degraded vector mode 影响。
- 产出后续优化候选清单，明确哪些查询适合进入 ranking signal explainability、query alias expansion 或数据补齐 change。
- 保持现有 25 条 gating 查询行为不退化，不在本 change 中调整 ranking 权重或 alias 规则。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `search-quality-diagnostics`: 增加 report-only 查询 triage 与后续优化候选分类要求。

## Impact

- 主要影响 `rst2md/rag/search_eval.py`、`rst2md/rag/search_eval_queries.json`、`rst2md/rag/cli.py` 中的 `eval-search` 诊断输出，以及对应测试。
- 不改变 `search_database` public API、数据库 schema、embedding 模型或 searcher ranking 权重。
- 后续 change 可基于 triage 结果安全进入 ranking signal、query rewrite 或 fixture 数据补齐。
