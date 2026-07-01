## MODIFIED Requirements

### Requirement: Query plan signals feed symbol recall and ranking
Search SHALL use query-plan symbol candidates outside FTS-only recall.

#### Scenario: alias symbol participates in exact symbol lookup
- **WHEN** `search_database` receives "attach node to scene tree"
- **THEN** exact or suffix symbol lookup MUST evaluate the `Node.add_child` query-plan candidate

#### Scenario: alias symbol can influence deterministic reranking
- **WHEN** a result symbol matches a query-plan alias-derived symbol candidate
- **THEN** deterministic reranking MUST be able to promote that result ahead of lower-confidence lexical or vector-only matches

#### Scenario: dot-notation symbol is recalled via suffix match
- **WHEN** `search_database` receives a query whose symbol candidate is a method suffix of an indexed dot-notation symbol (e.g. query `add_child` against indexed `Node.add_child`)
- **THEN** suffix symbol lookup MUST match the indexed `Class.method` symbol
- **AND** the matched candidate MUST record a `symbol_recall.suffix` ranking signal
- **AND** symbol normalization MUST preserve the dot boundary so that the suffix LIKE pattern `%.{normalized}` can match

#### Scenario: dot-notation symbol normalization stays symmetric
- **WHEN** a dot-notation symbol is normalized at index time and at query time
- **THEN** both sides MUST produce the same normalized form with the dot preserved
- **AND** underscore stripping MUST still apply so that `add_child` and `addchild` share one normalized form
