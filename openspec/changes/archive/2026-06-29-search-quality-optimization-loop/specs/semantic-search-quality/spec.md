## MODIFIED Requirements

### Requirement: Search quality is evaluated with categorized golden queries
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

## ADDED Requirements

### Requirement: CLI entry point is importable
The `godot-rag` project script SHALL point to `rag.cli:main` and the wheel SHALL include `rst2md/rag` package.

#### Scenario: pyproject.toml has correct script target
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[project.scripts]` SHALL contain `godot-rag = "rag.cli:main"`

#### Scenario: pyproject.toml includes rag package in wheel
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[tool.hatch.build.targets.wheel]` `packages` SHALL include `"rst2md/rag"`
