## 1. Evaluation Model And Metrics

- [x] 1.1 Define the golden-query fixture format and loader for query, category, top-K requirement, expected constraints, and report-only status.
- [x] 1.2 Implement metric calculation for `hit@1`, `hit@3`, `hit@5`, and `MRR@5` overall and by category.
- [x] 1.3 Implement failed-query result detail including expected constraints, observed top results, and failure classification.
- [x] 1.4 Add focused unit tests for metric calculation, expected-constraint matching, and failure classification.

## 2. Deterministic Fixture Evaluation

- [x] 2.1 Create a small deterministic fixture database builder or fixture dataset covering class, tutorial, addon, symbol-variant, doc type, and graph expansion cases.
- [x] 2.2 Add 30-50 categorized fixture golden queries with stable expected result constraints.
- [x] 2.3 Add focused tests that execute fixture evaluation without relying on generated local database artifacts.
- [x] 2.4 Add graph expansion enabled/disabled comparison coverage for queries where relation expansion matters.

## 3. Real Database Evaluation And Regression Gate

- [x] 3.1 Add an explicit manual evaluation entry point that accepts a database path and runs the real-database golden query set.
- [x] 3.2 Add human-readable and JSON report output with overall metrics, category metrics, failed queries, and graph expansion comparison details.
- [x] 3.3 Add baseline read/write support for real-database evaluation.
- [x] 3.4 Add regression-gate behavior that fails only when `hit@5` or `MRR@5` drops beyond configured thresholds.
- [x] 3.5 Ensure report-only or newly introduced queries appear in reports without failing the regression gate.

## 4. Documentation And Verification

- [x] 4.1 Document how to run fixture evaluation, real-database evaluation, and baseline refresh.
- [x] 4.2 Add CLI or command tests for text output, JSON output, first-run baseline creation, and regression failure.
- [x] 4.3 Run focused search quality tests.
- [x] 4.4 Run relevant RAG, semantic-search, CLI, and OpenSpec validation checks.
