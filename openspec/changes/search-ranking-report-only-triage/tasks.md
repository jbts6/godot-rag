## 1. Baseline and Test Setup

- [x] 1.1 Run the current search evaluation and record the 25 gating / 20 report-only baseline behavior.
- [x] 1.2 Add focused failing tests for report-only triage classifications and promotion recommendations.
- [x] 1.3 Add CLI/report tests for the triage summary in JSON and text output.

## 2. Triage Model and Classification

- [x] 2.1 Add a structured triage result model for report-only queries.
- [x] 2.2 Classify report-only queries as `promotion_ready`, `missing_expected_data`, `missing_recall`, `low_ranking`, `filter_mismatch`, or `degraded_search`.
- [x] 2.3 Attach evidence to each triage result: expected target presence, best rank, search mode, fallback reason, and observed top results.

## 3. Reporting and Follow-up Recommendations

- [x] 3.1 Include report-only triage summaries in JSON evaluation output.
- [x] 3.2 Include concise report-only triage summaries in text evaluation output.
- [x] 3.3 Emit advisory follow-up ownership for each non-promotion-ready query: data/fixture, recall, ranking, filter, or degraded search investigation.

## 4. Verification and Documentation

- [x] 4.1 Verify existing gating evaluation and baseline comparison behavior remains unchanged.
- [x] 4.2 Run focused and full test suites.
- [x] 4.3 Update WIP or related docs with the resulting next-step candidate list.
<!-- 4.3 candidate list captured in implementation summary; no owning WIP doc updated -->
