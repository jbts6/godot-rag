# Comet Design Handoff

- Change: search-quality-evaluation-expansion
- Phase: design
- Mode: compact
- Context hash: e84066c02ae4aae20172001bde2b4819b6ca29eb1090369b7c618c43d99ae4fd

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/search-quality-evaluation-expansion/proposal.md

- Source: openspec/changes/search-quality-evaluation-expansion/proposal.md
- Lines: 1-38
- SHA256: 9968b13c442587da23e47ea83b6f3dd8aa884573d17a3b6b2582e5a7ec04120d

```md
## Why

现有搜索质量 baseline 已经能记录版本和数据库指纹，但 gating query 集合偏小且当前满分，无法可靠暴露下一轮搜索优化的稳定性、速度和质量变化。继续直接调整 ranking 或重构搜索器会缺少足够的回归信号，因此需要先扩展评估覆盖和可观测指标。

## What Changes

- 扩展 packaged search quality query suite，使 gating queries 覆盖更多稳定场景，并继续保留不稳定场景为 report-only。
- 增加评估输出中的性能和稳定性指标，包括查询延迟、搜索模式、vector fallback/degraded 状态和失败诊断。
- 将质量评估的常规验证入口明确化，避免只依赖人工 spot check 或单纯 pytest。
- 为后续搜索器等价拆分定义保护边界：拆分前后必须保持搜索行为和质量 baseline 不退化。
- 不在本 change 中大幅调整 ranking 权重、更换 embedding 模型或修改数据库 schema。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `semantic-search-quality`: 扩展搜索质量评估集、指标和验证入口要求。
- `search-quality-diagnostics`: 扩展诊断输出，使性能、fallback/degraded 状态和失败原因可用于稳定性判断。

## Impact

- Affected code:
  - `rst2md/rag/search_eval.py`
  - `rst2md/rag/search_eval_queries.json`
  - `rst2md/rag/cli.py`
  - `rst2md/rag/searcher.py`
  - `rst2md/tests/`
  - `docs/search-quality/`
- Public APIs:
  - Existing search commands and JSON result shape should remain backward compatible.
  - `eval-search` output may gain fields, but existing fields should remain stable.
- Dependencies:
  - No new runtime dependency expected.
  - No database schema change expected.
```

## openspec/changes/search-quality-evaluation-expansion/design.md

- Source: openspec/changes/search-quality-evaluation-expansion/design.md
- Lines: 1-46
- SHA256: 36a6d881f45d950ca7d5d71737b67acfa69e62548e29ca1ab4255829c01e6f69

```md
## Context

当前搜索质量工作已经具备 deterministic fixture tests、真实数据库 `eval-search`、baseline regression、失败分类、query-suite hash、数据库 fingerprint 和 evaluator/search 版本元数据。近期 baseline 的 gating 集合只有 15 条且全部满分，通过率本身已经不能很好地区分真实质量变化。与此同时，`rst2md/rag/searcher.py` 的核心搜索实现仍集中在较大的 `_search_database_impl` 中，后续要优化稳定性、速度、质量或拆分结构，都需要更强的评估保护。

## Goals / Non-Goals

**Goals:**

- 扩展稳定 gating query 覆盖，优先覆盖真实用户高频和历史脆弱场景。
- 在评估报告中加入 latency、search mode、fallback/degraded reason 等稳定性与速度信号。
- 明确 routine validation 如何运行 deterministic checks 和真实数据库 gate。
- 为后续搜索器等价拆分建立“不改变行为”的验证边界。

**Non-Goals:**

- 不大幅调整 ranking 权重。
- 不更换 embedding 模型。
- 不修改数据库 schema。
- 不把所有 `WIP.md` 中的搜索策略优化一次性实现完。

## Decisions

### 1. 先扩评估信号，再调 ranking

直接改 ranking 会被当前满分 baseline 掩盖。先把 query suite 扩到至少 40 条、gating 至少 25 条，并增加 filter precision、normalization、graph、addon/doc-type 场景，可以让后续优化有更可信的回归信号。仍不稳定或依赖缺失数据的查询继续保持 report-only。

替代方案是先调权重再回填测试。这个顺序反馈快，但容易把当前 fixture 过拟合成目标，且无法解释真实数据库退化。

### 2. latency 与 fallback 进入评估报告，而不是只放 debug command

搜索质量不只看命中率。向量不可用、fallback 到 FTS、p95 延迟上升，都会影响用户体验和后续 ranking 判断。评估报告应记录这些信号，并在 JSON 和 text 输出中都可见。

替代方案是只在 `diagnostics` 命令里暴露运行状态。这样适合排障，但不能进入 baseline/CI 质量闭环。

### 3. 搜索器拆分先作为等价重构边界

`_search_database_impl` 应后续拆成 candidate retrieval、fusion/rerank、graph expansion、result formatting 等阶段。但本 change 的实现应先建立评估保护，最多做低风险的等价拆分，不同时改变 ranking。拆分后的每个阶段仍必须传递 search metadata，保证评估诊断不丢信息。

替代方案是本 change 同时完成完整结构拆分和 ranking 改进。这个范围过大，失败时难以判断是评估、结构还是 ranking 导致退化。

## Risks / Trade-offs

- 扩容 gating queries 可能引入不稳定用例 -> 先用 report-only 承接不稳定查询，只有 expected target 在 canonical database 存在且 rank 稳定时才转 gating。
- latency 指标受机器状态影响 -> 首版将 latency 作为可见诊断和可配置阈值，不默认使用过窄硬阈值。
- 评估输出字段增加可能影响调用方 -> 保留现有字段，只追加新字段。
- 搜索器拆分范围容易扩大 -> tasks 中将拆分限制为验证边界和小步等价改动；ranking 策略优化进入后续 change。
```

## openspec/changes/search-quality-evaluation-expansion/tasks.md

- Source: openspec/changes/search-quality-evaluation-expansion/tasks.md
- Lines: 1-31
- SHA256: 6d6d545eaa7b8177d828c2cd46f8c0bac6d93d74c6f59f2dbb31cdbb146df325

```md
## 1. Query Suite Expansion

- [ ] 1.1 Audit current `search_eval_queries.json` and categorize gaps across class, symbol, tutorial, engine, addon, normalization, graph, and filter precision.
- [ ] 1.2 Add stable gating queries until the packaged suite has at least 40 unique queries and at least 25 gating queries.
- [ ] 1.3 Keep unstable or data-dependent cases report-only and document why they are not gating.
- [ ] 1.4 Update query-suite tests for expanded count, category, tag, and filter precision requirements.

## 2. Evaluation Metrics and Diagnostics

- [ ] 2.1 Capture per-query elapsed time during `evaluate_database` without changing search result ranking.
- [ ] 2.2 Report p50/p95 latency summaries in text and JSON evaluation output.
- [ ] 2.3 Attach search mode and fallback/degraded reason to evaluation diagnostics where available.
- [ ] 2.4 Add regression tests for latency fields and fallback/degraded diagnostic fields.

## 3. Validation Workflow

- [ ] 3.1 Document the routine deterministic search quality validation command.
- [ ] 3.2 Document the real-database `eval-search` baseline comparison command and when it should be run.
- [ ] 3.3 Decide whether an existing project command should invoke the deterministic quality suite, and wire it if low risk.

## 4. Refactor Safety Boundary

- [ ] 4.1 Identify the smallest searcher extraction boundary that can be verified without ranking changes.
- [ ] 4.2 Add or update tests proving search results, metadata, and diagnostics remain stable across equivalent searcher restructuring.
- [ ] 4.3 Defer ranking, alias, and embedding-model changes to a later change unless required to make new diagnostics pass.

## 5. Verification

- [ ] 5.1 Run focused search quality and evaluator tests.
- [ ] 5.2 Run the project test suite.
- [ ] 5.3 Run real-database `eval-search` with baseline comparison when the release database is available.
```

## openspec/changes/search-quality-evaluation-expansion/specs/search-quality-diagnostics/spec.md

- Source: openspec/changes/search-quality-evaluation-expansion/specs/search-quality-diagnostics/spec.md
- Lines: 1-67
- SHA256: 514ac8426617fb60588d6c19610b54dd2bdf757a3efd92c94f6f546ecc0dc43d

```md
## MODIFIED Requirements

### Requirement: Failure diagnostics for evaluation queries
The system SHALL attach diagnostic metadata to failed evaluation queries when `diagnostic_limit` is specified. Diagnostics SHALL also expose enough search execution metadata to distinguish ranking failures from degraded search mode, vector fallback, graph expansion changes, and filter precision issues.

#### Scenario: Diagnostics show expected target exists in DB
- **WHEN** a query fails but its expected paths/symbols exist in the database
- **THEN** `FailureDiagnostics.expected_present` SHALL be `True` and `expected_rows` SHALL contain the matching rows

#### Scenario: Diagnostics show best rank in window
- **WHEN** a query fails and `diagnostic_limit` is set
- **THEN** `FailureDiagnostics.best_rank` SHALL be the rank of the best matching result within the diagnostic window, or `None` if not found

#### Scenario: Diagnostics include search execution mode
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** diagnostics MUST include whether the query used hybrid search or FTS-only fallback
- **AND** diagnostics MUST include the fallback or degraded reason when one exists

#### Scenario: Diagnostics included in JSON output
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the JSON output SHALL include `failures[].diagnostics` with `expected_present`, `best_rank`, `best_rank_no_graph`, `expected_rows`, `diagnostic_window`, search mode, and fallback/degraded fields

#### Scenario: Diagnostics included in text report
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the text report SHALL include `diagnostics:` lines showing `expected_present`, `best_rank` values, search mode, and fallback/degraded reason

### Requirement: Failure diagnostics guide promotion decisions
Search quality diagnostics SHALL expose whether a failed or report-only query is blocked by missing data, recall, ranking, filtering, graph expansion, or degraded search execution.

#### Scenario: report-only query has missing expected data
- **WHEN** a report-only query expects addon or symbol data that is absent from the canonical database
- **THEN** diagnostics MUST mark the expected target as not present
- **AND** the query MUST be ineligible for gating promotion

#### Scenario: report-only query has low ranking
- **WHEN** a report-only query's expected target is present but below the required rank
- **THEN** diagnostics MUST include the best observed rank in the diagnostic window
- **AND** the query MUST remain report-only until ranking improves

#### Scenario: report-only query is affected by degraded search mode
- **WHEN** a report-only query fails while vector search is unavailable or degraded
- **THEN** diagnostics MUST identify the degraded mode
- **AND** promotion decisions MUST not treat the failure as a pure ranking regression

## ADDED Requirements

### Requirement: Evaluation diagnostics include latency summaries
Search quality diagnostics SHALL include latency summaries for evaluated query runs.

#### Scenario: JSON report includes latency summary
- **WHEN** search quality evaluation emits JSON
- **THEN** the report MUST include latency summary fields for evaluated queries

#### Scenario: text report includes latency summary
- **WHEN** search quality evaluation emits text output
- **THEN** the report MUST include a concise latency summary suitable for spotting slowdowns

### Requirement: Searcher refactors preserve diagnostics
Internal searcher restructuring SHALL preserve externally visible search results, evaluation metrics, and diagnostic metadata.

#### Scenario: equivalent refactor keeps baseline stable
- **WHEN** searcher internals are split without intended ranking changes
- **THEN** deterministic quality tests and real-database baseline comparison MUST remain stable

#### Scenario: metadata remains available after refactor
- **WHEN** search execution internals are reorganized
- **THEN** evaluation diagnostics MUST still receive search mode, fallback/degraded reason, and latency data
```

## openspec/changes/search-quality-evaluation-expansion/specs/semantic-search-quality/spec.md

- Source: openspec/changes/search-quality-evaluation-expansion/specs/semantic-search-quality/spec.md
- Lines: 1-83
- SHA256: efd4a94eb98e7aeeba6891c6b5285d8b2681e9049097d02ba5faaecd1c9891fc

[TRUNCATED]

```md
## MODIFIED Requirements

### Requirement: Search quality is evaluated with categorized golden queries
The packaged query suite SHALL contain at least 40 unique query IDs with at least 25 gating queries and at least 10 report-only queries, covering `class`, `symbol`, `tutorial`, `engine`, and `addon` categories. Gating metrics SHALL report empty or missing category coverage explicitly instead of allowing a required category to disappear silently. The suite SHALL include stable checks for symbol format variants, natural-language alias intent, graph expansion behavior, and addon/doc-type filter precision.

#### Scenario: Query suite meets expanded size and tier requirements
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the result SHALL contain >= 40 queries with >= 25 gating and >= 10 report-only

#### Scenario: Query suite covers all required categories
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the query categories SHALL include `class`, `symbol`, `tutorial`, `engine`, and `addon`

#### Scenario: Query suite includes normalization and graph tags
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one query SHALL have tag `normalization` and at least one SHALL have tag `graph`

#### Scenario: Query suite includes filter precision checks
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one gating query SHALL validate addon or doc-type filter precision

#### Scenario: Required gating category disappears
- **WHEN** real-database evaluation computes gating metrics
- **AND** a required category has zero gating queries
- **THEN** the report MUST include an explicit category coverage warning

### Requirement: Search quality metrics are reported consistently
Search quality evaluation SHALL report ranking and performance metrics in a stable shape suitable for humans and regression checks.

#### Scenario: metrics are calculated overall and by category
- **WHEN** search quality evaluation completes
- **THEN** it MUST report `hit@1`, `hit@3`, `hit@5`, and `MRR@5`
- **AND** it MUST report those metrics overall and grouped by query category

#### Scenario: latency metrics are reported for evaluated queries
- **WHEN** search quality evaluation completes
- **THEN** it MUST report query latency summary metrics including p50 and p95
- **AND** latency metrics MUST be available in machine-readable JSON output

#### Scenario: failed queries include diagnostic detail
- **WHEN** a golden query fails its top-K expectation
- **THEN** the report MUST include the query, category, expected constraints, observed top results, and failure classification

#### Scenario: machine-readable output is available
- **WHEN** a developer requests JSON output from search quality evaluation
- **THEN** the evaluator MUST emit the same metric values, performance metrics, and failed-query details in machine-readable form

### Requirement: Real-database quality gates only clear regressions
Real-database search quality evaluation SHALL compare results with a baseline and fail only on clear regressions, including clear quality regressions and configured stability regressions.

#### Scenario: first run can establish a baseline
- **WHEN** real-database evaluation runs without an existing baseline
- **THEN** it MUST be able to write a baseline artifact
- **AND** it MUST report that no regression comparison was performed

#### Scenario: significant metric regression fails the gate
- **WHEN** real-database evaluation runs with an existing baseline
- **AND** `hit@5` drops by more than the configured percentage-point threshold or `MRR@5` drops by more than the configured relative threshold
- **THEN** the evaluation command MUST fail
- **AND** it MUST report the baseline value, current value, and threshold that triggered failure

#### Scenario: significant latency regression is visible
- **WHEN** real-database evaluation runs with an existing baseline containing latency metrics
- **AND** current p95 latency exceeds the configured threshold
- **THEN** the evaluation report MUST identify the latency regression

#### Scenario: non-gating queries are report-only
- **WHEN** a golden query is marked report-only or newly introduced outside the gating baseline
- **THEN** its result MUST appear in the report
- **AND** its failure MUST NOT cause the regression gate to fail

## ADDED Requirements

### Requirement: Search quality verification is part of routine validation
The project SHALL provide a documented routine command or script path that runs the deterministic search quality checks and the real-database evaluation gate when the release database is available.

#### Scenario: routine validation includes deterministic quality tests
- **WHEN** a developer runs the documented routine validation path
- **THEN** deterministic search quality tests MUST be included

```

Full source: openspec/changes/search-quality-evaluation-expansion/specs/semantic-search-quality/spec.md

