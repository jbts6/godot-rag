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
            i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def convert_rst_to_md(rst_text: str, *, allow_fallback: bool = False) -> str:
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
    text = text.replace(r"\<", "<")

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
