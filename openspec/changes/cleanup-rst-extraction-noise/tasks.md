## 1. Tests

- [x] 1.1 Add preprocessing tests for `:github_url: hide` removal and `tabs` / `code-tab` conversion.
- [x] 1.2 Add code-tab label tests covering `gdscript GDScript`, `csharp C#`, and 2D/3D display label variants.
- [x] 1.3 Add indentation tests proving nested code body indentation survives conversion.
- [x] 1.4 Add Markdown cleanup tests for concise `const` / `vararg`, empty API headings, non-empty API headings, and escaped `#` / `*` boundaries.
- [x] 1.5 Add code protection tests proving fenced and indented code blocks are not altered by new cleanup rules.

## 2. RST Preprocessing

- [x] 2.1 Implement `_preprocess_rst(rst_text: str) -> str` in `rst2md/rag/rst.py`.
- [x] 2.2 Strip `:github_url: hide` metadata and its immediate trailing blank-line noise.
- [x] 2.3 Convert supported `.. tabs::` blocks into `.. code-block:: <language>` blocks with a line-oriented indentation scanner.
- [x] 2.4 Parse only the first `.. code-tab::` argument token as the code language and ignore display-label tokens.
- [x] 2.5 Call `_preprocess_rst()` from `convert_rst_to_md()` before pandoc conversion and keep fallback behavior consistent where practical.

## 3. Markdown Postprocessing

- [x] 3.1 Shorten verbose `const` and `vararg` substitution boilerplate in `clean_markdown_segment()`.
- [x] 3.2 Remove empty `Properties`, `Constructors`, `Methods`, and `Operators` headings after other cleanup.
- [x] 3.3 Unescape selected `\#` and `\*` sequences only in non-code Markdown segments.
- [x] 3.4 Preserve existing cross-reference, wrapper tag, anchor, and code-block cleanup behavior.

## 4. Mirror Sync

- [x] 4.1 Apply the same converter changes to `godot_rag/rag/rst.py`.
- [x] 4.2 Compare `rst2md/rag/rst.py` and `godot_rag/rag/rst.py` to confirm the mirrored implementation stays in sync.

## 5. Verification

- [x] 5.1 Run `pytest rst2md/tests/`.
- [x] 5.2 Reconvert representative Godot RST samples containing class metadata, `const`, empty sections, escaped literals, and `tabs` / `code-tab` blocks.
- [x] 5.3 Scan generated Markdown for residual `github_url`, verbose `const` / `vararg`, bare language-tag paragraphs, empty API headings, and unintended escaped literal patterns.
- [x] 5.4 Review sample diffs to confirm code blocks are fenced, code body structure is preserved, and following prose remains outside code blocks.
