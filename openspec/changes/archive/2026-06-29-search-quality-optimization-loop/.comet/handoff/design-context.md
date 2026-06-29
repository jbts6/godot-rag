# Comet Design Handoff

- Change: search-quality-optimization-loop
- Phase: design
- Mode: compact
- Context hash: efaca42cc446214d506c7a29eca8b9499ccd76666170f41aaa5fc041478c2d61

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/search-quality-optimization-loop/proposal.md

- Source: openspec/changes/search-quality-optimization-loop/proposal.md
- Lines: 1-33
- SHA256: 69e6fbd4f845c85e9493d3e7b9435f444dc21a8441eb35622b0ea155955d0dba

```md
## Why

The `eval-search` CLI command is documented but not importable due to a packaging misconfiguration. The packaged golden-query suite is too small (5 entries) to catch regressions. Failed queries lack diagnostics, making it hard to diagnose whether failures are recall issues or ranking issues. There is no repeatable optimization loop for improving search quality.

## What Changes

- Fix `pyproject.toml` so `godot-rag` CLI points to the importable `rag.cli:main` module and includes `rst2md/rag` in wheel packaging.
- Add `FailureDiagnostics` dataclass and attach diagnostic metadata to failed evaluation queries (expected-present, best-rank, diagnostic window).
- Expand the packaged golden-query suite from 5 to 30+ entries with tiered gating (`report_only`) and coverage for `class`, `symbol`, `tutorial`, `engine`, and `addon` categories.
- Add conservative query rewriting (`expand_query_variants`) for natural-language aliases that map to known symbols.
- Add intent-aware ranking (`doc_type_boost`) that boosts tutorial results for "how to" queries.
- Update README with working `eval-search` commands and generate a reviewable baseline JSON.

## Capabilities

### New Capabilities
- `search-quality-diagnostics`: Failure diagnostics for evaluation queries — whether expected targets exist in DB, best rank in diagnostic window.
- `query-rewrite`: Conservative natural-language-to-symbol alias expansion for lexical recall.
- `intent-ranking`: Doc-type-aware ranking boost for tutorial-intent queries.

### Modified Capabilities
- `semantic-search-quality`: Expanded golden-query suite with tiered gating and broader category coverage.

## Impact

- `pyproject.toml`: CLI entry point and wheel packaging.
- `rst2md/rag/search_eval.py`: New dataclass, diagnostic helpers, JSON/text report fields.
- `rst2md/rag/query_rewrite.py`: New module for alias expansion and intent boost.
- `rst2md/rag/searcher.py`: FTS query variant merging and intent boost integration.
- `rst2md/rag/search_eval_queries.json`: Expanded from 5 to 30+ queries.
- Tests: `test_search_eval.py`, `test_search_eval_cli.py`, `test_searcher_module.py`, `test_rag_search.py`.
- `README.md`: Updated evaluation documentation.
- `docs/search-quality/baseline.json`: New baseline file.
```

## openspec/changes/search-quality-optimization-loop/design.md

- Source: openspec/changes/search-quality-optimization-loop/design.md
- Lines: 1-60
- SHA256: 68fac3694356774b81e9ce992eab969bca2fb5c0f3902ed4bb663039f487a191

```md
## Context

The godot-rag project has an existing search pipeline using SQLite FTS5 + sqlite-vec + RRF fusion. An `eval-search` CLI command exists but is broken due to packaging misconfiguration. The current golden-query suite has only 5 entries. Failed queries provide no diagnostic information, making it difficult to distinguish recall failures from ranking failures.

## Goals / Non-Goals

**Goals:**
- Make `eval-search` CLI runnable via correct packaging
- Provide failure diagnostics for debugging query failures
- Expand query coverage to 30+ tiered queries across 5 categories
- Improve recall for natural-language queries via conservative alias rewriting
- Improve ranking for tutorial-intent queries via doc-type boost
- Establish a reviewable baseline for regression detection

**Non-Goals:**
- Replace or retrain the embedding model
- Change SQLite, FTS5, sqlite-vec, or RRF fusion architecture
- Require full release-database evaluation in default CI
- Make broad/corpus-sensitive queries gating (keep as `report_only`)

## Decisions

### D1: Query rewriting as lexical recall candidates only

**Decision:** `expand_query_variants()` returns alias strings used only for FTS matching. Vector search continues using the original query text.

**Rationale:** Aliases are conservative symbol mappings (e.g., "attach node to scene tree" → "Node.add_child"). Using them for vector search would dilute semantic intent. FTS benefits from exact symbol matches; vector search does not.

**Alternatives considered:**
- Rewrite for both FTS and vector: rejected — aliases are lexical, not semantic
- Use aliases as RRF sub-queries: rejected — adds complexity without clear benefit

### D2: Intent boost as post-ranking score adjustment

**Decision:** Apply `doc_type_boost()` after candidate assembly, before final sort. Boost is a small additive value (0.05) applied to tutorial results for how-to queries.

**Rationale:** Keeps the boost transparent and separable from the core ranking. Does not alter FTS or vector scores. Easy to tune or remove.

**Alternatives considered:**
- Re-rank with separate model: rejected — overkill for tutorial intent
- Filter by doc_type: rejected — would remove relevant class results entirely

### D3: Tiered query suite with `report_only` flag

**Decision:** Use the existing `GoldenQuery.report_only` field to tier queries. Gating queries (≥12) must pass; report-only queries (≥8) surface regressions without blocking.

**Rationale:** Broad queries (aliases, intent, graph, addon) are valuable for diagnostics but too corpus-sensitive for CI gating. The tiering lets us track them without false failures.

### D4: Failure diagnostics as separate dataclass

**Decision:** `FailureDiagnostics` is a frozen dataclass attached to `QueryResult.diagnostics`. It is computed on-demand via `diagnostic_limit` parameter, not by default.

**Rationale:** Diagnostics require extra DB queries. Making it opt-in keeps the default evaluation fast. The `diagnostic_limit` controls how far to search for the expected target.

## Risks / Trade-offs

- **Alias rules are manually curated** → Risk: maintenance burden grows. Mitigation: start conservative (5 rules), expand based on observed failures.
- **Intent boost is heuristic** → Risk: may over-boost or under-boost. Mitigation: small value (0.05), easy to tune; tutorial queries are `report_only` initially.
- **Baseline JSON is point-in-time** → Risk: stale baseline after corpus changes. Mitigation: `--write-baseline` flag for refresh; baseline is reviewed, not auto-generated.
- **Diagnostic queries add latency** → Risk: slower evaluation. Mitigation: `diagnostic_limit` is opt-in; default evaluation skips diagnostics.
```

## openspec/changes/search-quality-optimization-loop/tasks.md

- Source: openspec/changes/search-quality-optimization-loop/tasks.md
- Lines: 1-57
- SHA256: 77a24849f4ab358c6f9aba1d12ed36cdaf7efc428bb8fb19487b2a70fd1c12f4

```md
## 1. Fix CLI Entry Point

- [ ] 1.1 Write failing packaging test in `test_search_eval_cli.py`
- [ ] 1.2 Run failing test to confirm it fails
- [ ] 1.3 Fix `pyproject.toml` script target and wheel packages
- [ ] 1.4 Verify test passes and `godot-rag eval-search --help` works
- [ ] 1.5 Commit: "fix: make eval-search CLI entrypoint importable"

## 2. Add Failure Diagnostics

- [ ] 2.1 Write failing diagnostics tests in `test_search_eval.py`
- [ ] 2.2 Run failing tests to confirm they fail
- [ ] 2.3 Add `FailureDiagnostics` dataclass and update `QueryResult` in `search_eval.py`
- [ ] 2.4 Add diagnostic helpers (`_query_constraints`, `_fetch_expected_rows`, `_find_matching_rank`)
- [ ] 2.5 Integrate diagnostics into `evaluate_database` with `diagnostic_limit` parameter
- [ ] 2.6 Add diagnostics to `report_to_dict` and `format_text_report`
- [ ] 2.7 Verify diagnostics tests pass
- [ ] 2.8 Commit: "feat: add failure diagnostics to search evaluation"

## 3. Expand Golden Query Suite

- [ ] 3.1 Write failing query-suite shape test in `test_search_eval.py`
- [ ] 3.2 Run failing test to confirm it fails
- [ ] 3.3 Replace `search_eval_queries.json` with 30+ tiered queries
- [ ] 3.4 Verify query loading and shape tests pass
- [ ] 3.5 Commit: "test: expand tiered search quality queries"

## 4. Add Query Rewriting

- [ ] 4.1 Write failing unit tests for `expand_query_variants` in `test_searcher_module.py`
- [ ] 4.2 Write failing search integration test in `test_rag_search.py`
- [ ] 4.3 Run failing tests to confirm they fail
- [ ] 4.4 Create `rst2md/rag/query_rewrite.py` with alias rules
- [ ] 4.5 Integrate query variants into `searcher.py` FTS path
- [ ] 4.6 Promote fixed alias queries out of `report_only` in query JSON
- [ ] 4.7 Verify rewrite tests pass
- [ ] 4.8 Commit: "feat: add conservative query rewrite aliases"

## 5. Add Intent-Aware Ranking

- [ ] 5.1 Write failing unit tests for `doc_type_boost` in `test_searcher_module.py`
- [ ] 5.2 Write failing integration test in `test_rag_search.py`
- [ ] 5.3 Run failing tests to confirm they fail
- [ ] 5.4 Add `doc_type_boost` to `query_rewrite.py`
- [ ] 5.5 Apply intent boost in `searcher.py` post-ranking
- [ ] 5.6 Promote tutorial intent query out of `report_only`
- [ ] 5.7 Verify intent tests pass
- [ ] 5.8 Commit: "feat: boost tutorial intent in search ranking"

## 6. Document and Baseline

- [ ] 6.1 Update README with working `eval-search` commands
- [ ] 6.2 Run full focused test suite
- [ ] 6.3 Run manual evaluation and verify output
- [ ] 6.4 Create baseline JSON at `docs/search-quality/baseline.json`
- [ ] 6.5 Verify baseline comparison works
- [ ] 6.6 Commit: "docs: document search quality optimization loop"
```

## openspec/changes/search-quality-optimization-loop/specs/intent-ranking/spec.md

- Source: openspec/changes/search-quality-optimization-loop/specs/intent-ranking/spec.md
- Lines: 1-19
- SHA256: 4a3098b6b962a6a1f7a5a1e2a9c4e9e82be35484c347766da93829a8837876c5

```md
## ADDED Requirements

### Requirement: Tutorial intent detection
The system SHALL detect tutorial intent from query patterns and boost tutorial doc-type results.

#### Scenario: How-to query boosts tutorial results
- **WHEN** a query starts with "how to " or contains " tutorial", " guide", or "learn "
- **THEN** `doc_type_boost` SHALL return 0.05 for `doc_type == "tutorial"` and 0.0 for other types

#### Scenario: Symbol query does not trigger intent boost
- **WHEN** a query contains "." or "_" (symbol-like pattern)
- **THEN** `doc_type_boost` SHALL return 0.0 for all doc types

### Requirement: Intent boost applied post-ranking
The system SHALL apply doc-type boost after candidate assembly, before final sort.

#### Scenario: Boost adjusts scores and re-sorts
- **WHEN** search results are assembled and intent boost is applicable
- **THEN** each result's score SHALL be increased by the boost value and results SHALL be re-sorted by adjusted score descending
```

## openspec/changes/search-quality-optimization-loop/specs/query-rewrite/spec.md

- Source: openspec/changes/search-quality-optimization-loop/specs/query-rewrite/spec.md
- Lines: 1-27
- SHA256: d054af25aa0cb5d82d8d756f7e8464ae99263c8bd19b591b63fafb1cf94ebb7e

```md
## ADDED Requirements

### Requirement: Conservative query alias expansion
The system SHALL expand natural-language queries into variant lists that include the original query plus any matching symbol aliases.

#### Scenario: Known alias pattern matches
- **WHEN** a query contains tokens matching an alias rule (e.g., "attach node to scene tree")
- **THEN** `expand_query_variants` SHALL return the original query followed by the matching symbol alias (e.g., "Node.add_child")

#### Scenario: No alias matches
- **WHEN** a query does not match any alias rule
- **THEN** `expand_query_variants` SHALL return a single-element list containing only the original query

#### Scenario: Exact symbol query deduplication
- **WHEN** a query is already a symbol name (e.g., "Node.add_child")
- **THEN** `expand_query_variants` SHALL return a single-element list without duplicates

### Requirement: Query variants used for FTS recall only
The system SHALL use query variants only for FTS matching, not for vector search.

#### Scenario: FTS uses all variants
- **WHEN** `search_database` is called with a query that has aliases
- **THEN** FTS search SHALL run against all variants and merge results by best score per document ID

#### Scenario: Vector search uses original query only
- **WHEN** `search_database` is called with a query that has aliases
- **THEN** vector search SHALL use only the original query text
```

## openspec/changes/search-quality-optimization-loop/specs/search-quality-diagnostics/spec.md

- Source: openspec/changes/search-quality-optimization-loop/specs/search-quality-diagnostics/spec.md
- Lines: 1-27
- SHA256: 9aa66e98e15b7f84a5c0da122cb4643df50994218b243f3b3c17c2f0e20ab08f

```md
## ADDED Requirements

### Requirement: Failure diagnostics for evaluation queries
The system SHALL attach diagnostic metadata to failed evaluation queries when `diagnostic_limit` is specified.

#### Scenario: Diagnostics show expected target exists in DB
- **WHEN** a query fails but its expected paths/symbols exist in the database
- **THEN** `FailureDiagnostics.expected_present` SHALL be `True` and `expected_rows` SHALL contain the matching rows

#### Scenario: Diagnostics show best rank in window
- **WHEN** a query fails and `diagnostic_limit` is set
- **THEN** `FailureDiagnostics.best_rank` SHALL be the rank of the best matching result within the diagnostic window, or `None` if not found

#### Scenario: Diagnostics included in JSON output
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the JSON output SHALL include `failures[].diagnostics` with `expected_present`, `best_rank`, `best_rank_no_graph`, `expected_rows`, and `diagnostic_window` fields

#### Scenario: Diagnostics included in text report
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the text report SHALL include `diagnostics:` lines showing `expected_present`, `best_rank` values

### Requirement: Diagnostic limit is opt-in
The system SHALL only compute diagnostics when `diagnostic_limit` parameter is explicitly provided.

#### Scenario: Default evaluation skips diagnostics
- **WHEN** `evaluate_database` is called without `diagnostic_limit`
- **THEN** `QueryResult.diagnostics` SHALL be `None` for all results
```

## openspec/changes/search-quality-optimization-loop/specs/semantic-search-quality/spec.md

- Source: openspec/changes/search-quality-optimization-loop/specs/semantic-search-quality/spec.md
- Lines: 1-27
- SHA256: 9416bd2fcbe388ee0e6c8dc81ba05da387c0b854cad5f2d8c505be2537c6d6ab

```md
## MODIFIED Requirements

### Requirement: Packaged golden-query suite coverage
The packaged query suite SHALL contain at least 30 unique query IDs with at least 12 gating queries and at least 8 report-only queries, covering `class`, `symbol`, `tutorial`, `engine`, and `addon` categories.

#### Scenario: Query suite meets size and tier requirements
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the result SHALL contain >= 30 queries with >= 12 gating and >= 8 report-only

#### Scenario: Query suite covers all required categories
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the query categories SHALL include `class`, `symbol`, `tutorial`, `engine`, and `addon`

#### Scenario: Query suite includes normalization and graph tags
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one query SHALL have tag `normalization` and at least one SHALL have tag `graph`

### Requirement: CLI entry point is importable
The `godot-rag` project script SHALL point to `rag.cli:main` and the wheel SHALL include `rst2md/rag` package.

#### Scenario: pyproject.toml has correct script target
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[project.scripts]` SHALL contain `godot-rag = "rag.cli:main"`

#### Scenario: pyproject.toml includes rag package in wheel
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[tool.hatch.build.targets.wheel]` `packages` SHALL include `"rst2md/rag"`
```

