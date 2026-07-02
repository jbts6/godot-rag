"""Discover addon layouts: docs, examples, and public API directories."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


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
    from rag.addon_configs import get_config

    config = get_config(addon_dir.name)
    display_name = (
        (config.display_name if config and config.display_name else None)
        or _read_plugin_name(addon_dir)
        or addon_dir.name
    )
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

    # Per-addon custom doc directories from config.
    if config:
        for custom_dir in config.custom_doc_dirs:
            _append_unique(layout.doc_dirs, addon_dir / custom_dir)

    # Root README (fallback to .github/README.md)
    readme = addon_dir / "README.md"
    if readme.is_file():
        layout.doc_files.append(readme)
    else:
        gh_readme = addon_dir / ".github" / "README.md"
        if gh_readme.is_file():
            layout.doc_files.append(gh_readme)

    # Example directories, including project-specific "*examples*" folders.
    for root in roots:
        for candidate in _EXAMPLE_DIR_CANDIDATES:
            _append_unique(layout.example_dirs, root / candidate)

    for root in roots:
        for child in root.iterdir():
            if not child.is_dir():
                continue
            name = child.name.lower()
            if "example" in name or name.endswith("_demo"):
                _append_unique(layout.example_dirs, child)

    # Per-addon custom example directories from config.
    if config:
        for custom_dir in config.custom_example_dirs:
            _append_unique(layout.example_dirs, addon_dir / custom_dir)

    # Public API summaries from nested plugin implementation roots. These are
    # declaration-only chunks, not full-source indexing.
    for root in roots:
        if root != addon_dir:
            _append_unique(layout.api_dirs, root)

    return layout


def collect_doc_files(layout: AddonLayout) -> List[Path]:
    """Collect all documentation .md/.rst files from doc_dirs and doc_files."""
    from fnmatch import fnmatch
    from rag.addon_configs import get_config

    config = get_config(layout.name)
    skip_patterns = config.skip_doc_patterns if config else []

    files = []
    for doc_dir in layout.doc_dirs:
        for ext in _DOC_EXTENSIONS:
            for doc in sorted(doc_dir.rglob(f"*{ext}")):
                if not doc.is_file():
                    continue
                rel = str(doc.relative_to(layout.root))
                if _is_excluded(rel):
                    continue
                if skip_patterns and any(fnmatch(doc.name, p) for p in skip_patterns):
                    continue
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
