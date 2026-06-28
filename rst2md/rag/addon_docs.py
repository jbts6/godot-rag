"""Discover and chunk addon documentation, examples, and public API summaries."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from rag.addon_discovery import (
    _CODE_EXTENSIONS,
    AddonLayout,
    collect_api_files,
    collect_doc_files,
    collect_example_files,
    discover_addon,
)
from rag.models import Chunk

_CSHARP_TYPE_RE = re.compile(
    r"^\s*(?:public|protected|internal)?\s*"
    r"(?:(?:static|abstract|sealed|partial)\s+)*"
    r"(?:class|interface|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)
_CSHARP_MEMBER_RE = re.compile(
    r"^\s*public\s+(?:(?:static|override|virtual|async|partial|new)\s+)*"
    r"[\w<>\[\],?.]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|\{)"
)
_GDSCRIPT_CLASS_NAME_RE = re.compile(r"^\s*class_name\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_GDSCRIPT_FUNC_RE = re.compile(
    r"^\s*(?:@(?:onready|export)\s+)?(?:static\s+)?func\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)
_GDSCRIPT_SIGNAL_RE = re.compile(r"^\s*signal\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_GDSCRIPT_ENUM_RE = re.compile(r"^\s*enum\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_GDSCRIPT_CONST_RE = re.compile(r"^\s*const\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_GDSCRIPT_VAR_RE = re.compile(
    r"^\s*(?:@(?:onready|export)\s+)?var\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)


def chunk_addon_markdown(addon_name: str, display_name: str, rel_path: str, markdown: str) -> List[Chunk]:
    """Chunk an addon markdown doc by headings. Returns addon_doc chunks."""
    from rag.chunker import _find_headings, HEADING_RE

    lines = markdown.split("\n")
    headings = _find_headings(lines)
    chunks = []

    breadcrumb_prefix = f"addons > {display_name}"

    if not headings:
        text = "\n".join(lines).strip()
        if text:
            doc_name = Path(rel_path).stem
            chunks.append(Chunk(
                path=rel_path,
                doc_type="addon",
                chunk_type="addon_doc",
                addon=addon_name,
                addon_name=display_name,
                symbol="",
                heading=doc_name,
                breadcrumb=f"{breadcrumb_prefix} > {doc_name}",
                start_line=1,
                end_line=len(lines),
                text=text,
            ))
        return chunks

    for i, (line_idx, level, title) in enumerate(headings):
        end_line = headings[i + 1][0] if i + 1 < len(headings) else len(lines)
        section_lines = lines[line_idx:end_line]
        section_text = "\n".join(section_lines).strip()
        if not section_text:
            continue

        doc_name = Path(rel_path).stem
        chunks.append(Chunk(
            path=rel_path,
            doc_type="addon",
            chunk_type="addon_doc",
            addon=addon_name,
            addon_name=display_name,
            symbol="",
            heading=title,
            breadcrumb=f"{breadcrumb_prefix} > {doc_name} > {title}",
            start_line=line_idx + 1,
            end_line=end_line,
            text=section_text,
        ))

    return chunks


def chunk_code_file(addon_name: str, display_name: str, rel_path: str, code: str) -> List[Chunk]:
    """Chunk a code file (.gd/.cs) as a single addon_example chunk."""
    lines = code.split("\n")
    if not code.strip():
        return []

    filename = Path(rel_path).name
    return [Chunk(
        path=rel_path,
        doc_type="addon",
        chunk_type="addon_example",
        addon=addon_name,
        addon_name=display_name,
        symbol=rel_path,
        heading=filename,
        breadcrumb=f"addons > {display_name} > {rel_path}",
        start_line=1,
        end_line=len(lines),
        text=code,
    )]


def _doc_comment_start(lines: List[str], index: int) -> int:
    start = index
    while start > 0:
        prev = lines[start - 1].strip()
        if prev.startswith("///") or prev.startswith("##") or prev.startswith("["):
            start -= 1
            continue
        break
    return start


def _extract_api_lines(code: str, suffix: str, fallback_symbol: str = "") -> tuple[str, List[str], List[str]]:
    lines = code.split("\n")
    selected: List[tuple[int, str]] = []
    primary_symbol = ""
    aliases: List[str] = []

    for idx, line in enumerate(lines):
        if suffix == ".cs":
            match = _CSHARP_TYPE_RE.match(line) or _CSHARP_MEMBER_RE.match(line)
            if not match:
                continue
            symbol = match.group(1)
            primary_symbol = primary_symbol or symbol
            aliases.append(symbol)
        elif suffix == ".gd":
            class_name_match = _GDSCRIPT_CLASS_NAME_RE.match(line)
            match = (
                class_name_match
                or _GDSCRIPT_FUNC_RE.match(line)
                or _GDSCRIPT_SIGNAL_RE.match(line)
                or _GDSCRIPT_ENUM_RE.match(line)
                or _GDSCRIPT_CONST_RE.match(line)
                or _GDSCRIPT_VAR_RE.match(line)
            )
            if not match:
                continue
            symbol = match.group(1)
            if symbol.startswith("_"):
                continue
            if class_name_match:
                primary_symbol = symbol
            elif not primary_symbol:
                primary_symbol = fallback_symbol
            aliases.append(symbol)
            owner = primary_symbol or fallback_symbol
            if owner and symbol != owner:
                aliases.append(f"{owner}.{symbol}")
        else:
            continue

        start = _doc_comment_start(lines, idx)
        for line_idx in range(start, idx + 1):
            selected.append((line_idx + 1, lines[line_idx].rstrip()))

    deduped = []
    seen = set()
    for line_no, text in selected:
        key = (line_no, text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f"{line_no}: {text}")

    deduped_aliases = []
    seen_aliases = set()
    for alias in aliases:
        if not alias or alias in seen_aliases:
            continue
        seen_aliases.add(alias)
        deduped_aliases.append(alias)

    return primary_symbol or fallback_symbol, deduped_aliases, deduped


def chunk_api_file(addon_name: str, display_name: str, rel_path: str, code: str) -> List[Chunk]:
    """Chunk public declarations from implementation code without indexing bodies."""
    symbol, aliases, api_lines = _extract_api_lines(code, Path(rel_path).suffix, Path(rel_path).stem)
    if not api_lines:
        return []

    filename = Path(rel_path).name
    text = "\n".join(api_lines)
    return [Chunk(
        path=rel_path,
        doc_type="addon",
        chunk_type="addon_api",
        addon=addon_name,
        addon_name=display_name,
        symbol=symbol or rel_path,
        heading=filename,
        breadcrumb=f"addons > {display_name} > API > {rel_path}",
        start_line=1,
        end_line=len(code.split("\n")),
        text=text,
        symbols=aliases,
    )]


def _read_doc_as_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() != ".rst":
        return text

    from rag.rst import clean_markdown, convert_rst_to_md

    return clean_markdown(convert_rst_to_md(text, allow_fallback=True))


def chunk_addon(addon_dir: Path) -> List[Chunk]:
    """Discover and chunk all docs and examples for a single addon."""
    layout = discover_addon(addon_dir)
    addon_name = layout.name
    display_name = layout.display_name
    chunks = []

    # Process documentation
    for md_file in collect_doc_files(layout):
        rel_path = str(md_file.relative_to(addon_dir))
        try:
            markdown = _read_doc_as_markdown(md_file)
        except (UnicodeDecodeError, OSError):
            continue
        chunk_path = f"addons/{addon_name}/{rel_path}"
        if md_file.suffix.lower() == ".rst":
            chunk_path = str(Path(chunk_path).with_suffix(".md"))
        file_chunks = chunk_addon_markdown(addon_name, display_name, chunk_path, markdown)
        chunks.extend(file_chunks)

    # Process examples
    for ex_file in collect_example_files(layout):
        rel_path = str(ex_file.relative_to(addon_dir))
        full_path = f"addons/{addon_name}/{rel_path}"
        try:
            content = ex_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if ex_file.suffix in _CODE_EXTENSIONS:
            chunks.extend(chunk_code_file(addon_name, display_name, full_path, content))
        else:
            # README in examples — split by heading, tag as addon_example
            for c in chunk_addon_markdown(addon_name, display_name, full_path, content):
                chunks.append(Chunk(
                    path=c.path,
                    doc_type="addon",
                    chunk_type="addon_example",
                    addon=c.addon,
                    addon_name=c.addon_name,
                    symbol=c.symbol,
                    heading=f"README: {c.heading}" if c.heading else "README",
                    breadcrumb=c.breadcrumb,
                    start_line=c.start_line,
                    end_line=c.end_line,
                    text=c.text,
                ))

    # Process declaration-only public API summaries from implementation code.
    for api_file in collect_api_files(layout):
        rel_path = str(api_file.relative_to(addon_dir))
        full_path = f"addons/{addon_name}/{rel_path}"
        try:
            content = api_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        chunks.extend(chunk_api_file(addon_name, display_name, full_path, content))

    return chunks
