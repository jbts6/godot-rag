## 1. Evaluation Stability

- [x] 1.1 Add baseline metadata for database fingerprint, query-suite hash, and relevant search/evaluation versions.
- [x] 1.2 Reject baseline writes for empty or incomplete real-database inputs with actionable diagnostics.
- [x] 1.3 Report required category coverage warnings when gating metrics contain zero queries for an expected category.

## 2. Query Planning and Ranking

- [x] 2.1 Introduce a structured query plan that captures original text, normalized symbols, alias-derived symbol candidates, doc-type intent, and addon intent.
- [x] 2.2 Route query-plan symbol candidates through exact, suffix, and prefix symbol recall while preserving existing FTS query variants.
- [ ] 2.3 Replace the narrow post-ranking intent boost with deterministic reranking signals for alias, symbol, doc-type, addon, path, and heading matches.

## 3. Search Quality Promotion

- [ ] 3.1 Add promotion checks that determine whether report-only queries are eligible to become gating queries.
- [ ] 3.2 Promote only stable natural-language symbol queries that pass against the canonical database.
- [ ] 3.3 Keep addon and missing-data queries report-only until diagnostics prove expected rows are present.

## 4. Verification

- [ ] 4.1 Add focused tests for baseline metadata, invalid database rejection, query planning, reranking, and promotion rules.
- [ ] 4.2 Refresh the real-database baseline after quality improvements pass.
- [ ] 4.3 Run focused search tests, full search quality evaluation, and baseline comparison.
