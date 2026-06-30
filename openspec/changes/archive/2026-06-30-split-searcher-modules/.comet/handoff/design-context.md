# Comet Design Handoff

- Change: split-searcher-modules
- Phase: design
- Mode: compact
- Context hash: 957d6f8b95ad514d2d377aa5028d25e099e0069a9698e80b57b89e261c24777b

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/split-searcher-modules/proposal.md

- Source: openspec/changes/split-searcher-modules/proposal.md
- Lines: 1-36
- SHA256: 4247f57bce2861f19a20fb5f24ce48c2b203e2f730b94f434ed470f42aa31e64

```md
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
```

## openspec/changes/split-searcher-modules/design.md

- Source: openspec/changes/split-searcher-modules/design.md
- Lines: 1-96
- SHA256: 9406a6720cb67857d2a20cff05eb89ae6b72ee0a85b291f9fe5f5bfaa463de4b

[TRUNCATED]

```md
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
```

Full source: openspec/changes/split-searcher-modules/design.md

## openspec/changes/split-searcher-modules/tasks.md

- Source: openspec/changes/split-searcher-modules/tasks.md
- Lines: 1-38
- SHA256: 6aa7e249150334f6368a666f9137d97c211344c9077fa41d7282ad8de7ba31ab

```md
## 1. 基线与前置调研

- [ ] 1.1 跑 45 条 query 套件 + 4 个测试文件 + p50/p95 延迟基准，记录拆分前基线（结果快照 + 延迟数值）
- [ ] 1.2 查 `vector_search` 外部 caller（`rg "vector_search" rst2md/ scripts/`），决定是否需 re-export 保持兼容
- [ ] 1.3 查 `test_searcher_module.py` 对 `rrf_fusion`/`rerank_results` 等私有 helper 的 import 方式，确定方案 A（改测试 import 路径）还是方案 B（searcher re-export）

## 2. 拆 fusion 模块

- [ ] 2.1 新建 `rst2md/rag/fusion.py`，移入 `rrf_fusion`/`_rerank_bonus`/`rerank_results`，处理依赖 import（`QueryPlan`、`SearchResult`、`replace`）
- [ ] 2.2 `searcher.py` 改为 `from rag.fusion import ...`，删除原函数体
- [ ] 2.3 按 1.3 结论更新 `test_searcher_module.py` 的 import 路径（若方案 A）
- [ ] 2.4 跑 `test_searcher_module.py` + `test_rag_search.py` + 45 条 query 套件，确认结果与基线一致 → verify: 全绿且结果快照 byte-级一致

## 3. 拆 snippet 模块

- [ ] 3.1 新建 `rst2md/rag/snippet.py`，移入 `_extract_snippet`
- [ ] 3.2 `searcher.py` 改为 `from rag.snippet import _extract_snippet`
- [ ] 3.3 跑 focused 测试 + 45 条 query 套件 → verify: 结果与基线一致

## 4. 拆 retrieval 模块

- [ ] 4.1 新建 `rst2md/rag/retrieval.py`，移入 `vector_search`/`_run_vector_query`/`_run_fts_query`/`_vector_availability`/`_smart_tokenize`/`_escape_fts5`
- [ ] 4.2 `searcher.py` 改为 `from rag.retrieval import ...`，删除原函数体
- [ ] 4.3 保留 `embeddings` 局部 import（optional dependency，沿用现状）
- [ ] 4.4 跑 focused 测试 + 45 条 query 套件 + fallback 路径测试（`test_search_metadata_reports_fts_only_when_vec_table_missing` 等）→ verify: 结果与基线一致

## 5. searcher 瘦身与编排

- [ ] 5.1 `searcher.py` 仅保留 `search_database`/`search_database_with_metadata`/`_search_database_impl`（编排层），确认编排调用各新模块且顺序不变
- [ ] 5.2 确认 `store.py` facade 仍能 re-export `search_database`（若 store 仍在用）
- [ ] 5.3 跑全量 `uv run pytest -q` → verify: 全绿

## 6. 全量验证与同步

- [ ] 6.1 跑 `eval-search` + p50/p95 延迟基准 → verify: 无回归（容差 ±5%）
- [ ] 6.2 跑 45 条 query 套件最终对比 → verify: 结果与拆分前基线完全一致
- [ ] 6.3 `./build.sh` 同步 `godot_rag/rag/` → verify: 构建产物更新且 import 正确
- [ ] 6.4 更新 `WIP.md` 标记第 3 步完成、归档 graph expansion 过时描述
```

## openspec/changes/split-searcher-modules/specs/rag-module-architecture/spec.md

- Source: openspec/changes/split-searcher-modules/specs/rag-module-architecture/spec.md
- Lines: 1-21
- SHA256: bdd4e7287d2b939ce4afca0f4bca0983d64f99da7d4cfa23599cba772d199c49

```md
## MODIFIED Requirements

### Requirement: Internal responsibilities are localized behind focused RAG modules
The implementation SHALL separate indexing, search execution, relation building, addon discovery, and CLI search command orchestration so each responsibility can be tested or changed without editing unrelated responsibilities in place.

#### Scenario: Database indexing is localized
- **WHEN** database build behavior changes in the future
- **THEN** schema initialization, document insertion, addon insertion, symbol insertion, FTS sync, and embedding storage concerns MUST live behind an indexing-focused module interface rather than directly inside the public `rag.store` facade

#### Scenario: Search execution is localized
- **WHEN** search ranking, vector fallback, FTS fallback, result mapping, or snippet extraction behavior changes in the future
- **THEN** those concerns MUST live behind focused search sub-modules (retrieval, fusion, snippet) rather than directly inside a single search module or the public `rag.store` facade
- **AND** the public `search_database` and `search_database_with_metadata` interfaces MUST remain stable

#### Scenario: Addon discovery is localized
- **WHEN** addon documentation layout rules or file collection rules change in the future
- **THEN** those concerns MUST live behind an addon-discovery-focused module interface rather than inside addon chunk production code

#### Scenario: CLI search orchestration is localized
- **WHEN** shared search command behavior changes in the future
- **THEN** database validation, graph expansion option handling, debug metadata routing, and output formatting MUST be centralized instead of duplicated across each search subcommand
```

