## MODIFIED Requirements

### Requirement: Conservative query alias expansion
The system SHALL expand natural-language queries into structured query-plan variants that include the original query plus any matching symbol aliases. For dot-notation symbol queries (`Class.method` or `Class.method()`), the system SHALL additionally append a method-suffix variant (the substring after the last `.` with trailing `()` stripped) so that suffix symbol recall can match inherited methods on ancestor classes.

The method-suffix variant SHALL only be appended when the segment before the `.` starts with an uppercase letter (class-like) and the segment after the `.` starts with a lowercase letter or underscore (method-like). This prevents over-splitting on non-symbol queries that happen to contain a dot.

#### Scenario: Known alias pattern matches
- **WHEN** a query contains tokens matching an alias rule (e.g., "attach node to scene tree")
- **THEN** `expand_query_variants` SHALL return the original query followed by the matching symbol alias (e.g., "Node.add_child")
- **AND** the query plan SHALL expose the matching symbol alias as a symbol candidate

#### Scenario: No alias matches
- **WHEN** a query does not match any alias rule
- **THEN** `expand_query_variants` SHALL return a single-element list containing only the original query
- **AND** the query plan SHALL expose no alias-derived symbol candidate

#### Scenario: Dot-notation symbol query produces method-suffix variant
- **WHEN** a query is a dot-notation symbol form matching `^[A-Z][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\(?\s*$` (e.g., "Node.connect", "ResourceLoader.load()")
- **THEN** `expand_query_variants` SHALL return the original query followed by the method-suffix variant (e.g., "Node.connect" → ["Node.connect", "connect"]; "ResourceLoader.load()" → ["ResourceLoader.load()", "load"])
- **AND** the query plan SHALL expose both the full dot-notation form and the method-suffix form as symbol candidates

#### Scenario: Non-symbol dot query is not split
- **WHEN** a query contains a dot but does not match the Class.method pattern (e.g., "scene_tree.tutorial" where the prefix is not uppercase, or "v2.1" where the suffix is numeric)
- **THEN** `expand_query_variants` SHALL NOT append a method-suffix variant
- **AND** the query plan SHALL expose only the original query

### Requirement: Query plan exposes structured search intent
The system SHALL build a structured query plan for each search query before recall and ranking. For dot-notation symbol queries, the query plan SHALL expose both the full dot-notation form and the method-suffix form so that exact and suffix symbol lookup can each evaluate both candidates.

#### Scenario: alias query creates symbol candidates
- **WHEN** a query contains tokens matching an alias rule such as "attach node to scene tree"
- **THEN** the query plan MUST include the original query
- **AND** it MUST include `Node.add_child` as an alias-derived symbol candidate

#### Scenario: exact dot-notation symbol query produces full and suffix candidates
- **WHEN** a query is a dot-notation symbol such as "Node.connect"
- **THEN** the query plan MUST include the original query
- **AND** it MUST include `Node.connect` as a symbol candidate (for exact symbol lookup)
- **AND** it MUST include `connect` as a symbol candidate (for suffix symbol lookup against inherited methods like `Object.connect`)

#### Scenario: unknown query keeps original text
- **WHEN** a query does not match any alias or symbol rule
- **THEN** the query plan MUST preserve the original query text
- **AND** it MUST expose no alias-derived symbol candidates
