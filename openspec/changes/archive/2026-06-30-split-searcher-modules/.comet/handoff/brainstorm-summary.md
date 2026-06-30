# Brainstorm Summary

- Change: split-searcher-modules
- Date: 2026-06-30

## 确认的技术方案

searcher.py 拆分后扮演 **facade + 编排** 角色（用户确认方案 1）：

- `retrieval.py`: `vector_search`, `_run_vector_query`, `_run_fts_query`, `_vector_availability`, `_smart_tokenize`, `_escape_fts5`, `_FTS5_SPECIAL`
- `fusion.py`: `rrf_fusion`, `_rerank_bonus`, `rerank_results`
- `snippet.py`: `_extract_snippet`
- `searcher.py`（瘦身）: `search_database`, `search_database_with_metadata`, `_search_database_impl`（编排）；re-export `vector_search`（保 `store.py` facade + test 兼容）

`_search_database_impl` 留 searcher.py 作编排层，顺序不变：`build_query_plan` → `_vector_availability` → `_run_vector_query` + `_run_fts_query` → `rrf_fusion` → `rerank_results` → `_extract_snippet`。

import 单向分层：`store` → `searcher` → `retrieval`/`fusion`/`snippet` → `db`/`models`/`query_plan`；`embeddings` 局部 import 保留。

客观事实（Q3/Q4 已查）：
- `vector_search` 无业务 caller，仅 `store.py:17` re-export + `test_searcher_module.py:18` import 检查。
- `test_searcher_module.py` 是 importability 契约测试（12 处 `from rag.searcher import X`）。

## 关键取舍与风险

- 选 facade+编排+改测试 而非 re-export 私有 helper：边界清晰，与 `rag-module-architecture` localization 一致；代价是改 `test_searcher_module.py` 12 处 import 路径（机械改动，断言不变）。
- 不选"纯编排不 re-export"：会动 `store.py` facade（违反非目标）。
- 风险：行为漂移（每步 focused 测试 + query 套件）、import 循环（单向分层）、延迟回归（p50/p95 ±5%）。

## 测试策略

`test_searcher_module.py` 12 处 import 改路径（机械改动，不改断言）：
- `_smart_tokenize`/`_escape_fts5`/`_FTS5_SPECIAL`/`_vector_availability`/`_run_vector_query`/`vector_search` → `from rag.retrieval`
- `rrf_fusion`/`rerank_results` → `from rag.fusion`
- `_extract_snippet` → `from rag.snippet`
- `search_database`/`search_database_with_metadata`/`_search_database_impl` → 仍 `from rag.searcher`

docstring 更新为 "importable from their focused modules"。验收：4 测试文件 + 45 query 套件 + p50/p95 前后对比 + fallback 路径不变。

## Spec Patch

无。proposal 的 Modified `rag-module-architecture`（Search execution scenario 深化到 retrieval/fusion/snippet）已覆盖本设计；`vector_search` re-export、test 改路径不改变 spec 行为。
