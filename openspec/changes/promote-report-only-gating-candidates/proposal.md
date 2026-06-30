## Why

Report-only triage shows that most observation queries are now stable enough to protect future ranking work. Promoting reviewed, non-addon promotion-ready queries to gating will increase regression coverage before changing ranking or alias behavior.

## What Changes

- Remove `report_only` from stable, non-addon promotion-ready evaluation queries.
- Keep addon promotion-ready queries as report-only because addon data is still treated as unstable by the promotion policy.
- Refresh the reviewed search-quality baseline against the updated gating set.
- Preserve the three remaining non-promotion-ready report-only queries for focused recall/ranking follow-up.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `search-quality-diagnostics`: evaluation query promotion policy and baseline coverage for reviewed report-only candidates.

## Impact

- Affects `rst2md/rag/search_eval_queries.json` and `docs/search-quality/baseline.json`.
- Affects tests that assert packaged evaluation query tier counts.
- Does not change search ranking, query rewrite, database schema, public APIs, or evaluation metric calculation.
