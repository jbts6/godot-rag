"""Discover and chunk addon documentation and examples."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from rag.models import Chunk

# Directories to exclude from doc scanning
_EXCLUDE_DIRS = {
    "_includes", "_layouts", "assets", ".github", "pages",
    "test", "tests", ".git",
}

# Non-doc files to skip
_SKIP_FILES = {
    "contributing.md", "code_of_conduct.md", "security.md",
    "changelog.md", "release_checklist.md", "license.md",
    "_config.yml", "_data",
}

# Code file extensions for examples
_CODE_EXTENSIONS = {".gd", ".cs"}


@dataclass
class AddonLayout:
    """Discovered layout of an addon's documentation and examples."""
    name: str
    root: Path
    doc_dirs: List[Path] = field(default_factory=list)
    doc_files: List[Path] = field(default_factory=list)
    example_dirs: List[Path] = field(default_factory=list)


def _is_excluded(rel_path: str) -> bool:
    """Check if a relative path should be excluded."""
    parts = Path(rel_path).parts
    for part in parts:
        if part in _EXCLUDE_DIRS:
            return True
        if part.startswith("_") and part not in ("_docs", "_first_steps", "_testing", "_advanced_testing", "_tutorials", "_faq", "_csharp_project_setup"):
            return True
    filename = Path(rel_path).name.lower()
    if filename in _SKIP_FILES:
        return True
    return False


def discover_addon(addon_dir: Path) -> AddonLayout:
    """Discover documentation and example directories in an addon."""
    layout = AddonLayout(name=addon_dir.name, root=addon_dir)

    # Doc directories
    for candidate in ["docs", "documentation", "doc/source"]:
        d = addon_dir / candidate
        if d.is_dir():
            layout.doc_dirs.append(d)

    # Root README
    readme = addon_dir / "README.md"
    if readme.is_file():
        layout.doc_files.append(readme)

    # Example directories
    for candidate in ["examples", "demo", "dev_scenes"]:
        d = addon_dir / candidate
        if d.is_dir():
            layout.example_dirs.append(d)

    return layout


def collect_doc_files(layout: AddonLayout) -> List[Path]:
    """Collect all documentation .md files from doc_dirs and doc_files."""
    files = []
    for doc_dir in layout.doc_dirs:
        for md in sorted(doc_dir.rglob("*.md")):
            rel = str(md.relative_to(layout.root))
            if not _is_excluded(rel):
                files.append(md)
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


def chunk_addon_markdown(addon_name: str, rel_path: str, markdown: str) -> List[Chunk]:
    """Chunk an addon markdown doc by headings. Returns addon_doc chunks."""
    from rag.chunker import _find_headings, HEADING_RE

    lines = markdown.split("\n")
    headings = _find_headings(lines)
    chunks = []

    breadcrumb_prefix = f"addons > {addon_name}"

    if not headings:
        text = "\n".join(lines).strip()
        if text:
            doc_name = Path(rel_path).stem
            chunks.append(Chunk(
                path=rel_path,
                doc_type="addon",
                chunk_type="addon_doc",
                addon=addon_name,
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
            symbol="",
            heading=title,
            breadcrumb=f"{breadcrumb_prefix} > {doc_name} > {title}",
            start_line=line_idx + 1,
            end_line=end_line,
            text=section_text,
        ))

    return chunks


def chunk_code_file(addon_name: str, rel_path: str, code: str) -> List[Chunk]:
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
        symbol=rel_path,
        heading=filename,
        breadcrumb=f"addons > {addon_name} > {rel_path}",
        start_line=1,
        end_line=len(lines),
        text=code,
    )]


def chunk_addon(addon_dir: Path) -> List[Chunk]:
    """Discover and chunk all docs and examples for a single addon."""
    layout = discover_addon(addon_dir)
    addon_name = layout.name
    chunks = []

    # Process documentation
    for md_file in collect_doc_files(layout):
        rel_path = str(md_file.relative_to(addon_dir))
        try:
            markdown = md_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        file_chunks = chunk_addon_markdown(addon_name, f"addons/{addon_name}/{rel_path}", markdown)
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
            chunks.extend(chunk_code_file(addon_name, full_path, content))
        else:
            # README in examples — split by heading, tag as addon_example
            for c in chunk_addon_markdown(addon_name, full_path, content):
                chunks.append(Chunk(
                    path=c.path,
                    doc_type="addon",
                    chunk_type="addon_example",
                    addon=c.addon,
                    symbol=c.symbol,
                    heading=f"README: {c.heading}" if c.heading else "README",
                    breadcrumb=c.breadcrumb,
                    start_line=c.start_line,
                    end_line=c.end_line,
                    text=c.text,
                ))

    return chunks
