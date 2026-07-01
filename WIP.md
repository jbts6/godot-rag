# WIP

本文件记录下一步主要工作。细节进入 Comet change 后，以对应 `openspec/changes/<change>/` 为准。

## 当前优先方向：搜索质量优化闭环

目标：先让搜索质量、速度和稳定性变化能被可靠测出来，再安全调整检索策略和代码结构。

### 1. 扩搜索质量评估集 ✅ 已完成

- 将 gating queries 从当前的小集合扩到覆盖 40-60 条稳定场景。
- 覆盖符号 alias、自然语言教程、addon API、engine 概念、camelCase/snake_case/dotted symbol 等场景。
- 增加负例和精确性检查：addon filter 不串库，class/tutorial/engine/addon 类型不互相污染。
- **已完成**：查询套件扩展到 45 个查询；已将稳定非 addon 候选提升后，当前为 38 gating，7 report-only。

### 2. 加入速度与稳定性基准 ✅ 已完成

- 在 `eval-search` 或相邻命令中报告 p50/p95、冷启动/热查询、FTS-only/hybrid 模式指标。
- 把 vector fallback reason 和 degraded 状态纳入 regression 保护。
- 将搜索质量命令接入常规验证路径，而不只依赖 `pytest`。
- **已完成**：添加延迟指标（p50/p95）和搜索执行元数据（search mode、fallback reason）到诊断输出。

### 3. 等价拆分搜索器结构 ✅ 已完成

- 拆分 `rst2md/rag/searcher.py` 中的 candidate retrieval、fusion/rerank、snippet extraction 为独立模块（`retrieval.py`、`fusion.py`、`snippet.py`）。
- 行为等价重构，排名不变。
- 全量测试通过（45 查询 + 单元测试）。

### 4. 搜索策略优化

- 扩展 alias/query rewrite 机制，减少硬编码孤例。
- 强化符号查询的精确优先级，让 `Node.add_child`、`addChild`、`node_add_child` 稳定命中同一族目标。
- 让 tutorial/addon/engine intent scoring 更可解释，并在诊断输出中展示命中原因。
- report-only triage 已完成：20 条观察项中 17 条 `promotion_ready`，2 条 `low_ranking`（`nodes-and-scenes-tutorial`、`vector-fallback-metadata`），1 条 `missing_recall`（`class-inheritance-node-object`）。
- gating promotion 已完成：13 条稳定非 addon 候选提升为 gating；4 条 addon 候选和 3 条非 ready 查询保持 report-only。
- ranking signal explainability 已完成：`RankingSignal` 模型 + `SearchResult.ranking_signals` 全链路信号录制（symbol recall / hybrid RRF+FTS / graph expansion / rerank bonus / doc-type & addon intent），CLI `--debug-search` 可观测，272 测试通过 + 1 xfail。
- **当前 baseline（38 gating / 7 report-only，hit@1=0.763 / hit@5=0.895 / mrr@5=0.805）剩 6 条 failure：**
  - gating：`scene-tree-tutorial`、`how-to-use-scene-tree-nodes`（tutorial, low_ranking）；`resource-loader`、`node-connect-signal`（symbol, query_normalization, `matched=null` 零召回）。
  - report-only：`class-inheritance-node-object`（class, missing_recall）；`vector-fallback-metadata`（engine, low_ranking）。
- 推荐切入顺序：先修 suffix-recall 死代码 bug（已由 `suffix-symbol-recall-fix` 完成，打开 `scene-tree-tutorial` 但 `resource-loader`/`node-connect-signal` 仍 `matched=null`），再处理 symbol query normalization（alias/ranking），最后 tutorial low-ranking 与 class-inheritance 召回缺口。

## 已完成的 Comet change

### 2026-07-01

- 名称：`suffix-symbol-recall-fix`
- 状态：🔄 build 完成，待 verify/archive
- 范围：修 `_canonical_form`（`rst2md/rag/symbols.py`）保留 dot 边界、只去 underscore，使 suffix symbol recall LIKE `'%.{normalized}'` 生效；转正 `test_suffix_symbol_match_records_signal` xfail；把 `symbol_recall.suffix` 加入 `RankingSignalCoverageTests.required`。
- 成果：273 pass（原 272 + 1 xfail 转正）；本地迁移 DB eval hit@5 0.895→0.921、mrr@5 0.805→0.818、`scene-tree-tutorial` 不再 failure。
- 非目标：不改 rerank 权重/alias/schema/embedding；不保证 `resource-loader`/`node-connect-signal` 进 window。
- 遗留：`resource-loader`/`node-connect-signal` 仍 `matched=null`（预期目标非 `Class.method` 形态，suffix 修复不足）→ 后续 `symbol-query-normalization-fix`；canonical `baseline.json` 未刷新（本地无完整 Godot docs）。

- 名称：`search-ranking-signal-explanations`
- 状态：✅ 已归档并复审（2026-07-01）
- 范围：在 `SearchResult.ranking_signals` 上录制命名确定性信号（`symbol_recall` exact/prefix/suffix、`hybrid_rrf`、`fts_score`、`graph_expansion`、`rerank_bonus` alias/symbol/doc_type_intent/addon_intent），CLI `--debug-search` 与结构化输出均可观测。
- 成果：6 文件 +969/-12 行；272 pass + 1 xfail；行为 byte-for-byte 等价（不改排名权重、不改 schema/embeddings）；spec 合并到 `intent-ranking`。
- 非目标：不修 ranking 权重、不动 DB schema、不换 embedding。
- 遗留：`symbol_recall.suffix` 录制代码 dormant（`_canonical_form` 去 dot → suffix LIKE 永不命中），有 `@expectedFailure` 测试等待修复；`_rerank_bonus` 的 `not plan.symbol_candidates` 守卫可能只针对 dot-notation，留待后续 change 评估。

### 2026-06-30

- 名称：`promote-report-only-gating-candidates`
- 状态：✅ 已完成（2026-06-30）
- 范围：把 13 条稳定非 addon `promotion_ready` 查询从 report-only 提升为 gating，保留 4 条 addon 候选和 3 条非 ready 查询为 report-only。
- 成果：查询套件保持 45 条，gating 从 25 增至 38，report-only 从 20 降至 7；刷新 `docs/search-quality/baseline.json` 并通过 baseline comparison。
- 下一步：解释并改善当前 baseline 中的 tutorial low-ranking、symbol normalization 和 class inheritance recall failure。

- 名称：`search-ranking-report-only-triage`
- 状态：✅ 已归档并复审（2026-06-30）
- 范围：为 20 条 report-only 查询输出 triage 分类、证据和 follow-up ownership，不调整 ranking 权重或 alias 规则。
- 成果：当前完整评估分布为 17 条 `promotion_ready`、2 条 `low_ranking`、1 条 `missing_recall`；复审修复了通过的 report-only 查询在 degraded fallback 下缺少诊断证据、可能误标为 `promotion_ready` 的问题。
- 下一步：审阅并提升稳定 gating 候选，同时针对 `nodes-and-scenes-tutorial`、`vector-fallback-metadata`、`class-inheritance-node-object` 建立 focused optimization change。

- 名称：`lock-searcher-helper-facade-compatibility`
- 状态：✅ 已提交（2026-06-30）
- 范围：补充 `rag.searcher` 对 `_smart_tokenize`、`_escape_fts5`、`vector_search`、`rrf_fusion`、`rerank_results`、`_extract_snippet` 等 legacy helper re-export 的兼容性测试。
- 成果：把 split-searcher-modules 审核中的残余风险转成自动化测试，防止后续清理 import 时误删 facade 兼容路径。

- 名称：`split-searcher-modules`
- 状态：✅ 已归档（2026-06-30）
- 范围：将 `searcher.py`（526 行、13 个顶层函数）按职责拆分为 `retrieval.py`、`fusion.py`、`snippet.py` 三个 focused sub-module。
- 成果：searcher.py 瘦身为 facade + 编排，行为 byte-for-byte 等价，172 测试全通过，store.py 零改动。
- 非目标：不改排名权重、不换 embedding、不动 DB schema、不实现 graph expansion。

### 2026-06-29

- 名称：`search-quality-evaluation-expansion`
- 状态：✅ 已归档（2026-06-29）
- 范围：评估集扩容、速度/稳定性指标设计、搜索器等价拆分的前置验证边界。
- 成果：查询套件扩展到 45 个，添加延迟指标和搜索执行元数据，更新 CLI 输出和文档。
- 非目标：本 change 不直接大幅调整 ranking 权重，不更换 embedding 模型，不改变数据库 schema。

## 下一步方向

### 推荐：`symbol-query-normalization-fix`

- 目标：让 `ResourceLoader.load`、`Node.connect` 这类 dot-notation 符号查询稳定命中预期目标。`suffix-symbol-recall-fix` 已修好归一化但这两条仍 `matched=null`——需查清预期目标 chunk 在索引里的 `symbol` 字段实际形态（可能只存了 `load`/`connect` 而非 `Class.method`），再决定补 alias 规则、调 query rewrite，还是在 rerank 里对 dot-notation 候选加权。
- 前提：借助上一轮 `ranking_signals` 定位预期目标的实际 symbol 与召回路径，避免盲调权重。
- 范围候选：`_ALIAS_RULES` 追加 `ResourceLoader.load`/`Node.connect` 别名；或 `expand_query_variants` 对 dot-notation 产出 `Class.method` + `method` 双候选并让 exact recall 命中。
- 验证：`resource-loader`、`node-connect-signal` 进 diagnostic window 且 `matched_rank ≤ required_at`，45 查询 baseline 不退化。

### 随后：`tutorial-intent-ranking-fix`

- 目标：针对 `how-to-use-scene-tree-nodes`（matched=10）的 low_ranking failure，借助 `ranking_signals` 解释为何 class 命中压过 tutorial 文档，再决定是否调 `doc_type_intent` 权重或 tutorial intent 触发条件。
- 注：`scene-tree-tutorial` 已被 `suffix-symbol-recall-fix` 解决（suffix 召回激活后 tutorial hit@5 0.714→0.857）。

### 备选：`class-inheritance-recall-fix`

- 目标：针对 `class-inheritance-node-object`（report-only, missing_recall）调查召回缺口来自 query rewrite、symbol alias、inheritance 文档结构还是 index 数据。
- 前提：保持评估输出可解释，避免在不知道召回缺口来源时直接调 ranking 权重。

### 备选：`addon-gating-stability-review`

- 目标：审阅 4 条仍为 `promotion_ready` 的 addon 查询，决定 addon 数据源是否足够稳定到可进入 gating。
- 前提：明确 addon fixture/数据更新策略，否则继续保持 report-only，避免外部 addon 数据漂移影响主搜索质量门禁。
