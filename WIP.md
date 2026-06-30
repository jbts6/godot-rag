# WIP

本文件记录下一步主要工作。细节进入 Comet change 后，以对应 `openspec/changes/<change>/` 为准。

## 当前优先方向：搜索质量优化闭环

目标：先让搜索质量、速度和稳定性变化能被可靠测出来，再安全调整检索策略和代码结构。

### 1. 扩搜索质量评估集 ✅ 已完成

- 将 gating queries 从当前的小集合扩到覆盖 40-60 条稳定场景。
- 覆盖符号 alias、自然语言教程、addon API、engine 概念、camelCase/snake_case/dotted symbol 等场景。
- 增加负例和精确性检查：addon filter 不串库，class/tutorial/engine/addon 类型不互相污染。
- **已完成**：查询套件扩展到 45 个查询（25 gating，20 report-only）。

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
- 推荐切入顺序：先跑现有 45 查询评估并分析 20 个 report-only 查询，再挑 1-2 类低风险 ranking 信号做小步 change，避免一次性重调权重。

## 已完成的 Comet change

### 2026-06-30

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

### 推荐：`search-ranking-report-only-triage`

- 目标：先用现有 45 查询评估集和 diagnostic window 对 20 个 report-only 查询做分类，区分 missing data、recall miss、low ranking、filter mismatch、degraded vector mode。
- 输出：一份候选优化清单，标明哪些查询可提升为 gating，哪些需要数据/fixture，哪些适合进入 ranking change。
- 理由：现在评估与 searcher 模块边界都已就绪，下一步最缺的是“先改哪一个 ranking 信号”的证据；直接调权重容易把质量变化和数据缺口混在一起。

### 随后：`search-ranking-signal-explanations`

- 目标：把 deterministic rerank 的 alias match、symbol match、doc-type intent、addon intent 等信号显式记录到诊断输出或测试可观测结构中。
- 范围：优先做 explainability，不先大幅改变权重；确保 `intent-ranking` 与 `query-rewrite` spec 中“named deterministic signal”的要求能被测试锁住。
- 验证：单元测试覆盖信号生成，`eval-search` 输出能说明命中原因，45 查询 baseline 不退化。

### 备选：`query-alias-rule-expansion`

- 目标：扩展 alias/query rewrite 规则，覆盖 report-only 中已有 `child node attach`、`start countdown timer`、`signals in gdscript tutorial` 等自然语言查询。
- 前提：先完成 triage，确认失败主因是 alias/normalization 或低排名，而不是目标数据缺失。
