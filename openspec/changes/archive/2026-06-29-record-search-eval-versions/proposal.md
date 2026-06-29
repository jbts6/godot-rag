## Why

`stabilize-search-quality-loop` was archived with a verification gap: the baseline metadata records the database counts and query-suite hash, but it does not record the evaluator/search versions required by the accepted technical design and task list. Without those version fields, a baseline can still be compared across evaluator or search-code changes without making the producing code identity explicit.

## What Changes

- Add version metadata to search quality evaluation reports and written baselines.
- Keep the existing database fingerprint and query-suite hash behavior unchanged.
- Refresh `docs/search-quality/baseline.json` so the checked-in baseline includes the new version metadata.
- Add regression tests that fail when version metadata is omitted.
- Tighten the `semantic-search-quality` spec so version metadata is an explicit acceptance scenario for baseline identity.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `semantic-search-quality`: Baseline identity metadata must include evaluator/search version fields in addition to database fingerprint and query-suite hash.

## Impact

- Affected code: `rst2md/rag/search_eval.py`.
- Affected tests: `rst2md/tests/test_search_eval.py`.
- Affected artifacts: `docs/search-quality/baseline.json`, `openspec/specs/semantic-search-quality/spec.md` through the delta spec.
- No CLI flag, external dependency, database schema, or runtime search behavior change is planned.
