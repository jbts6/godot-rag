# rst-markdown-noise-cleanup Specification

## Purpose
TBD - created by archiving change cleanup-rst-extraction-noise. Update Purpose after archive.
## Requirements
### Requirement: Godot RST metadata is removed before Markdown output
The converter SHALL remove Godot class reference metadata fields that are not user-facing documentation content.

#### Scenario: github_url metadata is hidden
- **WHEN** an RST document begins with `:github_url: hide`
- **THEN** the generated Markdown MUST NOT contain `github_url` or `hide` header noise from that field

### Requirement: Sphinx tabbed code examples preserve code block structure
The converter SHALL transform supported Sphinx `.. tabs::` / `.. code-tab::` blocks into Markdown fenced code blocks through pandoc-readable RST preprocessing.

#### Scenario: multi-language tabs become fenced code blocks
- **WHEN** an RST document contains a `.. tabs::` block with `.. code-tab:: gdscript` and `.. code-tab:: csharp` children
- **THEN** the generated Markdown MUST contain separate fenced code blocks for `gdscript` and `csharp`

#### Scenario: code-tab display labels do not pollute language identifiers
- **WHEN** a `.. code-tab::` directive includes a display label such as `gdscript GDScript`, `csharp C#`, or `gdscript 3D GDScript`
- **THEN** the generated Markdown fence language MUST use only the first directive token

#### Scenario: nested code indentation is preserved
- **WHEN** a code-tab body contains nested indentation inside the example code
- **THEN** the generated Markdown code block MUST preserve the relative indentation of the code body

#### Scenario: tabs block does not consume following prose
- **WHEN** prose follows a `.. tabs::` block at the parent indentation level
- **THEN** the following prose MUST remain normal Markdown text outside the generated code blocks

### Requirement: Godot method qualifiers are concise
The Markdown cleaner SHALL replace verbose Godot substitution expansion boilerplate for method qualifiers with concise code spans.

#### Scenario: const boilerplate is shortened
- **WHEN** generated Markdown contains `` `const (This method has no side effects...)` `` boilerplate
- **THEN** the cleaned Markdown MUST contain `` `const` `` instead

#### Scenario: vararg boilerplate is shortened
- **WHEN** generated Markdown contains `` `vararg (This method accepts any number of arguments...)` `` boilerplate
- **THEN** the cleaned Markdown MUST contain `` `vararg` `` instead

### Requirement: Empty API section headings are removed
The Markdown cleaner SHALL remove Godot API section headings that become empty after table noise cleanup.

#### Scenario: empty API heading before another heading is removed
- **WHEN** a `## Properties`, `## Constructors`, `## Methods`, or `## Operators` heading is followed only by whitespace before another heading
- **THEN** that empty heading MUST be removed from the cleaned Markdown

#### Scenario: non-empty API heading is retained
- **WHEN** a supported API section heading contains body content before the next heading
- **THEN** that heading MUST remain in the cleaned Markdown

### Requirement: Escaped literal characters are cleaned only in non-code text
The Markdown cleaner SHALL unescape selected pandoc-escaped literal characters in normal text while preserving code content exactly.

#### Scenario: non-code hash and asterisk escapes are unescaped
- **WHEN** non-code Markdown text contains pandoc escapes for literal `#` or `*`
- **THEN** the cleaned Markdown MUST use the literal characters where doing so preserves intended prose

#### Scenario: fenced code content is not altered
- **WHEN** escaped `#` or `*` characters appear inside a fenced code block
- **THEN** the cleaned Markdown MUST preserve the code block content unchanged

#### Scenario: indented code content is not altered
- **WHEN** escaped `#` or `*` characters appear inside an indented code block
- **THEN** the cleaned Markdown MUST preserve the code line content unchanged

