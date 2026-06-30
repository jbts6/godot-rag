## Context

`rst2md/rag/searcher.py` 是 deepen-rag-modules 从 `store.py` 拆出的 "search-focused module"，收纳了 vector availability、vector query、FTS query、RRF fusion、snippet extraction、`search_database`、`search_database_with_metadata`。当时满足 `rag-module-architecture` Requirement 2 的 "behind a search-focused module interface"。

现在 searcher.py 长到 526 行、13 个顶层函数，内部仍把多个职责混在一起：

| 职责 | 函数 |
|------|------|
| FTS5 query 构造 | `_smart_tokenize`, `_escape_fts5` |
| Vector 查询 | `vector_search` |
| Fusion | `rrf_fusion` |
| Rerank | `_rerank_bonus`, `rerank_results` |
| Snippet | `_extract_snippet` |
| Retrieval 内部 | `_vector_availability`, `_run_vector_query`, `_run_fts_query`, `_search_database_impl` |
| 公开 API | `search_database_with_metadata`, `search_database` |

WIP 第 4 步要在 ranking 层做 alias rewrite、符号精确优先级、intent scoring 可解释化。在职责纠缠的单文件里改排名，回归归因困难。本 change 把 searcher 内部按职责拆成 focused sub-modules，为第 4 步建立可归因边界。

`rg` 确认 `rst2md/rag/` 对 `graph|expand|neighbor|edge` 零命中——graph expansion 实际未实现，CLAUDE.md/WIP 的措辞沿自 deepen-rag-modules 时代描述，本 change 不实现它，并在 spec delta 里修正该描述。

## Goals / Non-Goals

**Goals:**
- 把 retrieval / fusion / snippet 从 searcher.py 拆到独立模块。
- searcher.py 瘦身为公开 API + 编排。
- 保持 `search_database` / `search_database_with_metadata` 签名与返回结构、排名结果、fallback 行为、DB schema 全部不变。
- 用现有 4 个测试文件 + 45 条 query 套件 + p50/p95 延迟基准护住每步移动。

**Non-Goals:**
- 不改排名权重、不换 embedding、不改 DB schema。
- 不动 `query_plan.py` / `db.py` / `symbols.py` / `models.py` / `store.py` facade。
- 不实现 graph expansion。
- 不改 CLI。
- 不引入新运行时依赖。

## Decisions

### Decision 1: 模块边界划分

- `retrieval.py`: `vector_search`, `_run_vector_query`, `_run_fts_query`, `_vector_availability`, `_smart_tokenize`, `_escape_fts5`。
  - `_smart_tokenize` / `_escape_fts5` 归 retrieval：只服务 `_run_fts_query` 的 FTS5 query 构造，内聚。
  - 备选：单独 `query_construct.py`——只有一个消费者，过度拆分，放弃。
- `fusion.py`: `rrf_fusion`, `_rerank_bonus`, `rerank_results`。
- `snippet.py`: `_extract_snippet`。
- `searcher.py`（瘦身后）: `search_database`, `search_database_with_metadata`, `_search_database_impl`（编排）。

### Decision 2: `_search_database_impl` 编排层归属

推荐留 `searcher.py`：它是编排核心（串联 retrieval → fusion → rerank → snippet），与公开 API 同层。

- 备选：下放 `retrieval.py`——但它在编排中调用 fusion/rerank/snippet，下放会让 retrieval 反向依赖 fusion/snippet，破坏分层。放弃。
- 此项最终归属留 design 阶段 brainstorming 确认（见 Open Questions）。

### Decision 3: import 分层与循环依赖

- `retrieval` / `fusion` / `snippet` 只依赖 `db.py`（primitives）、`models.py`、`query_plan.py`。
- `searcher.py` 依赖 `retrieval` / `fusion` / `snippet`。
- 不允许反向依赖。
- `embeddings` 保留局部 import（optional dependency，沿用现状）。
- `store.py` 若仍 re-export `search_database`，从 `searcher` 导入，不变。

### Decision 4: 测试 import 兼容策略（待定）

`test_searcher_module.py` 可能直接 import `rrf_fusion` / `rerank_results` 等私有 helper。移动后需处理：

- 方案 A（倾向）: 改测试 import 路径（`from rag.fusion import rrf_fusion`），不引入兼容层。
- 方案 B: `searcher.py` re-export 这些函数，测试不改。
- 倾向 A，避免 facade 膨胀；但需先查 `test_searcher_module.py` 实际 import 方式再定（见 Open Questions）。

## Risks / Trade-offs

- [行为漂移] → 每拆一块立即跑 focused 测试 + 45 query 套件前后对比。
- [import 循环] → 分层单向（retrieval/fusion/snippet ← searcher），不反向。
- [测试耦合私有 helper] → 先查 import 方式，再选方案 A/B。
- [大 diff 机械移动] → 一次一个职责，每步测试，不积攒。
- [延迟回归] → p50/p95 前后对比，容差 ±5%；多一层 import 不应超此阈值。

## Migration Plan

1. 基线：跑 45 query 套件 + 4 测试文件 + 延迟基准，记录前后对比基线。
2. 拆 `fusion.py`（最独立，无下游依赖）→ 跑测试。
3. 拆 `snippet.py` → 跑测试。
4. 拆 `retrieval.py`（含 `_smart_tokenize`/`_escape_fts5`）→ 跑测试。
5. `searcher.py` 瘦身为编排 + 公开 API → 跑测试。
6. 处理 `test_searcher_module.py` import 路径（按 Decision 4）→ 跑测试。
7. 全量 `uv run pytest -q` + `eval-search` 前后对比。
8. `./build.sh` 同步 `godot_rag/rag/`。

Rollback：公开接口保持不变，revert 拆分 commit 或把代码移回 `searcher.py` 即可。

## Open Questions

1. `_search_database_impl` 编排层归属最终确认（推荐留 searcher，brainstorming 验证）。
2. 模块命名最终确认（retrieval/fusion/snippet vs 其他）。
3. `test_searcher_module.py` 对 `rrf_fusion`/`rerank_results` 等私有 helper 的 import 方式 → 决定方案 A（改测试）还是 B（re-export）。
4. `vector_search`（无下划线，可能公开）外部 caller 排查 → 决定是否 re-export 保持兼容。
