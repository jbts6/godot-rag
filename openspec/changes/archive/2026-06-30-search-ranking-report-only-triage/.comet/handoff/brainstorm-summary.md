# Brainstorm Summary

- Change: search-ranking-report-only-triage
- Date: 2026-06-30

## 确认的技术方案

在 `search_eval.py` 的评估诊断层增加 report-only triage，而不是改动 searcher/ranking。评估阶段继续执行当前查询、诊断和 baseline 流程；当查询为 `report_only` 且有 diagnostic window 时，生成结构化 triage 结果。

核心结构建议：

- `ReportOnlyTriage`：承载 query id、classification、evidence、recommended_followup。
- classification 固定为 `promotion_ready`、`missing_expected_data`、`missing_recall`、`low_ranking`、`filter_mismatch`、`degraded_search`。
- evidence 复用 `FailureDiagnostics` 和 observed top results：expected_present、best_rank、search_mode、fallback_reason、observed。
- JSON report 作为权威机器可读输出；text report 输出精简摘要。

## 关键取舍与风险

- 不把 triage 放进 `SearchMetadata`，避免把评估工作流概念泄漏到 runtime search API。
- 不自动修改 `search_eval_queries.json`，promotion 只给候选建议，避免 baseline 策略被诊断命令隐式改变。
- 分类集保持小而确定，便于测试和后续自动聚合。
- 风险：某些 report-only 查询可能多原因失败。缓解：按保守优先级分类，并输出证据供人工复核。
- 风险：现有 spec 曾提 graph expansion，但当前 searcher 无 graph expansion 实现。缓解：不新增 graph 行为，只基于现有诊断字段分类。

## 测试策略

- 先写失败测试覆盖每个分类分支。
- 覆盖 JSON 输出包含 report-only triage。
- 覆盖 text 输出包含精简 triage summary。
- 覆盖 promotion-ready 只作为 advisory，不自动修改 query suite。
- 回归验证现有 gating evaluation、baseline comparison 和 searcher module tests。

## Spec Patch

无。当前 delta spec 已包含 report-only triage requirement 与四个验收场景。
