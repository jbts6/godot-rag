## Context

The current RAG search pipeline already includes symbol matching, FTS5 lexical search, vector semantic search, RRF fusion, graph expansion, snippets, and fallback metadata. Recent work also added a small set of golden-query tests and release database vector validation. That means the next search-quality bottleneck is not an obvious missing search stage; it is the lack of a broad, repeatable way to measure whether a search change improves or degrades quality.

The evaluation flow must cover two different needs. Fast checks should run against deterministic fixtures in tests. Full-corpus checks should run manually against the generated release database and compare against a baseline, without committing generated database binaries.

## Goals / Non-Goals

**Goals:**

- Provide a deterministic fixture-level evaluation layer suitable for CI.
- Provide a manual real-database evaluation path for the generated release database.
- Report `hit@1`, `hit@3`, `hit@5`, and `MRR@5` overall and by query category.
- Classify failed queries into actionable failure buckets for future search work.
- Gate only obvious regressions against a stored baseline for full-corpus evaluation.
- Keep generated SQLite database files untracked.

**Non-Goals:**

- No ranking algorithm changes.
- No embedding model changes.
- No database schema changes.
- No mandatory full release-database evaluation in default CI.
- No complex judgment model or LLM-based relevance scoring in the first version.

## Decisions

### Decision 1: Use a two-layer evaluation flow

The first layer uses small deterministic fixtures and belongs in tests. It should be quick enough to run during normal verification and should cover stable behavior such as symbol variants, doc type filters, addon filters, graph expansion on/off, and obvious query normalization cases.

The second layer uses the real release database and is run manually, for example by a CLI subcommand or build tool command. It should evaluate a larger query set and compare metrics with a baseline artifact.

Alternative considered: only evaluate the real release database. That would be more realistic, but it would make local and CI feedback slow and dependent on generated artifacts. Another alternative is fixture-only evaluation, but that would miss release-corpus noise and real chunking issues.

### Decision 2: Store golden queries as text fixtures

Golden queries should live in a small, reviewable text format such as YAML or JSON. Each entry should include a query, category, top-K requirement, and at least one expected path, symbol, doc type, or addon constraint. The first version should keep the model simple and avoid a large relevance schema.

Alternative considered: encode all cases directly in tests. That is simple initially, but it makes query set review, baseline evolution, and manual real-database evaluation harder.

### Decision 3: Compare real-database metrics against a baseline

The full-corpus evaluation should create a baseline on first run and fail only when later results clearly regress. Suggested starting thresholds are a `hit@5` drop greater than 5 percentage points or an `MRR@5` drop greater than 10 percent. New or experimental queries should be report-only until promoted into the gating baseline.

Alternative considered: enforce fixed absolute thresholds. That is too brittle while the query set is still maturing and the corpus may change.

### Decision 4: Make failures diagnostic, not just numeric

Evaluation output should include failed query details and a lightweight failure classification. The first version can use deterministic classifications from result state and query metadata: no expected result in top-K, expected result present but below required rank, graph expansion changed result quality, addon/doc type mismatch, chunk text appears noisy, or normalization-sensitive query failure.

Alternative considered: leave classification to manual inspection. That is acceptable for a handful of queries but does not scale once evaluation becomes part of release review.

## Risks / Trade-offs

- Golden queries can overfit fixtures -> keep fixture tests focused on stable contracts and use real-database evaluation for corpus-level quality.
- Baselines can hide low absolute quality -> report absolute metrics even when only regression gates fail the command.
- Corpus changes can legitimately alter expected paths -> make baseline updates explicit and reviewable.
- Failure classification can be imperfect -> treat classification as triage metadata, not a normative judgment.
- Full evaluation can be slow -> keep it manual by default and document when to run it.

## Migration Plan

1. Add the evaluation data model and metric calculation with focused unit tests.
2. Add a small deterministic fixture query set and CI-level tests.
3. Add a manual evaluation entry point for a provided database path.
4. Add baseline read/write and regression-gate behavior for real-database evaluation.
5. Document the verification flow and how to refresh baselines.

Rollback is straightforward because search behavior is unchanged: remove the evaluation command, fixtures, and tests without changing the search database or ranking pipeline.

## Open Questions

- Exact fixture file format: YAML is easier to read, JSON avoids adding a parser dependency if no YAML parser is already available.
- Exact command name: `godot-rag eval-search`, `godot-rag quality`, or a build-tool command under `godot-rag-build`.
- Baseline storage path: under `rst2md/rag/eval/`, `tests/fixtures/`, or `docs/search-quality/`.
