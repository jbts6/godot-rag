## ADDED Requirements

### Requirement: Public RAG interfaces remain stable during module deepening
The system SHALL preserve existing public search, database build, addon chunking, and CLI behavior while internal RAG implementation responsibilities are moved behind deeper modules.

#### Scenario: Existing store imports continue to work
- **WHEN** callers import and use `build_database`, `search_database`, `search_database_with_metadata`, `get_stats`, or `list_addons` from `rag.store`
- **THEN** those imports MUST remain valid
- **AND** the observable behavior of those functions MUST remain compatible with the behavior before this change

#### Scenario: Existing search CLI commands keep their behavior
- **WHEN** a user invokes `godot-rag s`, `godot-rag search`, `godot-rag s-class`, `godot-rag s-tutorial`, `godot-rag s-engine`, or `godot-rag s-addon` with existing supported options
- **THEN** the command MUST accept the same arguments
- **AND** it MUST produce the same text or JSON output shape for equivalent database contents

#### Scenario: Addon chunking keeps existing output semantics
- **WHEN** addon documentation, examples, and public declarations are chunked through `chunk_addon`
- **THEN** the generated chunk paths, document types, chunk types, addon identifiers, symbols, headings, breadcrumbs, line spans, and text semantics MUST remain compatible with the behavior before this change

### Requirement: Internal responsibilities are localized behind focused RAG modules
The implementation SHALL separate indexing, search execution, relation building, addon discovery, and CLI search command orchestration so each responsibility can be tested or changed without editing unrelated responsibilities in place.

#### Scenario: Database indexing is localized
- **WHEN** database build behavior changes in the future
- **THEN** schema initialization, document insertion, addon insertion, symbol insertion, FTS sync, and embedding storage concerns MUST live behind an indexing-focused module interface rather than directly inside the public `rag.store` facade

#### Scenario: Search execution is localized
- **WHEN** search ranking, vector fallback, FTS fallback, result mapping, or graph expansion behavior changes in the future
- **THEN** those concerns MUST live behind a search-focused module interface rather than directly inside the public `rag.store` facade

#### Scenario: Addon discovery is localized
- **WHEN** addon documentation layout rules or file collection rules change in the future
- **THEN** those concerns MUST live behind an addon-discovery-focused module interface rather than inside addon chunk production code

#### Scenario: CLI search orchestration is localized
- **WHEN** shared search command behavior changes in the future
- **THEN** database validation, graph expansion option handling, debug metadata routing, and output formatting MUST be centralized instead of duplicated across each search subcommand
