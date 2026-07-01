# query-rewrite Specification

## Purpose
TBD - created by archiving change search-quality-optimization-loop. Update Purpose after archive.
## Requirements
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

#### Scenario: dot-notation symbol is recalled via suffix match
- **WHEN** `search_database` receives a query whose symbol candidate is a method suffix of an indexed dot-notation symbol (e.g. query `add_child` against indexed `Node.add_child`)
- **THEN** suffix symbol lookup MUST match the indexed `Class.method` symbol
- **AND** the matched candidate MUST record a `symbol_recall.suffix` ranking signal
- **AND** symbol normalization MUST preserve the dot boundary so that the suffix LIKE pattern `%.{normalized}` can match

#### Scenario: dot-notation symbol normalization stays symmetric
- **WHEN** a dot-notation symbol is normalized at index time and at query time
- **THEN** both sides MUST produce the same normalized form with the dot preserved
- **AND** underscore stripping MUST still apply so that `add_child` and `addchild` share one normalized form

