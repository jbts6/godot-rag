## MODIFIED Requirements

### Requirement: Inheritance relation traversal in search

When the query plan expresses inheritance intent, search SHALL first ensure that the relevant `class_summary` chunks are present in the candidate set — the query's named classes SHALL be recalled even when their FTS/vector score falls below the default top-K threshold — and SHALL then traverse `inherits` relations from each `class_summary` chunk in the candidate set, adding parent `class_summary` chunks to the result set with a score boost higher than the generic graph-expansion weight.

The recall precondition exists because the directed `inherits` traversal can only fire on source chunks already in the candidate set. Without the precondition, the traversal is vacuously satisfied (no source chunks → no traversal) and the feature delivers no value for inheritance queries whose target `class_summary` is not in the default top-K — which is the observed production gap for `Node inherits Object` (Node `class_summary` absent from top-K → `inherits` traversal never fires → Object `class_summary` never recalled → `rank=None`).

#### Scenario: inheritance query recalls target class_summary into candidate set

- **WHEN** the query "Node inherits Object" is searched with inheritance intent
- **AND** the Node `class_summary` chunk's default FTS/vector score falls below the top-K threshold
- **THEN** the search SHALL still include the Node `class_summary` chunk in the candidate set passed to `inherits` traversal
- **AND** this recall SHALL be scoped to inheritance-intent queries (non-inheritance queries MUST NOT receive this boost)

#### Scenario: inheritance query recalls parent class_summary

- **WHEN** the query "Node inherits Object" is searched with inheritance intent
- **AND** the Node `class_summary` chunk is in the candidate set (per the recall precondition above)
- **THEN** the result set SHALL include the Object `class_summary` chunk
- **AND** the Object chunk SHALL carry a `graph.inherits` ranking signal

#### Scenario: inheritance traversal is scoped to inherits relation

- **WHEN** inheritance intent traversal runs
- **THEN** the SQL query MUST filter `r.relation = 'inherits'` (not generic graph expansion)
- **AND** traversal MUST NOT pull `references`, `see_also`, or `parent` edges via this code path (those remain on the generic graph expansion path)

#### Scenario: no inherits edge does not crash

- **WHEN** inheritance intent is detected but no `inherits` edge exists in the relations table
- **THEN** traversal SHALL return no additional chunks
- **AND** the search SHALL NOT raise an error
