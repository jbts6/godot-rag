# Comet Design Handoff

- Change: stabilize-search-quality-loop
- Phase: design
- Mode: compact
- Context hash: fa16739c0afee46429fecad0e028923452de106902917c8ef2baab4bf2370cff

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/stabilize-search-quality-loop/proposal.md

- Source: openspec/changes/stabilize-search-quality-loop/proposal.md
- Lines: 1-30
- SHA256: fe07e1fa4e3753a26db52afdb6ce53af5b378049e7e968baf13105fb04760fe9

```md
## Why

The current search quality gate is now guarded against empty-baseline mistakes, but it still does not make real search quality improvements repeatable. Report-only failures show that natural-language symbol aliases, category/filter coverage, and ranking stability need a tighter loop before more queries can safely become gating.

## What Changes

- Harden real-database baseline handling with DB/query-suite metadata and guards that reject empty or incomplete evaluation databases.
- Introduce a query-planning layer that makes aliases, symbol intent, doc-type intent, and addon intent available to all relevant search stages.
- Apply deterministic reranking so alias/symbol matches and intent-consistent results can be promoted without adding external reranker dependencies.
- Add promotion rules and tests for moving stable report-only queries back into the gating set.
- Preserve report-only visibility for unstable queries while making failures actionable by classification and category.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `semantic-search-quality`: baseline metadata, canonical database safeguards, category coverage checks, and report-only promotion rules.
- `query-rewrite`: query aliases expand into a structured query plan used beyond FTS-only recall.
- `intent-ranking`: intent signals participate in deterministic reranking, not only a small post-ranking doc-type boost.
- `search-quality-diagnostics`: evaluation failures expose enough metadata to distinguish empty/incomplete data, missing recall, low ranking, and filter/category issues.

## Impact

- Affected code: `rst2md/rag/search_eval.py`, `rst2md/rag/searcher.py`, query expansion helpers, search quality query fixtures, and related tests.
- Affected artifacts: `rst2md/rag/search_eval_queries.json`, `docs/search-quality/baseline.json`, and OpenSpec delta specs for modified capabilities.
- No new runtime service, external model, learned reranker, or database schema migration is planned.
```

## openspec/changes/stabilize-search-quality-loop/design.md

- Source: openspec/changes/stabilize-search-quality-loop/design.md
- Lines: 1-62
- SHA256: ce9d885492248b1859dd86f84672c46b31b3530f7ac467d00d37fd38e072a11e

```md
## Context

Search evaluation now has a real-database baseline, but the loop is still fragile: a baseline can be refreshed from the wrong database unless the artifact records what it represents, category coverage can silently collapse, and report-only failures are not yet tied to a promotion path. Search ranking also treats alias expansion as an FTS-only fallback, so natural-language symbol intent is not consistently available to exact symbol lookup, hybrid candidate generation, graph comparison, or final ranking.

The existing implementation already has useful pieces: golden query categories, report-only queries, failure classification, conservative alias expansion, vector fallback metadata, and a small intent boost. This change should connect those pieces into a stable quality loop instead of replacing the search stack.

## Goals / Non-Goals

**Goals:**

- Make baseline artifacts self-describing and reject empty or incomplete canonical databases before writing a baseline.
- Keep report-only failures visible while defining explicit rules for promoting stable queries back into gating.
- Introduce a structured query plan that carries original text, normalized symbol candidates, alias candidates, doc-type intent, and addon intent.
- Use query-plan signals across recall and deterministic reranking so natural-language symbol queries can rank expected symbols in top-K.
- Add tests that protect the specific regression classes found by the current report-only failures.

**Non-Goals:**

- Do not add an LLM, learned reranker, external search service, or new model dependency.
- Do not perform a broad rewrite of search storage or database schema.
- Do not require committing generated database binaries.
- Do not promote addon queries to gating until the underlying indexed data is proven present and stable.

## Decisions

1. Use a canonical evaluation metadata gate before baseline writes.

   The evaluator will record database fingerprint fields such as document, chunk, symbol, and vector counts, plus a query-suite hash. Baseline writing will fail early when required counts are zero or inconsistent. This is preferred over relying on README discipline because it makes invalid baselines impossible to create through the CLI path.

2. Represent query understanding as a `QueryPlan`.

   A small internal data object will be created from each query. It will include the original query, normalized query, alias-derived symbol candidates, symbol-like candidates, doc-type intent, and addon intent. Existing alias expansion will feed this object first; recall channels can then consume structured signals instead of each stage recomputing partial normalization.

3. Keep recall broad and ranking deterministic.

   Exact/suffix/prefix symbol lookup should evaluate query-plan symbol candidates. FTS should still run original and alias variants. Vector search should keep the original natural-language query by default, but the final candidate pool should carry the plan signals into a deterministic reranker. This avoids vector overfitting to symbol aliases while still promoting exact alias hits.

4. Treat promotion as a tested lifecycle.

   Report-only queries become gating only when the expected target is present in the canonical database, the query passes within top-K under graph-enabled evaluation, and no category coverage check is violated. This keeps unstable addon and ingestion-dependent queries visible without making the gate flaky.

## Risks / Trade-offs

- Alias boosts can over-promote symbol results for tutorial-like queries -> keep symbol-like and tutorial intent mutually constrained, and test how-to/tutorial queries separately.
- Baseline metadata can make local workflows stricter -> provide clear failure messages that name the missing DB counts or mismatched query hash.
- A deterministic reranker can become a pile of magic constants -> keep boosts named, small, and covered by focused tests for each failure class.
- Addon failures may reflect missing indexed content rather than ranking -> keep addon queries report-only until diagnostics show expected addon rows are present.

## Migration Plan

1. Add metadata validation without changing search behavior.
2. Add query-plan construction and tests for alias/symbol/doc-type/addon intent.
3. Wire query-plan symbol candidates into existing recall paths.
4. Add deterministic reranking and promote only queries that pass on the canonical database.
5. Refresh the baseline with metadata once the quality gate is stable.

Rollback is straightforward: revert the change commits and restore the previous baseline/query fixture. No database migration is required.

## Open Questions

- The canonical database for local verification is assumed to be `godot_rag.db`; CI may need an equivalent generated or fixture database if that file is not available.
- Addon query promotion depends on whether addon documents are indexed in the canonical database; this change should diagnose that before changing addon gating.
```

## openspec/changes/stabilize-search-quality-loop/tasks.md

- Source: openspec/changes/stabilize-search-quality-loop/tasks.md
- Lines: 1-23
- SHA256: 2bb4cd386164fe0dd0dd07b007900d1a5707e39df5e6f89ee0188514b9b72254

```md
## 1. Evaluation Stability

- [ ] 1.1 Add baseline metadata for database fingerprint, query-suite hash, and relevant search/evaluation versions.
- [ ] 1.2 Reject baseline writes for empty or incomplete real-database inputs with actionable diagnostics.
- [ ] 1.3 Report required category coverage warnings when gating metrics contain zero queries for an expected category.

## 2. Query Planning and Ranking

- [ ] 2.1 Introduce a structured query plan that captures original text, normalized symbols, alias-derived symbol candidates, doc-type intent, and addon intent.
- [ ] 2.2 Route query-plan symbol candidates through exact, suffix, and prefix symbol recall while preserving existing FTS query variants.
- [ ] 2.3 Replace the narrow post-ranking intent boost with deterministic reranking signals for alias, symbol, doc-type, addon, path, and heading matches.

## 3. Search Quality Promotion

- [ ] 3.1 Add promotion checks that determine whether report-only queries are eligible to become gating queries.
- [ ] 3.2 Promote only stable natural-language symbol queries that pass against the canonical database.
- [ ] 3.3 Keep addon and missing-data queries report-only until diagnostics prove expected rows are present.

## 4. Verification

- [ ] 4.1 Add focused tests for baseline metadata, invalid database rejection, query planning, reranking, and promotion rules.
- [ ] 4.2 Refresh the real-database baseline after quality improvements pass.
- [ ] 4.3 Run focused search tests, full search quality evaluation, and baseline comparison.
```

## openspec/changes/stabilize-search-quality-loop/specs/intent-ranking/spec.md

- Source: openspec/changes/stabilize-search-quality-loop/specs/intent-ranking/spec.md
- Lines: 1-31
- SHA256: 1680a359e5d05058ce0ea556ed1b1a0880706c0bac91d933e482db2a9129e3a0

```md
## ADDED Requirements

### Requirement: Deterministic reranking uses query-plan signals
Search SHALL apply deterministic reranking signals after candidate assembly and before returning final results.

#### Scenario: alias symbol match is promoted
- **WHEN** a candidate result symbol exactly matches a query-plan alias-derived symbol candidate
- **THEN** reranking MUST increase that candidate's final rank relative to candidates without symbol, path, heading, or intent matches

#### Scenario: doc-type intent remains constrained
- **WHEN** a query expresses tutorial intent
- **THEN** reranking MUST prefer tutorial results without suppressing exact symbol matches for symbol-like queries

#### Scenario: addon intent can be represented without gating unstable data
- **WHEN** a query expresses addon intent
- **THEN** reranking MUST expose addon intent as a ranking signal
- **AND** evaluation MUST keep addon queries report-only unless expected addon rows exist in the canonical database

## MODIFIED Requirements

### Requirement: Intent boost applied post-ranking
The system SHALL apply deterministic intent reranking after candidate assembly, before final sort. Existing doc-type boosts SHALL become one named reranking signal rather than the only intent-ranking mechanism.

#### Scenario: Boost adjusts scores and re-sorts
- **WHEN** search results are assembled and intent boost is applicable
- **THEN** each result's score SHALL be adjusted by named reranking signals
- **AND** results SHALL be re-sorted by adjusted score descending

#### Scenario: Reranking is explainable in tests
- **WHEN** a focused search ranking test asserts an alias or intent promotion
- **THEN** the expected promotion MUST correspond to a named deterministic signal
```

## openspec/changes/stabilize-search-quality-loop/specs/query-rewrite/spec.md

- Source: openspec/changes/stabilize-search-quality-loop/specs/query-rewrite/spec.md
- Lines: 1-56
- SHA256: 71ba38c2f2c7185d4f3b6a1e7eb9cbd0d581059f5e90df92cfd11143d3c9ec8c

```md
## ADDED Requirements

### Requirement: Query plan exposes structured search intent
The system SHALL build a structured query plan for each search query before recall and ranking.

#### Scenario: alias query creates symbol candidates
- **WHEN** a query contains tokens matching an alias rule such as "attach node to scene tree"
- **THEN** the query plan MUST include the original query
- **AND** it MUST include `Node.add_child` as an alias-derived symbol candidate

#### Scenario: exact symbol query remains deduplicated
- **WHEN** a query is already a symbol name such as "Node.add_child"
- **THEN** the query plan MUST include a single normalized symbol candidate for `Node.add_child`
- **AND** it MUST NOT duplicate that candidate through alias expansion

#### Scenario: unknown query keeps original text
- **WHEN** a query does not match any alias or symbol rule
- **THEN** the query plan MUST preserve the original query text
- **AND** it MUST expose no alias-derived symbol candidates

### Requirement: Query plan signals feed symbol recall and ranking
Search SHALL use query-plan symbol candidates outside FTS-only recall.

#### Scenario: alias symbol participates in exact symbol lookup
- **WHEN** `search_database` receives "attach node to scene tree"
- **THEN** exact or suffix symbol lookup MUST evaluate the `Node.add_child` query-plan candidate

#### Scenario: alias symbol can influence deterministic reranking
- **WHEN** a result symbol matches a query-plan alias-derived symbol candidate
- **THEN** deterministic reranking MUST be able to promote that result ahead of lower-confidence lexical or vector-only matches

## MODIFIED Requirements

### Requirement: Conservative query alias expansion
The system SHALL expand natural-language queries into structured query-plan variants that include the original query plus any matching symbol aliases.

#### Scenario: Known alias pattern matches
- **WHEN** a query contains tokens matching an alias rule (e.g., "attach node to scene tree")
- **THEN** `expand_query_variants` SHALL return the original query followed by the matching symbol alias (e.g., "Node.add_child")
- **AND** the query plan SHALL expose the matching symbol alias as a symbol candidate

#### Scenario: No alias matches
- **WHEN** a query does not match any alias rule
- **THEN** `expand_query_variants` SHALL return a single-element list containing only the original query
- **AND** the query plan SHALL expose no alias-derived symbol candidate

#### Scenario: Exact symbol query deduplication
- **WHEN** a query is already a symbol name (e.g., "Node.add_child")
- **THEN** `expand_query_variants` SHALL return a single-element list without duplicates
- **AND** the query plan SHALL keep one normalized symbol candidate

## REMOVED Requirements

### Requirement: Query variants used for FTS recall only
**Reason**: Alias-derived symbol intent must participate in exact symbol recall and deterministic reranking to fix natural-language symbol queries.
**Migration**: Use the query plan as the shared source of alias and symbol candidates while preserving FTS variant behavior for lexical recall.
```

## openspec/changes/stabilize-search-quality-loop/specs/search-quality-diagnostics/spec.md

- Source: openspec/changes/stabilize-search-quality-loop/specs/search-quality-diagnostics/spec.md
- Lines: 1-27
- SHA256: 6c414534df686cc4551adb19d17262aea76d811e507b4903b32562636573784b

```md
## ADDED Requirements

### Requirement: Evaluation reports baseline input validity
Search quality diagnostics SHALL report whether the evaluated database is valid for baseline writes and regression comparisons.

#### Scenario: invalid baseline input is diagnosed
- **WHEN** a database fails baseline input validation
- **THEN** diagnostics MUST include the failing count or consistency check
- **AND** the command output MUST explain why the baseline was not written

#### Scenario: baseline comparison reports query-suite mismatch
- **WHEN** a baseline comparison uses a query suite whose hash differs from the baseline metadata
- **THEN** diagnostics MUST report the mismatch
- **AND** regression messages MUST distinguish query-suite drift from ranking regression

### Requirement: Failure diagnostics guide promotion decisions
Search quality diagnostics SHALL expose whether a failed or report-only query is blocked by missing data, recall, ranking, or filtering.

#### Scenario: report-only query has missing expected data
- **WHEN** a report-only query expects addon or symbol data that is absent from the canonical database
- **THEN** diagnostics MUST mark the expected target as not present
- **AND** the query MUST be ineligible for gating promotion

#### Scenario: report-only query has low ranking
- **WHEN** a report-only query's expected target is present but below the required rank
- **THEN** diagnostics MUST include the best observed rank in the diagnostic window
- **AND** the query MUST remain report-only until ranking improves
```

## openspec/changes/stabilize-search-quality-loop/specs/semantic-search-quality/spec.md

- Source: openspec/changes/stabilize-search-quality-loop/specs/semantic-search-quality/spec.md
- Lines: 1-64
- SHA256: 63d170e82a2291a45c3d543c92652d86b5797f9e59d32a5d845abff3c6f5bfdd

```md
## ADDED Requirements

### Requirement: Baseline artifacts identify their evaluation inputs
Search quality baselines SHALL record enough metadata to prove which database and query suite produced the metrics.

#### Scenario: baseline includes database fingerprint
- **WHEN** a baseline is written from a populated evaluation database
- **THEN** the baseline JSON MUST include document, chunk, symbol, and vector row counts
- **AND** it MUST include a deterministic database fingerprint derived from those counts and available file metadata

#### Scenario: baseline includes query suite identity
- **WHEN** a baseline is written
- **THEN** the baseline JSON MUST include a deterministic hash of the loaded query definitions
- **AND** a later comparison MUST report when the current query-suite hash differs from the baseline hash

### Requirement: Invalid evaluation databases cannot create baselines
Real-database search quality evaluation SHALL reject empty or incomplete databases before writing a baseline.

#### Scenario: empty database baseline write is rejected
- **WHEN** baseline writing is requested for a database with zero documents, chunks, or symbols
- **THEN** the command MUST fail
- **AND** no baseline file MUST be written
- **AND** the error MUST identify the zero-count tables

#### Scenario: vector row mismatch is reported
- **WHEN** baseline writing is requested for a database with a `vec_chunks` row count that does not match the `chunks` row count
- **THEN** the command MUST fail unless vector checks are explicitly disabled for a fixture-only evaluation
- **AND** the error MUST identify the vector row mismatch

### Requirement: Report-only promotion follows objective rules
Search quality evaluation SHALL define when report-only queries can become gating queries.

#### Scenario: stable report-only query is eligible for promotion
- **WHEN** a report-only query has an expected target present in the canonical database
- **AND** graph-enabled evaluation ranks the expected target within the query required window
- **AND** the query category remains represented in gating metrics
- **THEN** the query MAY be promoted to gating in the query fixture

#### Scenario: unstable report-only query remains visible
- **WHEN** a report-only query fails promotion criteria
- **THEN** it MUST remain in evaluation output
- **AND** its failure MUST NOT cause the regression gate to fail

## MODIFIED Requirements

### Requirement: Search quality is evaluated with categorized golden queries
The packaged query suite SHALL contain at least 30 unique query IDs with at least 12 gating queries and at least 8 report-only queries, covering `class`, `symbol`, `tutorial`, `engine`, and `addon` categories. Gating metrics SHALL report empty or missing category coverage explicitly instead of allowing a required category to disappear silently.

#### Scenario: Query suite meets size and tier requirements
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the result SHALL contain >= 30 queries with >= 12 gating and >= 8 report-only

#### Scenario: Query suite covers all required categories
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the query categories SHALL include `class`, `symbol`, `tutorial`, `engine`, and `addon`

#### Scenario: Query suite includes normalization and graph tags
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one query SHALL have tag `normalization` and at least one SHALL have tag `graph`

#### Scenario: Required gating category disappears
- **WHEN** real-database evaluation computes gating metrics
- **AND** a required category has zero gating queries
- **THEN** the report MUST include an explicit category coverage warning
```

