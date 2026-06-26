"""RST conversion helpers used by the build pipeline and addon ingestion."""

from __future__ import annotations

import re
import shutil
import subprocess


WRAPPER_TAGS = (
    "div", "section", "span", "article", "aside",
    "nav", "header", "footer", "figure", "figcaption",
    "main", "details", "summary", "colgroup", "col",
    "thead", "tbody", "tfoot",
)

FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_indented_under(line: str, parent_indent: int) -> bool:
    return not line.strip() or _indent_width(line) > parent_indent


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
            # 如果没有更多内容，删除尾部空行
            if i >= len(lines):
                while out and not out[-1].strip():
                    out.pop()
            continue

        out.append(line)
        i += 1

    text = "\n".join(out)
    if keep_trailing_newline:
        text += "\n"
    return text


def _fallback_rst_to_md(rst_text: str) -> str:
    """Best-effort RST to Markdown conversion when pandoc is unavailable."""
    lines = rst_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        if line.strip() and re.fullmatch(r"[=\-~^`#*]{3,}", next_line.strip()):
            level = {"=": "#", "-": "##", "~": "###", "^": "####"}.get(next_line.strip()[0], "##")
            out.append(f"{level} {line.strip()}")
            i += 2
            continue
        if line.lstrip().startswith(".. "):
            # Skip directive header and its indented body
            i += 1
            while i < len(lines) and lines[i] and (lines[i][0] in " \t"):
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def convert_rst_to_md(rst_text: str, *, allow_fallback: bool = False) -> str:
    rst_text = _preprocess_rst(rst_text)
    if not shutil.which("pandoc"):
        if allow_fallback:
            return _fallback_rst_to_md(rst_text)
        raise RuntimeError("pandoc not found")

    result = subprocess.run(
        ["pandoc", "-f", "rst", "-t", "gfm", "--wrap=none"],
        input=rst_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        if allow_fallback:
            return _fallback_rst_to_md(rst_text)
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def clean_markdown_segment(text: str) -> str:
    """Clean generated Markdown outside fenced code blocks."""
    for tag in WRAPPER_TAGS:
        text = re.sub(rf"</?{tag}[^>]*>", "", text, flags=re.IGNORECASE)

    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    text = re.sub(r":ref:`([^<`]+)\s*<[^>]+>`", r"\1", text)
    text = re.sub(r":doc:`([^`]+)`", r"\1", text)
    text = re.sub(r":math:`([^`]+)`", r"$\1$", text)
    text = re.sub(r":(\w+):`([^`]+)`", r"`\2`", text)

    text = re.sub(r"\s*`🔗<[^`>]+>`", "", text)
    text = re.sub(r"`([^`\n<>]+)<[^`\n<>]+>`", r"`\1`", text)
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
    text = text.replace(r"\<", "<")
    text = text.replace(r"\#", "#")
    text = text.replace(r"\*", "*")

    text = re.sub(r"\.\.\s+(\w+)::", r"**\1:**", text)
    text = re.sub(r"^\.\.\s.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r":class:\s*\S+", "", text)

    text = re.sub(r"\[]$$[^)]*$$", "", text)

    text = re.sub(r"^-{4,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^={4,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*{4,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\^{4,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^~{4,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*classref[-\w]*\s*$", "", text, flags=re.MULTILINE)

    text = re.sub(r"^\s*[\|\-][\|\-:\s]*$", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^## (Properties|Constructors|Methods|Operators)\s*\n+(?=(## |\Z))",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines)


def clean_markdown(md: str) -> str:
    segments = []
    buffer = []
    in_code = False

    for line in md.splitlines(keepends=True):
        if FENCE_RE.match(line):
            if in_code:
                buffer.append(line)
                segments.append(("code", "".join(buffer)))
                buffer = []
                in_code = False
            else:
                if buffer:
                    segments.append(("text", "".join(buffer)))
                    buffer = []
                buffer.append(line)
                in_code = True
            continue

        if not in_code and (line.startswith("    ") or line.startswith("\t")):
            if buffer:
                segments.append(("text", "".join(buffer)))
                buffer = []
            segments.append(("code", line))
            continue

        buffer.append(line)

    if buffer:
        segments.append(("code" if in_code else "text", "".join(buffer)))

    text = "".join(
        segment if kind == "code" else clean_markdown_segment(segment)
        for kind, segment in segments
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)
