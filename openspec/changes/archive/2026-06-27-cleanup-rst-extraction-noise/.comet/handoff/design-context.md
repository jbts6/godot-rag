# Comet Design Handoff

- Change: cleanup-rst-extraction-noise
- Phase: design
- Mode: compact
- Context hash: 833854ccc9e92cd6a572c749c8c7795547345aa2c0a1add0bc63719c4e1ab352

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/cleanup-rst-extraction-noise/proposal.md

- Source: openspec/changes/cleanup-rst-extraction-noise/proposal.md
- Lines: 1-29
- SHA256: 6b0d16c6aef0ea8de17775a2a1ef988999e8c21bceefd6965ca87504a1f9a031

```md
## Why

Godot RST documents currently convert to Markdown with repeated extraction noise that reduces readability and retrieval quality across the generated documentation corpus. The most damaging issue is that Sphinx `tabs` / `code-tab` examples are not understood by pandoc, causing language tags to leak into prose and multi-line examples to lose fenced code block structure.

## What Changes

- Add RST pre-processing before pandoc conversion to remove the Godot `:github_url: hide` metadata field.
- Add RST pre-processing that converts supported Sphinx `.. tabs::` / `.. code-tab::` blocks into pandoc-readable `.. code-block::` blocks while preserving code body structure.
- Normalize Godot method qualifiers in Markdown output so verbose `const` and `vararg` substitution descriptions become concise code spans.
- Remove empty API section headings produced by cleaned-out table noise.
- Unescape selected pandoc-escaped literal characters in non-code Markdown segments while preserving fenced and indented code content.
- Add focused tests for the preprocessing, postprocessing, and key boundary cases.

## Capabilities

### New Capabilities

- `rst-markdown-noise-cleanup`: Clean known Godot RST-to-Markdown conversion noise while preserving code examples and Markdown semantics.

### Modified Capabilities

- None.

## Impact

- Affected implementation files: `rst2md/rag/rst.py` and mirrored `godot_rag/rag/rst.py`.
- Affected tests: `rst2md/tests/test_rst2md_batch.py`.
- Affected outputs: Markdown generated from Godot RST documentation by `rst2md/rst2md_batch.py` and addon ingestion paths that call `convert_rst_to_md()` followed by `clean_markdown()`.
- No caller API changes, storage schema changes, or new runtime dependencies are expected.
```

## openspec/changes/cleanup-rst-extraction-noise/design.md

- Source: openspec/changes/cleanup-rst-extraction-noise/design.md
- Lines: 1-83
- SHA256: c77b2d30d835c07edcd1228791bfa9a867502790ef07d8fd96be379f2d039a13

[TRUNCATED]

```md
## Context

`rst2md/rag/rst.py` converts RST to Markdown with pandoc and then cleans generated Markdown with `clean_markdown()`. The current cleaner already separates text from fenced and indented code blocks before applying text cleanup, which is the right boundary for Markdown post-processing.

The remaining noise comes from two sources. Some Godot/Sphinx RST constructs are not understood by pandoc and should be normalized before conversion. Other artifacts are produced by pandoc output and should be cleaned only in non-code Markdown segments.

The implementation must keep `rst2md/rag/rst.py` and `godot_rag/rag/rst.py` in sync.

## Goals / Non-Goals

**Goals:**

- Remove the known `:github_url: hide`, verbose `const` / `vararg`, empty API heading, escaped `#` / `*`, and bare language tag noise patterns.
- Preserve multi-line code examples from Sphinx `tabs` / `code-tab` blocks as fenced code blocks.
- Keep code content protected from Markdown cleanup.
- Cover risky parsing and cleanup behavior with focused tests.

**Non-Goals:**

- No changes to callers such as `rst2md_batch.py`, `addon_docs.py`, or `store.py`.
- No new converter dependency or replacement for pandoc.
- No broad Markdown normalization beyond the listed Godot RST noise patterns.
- No storage/index schema changes.

## Decisions

### Preprocess RST before pandoc for unsupported Sphinx/Godot constructs

Add `_preprocess_rst(rst_text: str) -> str` and call it inside `convert_rst_to_md()` before invoking pandoc. This keeps caller behavior unchanged while ensuring both batch conversion and addon ingestion receive the same normalized input.

Alternative considered: clean the broken Markdown after pandoc. This is weaker for `tabs` / `code-tab` because pandoc has already lost code block structure by then.

### Implement tabs conversion with a line scanner

Use a line-oriented indentation scanner for `.. tabs::` blocks instead of a broad regular expression. The scanner should:

- Detect `.. tabs::` directive lines and collect only the indented child block.
- Detect child `.. code-tab::` directives within the tabs block.
- Parse the first directive argument token as the code language; ignore display-label tokens such as `GDScript`, `C#`, `2D`, or `3D`.
- Dedent each code body relative to the code-tab body indentation and re-indent it under `.. code-block:: <language>`.
- Stop the tabs block before following prose at the parent indentation level.

Alternative considered: direct regex replacement of `.. code-tab:: <lang>`. This is fragile because real Godot docs include optional labels and nested code indentation.

### Keep Markdown post-processing inside existing text/code segmentation

Extend `clean_markdown_segment()` for text-only cleanup:

- Replace verbose `const` and `vararg` code spans with concise code spans.
- Remove API section headings that are empty after table/noise cleanup.
- Unescape selected `\#` and `\*` sequences only in non-code segments.

The existing `clean_markdown()` segmentation remains the protection boundary for fenced and indented code blocks.

Alternative considered: global replacements over the full Markdown document. This would be simpler but risks changing examples and literal code.

### Validate with focused unit tests plus corpus spot checks

Add tests for `_preprocess_rst()` or `convert_rst_to_md()` behavior around `tabs` / `code-tab`, especially display labels and nested indentation. Add tests for post-processing boundary behavior in `clean_markdown()`.

Run the existing test suite for `rst2md/tests/`, then reconvert representative RST samples and scan for residual noise patterns.

## Risks / Trade-offs

- Tabs block parser misses an indentation edge case -> Mitigation: test with real Godot samples that include blank lines, display labels, and nested C# braces.
- Unescaping `\#` or `\*` changes Markdown semantics in rare prose positions -> Mitigation: keep replacement scoped to non-code segments and add tests for line-start and emphasis-adjacent cases before broadening behavior.
- Mirror file drifts from the primary implementation -> Mitigation: update both `rst2md/rag/rst.py` and `godot_rag/rag/rst.py` together and compare them during verification.
- Fallback conversion still skips directives when pandoc is unavailable -> Mitigation: `_preprocess_rst()` should run before both pandoc and fallback paths where practical, but full code-block fidelity remains a pandoc-path requirement.

## Migration Plan

1. Add focused tests for the new preprocessing and cleanup expectations.
2. Implement `_preprocess_rst()` and call it from `convert_rst_to_md()`.
3. Extend `clean_markdown_segment()` for the post-processing rules.
4. Mirror the implementation to `godot_rag/rag/rst.py`.
5. Run unit tests, reconvert representative Godot RST samples, and scan generated Markdown for the listed residual noise patterns.

Rollback is a normal code revert of the changed converter/test files; no data migration is required.

## Open Questions
```

Full source: openspec/changes/cleanup-rst-extraction-noise/design.md

## openspec/changes/cleanup-rst-extraction-noise/tasks.md

- Source: openspec/changes/cleanup-rst-extraction-noise/tasks.md
- Lines: 1-34
- SHA256: c37a0fdd189b3b982517f74c6d3a3ae7c6ff91cdd6359b3251f7090bfeb6b45c

```md
## 1. Tests

- [ ] 1.1 Add preprocessing tests for `:github_url: hide` removal and `tabs` / `code-tab` conversion.
- [ ] 1.2 Add code-tab label tests covering `gdscript GDScript`, `csharp C#`, and 2D/3D display label variants.
- [ ] 1.3 Add indentation tests proving nested code body indentation survives conversion.
- [ ] 1.4 Add Markdown cleanup tests for concise `const` / `vararg`, empty API headings, non-empty API headings, and escaped `#` / `*` boundaries.
- [ ] 1.5 Add code protection tests proving fenced and indented code blocks are not altered by new cleanup rules.

## 2. RST Preprocessing

- [ ] 2.1 Implement `_preprocess_rst(rst_text: str) -> str` in `rst2md/rag/rst.py`.
- [ ] 2.2 Strip `:github_url: hide` metadata and its immediate trailing blank-line noise.
- [ ] 2.3 Convert supported `.. tabs::` blocks into `.. code-block:: <language>` blocks with a line-oriented indentation scanner.
- [ ] 2.4 Parse only the first `.. code-tab::` argument token as the code language and ignore display-label tokens.
- [ ] 2.5 Call `_preprocess_rst()` from `convert_rst_to_md()` before pandoc conversion and keep fallback behavior consistent where practical.

## 3. Markdown Postprocessing

- [ ] 3.1 Shorten verbose `const` and `vararg` substitution boilerplate in `clean_markdown_segment()`.
- [ ] 3.2 Remove empty `Properties`, `Constructors`, `Methods`, and `Operators` headings after other cleanup.
- [ ] 3.3 Unescape selected `\#` and `\*` sequences only in non-code Markdown segments.
- [ ] 3.4 Preserve existing cross-reference, wrapper tag, anchor, and code-block cleanup behavior.

## 4. Mirror Sync

- [ ] 4.1 Apply the same converter changes to `godot_rag/rag/rst.py`.
- [ ] 4.2 Compare `rst2md/rag/rst.py` and `godot_rag/rag/rst.py` to confirm the mirrored implementation stays in sync.

## 5. Verification

- [ ] 5.1 Run `pytest rst2md/tests/`.
- [ ] 5.2 Reconvert representative Godot RST samples containing class metadata, `const`, empty sections, escaped literals, and `tabs` / `code-tab` blocks.
- [ ] 5.3 Scan generated Markdown for residual `github_url`, verbose `const` / `vararg`, bare language-tag paragraphs, empty API headings, and unintended escaped literal patterns.
- [ ] 5.4 Review sample diffs to confirm code blocks are fenced, code body structure is preserved, and following prose remains outside code blocks.
```

## openspec/changes/cleanup-rst-extraction-noise/specs/rst-markdown-noise-cleanup/spec.md

- Source: openspec/changes/cleanup-rst-extraction-noise/specs/rst-markdown-noise-cleanup/spec.md
- Lines: 1-64
- SHA256: 0cf6a056910d0255bc8d720691028477caf719e6183454f9434d2ed749ab1435

```md
## ADDED Requirements

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
```

