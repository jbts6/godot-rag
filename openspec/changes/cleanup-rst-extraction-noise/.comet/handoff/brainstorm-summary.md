# Brainstorm Summary

- Change: cleanup-rst-extraction-noise
- Date: 2026-06-26

## 确认的事实与约束

- OpenSpec canonical capability is `rst-markdown-noise-cleanup`.
- Implementation scope is limited to `rst2md/rag/rst.py`, mirrored `godot_rag/rag/rst.py`, and focused tests in `rst2md/tests/test_rst2md_batch.py`.
- Callers such as `rst2md_batch.py`, `addon_docs.py`, and `store.py` stay unchanged.
- Current `clean_markdown()` already protects fenced and indented code blocks by splitting code and text segments before calling `clean_markdown_segment()`.
- `convert_rst_to_md()` currently sends raw RST directly to pandoc and falls back to `_fallback_rst_to_md()` only when allowed.
- The existing design draft at `docs/superpowers/specs/2026-06-26-rst-noise-cleanup-design.md` is the natural Design Doc candidate to refine rather than duplicating a second design file.

## 确认的技术方案

- Add a scoped `_preprocess_rst()` before pandoc, implemented with a line-oriented scanner for `.. tabs::` blocks.
- Convert supported `.. code-tab::` children into pandoc-readable `.. code-block:: <language>` blocks.
- Parse only the first `.. code-tab::` argument token as the language and ignore display-label tokens.
- Extend existing Markdown text-segment cleanup in `clean_markdown_segment()` for `const` / `vararg`, empty API headings, and selected escaped literals.
- Keep `clean_markdown()` as the code/text protection boundary.
- Keep fallback conversion best-effort; full fenced code block fidelity is only promised for the pandoc path.
- Keep residual corpus noise scanning as ad hoc verification, not a committed helper or automated test.

## 备选方案

- Repair broken Markdown after pandoc: rejected because code block structure is already lost for `tabs` / `code-tab`.
- Replace pandoc or use Sphinx/docutils parsing: rejected because it expands dependency and caller risk beyond this cleanup.

## 关键取舍与风险

- `code-tab` labels such as `gdscript GDScript`, `csharp C#`, and `gdscript 3D GDScript` must not become fence languages; only the first token should be used.
- Global Markdown replacement is risky; `\#` and `\*` cleanup must stay outside code blocks and needs boundary tests.
- Mirror drift is a real risk; verification should compare the two `rst.py` files after implementation.
- Residual corpus noise scanning is confirmed as an ad hoc verification command for this change, not a committed helper or automated test.
- Fallback conversion remains best-effort. `_preprocess_rst()` may run before fallback, but full fenced code block fidelity is only promised for the pandoc conversion path.

## 待确认问题

- None.

## 测试策略

- Add unit tests for `_preprocess_rst()` or `convert_rst_to_md()` covering metadata stripping, tabs conversion, code-tab labels, nested indentation, and following prose.
- Add unit tests for `clean_markdown()` covering concise qualifiers, empty and non-empty API headings, non-code escaped literals, and fenced/indented code preservation.
- Run `pytest rst2md/tests/`.
- Reconvert representative real Godot RST samples and run ad hoc residual-noise scans.
- Compare `rst2md/rag/rst.py` and `godot_rag/rag/rst.py` after implementation.

## Spec Patch

- None currently required. Existing OpenSpec scenarios already cover the confirmed boundaries.
