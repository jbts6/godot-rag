# Search Quality Evaluation Design

## Context

The RAG search pipeline already combines symbol matching, FTS5 lexical search, vector semantic search, RRF fusion, graph expansion, snippets, and fallback metadata. The next bottleneck is not another ad hoc ranking tweak; it is the lack of a broad, repeatable way to measure whether search changes improve or degrade quality.

The evaluation flow needs two layers: fast deterministic fixture checks for normal verification, and full-corpus checks against a generated release database for manual quality review.

## Goals

- Add a deterministic fixture-level search quality evaluation layer suitable for tests and CI.
- Add a manual real-database evaluation path for the generated release database.
- Report `hit@1`, `hit@3`, `hit@5`, and `MRR@5` overall and by query category.
- Compare real-database evaluation with a stored baseline and fail only on clear regressions.
- Classify failed queries into actionable failure modes for future search work.

## Non-Goals

- No ranking algorithm changes.
- No embedding model changes.
- No database schema changes.
- No mandatory real-database evaluation in default CI.
- No LLM-based relevance scoring in the first version.

## Approach

Use text fixtures for categorized golden queries. Each query records the query text, category, required top-K, and expected constraints such as path, symbol, doc type, or addon. Fixture-level tests build or use a small deterministic database and run quickly.

Add an explicit manual evaluation entry point for a provided database path. The command reports metrics and failed-query details in text and JSON. When a baseline exists, the evaluator compares current metrics to baseline values and fails only when `hit@5` or `MRR@5` crosses configured regression thresholds. New or report-only queries appear in the report but do not fail the gate.

Failure classification should start deterministic and lightweight: missing recall, low ranking, filter mismatch, graph expansion impact, chunk noise, or query normalization sensitivity.

## OpenSpec Artifacts

The implementation contract lives in `openspec/changes/search-quality-evaluation/`:

- `proposal.md`
- `design.md`
- `specs/semantic-search-quality/spec.md`
- `tasks.md`

## Verification

- OpenSpec validation: `openspec validate search-quality-evaluation --strict`
- Focused tests: metric calculation, fixture evaluation, CLI/report output, baseline creation, and regression failure.
- Relevant RAG tests after implementation.
