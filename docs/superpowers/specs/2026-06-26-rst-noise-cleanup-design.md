---
comet_change: cleanup-rst-extraction-noise
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-27-cleanup-rst-extraction-noise
status: final
---

# RST Extraction Noise Cleanup

## Problem

`rst.py` converts Godot RST docs to Markdown via pandoc, then cleans with `clean_markdown()`. Six noise patterns remain across 1078 files:

| Noise | Count | Cause |
|---|---|---|
| `github_url\nhide` header | 1078 | RST field list `:github_url: hide` not understood by pandoc |
| `const (This method has no side effects...)` | 5452 | RST substitution `\|const\|` expands to verbose abbr |
| Empty section headers | 1360 | RST `.. table::` converted to `\|\|` by pandoc, then cleaned to nothing |
| `\#` escaped hashes | 629 | pandoc escaping `#` in non-code context |
| Bare `gdscript`/`csharp` lang tags | 719 | `.. tabs::` / `.. code-tab::` custom directives not understood by pandoc |
| `\*` escaped asterisks | 173 | pandoc escaping `*` in non-code context |

The code block issue is the most impactful: multi-line code gets flattened into a single paragraph, losing structure and fences.

## Approach

All changes in `rst.py`. Two phases: RST pre-processing (before pandoc) and MD post-processing (in `clean_markdown`).

No new files. No changes to callers (`rst2md_batch.py`, `addon_docs.py`, `store.py`).

## Phase 1: RST Pre-processing

New function `_preprocess_rst(rst_text: str) -> str`, called inside `convert_rst_to_md()` before passing to pandoc.

### 1a. Convert `.. tabs::` / `.. code-tab::` to `.. code-block::`

Pandoc understands `.. code-block:: lang` and produces fenced code blocks. The `.. tabs::` directive is a Sphinx extension pandoc doesn't know.

Input pattern:
```rst
.. tabs::

 .. code-tab:: gdscript

    var box = AABB(Vector3(5, 0, 5))
    var absolute = box.abs()

 .. code-tab:: csharp

    var box = new Aabb(new Vector3(5, 0, 5));
```

Output:
```rst
.. code-block:: gdscript

   var box = AABB(Vector3(5, 0, 5))
   var absolute = box.abs()

.. code-block:: csharp

   var box = new Aabb(new Vector3(5, 0, 5));
```

Algorithm:
1. Find `.. tabs::` lines
2. For each `.. code-tab:: <lang>` inside the tabs block (indented under `.. tabs::`)
3. Replace `.. tabs::` + all `.. code-tab::` children with `.. code-block:: <lang>` blocks
4. Preserve code body indentation (dedent by the code-tab indent level, re-indent to 3 spaces for `.. code-block::`)

### 1b. Strip `:github_url: hide`

Remove the line `:github_url: hide` and any trailing blank line. This is the first meaningful line in every Godot class RST file.

## Phase 2: MD Post-processing

Additions to `clean_markdown_segment()`.

### 2a. Simplify `const`/`vararg` boilerplate

```python
text = re.sub(
    r'`const \(This method has no side effects[^)]*\)`',
    '`const`',
    text,
)
text = re.sub(
    r'`vararg \(This method accepts any number of arguments[^)]*\)`',
    '`vararg`',
    text,
)
```

### 2b. Remove empty section headers

After all other cleaning, remove `## Properties`, `## Constructors`, `## Methods`, `## Operators` when followed immediately by another heading or end-of-text:

```python
text = re.sub(
    r'^## (Properties|Constructors|Methods|Operators)\s*\n+(?=(## |\Z))',
    '',
    text,
    flags=re.MULTILINE,
)
```

### 2c. Unescape `\#` and `\*` outside code fences

`clean_markdown()` already splits text/code segments. In the text segments, replace `\#` → `#` and `\*` → `*`. This is already partially done for `\<` (line 78); extend the same pattern.

## Files Modified

- `rst2md/rag/rst.py` — primary implementation
- `godot_rag/rag/rst.py` — mirror (keep in sync)
- `rst2md/tests/test_rst2md_batch.py` — update test expectations

## Verification

1. Run existing tests: `pytest rst2md/tests/`
2. Re-convert a sample RST file and diff against current output
3. Spot-check: code blocks should be fenced, `const` should be short, no `github_url` header
4. Scan all 1078 MD files for residual noise patterns (the Python scan script used during analysis)
