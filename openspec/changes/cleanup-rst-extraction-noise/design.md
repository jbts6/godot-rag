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

- Should the residual noise scan become a committed test helper, or remain an ad hoc verification command for this change?
- Should fallback conversion attempt to preserve preprocessed code blocks, or is fallback still allowed to be best-effort text extraction only?
