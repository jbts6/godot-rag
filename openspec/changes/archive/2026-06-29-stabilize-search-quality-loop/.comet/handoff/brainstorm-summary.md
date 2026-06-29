# Brainstorm Summary

- Change: stabilize-search-quality-loop
- Date: 2026-06-29

## 确认的技术方案

用户已确认采用“评估加固 + QueryPlan + 确定性 rerank”的增量路径：

1. 先加固 `eval-search` 输入和 baseline artifact。baseline 写入必须记录 DB 指纹、query-suite hash 和关键计数；空库、无 chunks、无 symbols 或 vector/chunk 行数不一致时拒绝写入 baseline。
2. 引入内部 `QueryPlan`，承载 original query、normalized query、symbol candidates、alias-derived symbol candidates、doc-type intent 和 addon intent。现有 alias expansion 继续保留，但改为 query plan 的输入之一。
3. 让 exact/suffix/prefix symbol recall 使用 query-plan symbol candidates；FTS 继续使用 original + alias variants；vector 默认仍使用原始自然语言 query，避免 symbol alias 污染语义召回。
4. 在候选集合完成后使用命名、确定性的 rerank signals：alias symbol match、exact symbol match、path/heading/breadcrumb match、doc-type intent、addon intent。替代当前单一的小幅 `doc_type_boost` 思路。
5. report-only promotion 使用客观门槛：expected target present、graph-enabled top-K pass、category coverage 不塌陷。addon/missing-data 类保持 report-only，直到诊断证明数据已稳定存在。

## 关键取舍与风险

- 不引入 LLM/learned reranker，优先选择可测试、可解释、可回滚的确定性信号。
- QueryPlan 是内部结构，不新增 public API；降低外部兼容风险。
- alias rerank 可能过度提升符号结果；通过 tutorial/symbol-like intent 的互斥测试约束。
- baseline metadata 会让本地错误更早暴露；需要清晰错误消息说明是哪类 DB/input 不合法。
- addon 查询暂不晋升为 gating，避免把数据入库问题误判成 ranking 问题。

## 测试策略

- 单元测试：baseline metadata、空/不完整 DB 拒绝、query-suite hash、QueryPlan alias/symbol/doc-type/addon intent。
- 搜索器测试：natural-language alias 进入 symbol recall，alias match 通过 rerank 排名前移，tutorial intent 不压制明确 symbol query。
- 评估测试：category coverage warning、report-only promotion eligibility、missing-data query 不可晋升。
- 集成验证：聚焦 pytest、`godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph`。

## Spec Patch

已在 OpenSpec delta specs 中加入：

- `semantic-search-quality`: baseline metadata、invalid DB rejection、promotion criteria、category coverage warning。
- `query-rewrite`: QueryPlan 和 alias-derived symbol candidates 进入 symbol recall/rerank。
- `intent-ranking`: deterministic reranking signals。
- `search-quality-diagnostics`: baseline input validity 和 promotion decision diagnostics。
