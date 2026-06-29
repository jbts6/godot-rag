# Brainstorm Summary

- Change: search-quality-optimization-loop
- Date: 2026-06-29

## 确认的技术方案

1. **Query Rewrite（D1）**：`expand_query_variants()` 仅用于 FTS 召回，vector search 继续使用原始查询。5 条保守别名规则，token 子集匹配。
2. **Intent Boost（D2）**：`doc_type_boost()` 在候选组装后、最终排序前应用。tutorial 结果 +0.05 boost，symbol 查询（含 `.` 或 `_`）不触发。
3. **Tiered Queries（D3）**：利用现有 `report_only` 字段。≥12 gating queries 必须通过，≥8 report-only queries 仅报告不阻塞。
4. **Failure Diagnostics（D4）**：`FailureDiagnostics` frozen dataclass，通过 `diagnostic_limit` 参数 opt-in。默认评估不计算诊断。

## 关键取舍与风险

- 别名规则手动维护 → 从 5 条规则开始，按需扩展
- Intent boost 是启发式 → 小值 (0.05)，易调优
- Baseline 是时间点快照 → `--write-baseline` 刷新
- 诊断查询增加延迟 → opt-in，不影响默认评估

## 测试策略

- TDD 循环：每个任务先写失败测试，再实现
- 单元测试 + 集成测试覆盖
- 最终全量测试验证

## Spec Patch

无
