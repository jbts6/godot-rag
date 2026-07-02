## MODIFIED Requirements

### Requirement: Tutorial intent detection
The system SHALL detect tutorial intent from query patterns. The legacy fixed additive boost (`doc_type_boost` returning 0.05 for tutorial doc_type) SHALL be replaced by a floor-plus-multiplicative rerank boost applied in `_rerank_bonus`. The `doc_type_boost` function SHALL return 0.0 for all inputs (retained for backward compatibility with existing callers and tests) and the substantive tutorial weighting SHALL move to the rerank stage.

The boost SHALL use two tunable constants: `TUTORIAL_SCORE_FLOOR` (minimum pre-rerank score eligible for multiplicative treatment, default ≥ 3.0) and `TUTORIAL_BOOST_FACTOR` (multiplicative factor, default ≥ 5.0). Both SHALL be set to the smallest combination that lifts both `scene tree tutorial` and `how to use scene tree nodes` queries into rank ≤5 on the canonical baseline, with spec-fixed lower bounds.

The rerank bonus formula SHALL be `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`, yielding a reranked score of `result.score + max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`. When `result.score >= TUTORIAL_SCORE_FLOOR`, this reduces to `result.score * TUTORIAL_BOOST_FACTOR`. When `result.score < TUTORIAL_SCORE_FLOOR`, the floor lifts the effective base so that low-bm25 tutorial results can still overtake high-bm25 class results.

#### Scenario: How-to query triggers tutorial intent
- **WHEN** a query starts with "how to " or contains " tutorial", " guide", or "learn "
- **THEN** `_doc_type_intent` SHALL return "tutorial"
- **AND** `doc_type_boost` SHALL return 0.0 for all doc types (legacy function retained but neutralized)
- **AND** `_rerank_bonus` SHALL apply a floor-plus-multiplicative boost to tutorial doc_type results when no symbol candidates exist in the plan

#### Scenario: Symbol query does not trigger intent boost
- **WHEN** a query contains "." or "_" (symbol-like pattern)
- **THEN** `_doc_type_intent` SHALL return None
- **AND** `_rerank_bonus` SHALL NOT apply the tutorial boost to any result

#### Scenario: Tutorial boost is floored multiplicative on result score
- **WHEN** `_rerank_bonus` is called for a result whose `doc_type == "tutorial"` and the plan has tutorial intent and no symbol candidates
- **THEN** the bonus SHALL equal `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- **AND** the reranked score SHALL equal `result.score + max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- **AND** the bonus SHALL be recorded as a named ranking signal `rerank.doc_type_intent` with weight equal to the bonus amount

#### Scenario: Low tutorial score is floored before boost
- **WHEN** `_rerank_bonus` is called for a tutorial result whose `result.score < TUTORIAL_SCORE_FLOOR` (e.g., score=0.66, FLOOR=3.0, FACTOR=5.0)
- **THEN** the reranked score SHALL equal `result.score + TUTORIAL_SCORE_FLOOR * (TUTORIAL_BOOST_FACTOR - 1)` (e.g., 0.66 + 3*4 = 12.66)
- **AND** the reranked score MUST be able to overtake class-doc results with bm25-scaled scores up to `TUTORIAL_SCORE_FLOOR * (TUTORIAL_BOOST_FACTOR - 1)` (e.g., 12.0)

#### Scenario: High tutorial score is not overshooting
- **WHEN** `_rerank_bonus` is called for a tutorial result whose `result.score >= TUTORIAL_SCORE_FLOOR` (e.g., score=5.0, FLOOR=3.0, FACTOR=5.0)
- **THEN** the reranked score SHALL equal `result.score * TUTORIAL_BOOST_FACTOR` (e.g., 25.0)
- **AND** the reranked score MUST remain below the symbol exact-match score (100.0) so that symbol candidates, when present, are not suppressed

### Requirement: Deterministic reranking uses query-plan signals
Search SHALL apply deterministic reranking signals after candidate assembly and before returning final results. For tutorial intent, the reranking SHALL be floor-plus-multiplicative rather than purely additive so that tutorial results with low lexical scores can overtake class results with high bm25 scores when the user expresses tutorial intent.

#### Scenario: alias symbol match is promoted
- **WHEN** a candidate result symbol exactly matches a query-plan alias-derived symbol candidate
- **THEN** reranking MUST increase that candidate's final rank relative to candidates without symbol, path, heading, or intent matches

#### Scenario: tutorial intent floored-multiplicative promotes tutorial results
- **WHEN** a query expresses tutorial intent (e.g., "scene tree tutorial") and a candidate result has `doc_type == "tutorial"`
- **THEN** reranking MUST apply bonus `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)` (defaults FLOOR ≥ 3.0, FACTOR ≥ 5.0)
- **AND** the candidate MUST be able to overtake class-doc results whose bm25-scaled scores would otherwise dominate under additive-only boosting

#### Scenario: doc-type intent remains constrained
- **WHEN** a query expresses tutorial intent
- **THEN** reranking MUST prefer tutorial results without suppressing exact symbol matches for symbol-like queries

#### Scenario: addon intent can be represented without gating unstable data
- **WHEN** a query expresses addon intent
- **THEN** reranking MUST expose addon intent as a ranking signal
- **AND** evaluation MUST keep addon queries report-only unless expected addon rows exist in the canonical database

## ADDED Requirements

### Requirement: Inheritance intent detection
The system SHALL detect inheritance intent from query patterns and surface it on the query plan so that the searcher can apply targeted `inherits`-relation traversal. Inheritance intent SHALL be triggered by the keywords `inherits`, `subclass of`, `parent class`, and `derived from` (case-insensitive, whole-word/whole-phrase matching). The bare verb `extends` SHALL NOT trigger inheritance intent to avoid false positives on queries like "how to extend Node functionality".

#### Scenario: inherits keyword triggers inheritance intent
- **WHEN** a query contains the token "inherits" (case-insensitive) as a whole word (e.g., "Node inherits Object")
- **THEN** `_inheritance_intent` SHALL return True
- **AND** the query plan SHALL set `inheritance_intent = True`

#### Scenario: synonym phrases trigger inheritance intent
- **WHEN** a query contains any of the phrases "subclass of", "parent class", or "derived from" (case-insensitive)
- **THEN** `_inheritance_intent` SHALL return True
- **AND** the query plan SHALL set `inheritance_intent = True`

#### Scenario: bare verb extends does not trigger inheritance intent
- **WHEN** a query contains the word "extends" or "extend" but NOT in the `Class extends Class` form (e.g., "how to extend Node functionality")
- **THEN** `_inheritance_intent` SHALL return False
- **AND** the query plan SHALL set `inheritance_intent = False`

#### Scenario: non-inheritance query does not trigger
- **WHEN** a query does not contain any inheritance keyword (e.g., "Node connect", "tutorial scene tree")
- **THEN** `_inheritance_intent` SHALL return False
- **AND** the query plan SHALL set `inheritance_intent = False`

### Requirement: Inheritance relation traversal in search
When the query plan expresses inheritance intent, search SHALL traverse `inherits` relations from each class_summary chunk in the top-K candidate set and add parent class_summary chunks to the result set with a score boost higher than the generic graph-expansion weight.

#### Scenario: inheritance query recalls parent class_summary
- **WHEN** search is executed for a query with `plan.inheritance_intent == True`
- **AND** a `class_summary` chunk for the queried child class exists in the top-K candidates
- **AND** an `inherits` edge from that class_summary to a parent class_summary exists in `chunk_relations`
- **THEN** the parent class_summary chunk MUST be added to the result set
- **AND** its score MUST be at least `child_result.score * 0.7`
- **AND** the result MUST include a `graph.inherits` ranking signal with the relation metadata

#### Scenario: inheritance traversal is scoped to inherits relation
- **WHEN** inheritance intent traversal runs
- **THEN** the SQL query MUST filter `r.relation = 'inherits'` (not generic graph expansion)
- **AND** traversal MUST NOT pull `references`, `see_also`, or `parent` edges via this code path (those remain on the generic graph expansion path)

#### Scenario: no inherits edge does not crash
- **WHEN** inheritance intent is set but no `inherits` edge exists from any top-K class_summary
- **THEN** search SHALL return without adding inheritance-derived results
- **AND** no exception SHALL be raised
