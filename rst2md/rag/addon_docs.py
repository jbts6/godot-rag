"""Discover and chunk addon documentation, examples, and public API summaries."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from rag.models import Chunk

# Directories to exclude from doc scanning
_EXCLUDE_DIRS = {
    "_includes", "_layouts", "assets", ".github", "pages",
    "test", "tests", ".git",
}
_ALLOWED_UNDERSCORE_DIRS = {
    "_docs", "_first_steps", "_testing", "_advanced_testing",
    "_tutorials", "_faq", "_csharp_project_setup",
}

# Non-doc files to skip
_SKIP_FILES = {
    "contributing.md", "code_of_conduct.md", "security.md",
    "changelog.md", "release_checklist.md", "license.md",
    "_config.yml", "_data",
}

# Code file extensions for examples
_CODE_EXTENSIONS = {".gd", ".cs"}
_DOC_EXTENSIONS = {".md", ".rst"}
_DOC_DIR_CANDIDATES = ("docs", "Docs", "documentation", "Documentation", "doc/source")
_EXAMPLE_DIR_CANDIDATES = ("examples", "demo", "dev_scenes")
_API_SKIP_PARTS = {
    "docs", "documentation", "doc", "examples", "demo", "dev_scenes",
    "test", "tests", ".git", "assets",
}

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


@dataclass
class AddonLayout:
    """Discovered layout of an addon's documentation and examples."""
    name: str                    # Folder name (e.g. "statecharts")
    display_name: str            # Real plugin name (e.g. "Godot State Charts")
    root: Path
    doc_dirs: List[Path] = field(default_factory=list)
    doc_files: List[Path] = field(default_factory=list)
    example_dirs: List[Path] = field(default_factory=list)
    api_dirs: List[Path] = field(default_factory=list)


def _is_excluded(rel_path: str) -> bool:
    """Check if a relative path should be excluded."""
    parts = Path(rel_path).parts
    for part in parts:
        part_lower = part.lower()
        if part_lower in _EXCLUDE_DIRS:
            return True
        if part.startswith("_") and part not in _ALLOWED_UNDERSCORE_DIRS:
            return True
    filename = Path(rel_path).name.lower()
    if filename in _SKIP_FILES:
        return True
    return False


def _same_path(left: Path, right: Path) -> bool:
    try:
        return str(left.resolve()).casefold() == str(right.resolve()).casefold()
    except OSError:
        return str(left).casefold() == str(right).casefold()


def _existing_path(path: Path) -> Path:
    """Return the existing directory path with on-disk casing when possible."""
    try:
        for child in path.parent.iterdir():
            if _same_path(child, path):
                return child
    except OSError:
        pass
    return path


def _append_unique(paths: List[Path], path: Path) -> None:
    if path.is_dir() and not any(_same_path(path, existing) for existing in paths):
        paths.append(_existing_path(path))


def _plugin_roots(addon_dir: Path) -> List[Path]:
    roots = [addon_dir]
    for cfg in sorted(addon_dir.rglob("plugin.cfg")):
        try:
            rel_parts = cfg.relative_to(addon_dir).parts
        except ValueError:
            continue
        if len(rel_parts) > 4:
            continue
        parent = cfg.parent
        if not any(_same_path(parent, r) for r in roots):
            roots.append(parent)
    return roots


def _read_plugin_name(addon_dir: Path) -> Optional[str]:
    """Read the real plugin name from plugin.cfg.

    Searches up to 3 levels deep. If multiple plugin.cfg files exist,
    returns the first name that isn't a known test framework (e.g. "Gut").
    """
    _SKIP_NAMES = {"Gut"}
    names = []
    for cfg in addon_dir.rglob("plugin.cfg"):
        if len(cfg.relative_to(addon_dir).parts) > 3:
            continue
        try:
            text = cfg.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        match = re.search(r'^name="?([^"\n]+)"?', text, re.MULTILINE)
        if match:
            names.append(match.group(1).strip())
    # Prefer names that aren't in the skip list
    for n in names:
        if n not in _SKIP_NAMES:
            return n
    return names[0] if names else None


def discover_addon(addon_dir: Path) -> AddonLayout:
    """Discover documentation and example directories in an addon."""
    display_name = _read_plugin_name(addon_dir) or addon_dir.name
    layout = AddonLayout(
        name=addon_dir.name,
        display_name=display_name,
        root=addon_dir,
    )

    roots = _plugin_roots(addon_dir)

    # Doc directories from addon root and nested plugin roots.
    for root in roots:
        for candidate in _DOC_DIR_CANDIDATES:
            _append_unique(layout.doc_dirs, root / candidate)

    # Root README
    readme = addon_dir / "README.md"
    if readme.is_file():
        layout.doc_files.append(readme)

    # Example directories, including project-specific "*examples*" folders.
    for root in roots:
        for candidate in _EXAMPLE_DIR_CANDIDATES:
            _append_unique(layout.example_dirs, root / candidate)

    for child in addon_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name.lower()
        if "example" in name or name.endswith("_demo"):
            _append_unique(layout.example_dirs, child)

    # Public API summaries from nested plugin implementation roots. These are
    # declaration-only chunks, not full-source indexing.
    for root in roots:
        if root != addon_dir:
            _append_unique(layout.api_dirs, root)

    return layout


def collect_doc_files(layout: AddonLayout) -> List[Path]:
    """Collect all documentation .md/.rst files from doc_dirs and doc_files."""
    files = []
    for doc_dir in layout.doc_dirs:
        for ext in _DOC_EXTENSIONS:
            for doc in sorted(doc_dir.rglob(f"*{ext}")):
                if not doc.is_file():
                    continue
                rel = str(doc.relative_to(layout.root))
                if not _is_excluded(rel):
                    files.append(doc)
    for f in layout.doc_files:
        files.append(f)
    return files


def collect_example_files(layout: AddonLayout) -> List[Path]:
    """Collect example code files (.gd, .cs) and README.md from example dirs."""
    files = []
    for example_dir in layout.example_dirs:
        for f in sorted(example_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = str(f.relative_to(layout.root))
            if _is_excluded(rel):
                continue
            if f.suffix in _CODE_EXTENSIONS:
                files.append(f)
            elif f.name.lower() == "readme.md":
                files.append(f)
    return files


def collect_api_files(layout: AddonLayout) -> List[Path]:
    """Collect code files used for declaration-only public API chunks."""
    files = []
    for api_dir in layout.api_dirs:
        for f in sorted(api_dir.rglob("*")):
            if not f.is_file() or f.suffix not in _CODE_EXTENSIONS:
                continue
            rel = str(f.relative_to(layout.root))
            if _is_excluded(rel):
                continue
            parts = [p.lower() for p in Path(rel).parts]
            if any(part in _API_SKIP_PARTS or "example" in part for part in parts):
                continue
            files.append(f)
    return files


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
