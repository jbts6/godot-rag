## MODIFIED Requirements

### Requirement: Internal responsibilities are localized behind focused RAG modules
The implementation SHALL separate indexing, search execution, relation building, addon discovery, and CLI search command orchestration so each responsibility can be tested or changed without editing unrelated responsibilities in place.

#### Scenario: Database indexing is localized
- **WHEN** database build behavior changes in the future
- **THEN** schema initialization, document insertion, addon insertion, symbol insertion, FTS sync, and embedding storage concerns MUST live behind an indexing-focused module interface rather than directly inside the public `rag.store` facade

#### Scenario: Search execution is localized
- **WHEN** search ranking, vector fallback, FTS fallback, result mapping, or snippet extraction behavior changes in the future
- **THEN** those concerns MUST live behind focused search sub-modules (retrieval, fusion, snippet) rather than directly inside a single search module or the public `rag.store` facade
- **AND** the public `search_database` and `search_database_with_metadata` interfaces MUST remain stable

#### Scenario: Addon discovery is localized
- **WHEN** addon documentation layout rules or file collection rules change in the future
- **THEN** those concerns MUST live behind an addon-discovery-focused module interface rather than inside addon chunk production code

#### Scenario: CLI search orchestration is localized
- **WHEN** shared search command behavior changes in the future
- **THEN** database validation, graph expansion option handling, debug metadata routing, and output formatting MUST be centralized instead of duplicated across each search subcommand
