# Search Quality Optimization Loop Design

## Context

The search quality evaluation harness is in place, but the next bottleneck is the feedback loop around it.

Current observations from local evaluation:

- Packaged golden queries: 5 total, with 1 addon query marked `report_only`.
- `godot-rag eval-search` does not run from the installed script entry point in the current workspace; the working command is `PYTHONPATH=rst2md uv run python rst2md/rag/cli.py eval-search ...`.
- `godot_rag.db` currently reports `hit@5=0.000` and `mrr@5=0.000` for the 4 gating queries.
- Failure classes include `query_normalization`, `missing_recall`, and `low_ranking`.
- `Node.add_child` and `Timer.is_stopped` are present in the database but not retrieved by their natural-language golden queries; `Signal.emit` is not present as an exact chunk symbol in the checked database.

That means the next phase should not start with broad ranking tuning. It should first make evaluation repeatable, then turn each failed query into a diagnosable search-quality task.

## Goals

- Make the manual search-quality evaluation command runnable from the documented project entry point.
- Expand golden queries from the v1 smoke set into a meaningful categorized suite.
- Separate stable release gates from exploratory `report_only` queries.
- Add enough diagnostics to tell whether a failure is caused by ingestion, recall, ranking, filters, graph expansion, or query normalization.
- Fix the first observed failure families with small, testable search changes.

## Non-Goals

- No embedding model change.
- No new vector database or schema rewrite.
- No broad RRF weight search without query-level failure evidence.
- No requirement to run full release-database evaluation in default CI.

## Approach

### 1. Harden the Evaluation Entry Point

The expected command should be runnable without manually setting `PYTHONPATH`.

Implementation should align package metadata, module paths, and documented commands so `eval-search` works through the same CLI surface users already expect. The command should continue to support custom query files, baseline write/compare mode, JSON output, graph comparison, and threshold flags.

This is the first step because every later search change depends on a trusted verification path.

### 2. Expand and Tier Golden Queries

The current 5-query set is useful as a smoke test but too small to guide optimization.

Add a larger query file with roughly 30-50 entries across:

- class-symbol intent, such as methods, properties, and signals.
- tutorial intent, especially "how to" natural-language queries.
- engine/detail pages.
- addon docs and examples.
- query normalization cases, including dotted symbols, snake case, and natural-language aliases.
- graph expansion cases where related chunks should help or where expansion can add noise.

Each query should be either:

- `gating`: stable enough to affect pass/fail and baseline regression checks.
- `report_only`: useful for tracking but immature, corpus-sensitive, or addon-dependent.

The first expansion should favor stable expectations over breadth. A smaller high-confidence gating set is more useful than a large suite that needs constant baseline churn.

### 3. Add Failure Diagnostics

Evaluation output should explain where the expected target disappeared.

For each failed query, report:

- whether expected paths or symbols exist in the current database.
- the best rank found within an extended diagnostic window, such as top 50.
- whether the target appeared in lexical results, vector results, graph-expanded results, or none of them.
- whether filters excluded plausible matches.
- whether graph expansion changed pass/fail or displaced better direct matches.

These diagnostics should be available in JSON for tooling and summarized in text output for manual release review.

### 4. Fix the First Failure Families

Use the current failed queries as the first optimization slice:

- `query_normalization`: add a conservative natural-language alias or rewrite layer for high-confidence Godot API intents, for example mapping "attach node to scene tree" toward `Node.add_child`.
- `missing_recall`: distinguish missing index coverage from retrieval failure. If a symbol is absent from chunks, fix ingestion or symbol extraction; if present but not found, improve candidate generation.
- `low_ranking`: add intent-aware boosts only after diagnostics show the expected target is being retrieved but ranked too low. Tutorial-oriented wording should not be dominated by unrelated class chunks.

Each fix should include a focused fixture test and a full evaluation run against the local release database.

## Data Flow

1. `eval-search` loads categorized golden queries.
2. Search runs with graph expansion enabled, and optionally compares graph expansion disabled.
3. Evaluator computes `hit@1`, `hit@3`, `hit@5`, and `mrr@5`.
4. Diagnostics inspect database presence and extended retrieval windows for failures.
5. Baseline comparison gates only stable `gating` queries.
6. Search changes are accepted only when they improve or preserve the expanded evaluation suite.

## Verification

- Unit tests cover query loading, tier handling, baseline gating, and failure diagnostics.
- Search fixture tests cover representative normalization, recall, ranking, filter, and graph cases.
- Manual release-database verification runs:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --compare-graph
```

- A baseline refresh is explicit and reviewable:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --write-baseline
```

## Rollout

1. Fix the CLI entry point and documentation.
2. Add diagnostics without changing ranking behavior.
3. Expand query coverage and establish a reviewed baseline.
4. Implement the first query-normalization, recall, and ranking fixes.
5. Re-run evaluation and keep any still-immature cases as `report_only`.

## Risks

- A larger query set can overfit current corpus details. Mitigation: keep unstable expectations in `report_only`.
- Diagnostics can become noisy. Mitigation: emit concise summaries by default and detailed fields in JSON.
- Alias rewriting can create false positives. Mitigation: keep aliases conservative, versioned in tests, and avoid broad LLM-style rewrites.
- Baselines can hide poor absolute quality. Mitigation: always print absolute metrics even when regression gates pass.
