# Brainstorm Summary

- Change: search-quality-evaluation-expansion
- Date: 2026-06-29

## 确认的技术方案

采用三层推进，不先调整 ranking：

1. 评估集层：先 audit 当前 `search_eval_queries.json`，补到至少 40 条 unique query、25 条 gating、10 条 report-only。新增场景优先覆盖 `class`、`symbol`、`tutorial`、`engine`、`addon`、normalization、graph、filter precision。所有不稳定或依赖缺失 canonical 数据的查询保持 report-only。
2. 指标/诊断层：在 `evaluate_database` 外围测每条 query elapsed time，汇总 p50/p95；把 search mode、fallback/degraded reason 带进失败诊断和 JSON/text report。只追加字段，保留现有输出字段。
3. 结构安全层：本 change 只定义并测试搜索器等价拆分边界；如做拆分，也必须保持现有 ranking/baseline 不变。alias/ranking/embedding 模型优化放后续 change。

## 关键取舍与风险

- latency 指标会受本机波动影响，所以首版以可观察和可配置阈值为主，不默认设过窄硬阈值。
- gating 扩容有误伤风险，所以新增查询必须先证明 expected target 存在且稳定；否则 report-only。
- 搜索器结构拆分容易扩大范围，所以本 change 不把完整重构和 ranking 优化混在一起。

## 测试策略

- 更新 `test_search_eval.py` 覆盖 query suite 数量、类别、tag、filter precision、latency JSON/text 字段、fallback/degraded diagnostics。
- 更新 CLI/evaluator 测试覆盖新增输出字段和 baseline 兼容。
- 跑 focused search quality/evaluator tests，再跑全量 `rtk uv run pytest -q`。
- 如果本地 release DB 可用，跑 `eval-search --baseline docs/search-quality/baseline.json --compare-graph`。

## Spec Patch

已回写到 OpenSpec delta specs：

- `openspec/changes/search-quality-evaluation-expansion/specs/semantic-search-quality/spec.md`
- `openspec/changes/search-quality-evaluation-expansion/specs/search-quality-diagnostics/spec.md`
