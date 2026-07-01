# Changelog

本文件记录已归档的 Comet changes。更细的提案、设计和任务记录保留在 `openspec/changes/archive/`。

## 2026-07-01 (待归档)

### `suffix-symbol-recall-fix` (build 完成，待 verify/archive)

- 修复 `_canonical_form`（`rst2md/rag/symbols.py`）剥离 dot 导致 suffix symbol recall 死代码的 bug：归一化改为保留 dot 边界、只去 underscore，使 suffix LIKE `'%.{normalized}'` 能命中 `Class.method` 形态符号。
- 转正 `test_suffix_symbol_match_records_signal`（移除 `@expectedFailure`），并把 `symbol_recall.suffix` 加入 `RankingSignalCoverageTests` 的 `required` 集。
- 全套 273 pass（原 272 + 1 xfail 转正）。本地迁移 DB eval：hit@5 0.895→0.921、mrr@5 0.805→0.818，`scene-tree-tutorial` 不再 failure。
- **升级注意**：已发布的 DB 需重建索引（`godot-rag build`）才能激活 suffix symbol recall；旧 DB 不重建则 suffix 召回仍失效（无崩溃，行为退化为原状态）。
- 未解决：`resource-loader`/`node-connect-signal` 仍 `matched=null`（预期目标非 `Class.method` 形态），留待后续 alias/ranking change。

## 2026-06-30

### build orchestrator

- `godot-docs` 子模块指纹改为 commit hash，避免每次全量遍历目录。

### `split-searcher-modules`

- 任务：21/21
- 将 `searcher.py`（526 行、13 个顶层函数）按职责拆分为 `retrieval.py`、`fusion.py`、`snippet.py` 三个 focused sub-module。
- `searcher.py` 瘦身为 facade + 编排（`_search_database_impl` + 公开 API + re-export）。
- 行为 byte-for-byte 等价重构，172 测试全通过，`store.py` 零改动。
- 更新 `test_searcher_module.py` import 路径指向 focused modules（Scheme A）。
- `build.sh` 同步构建产物到 `godot_rag/rag/`。

## 2026-06-29

### `search-quality-evaluation-expansion`

- 任务：17/17
- 扩展 packaged search quality query suite 至 45 个查询（25 gating，20 report-only）。
- 增加评估延迟指标（p50/p95）和搜索执行元数据（search mode、fallback reason）到诊断输出。
- 更新 CLI 输出、README 验证文档和重构安全测试。

### `record-search-eval-versions`

- 任务：5/5
- 为搜索质量评估报告和写入的 baseline 增加 evaluator/search 版本元数据。
- 保持既有 database fingerprint 和 query-suite hash 行为不变，并刷新 `docs/search-quality/baseline.json`。

### `search-quality-evaluation`

- 任务：17/17
- 增加确定性的 golden-query 搜索质量评估层，适合测试和 CI。
- 增加真实 release database 的评估命令和 baseline regression 比较，报告 `hit@1`、`hit@3`、`hit@5`、`MRR@5`。

### `search-quality-optimization-loop`

- 任务：40/40
- 修复 `godot-rag` CLI 打包入口，使其指向可导入的 `rag.cli:main` 并包含 `rst2md/rag` 包。
- 增加失败诊断、query planning、report-only promotion、category coverage 和 baseline 保护，稳定搜索质量优化闭环。

### `search-quality-review-hotfix`

- 任务：2/2
- 只保留当前真实数据库稳定通过的查询作为 gating queries。
- 将不稳定的自然语言 alias、addon 和弱 tutorial 检查退回 `report_only`。

### `stabilize-search-quality-loop`

- 任务：12/12
- 强化真实数据库 baseline handling，增加数据库/query-suite 元数据和空库保护。
- 引入 query-planning 层，让 alias、symbol intent、doc-type intent 和 addon intent 能被搜索阶段复用。

## 2026-06-28

### `build-efficiency`

- 任务：23/23
- 增加 Python release build tool，并通过 `godot-rag-build` project script 暴露。
- 将 `build.sh` 改成薄 wrapper，并引入保守的阶段输入 fingerprint 以跳过未变更阶段。

### `build-efficiency-hotfix`

- 任务：8/8
- 扩展阶段 fingerprint，覆盖主要输入和工具版本。
- 修复 standalone diagnostics 的 `PYTHONPATH` 环境，并让 publish gate 失败持久化为失败报告。

### `deepen-rag-modules`

- 任务：17/17
- 从 `store.py` 拆出数据库 indexing 内部职责，同时保留 `rag.store` 的 public imports。
- 拆分 search execution、result mapping、vector/FTS fallback、RRF fusion、graph expansion 和 addon discovery 相关职责。

### `fix-semantic-search-acceptance-gaps`

- 任务：9/9
- 将语义搜索验收测试改为确定性 fixture，避免依赖 ignored/generated 本地目录。
- 增强 debug search metadata 与 degraded vector 状态可观察性。

### `semantic-search-quality-hardening`

- 任务：13/13
- 增加 release database generation、relevance evaluation、model performance 和 fallback observability 的语义搜索质量要求。
- 增加 CLI 默认数据库向量 embedding 验证和 golden-query relevance checks。

## 2026-06-27

### `cleanup-rst-extraction-noise`

- 任务：20/20
- 增加 RST 预处理，清理 Godot `:github_url: hide` metadata。
- 将 Sphinx tabs/code-tab 转成 pandoc 可读的 code-block，并规范 Godot 方法 qualifier 的 Markdown 输出。

### `polish-and-fixes`

- 任务：11/11
- 修复 addon 搜索的 `--no-expand` 支持。
- 修复 graph expansion 的 addon 过滤，并增加 `godot-rag stats` 等可用性改进。

### `rag-search-improvement`

- 任务：13/13
- 提升符号模糊查询命中率。
- 让搜索结果包含上下文关联信息，并改善 BM25 分数分布。

### `semantic-search`

- 任务：13/13
- 增加 `see_also` 关系提取。
- 引入 sqlite-vec + model2vec，实现 FTS5 + 向量双路召回与 RRF 融合排序。
