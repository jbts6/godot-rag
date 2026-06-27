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
