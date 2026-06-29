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
