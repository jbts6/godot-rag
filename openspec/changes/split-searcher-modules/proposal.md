## Why

`rst2md/rag/searcher.py` 已长到 526 行、13 个顶层函数，把 candidate retrieval、RRF fusion/rerank、snippet 提取、FTS5 query 构造混在一个文件里。WIP 第 4 步要在 ranking 层做 alias rewrite、符号精确优先级、intent scoring 可解释化——在这些职责纠缠的代码里改排名，回归归因困难，且每次调整都需穿越无关关注点。

本 change 在 searcher 内部按职责拆出 focused sub-modules，为 ranking 优化建立可归因的模块边界，再做第 4 步。第一阶段只做行为等价重构，不改排名。这是 `rag-module-architecture` 的 localization 要求在 searcher 内部的进一步深化。

## What Changes

- 从 `searcher.py` 拆出 **retrieval**：candidate retrieval 与查询构造，含 `_search_database_impl` 编排、`_run_vector_query`、`_run_fts_query`、`_vector_availability`、`vector_search`、`_smart_tokenize`、`_escape_fts5`。
- 拆出 **fusion**：`rrf_fusion`、`_rerank_bonus`、`rerank_results`。
- 拆出 **snippet**：`_extract_snippet`。
- `searcher.py` 瘦身后只留公开 API（`search_database`、`search_database_with_metadata`）+ 编排。
- 保持 `search_database` / `search_database_with_metadata` 签名与返回结构不变（39 + 9 caller）。
- 不改排名结果、不改 degraded/FTS-only fallback 行为、不改 DB schema、不换 embedding。
- 不实现 graph expansion：经 `rg` 确认 `rst2md/rag/` 对 `graph|expand|neighbor|edge` 零命中，CLAUDE.md/WIP 的 "graph expansion" 措辞沿自 deepen-rag-modules 时代，实际未实现。
- 模块命名与 `_search_database_impl` 编排层归属（留 searcher vs 下放 retrieval）留 design 阶段定。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `rag-module-architecture`: 深化 Requirement 2「Internal responsibilities are localized behind focused RAG modules」的 Search execution scenario——search execution concerns 从单一 `searcher.py` 进一步细分到 retrieval / fusion / snippet focused sub-modules，使排名、fallback、result mapping、snippet 各自可独立测试与变更。Public interface stability（Requirement 1）不变。

## Impact

- **受影响代码**：
  - `rst2md/rag/searcher.py`（瘦身为编排 + 公开 API）
  - 新建 `rst2md/rag/retrieval.py` / `fusion.py` / `snippet.py`（命名待 design）
  - `godot_rag/rag/` 为构建产物，由 `build.sh` 从 `rst2md/rag/` 同步，不手动改
- **公开 API**：`search_database` / `search_database_with_metadata` 签名与返回结构不变。
- **测试**：`rst2md/tests/test_searcher_module.py`、`test_rag_search.py`、`test_semantic_search.py`、`test_rag_addon.py` 护重构；45 条 query 套件 + p50/p95 延迟基准前后对比。
- **依赖**：无新增运行时依赖；无 DB schema 行为变更。
