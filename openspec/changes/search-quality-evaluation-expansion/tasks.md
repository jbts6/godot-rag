## 1. Query Suite Expansion

- [x] 1.1 Audit current `search_eval_queries.json` and categorize gaps across class, symbol, tutorial, engine, addon, normalization, graph, and filter precision.
- [x] 1.2 Add stable gating queries until the packaged suite has at least 40 unique queries and at least 25 gating queries.
- [x] 1.3 Keep unstable or data-dependent cases report-only and document why they are not gating.
- [x] 1.4 Update query-suite tests for expanded count, category, tag, and filter precision requirements.

## 2. Evaluation Metrics and Diagnostics

- [x] 2.1 Capture per-query elapsed time during `evaluate_database` without changing search result ranking.
- [x] 2.2 Report p50/p95 latency summaries in text and JSON evaluation output.
- [x] 2.3 Attach search mode and fallback/degraded reason to evaluation diagnostics where available.
- [x] 2.4 Add regression tests for latency fields and fallback/degraded diagnostic fields.

## 3. Validation Workflow

- [x] 3.1 Document the routine deterministic search quality validation command.
- [x] 3.2 Document the real-database `eval-search` baseline comparison command and when it should be run.
- [x] 3.3 Decide whether an existing project command should invoke the deterministic quality suite, and wire it if low risk.

## 4. Refactor Safety Boundary

- [x] 4.1 Identify the smallest searcher extraction boundary that can be verified without ranking changes.
- [x] 4.2 Add or update tests proving search results, metadata, and diagnostics remain stable across equivalent searcher restructuring.
- [x] 4.3 Defer ranking, alias, and embedding-model changes to a later change unless required to make new diagnostics pass.

## 5. Verification

- [x] 5.1 Run focused search quality and evaluator tests.
- [x] 5.2 Run the project test suite.
- [x] 5.3 Run real-database `eval-search` with baseline comparison when the release database is available.
