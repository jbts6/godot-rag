---
comet_change: split-searcher-modules
role: technical-design
canonical_spec: openspec
---

# Split Searcher Modules — Design Doc

## Context

`rst2md/rag/searcher.py` 是 deepen-rag-modules 从 `store.py` 拆出的 "search-focused module"，当时满足 `rag-module-architecture` Requirement 2 的 "behind a search-focused module interface"。如今 searcher.py 长到 526 行、13 个顶层函数，内部仍把 candidate retrieval、RRF fusion/rerank、snippet 提取、FTS5 query 构造混在一起。WIP 第 4 步要在 ranking 层做 alias rewrite、符号精确优先级、intent scoring 可解释化——在职责纠缠的单文件里改排名，回归归因困难。

本 change 在 searcher 内部按职责拆出 focused sub-modules，为第 4 步建立可归因边界。行为等价，不改排名。这是 `rag-module-architecture` localization 要求在 searcher 内部的深化（proposal 已 Modified 该 spec 的 Search execution scenario）。

`rg` 确认 `rst2md/rag/` 对 `graph|expand|neighbor|edge` 零命中——graph expansion 实际未实现，措辞沿自 deepen-rag-modules 时代，本 change 不实现它。

## Goals / Non-Goals

**Goals:**
- 把 retrieval / fusion / snippet 从 searcher.py 拆到独立模块。
- searcher.py 瘦身为 facade + 编排（保留公开 API + `_search_database_impl`）。
- 保持 `search_database` / `search_database_with_metadata` 签名与返回结构、排名结果、fallback 行为、DB schema 全部不变。
- 用现有 4 个测试文件 + 45 条 query 套件 + p50/p95 延迟基准护住每步移动。

**Non-Goals:**
- 不改排名权重、不换 embedding、不改 DB schema。
- 不动 `query_plan.py` / `db.py` / `symbols.py` / `models.py` / `store.py` facade。
- 不实现 graph expansion。不改 CLI。不引入新运行时依赖。

## Decisions

### D1: searcher 角色 = facade + 编排

searcher.py 保留 `_search_database_impl` 编排 + re-export 公开 API（`search_database` / `search_database_with_metadata` / `vector_search`）。私有 helper 移到新模块且 searcher 不 re-export。`test_searcher_module.py` 的 import 路径改为新模块。

- 备选 A（re-export 私有 helper）：测试不动，但 searcher 变成大 re-export 表面，边界模糊，与 focused sub-modules 精神冲突。弃。
- 备选 B（纯编排不 re-export）：`vector_search` 等全去新模块，`store.py` 须改从新模块 import——违反"不动 store.py"非目标。弃。

### D2: 模块边界

| 模块 | 函数 |
|------|------|
| `retrieval.py` | `vector_search`, `_run_vector_query`, `_run_fts_query`, `_vector_availability`, `_smart_tokenize`, `_escape_fts5`, `_FTS5_SPECIAL` |
| `fusion.py` | `rrf_fusion`, `_rerank_bonus`, `rerank_results` |
| `snippet.py` | `_extract_snippet` |
| `searcher.py`（瘦身后） | `search_database`, `search_database_with_metadata`, `_search_database_impl`；re-export `vector_search` |

`_smart_tokenize` / `_escape_fts5` / `_FTS5_SPECIAL` 归 retrieval：只服务 `_run_fts_query` 的 FTS5 query 构造，内聚。

### D3: `_search_database_impl` 编排层留 searcher

顺序不变：`build_query_plan` → `_vector_availability` → `_run_vector_query` + `_run_fts_query` → `rrf_fusion` → `rerank_results` → `_extract_snippet` → `SearchResult` + `SearchMetadata`。

留 searcher 因它编排 fusion/rerank/snippet，下放 retrieval 会让 retrieval 反向依赖 fusion/snippet，破坏分层。

### D4: import 单向分层

```
store.py (facade, 不变) → from rag.searcher import *
searcher.py → from rag.retrieval / fusion / snippet import *
retrieval / fusion / snippet → 只依赖 db / models / query_plan
embeddings 局部 import 保留（optional dependency）
```

无循环：retrieval/fusion/snippet 不反向依赖 searcher 或彼此。

### D5: `vector_search` re-export

`vector_search` 移到 `retrieval.py`，但 `searcher.py` re-export 它。客观排查：无业务 caller，仅 `store.py:17` facade re-export + `test_searcher_module.py:18` import 检查。re-export 零成本保兼容。

### D6: 测试 import 策略（方案 A）

`test_searcher_module.py` 是 importability 契约测试（docstring: "search functions should be importable from rag.searcher"），12 处 `from rag.searcher import X`。改路径（机械改动，断言不变）：

- `_smart_tokenize` / `_escape_fts5` / `_FTS5_SPECIAL` / `_vector_availability` / `_run_vector_query` / `vector_search` → `from rag.retrieval`
- `rrf_fusion` / `rerank_results` → `from rag.fusion`
- `_extract_snippet` → `from rag.snippet`
- `search_database` / `search_database_with_metadata` / `_search_database_impl` → 仍 `from rag.searcher`

docstring 更新为 "importable from their focused modules"。其他测试文件通过 `search_database` 间接测，不直接 import helper，不受影响。

## Data Flow

```
search_database(args) / search_database_with_metadata(args)
        │
        ▼
_search_database_impl (searcher.py, 编排层)
        │
        ├─ build_query_plan (query_plan.py) → plan
        ├─ _vector_availability (retrieval) → hybrid / fts-only
        ├─ _run_vector_query + _run_fts_query (retrieval) → candidates
        ├─ rrf_fusion (fusion) → fused
        ├─ rerank_results (fusion) → ranked
        └─ _extract_snippet (snippet) → formatted
                │
                ▼
        SearchResult + SearchMetadata
```

## Risks / Trade-offs

- [行为漂移] → 每拆一块立即跑 focused 测试 + 45 query 套件前后对比。
- [import 循环] → 单向分层（retrieval/fusion/snippet ← searcher），不反向。
- [测试耦合私有 helper] → 已查清：仅 `test_searcher_module.py` 直接 import helper，方案 A 机械改路径。
- [大 diff 机械移动] → 一次一个职责，每步测试，不积攒。
- [延迟回归] → p50/p95 前后对比，容差 ±5%；多一层 import 不应超此阈值。

## Migration Plan

1. 基线：跑 45 query 套件 + 4 测试文件 + p50/p95 延迟基准，记录前后对比基线。
2. 拆 `fusion.py`（最独立，无下游依赖）→ searcher 改 import → 跑测试。
3. 拆 `snippet.py` → searcher 改 import → 跑测试。
4. 拆 `retrieval.py`（含 `_smart_tokenize`/`_escape_fts5`/`_FTS5_SPECIAL`）→ searcher 改 import → 跑测试。
5. `searcher.py` 瘦身为编排 + 公开 API + re-export `vector_search` → 跑测试。
6. 改 `test_searcher_module.py` 12 处 import 路径 + docstring（按 D6）→ 跑测试。
7. 全量 `uv run pytest -q` + `eval-search` 前后对比。
8. `./build.sh` 同步 `godot_rag/rag/`。

Rollback：公开接口保持不变，revert 拆分 commit 或把代码移回 `searcher.py` 即可。

## Test Strategy

- **契约**：`search_database` / `search_database_with_metadata` 签名与返回结构不变；4 个测试文件（`test_searcher_module` / `test_rag_search` / `test_semantic_search` / `test_rag_addon`）全绿。
- **等价**：45 条 query 套件拆分前后结果完全一致（byte-级快照对比）。
- **性能**：p50/p95 延迟无回归（容差 ±5%）。
- **边界**：degraded / FTS-only fallback 路径行为不变（`test_search_metadata_reports_fts_only_when_vec_table_missing` 等仍绿）。
- **importability**：`test_searcher_module.py` 改路径后仍验证各函数可从对应 focused module 导入。

## Spec Patch

无。proposal 的 Modified `rag-module-architecture`（Search execution scenario 深化到 retrieval/fusion/snippet focused sub-modules）已覆盖本设计；`vector_search` re-export 与 test import 改路径不改变 spec 行为。
