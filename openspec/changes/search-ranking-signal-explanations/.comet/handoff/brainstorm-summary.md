# Brainstorm Summary

- Change: search-ranking-signal-explanations
- Date: 2026-06-30

## 确认的技术方案

采用方案 A：在 `SearchResult` 上追加结构化 `ranking_signals` 列表，让每条结果携带自己的解释。

- `RankingSignal` 采用小型冻结 dataclass，表达 `name`、`weight`、`value`、`details` 等字段。
- searcher 在候选结果组装、graph expansion、rerank 阶段逐步追加命名信号。
- rerank 使用 `replace()` 时必须复制 `ranking_signals`，避免可变 list 被多个结果共享。
- CLI 的结构化输出路径会携带 `ranking_signals`；默认人类可读输出保持简洁，不额外膨胀。

## 已确认约束

- 保持 `search_database()` 和现有 `SearchResult` 字段兼容。
- 不重调排序权重，不新增召回通道，不改数据库 schema。
- 信号必须覆盖 symbol、FTS/BM25、hybrid/RRF、graph expansion、deterministic rerank。
- `rst2md/rag/cli.py` 已有 `_result_to_dict()`、`--json` 和 `--debug-search` 输出路径，后续实现应优先扩展这些路径。

## 候选方案

- 候选 A：在 `SearchResult` 直接添加 `ranking_signals`，各排序阶段追加信号。
- 候选 B：只在 `SearchResponse.metadata` 放解释索引或 sidecar map。
- 候选 C：新增 debug-only explain API，不修改常规结果模型。

## 关键取舍与风险

- 候选 A 最直接、最可测试，但需要小心 dataclass 默认值和 rerank `replace()` 时的列表复制。
- 候选 B 对结果模型侵入较小，但解释是 per-result 数据，sidecar 容易和结果排序/裁剪脱节。
- 候选 C 对默认路径最保守，但测试和诊断会走不同路径，容易漂移。

## 测试策略

覆盖模型默认值、各类信号记录、rerank 行为不变、结构化输出包含信号、默认人类可读输出保持原样。

## Spec Patch

当前暂无新的 Spec Patch 候选。

## 待确认问题

- 无。`--debug-search` 的人类可读文本输出会打印极简信号摘要，完整信号仍在 JSON/结构化输出中提供。
