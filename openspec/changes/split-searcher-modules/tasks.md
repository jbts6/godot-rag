## 1. 基线与前置调研

- [x] 1.1 跑 45 条 query 套件 + 4 个测试文件 + p50/p95 延迟基准，记录拆分前基线（结果快照 + 延迟数值）
- [x] 1.2 查 `vector_search` 外部 caller（`rg "vector_search" rst2md/ scripts/`），决定是否需 re-export 保持兼容
- [x] 1.3 查 `test_searcher_module.py` 对 `rrf_fusion`/`rerank_results` 等私有 helper 的 import 方式，确定方案 A（改测试 import 路径）还是方案 B（searcher re-export）

## 2. 拆 fusion 模块

- [x] 2.1 新建 `rst2md/rag/fusion.py`，移入 `rrf_fusion`/`_rerank_bonus`/`rerank_results`，处理依赖 import（`QueryPlan`、`SearchResult`、`replace`）
- [x] 2.2 `searcher.py` 改为 `from rag.fusion import ...`，删除原函数体
- [x] 2.3 按 1.3 结论更新 `test_searcher_module.py` 的 import 路径（若方案 A）
- [x] 2.4 跑 `test_searcher_module.py` + `test_rag_search.py` + 45 条 query 套件，确认结果与基线一致 → verify: 全绿且结果快照 byte-级一致

## 3. 拆 snippet 模块

- [x] 3.1 新建 `rst2md/rag/snippet.py`，移入 `_extract_snippet`
- [x] 3.2 `searcher.py` 改为 `from rag.snippet import _extract_snippet`
- [x] 3.3 跑 focused 测试 + 45 条 query 套件 → verify: 结果与基线一致

## 4. 拆 retrieval 模块

- [x] 4.1 新建 `rst2md/rag/retrieval.py`，移入 `vector_search`/`_run_vector_query`/`_run_fts_query`/`_vector_availability`/`_smart_tokenize`/`_escape_fts5`
- [x] 4.2 `searcher.py` 改为 `from rag.retrieval import ...`，删除原函数体
- [x] 4.3 保留 `embeddings` 局部 import（optional dependency，沿用现状）
- [x] 4.4 跑 focused 测试 + 45 条 query 套件 + fallback 路径测试（`test_search_metadata_reports_fts_only_when_vec_table_missing` 等）→ verify: 结果与基线一致

## 5. searcher 瘦身与编排

- [x] 5.1 `searcher.py` 仅保留 `search_database`/`search_database_with_metadata`/`_search_database_impl`（编排层），确认编排调用各新模块且顺序不变
- [x] 5.2 确认 `store.py` facade 仍能 re-export `search_database`（若 store 仍在用）
- [x] 5.3 跑全量 `uv run pytest -q` → verify: 全绿

## 6. 全量验证与同步

- [x] 6.1 跑 `eval-search` + p50/p95 延迟基准 → verify: 无回归（容差 ±5%）
- [x] 6.2 跑 45 条 query 套件最终对比 → verify: 结果与拆分前基线完全一致
- [x] 6.3 `./build.sh` 同步 `godot_rag/rag/` → verify: 构建产物更新且 import 正确
- [x] 6.4 更新 `WIP.md` 标记第 3 步完成、归档 graph expansion 过时描述
