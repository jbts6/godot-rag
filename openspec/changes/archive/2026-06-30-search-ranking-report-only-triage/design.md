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
