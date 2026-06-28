from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path


def _hash_bytes(chunks: list[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def fingerprint_items(items: Mapping[str, str]) -> str:
    chunks: list[bytes] = []
    for key in sorted(items):
        chunks.append(key.encode("utf-8") + b"\0" + items[key].encode("utf-8") + b"\0")
    return _hash_bytes(chunks)


def fingerprint_file(path: Path) -> str:
    if not path.exists():
        return fingerprint_items({str(path): "missing"})
    return _hash_bytes([str(path).encode("utf-8"), b"\0", path.read_bytes()])


def fingerprint_tree(
    path: Path,
    *,
    include_suffixes: tuple[str, ...] | None = None,
    exclude_dirs: tuple[str, ...] = (),
) -> str:
    if not path.exists():
        return fingerprint_items({str(path): "missing"})
    chunks: list[bytes] = []
    excluded = set(exclude_dirs)
    for child in sorted(path.rglob("*")):
        if any(part in excluded for part in child.relative_to(path).parts):
            continue
        if child.is_dir():
            continue
        if include_suffixes and child.suffix not in include_suffixes:
            continue
        rel = child.relative_to(path).as_posix()
        chunks.append(rel.encode("utf-8") + b"\0")
        chunks.append(child.read_bytes() + b"\0")
    return _hash_bytes(chunks)
