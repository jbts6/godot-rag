---
change: cleanup-rst-extraction-noise
design-doc: docs/superpowers/specs/2026-06-26-rst-noise-cleanup-design.md
base-ref: 1e42e4dab6e2589058b3f89265a48858c8009cdd
---

# RST Noise Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理 Godot RST 转 Markdown 时遗留的 metadata、tabs/code-tab、verbose qualifier、空 API 标题和非代码转义噪音。

**Architecture:** 在 pandoc 前增加 `_preprocess_rst()`，只处理 pandoc 不理解的 RST 输入；在现有 `clean_markdown()` 文本/代码分段边界内扩展 Markdown 清理，保证 fenced 和 indented code 不被新规则改写。`rst2md/rag/rst.py` 是主实现，`godot_rag/rag/rst.py` 保持镜像一致。

**Tech Stack:** Python 3、stdlib `re` / `subprocess`、pandoc、`unittest`/`pytest`。

## Global Constraints

- 不新增转换依赖，不替换 pandoc。
- 不修改 `rst2md_batch.py`、`addon_docs.py`、`store.py` 等调用方行为。
- 新清理规则只覆盖设计文档列出的 Godot RST 噪音模式。
- Markdown 后处理必须继续保护 fenced code block 和 indented code block。
- `rst2md/rag/rst.py` 与 `godot_rag/rag/rst.py` 的 converter 实现必须保持同步。

---

### Task 1: 添加 RST 预处理失败测试

**Files:**
- Modify: `rst2md/tests/test_rst2md_batch.py`

**Interfaces:**
- Consumes: `rst2md_batch.clean_markdown`
- Produces: 对 `rag.rst._preprocess_rst(rst_text: str) -> str` 的测试约束

- [ ] **Step 1: 写入失败测试**

在 `rst2md/tests/test_rst2md_batch.py` 顶部导入 `_preprocess_rst`：

```python
from rag.rst import _preprocess_rst
```

新增测试类：

```python
class PreprocessRstTests(unittest.TestCase):
    def test_removes_github_url_hide_and_trailing_blank_line(self):
        rst = ":github_url: hide\n\nTitle\n=====\n"

        self.assertEqual(_preprocess_rst(rst), "Title\n=====\n")

    def test_converts_tabs_and_code_tab_blocks_to_code_blocks(self):
        rst = (
            ".. tabs::\n"
            "\n"
            " .. code-tab:: gdscript GDScript\n"
            "\n"
            "    var box = AABB(Vector3(5, 0, 5))\n"
            "    var absolute = box.abs()\n"
            "\n"
            " .. code-tab:: csharp C#\n"
            "\n"
            "    var box = new Aabb(new Vector3(5, 0, 5));\n"
            "\n"
            "Following prose.\n"
        )

        self.assertEqual(
            _preprocess_rst(rst),
            ".. code-block:: gdscript\n"
            "\n"
            "   var box = AABB(Vector3(5, 0, 5))\n"
            "   var absolute = box.abs()\n"
            "\n"
            ".. code-block:: csharp\n"
            "\n"
            "   var box = new Aabb(new Vector3(5, 0, 5));\n"
            "\n"
            "Following prose.\n",
        )

    def test_code_tab_uses_first_argument_token_as_language(self):
        rst = (
            ".. tabs::\n"
            "\n"
            " .. code-tab:: gdscript 3D GDScript\n"
            "\n"
            "    print(\"3D\")\n"
        )

        self.assertIn(".. code-block:: gdscript", _preprocess_rst(rst))
        self.assertNotIn("3D GDScript", _preprocess_rst(rst))

    def test_preserves_nested_code_body_indentation(self):
        rst = (
            ".. tabs::\n"
            "\n"
            " .. code-tab:: gdscript\n"
            "\n"
            "    if visible:\n"
            "        print(\"shown\")\n"
        )

        self.assertEqual(
            _preprocess_rst(rst),
            ".. code-block:: gdscript\n"
            "\n"
            "   if visible:\n"
            "       print(\"shown\")\n",
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest rst2md/tests/test_rst2md_batch.py -q`

Expected: FAIL，原因是 `rag.rst` 尚未导出 `_preprocess_rst` 或 tabs 转换尚未实现。

### Task 2: 实现 RST 预处理并接入转换入口

**Files:**
- Modify: `rst2md/rag/rst.py`

**Interfaces:**
- Produces: `_preprocess_rst(rst_text: str) -> str`
- Updates: `convert_rst_to_md(rst_text: str, *, allow_fallback: bool = False) -> str`

- [ ] **Step 1: 添加缩进辅助函数和 tabs scanner**

在 `FENCE_RE` 后添加：

```python
def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_indented_under(line: str, parent_indent: int) -> bool:
    return not line.strip() or _indent_width(line) > parent_indent
```

添加 `_convert_tabs_block()`：

```python
def _convert_tabs_block(lines: list[str], start: int) -> tuple[list[str], int]:
    tabs_indent = _indent_width(lines[start])
    i = start + 1
    block: list[str] = []

    while i < len(lines) and _is_indented_under(lines[i], tabs_indent):
        block.append(lines[i])
        i += 1

    converted: list[str] = []
    j = 0
    while j < len(block):
        line = block[j]
        stripped = line.strip()
        if not stripped.startswith(".. code-tab::"):
            j += 1
            continue

        directive_indent = _indent_width(line)
        args = stripped.removeprefix(".. code-tab::").strip().split()
        language = args[0] if args else "text"

        body: list[str] = []
        j += 1
        while j < len(block):
            candidate = block[j]
            candidate_stripped = candidate.strip()
            if (
                candidate_stripped.startswith(".. code-tab::")
                and _indent_width(candidate) <= directive_indent
            ):
                break
            body.append(candidate)
            j += 1

        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()

        body_indent = min((_indent_width(item) for item in body if item.strip()), default=directive_indent + 1)
        converted.append(f"{' ' * tabs_indent}.. code-block:: {language}")
        converted.append("")
        for body_line in body:
            if body_line.strip():
                converted.append(" " * (tabs_indent + 3) + body_line[body_indent:])
            else:
                converted.append("")
        converted.append("")

    while converted and not converted[-1].strip():
        converted.pop()
    if converted:
        converted.append("")
    return converted, i
```

- [ ] **Step 2: 添加 `_preprocess_rst()`**

```python
def _preprocess_rst(rst_text: str) -> str:
    lines = rst_text.splitlines()
    keep_trailing_newline = rst_text.endswith("\n")
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.strip() == ":github_url: hide":
            i += 1
            if i < len(lines) and not lines[i].strip():
                i += 1
            continue

        if line.strip() == ".. tabs::":
            converted, i = _convert_tabs_block(lines, i)
            out.extend(converted)
            continue

        out.append(line)
        i += 1

    text = "\n".join(out)
    if keep_trailing_newline:
        text += "\n"
    return text
```

- [ ] **Step 3: 在 `convert_rst_to_md()` 开头调用预处理**

```python
def convert_rst_to_md(rst_text: str, *, allow_fallback: bool = False) -> str:
    rst_text = _preprocess_rst(rst_text)
    ...
```

Fallback 分支继续使用同一个预处理后的 `rst_text`。

- [ ] **Step 4: 运行 Task 1 测试确认通过**

Run: `pytest rst2md/tests/test_rst2md_batch.py -q`

Expected: PASS。

### Task 3: 添加 Markdown 清理失败测试

**Files:**
- Modify: `rst2md/tests/test_rst2md_batch.py`

**Interfaces:**
- Consumes: `rst2md_batch.clean_markdown`
- Produces: 对 `clean_markdown_segment()` 新清理规则的测试约束

- [ ] **Step 1: 添加 qualifier、空标题、非代码转义测试**

在 `CleanMarkdownTests` 内新增：

```python
    def test_simplifies_const_and_vararg_boilerplate(self):
        markdown = (
            "`const (This method has no side effects. It doesn't modify any of the instance's member variables.)` "
            "`vararg (This method accepts any number of arguments after the ones described here.)`"
        )

        self.assertEqual(clean_markdown(markdown), "`const` `vararg`")

    def test_removes_empty_api_headings_but_keeps_non_empty_headings(self):
        markdown = (
            "## Properties\n"
            "\n"
            "## Methods\n"
            "\n"
            "`void` **do_it**()\n"
            "\n"
            "## Operators\n"
        )

        self.assertEqual(clean_markdown(markdown), "## Methods\n\n`void` **do_it**()")

    def test_unescapes_hash_and_asterisk_outside_code(self):
        markdown = "Use \\# for color names and \\* for wildcard prose."

        self.assertEqual(clean_markdown(markdown), "Use # for color names and * for wildcard prose.")

    def test_does_not_unescape_hash_or_asterisk_inside_code_blocks(self):
        markdown = (
            "```gdscript\n"
            "var color = \"\\#fff\"\n"
            "var glob = \"\\*\"\n"
            "```\n"
            "\n"
            "Outside \\# and \\*."
        )

        self.assertEqual(
            clean_markdown(markdown),
            "```gdscript\n"
            "var color = \"\\#fff\"\n"
            "var glob = \"\\*\"\n"
            "```\n"
            "\n"
            "Outside # and *.",
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest rst2md/tests/test_rst2md_batch.py -q`

Expected: FAIL，原因是新 Markdown 清理规则尚未实现。

### Task 4: 实现 Markdown 后处理规则

**Files:**
- Modify: `rst2md/rag/rst.py`

**Interfaces:**
- Updates: `clean_markdown_segment(text: str) -> str`

- [ ] **Step 1: 添加 concise qualifier 替换**

在 cross-reference cleanup 后、directive cleanup 前加入：

```python
    text = re.sub(
        r"`const \(This method has no side effects[^`]*\)`",
        "`const`",
        text,
    )
    text = re.sub(
        r"`vararg \(This method accepts any number of arguments[^`]*\)`",
        "`vararg`",
        text,
    )
```

- [ ] **Step 2: 扩展非代码文本转义清理**

把现有 `text = text.replace(r"\<", "<")` 扩展为：

```python
    text = text.replace(r"\<", "<")
    text = text.replace(r"\#", "#")
    text = text.replace(r"\*", "*")
```

- [ ] **Step 3: 移除空 API heading**

在 `text = re.sub(r"\n{3,}", "\n\n", text)` 前加入：

```python
    text = re.sub(
        r"^## (Properties|Constructors|Methods|Operators)\s*\n+(?=(## |\Z))",
        "",
        text,
        flags=re.MULTILINE,
    )
```

- [ ] **Step 4: 运行 Markdown 清理测试确认通过**

Run: `pytest rst2md/tests/test_rst2md_batch.py -q`

Expected: PASS。

### Task 5: 镜像同步 converter 实现

**Files:**
- Modify: `godot_rag/rag/rst.py`

**Interfaces:**
- Consumes: `rst2md/rag/rst.py` 的 converter implementation
- Produces: 同步后的 `godot_rag/rag/rst.py`

- [ ] **Step 1: 将主实现同步到镜像文件**

将 `rst2md/rag/rst.py` 的内容复制到 `godot_rag/rag/rst.py`，保持两个文件一致。

- [ ] **Step 2: 比较两个文件**

Run: `cmp -s rst2md/rag/rst.py godot_rag/rag/rst.py`

Expected: exit code 0。

- [ ] **Step 3: 运行测试**

Run: `pytest rst2md/tests/test_rst2md_batch.py -q`

Expected: PASS。

### Task 6: 代表性转换与残留噪音扫描

**Files:**
- No code changes expected

**Interfaces:**
- Consumes: `convert_rst_to_md()`、`clean_markdown()`
- Produces: 验证证据

- [ ] **Step 1: 运行完整 rst2md 测试目录**

Run: `pytest rst2md/tests/ -q`

Expected: PASS。

- [ ] **Step 2: 运行代表性内联转换 spot check**

Run:

```bash
python - <<'PY'
from rag.rst import clean_markdown, convert_rst_to_md

rst = """:github_url: hide

Title
=====

.. tabs::

 .. code-tab:: gdscript GDScript

    if visible:
        print("# *")

After \\|const\\| and \\|vararg\\|.
"""

md = clean_markdown(convert_rst_to_md(rst, allow_fallback=True))
print(md)
assert "github_url" not in md
assert "``` gdscript" in md or "```gdscript" in md
assert "if visible:" in md
PY
```

Expected: command exits 0。

- [ ] **Step 3: 扫描测试转换输出中的残留模式**

如果有临时输出目录，扫描以下模式：

```bash
rg -n "github_url|const \\(This method has no side effects|vararg \\(This method accepts any number of arguments|^gdscript$|^csharp$|\\\\#|\\\\\\*" <output-dir>
```

Expected: 没有来自本 change 覆盖模式的残留命中；若扫描对象包含代码块，需人工确认代码内命中不属于清理目标。

- [ ] **Step 4: 更新 OpenSpec tasks.md**

把 `openspec/changes/cleanup-rst-extraction-noise/tasks.md` 中已完成项勾选为 `- [x]`，并在需要时记录验证命令。
