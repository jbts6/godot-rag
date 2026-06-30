# Comet Design Handoff

- Change: search-ranking-report-only-triage
- Phase: design
- Mode: compact
- Context hash: 8cb9b32b42ba11df86a7464b7b839fe083630b30943e1b839cd888e884797566

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/search-ranking-report-only-triage/proposal.md

- Source: openspec/changes/search-ranking-report-only-triage/proposal.md
- Lines: 1-26
- SHA256: 914fee8daad379f78b1ecdf5509c439131b1fdd0e8e3fd6540b1ba55930af7ff

```md
## Why

当前搜索质量闭环已经有 45 条评估查询、延迟指标、搜索执行元数据和拆分后的 searcher 边界，但 20 条 `report_only` 查询仍只是“观察项”。在继续调整 ranking、alias 或 intent scoring 前，需要先把这些观察项按数据缺口、召回、低排名、过滤和 degraded search mode 分类，避免把数据问题误判为 ranking 问题。

## What Changes

- 为 `eval-search` 增加面向 `report_only` 查询的 triage 输出或可复用分类结构。
- 对每个 `report_only` 查询给出明确状态：可考虑晋升 gating、需要数据/fixture、需要 recall/ranking 改进、需要 filter 修正，或受 degraded vector mode 影响。
- 产出后续优化候选清单，明确哪些查询适合进入 ranking signal explainability、query alias expansion 或数据补齐 change。
- 保持现有 25 条 gating 查询行为不退化，不在本 change 中调整 ranking 权重或 alias 规则。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `search-quality-diagnostics`: 增加 report-only 查询 triage 与后续优化候选分类要求。

## Impact

- 主要影响 `rst2md/rag/search_eval.py`、`rst2md/rag/search_eval_queries.json`、`rst2md/rag/cli.py` 中的 `eval-search` 诊断输出，以及对应测试。
- 不改变 `search_database` public API、数据库 schema、embedding 模型或 searcher ranking 权重。
- 后续 change 可基于 triage 结果安全进入 ranking signal、query rewrite 或 fixture 数据补齐。
```

## openspec/changes/search-ranking-report-only-triage/design.md

- Source: openspec/changes/search-ranking-report-only-triage/design.md
- Lines: 1-65
- SHA256: 08d8d24cb2a4891dfc6620c110f5b8012682128e2f8fac65d7ee4527228ac315

```md
## Context

The search quality loop now has 45 evaluation queries, latency metadata, fallback metadata, baseline protection, and a split searcher implementation. The remaining gap is decision support: 20 queries are marked `report_only`, but the current workflow does not produce a concise triage list that says whether a query is ready for gating, blocked by data, or needs recall/ranking/filter work.

This change should sit in the evaluation and diagnostics layer, not in search ranking itself. Its purpose is to make the next ranking change evidence-driven.

## Goals / Non-Goals

**Goals:**

- Classify every report-only query with actionable evidence.
- Reuse existing diagnostic data wherever possible: expected target presence, best rank, observed results, search mode, and fallback reason.
- Produce a clear candidate list for follow-up changes such as ranking signal explanations, query alias expansion, or fixture/data work.
- Preserve existing gating behavior and baseline protection.

**Non-Goals:**

- Do not adjust ranking weights, RRF fusion, vector recall, query rewrite rules, or alias rules.
- Do not promote report-only queries automatically.
- Do not change the search database schema, embedding model, or `search_database` public API.

## Decisions

### Decision 1: Triage belongs in search evaluation diagnostics

The triage logic will live near `search_eval.py`, because it derives decisions from evaluation outcomes and diagnostics rather than from search execution. This keeps ranking code focused on producing results and keeps promotion decisions in the evaluator.

Alternative considered: add triage fields directly to `SearchMetadata`. That would mix evaluation-specific workflow decisions into the runtime search API and create pressure to expose report-only concepts outside evaluation.

### Decision 2: Use a small deterministic classification set

The output should use a bounded set of classifications:

- `promotion_ready`
- `missing_expected_data`
- `missing_recall`
- `low_ranking`
- `filter_mismatch`
- `degraded_search`

This set maps directly to next actions. It is intentionally not a generic explanation engine.

Alternative considered: free-form textual recommendations only. Text is readable, but hard to test and hard to aggregate across 20 report-only queries.

### Decision 3: Recommendations are advisory

This change may identify queries eligible for gating promotion, but it will not edit `search_eval_queries.json` to promote them automatically. Promotion should remain a separate explicit decision after reviewing the triage output.

Alternative considered: automatically flip eligible queries from report-only to gating. That would combine diagnostics with policy mutation and make baseline drift harder to review.

## Risks / Trade-offs

- Triage can overfit current diagnostic fields -> Keep classifications evidence-based and expose the evidence in output.
- Some failures may be ambiguous -> Prefer a conservative classification and include observed results so a human can override.
- Output can become noisy -> Summarize report-only triage separately from gating failures.
- The existing spec mentions graph expansion from older language, while current searcher has no graph expansion implementation -> Do not introduce graph behavior; classify only evidence that exists in current evaluation/search metadata.

## Migration Plan

No data migration is required. Implementation should add tests first, then extend evaluator structures and CLI/report output. Existing gating evaluation and baseline comparison must remain compatible.

## Open Questions

- Should the triage summary be available in JSON only, or both JSON and text output? Initial recommendation: both, with JSON as the authoritative machine-readable form.
- Should promotion recommendations be written to a separate report artifact? Initial recommendation: no; keep output in evaluation reports until a later workflow needs persisted triage artifacts.
```

## openspec/changes/search-ranking-report-only-triage/tasks.md

- Source: openspec/changes/search-ranking-report-only-triage/tasks.md
- Lines: 1-23
- SHA256: 0099695e308514ea8592bd06145477846b203285b2485a8d9e728dd5a089501d

```md
## 1. Baseline and Test Setup

- [ ] 1.1 Run the current search evaluation and record the 25 gating / 20 report-only baseline behavior.
- [ ] 1.2 Add focused failing tests for report-only triage classifications and promotion recommendations.
- [ ] 1.3 Add CLI/report tests for the triage summary in JSON and text output.

## 2. Triage Model and Classification

- [ ] 2.1 Add a structured triage result model for report-only queries.
- [ ] 2.2 Classify report-only queries as `promotion_ready`, `missing_expected_data`, `missing_recall`, `low_ranking`, `filter_mismatch`, or `degraded_search`.
- [ ] 2.3 Attach evidence to each triage result: expected target presence, best rank, search mode, fallback reason, and observed top results.

## 3. Reporting and Follow-up Recommendations

- [ ] 3.1 Include report-only triage summaries in JSON evaluation output.
- [ ] 3.2 Include concise report-only triage summaries in text evaluation output.
- [ ] 3.3 Emit advisory follow-up ownership for each non-promotion-ready query: data/fixture, recall, ranking, filter, or degraded search investigation.

## 4. Verification and Documentation

- [ ] 4.1 Verify existing gating evaluation and baseline comparison behavior remains unchanged.
- [ ] 4.2 Run focused and full test suites.
- [ ] 4.3 Update WIP or related docs with the resulting next-step candidate list.
```

## openspec/changes/search-ranking-report-only-triage/specs/search-quality-diagnostics/spec.md

- Source: openspec/changes/search-ranking-report-only-triage/specs/search-quality-diagnostics/spec.md
- Lines: 1-22
- SHA256: 6ad00187e2181b07ba99a687f4f5ebcdeff0195a683d400557a09e4b44fd0de2

```md
## ADDED Requirements

### Requirement: Report-only query triage is summarized
Search quality diagnostics SHALL produce a triage summary for report-only evaluation queries when diagnostics are requested.

#### Scenario: report-only queries are classified
- **WHEN** search quality evaluation runs with report-only queries and a diagnostic window
- **THEN** each report-only query MUST be assigned a triage classification
- **AND** the classification MUST distinguish missing expected data, missing recall, low ranking, filter mismatch, degraded search execution, and promotion-ready results

#### Scenario: triage output includes evidence
- **WHEN** a report-only query is classified
- **THEN** the triage output MUST include the evidence used for the decision, including expected target presence, best observed rank when available, search mode, fallback reason, and observed top results

#### Scenario: promotion-ready queries are explicit
- **WHEN** a report-only query's expected target is present and matches within its required rank without degraded search execution
- **THEN** diagnostics MUST mark the query as eligible for gating promotion
- **AND** the output MUST identify that promotion as a candidate recommendation rather than silently changing the query suite

#### Scenario: follow-up ownership is identified
- **WHEN** a report-only query is not promotion-ready
- **THEN** diagnostics MUST identify the likely follow-up type as data or fixture work, recall work, ranking work, filter work, or degraded search investigation
```

