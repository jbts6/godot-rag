# Task 3: Fingerprints, Manifest Cache, And Clean Cache

## Task Description

**Files:**
- Create: `godot_rag_build/fingerprints.py`
- Create: `godot_rag_build/cache.py`
- Test: `rst2md/tests/test_build_release_cache.py`

**Interfaces:**
- Consumes: `StageContext` from Task 2.
- Produces: `fingerprint_file(path: Path) -> str`
- Produces: `fingerprint_tree(path: Path, *, include_suffixes: tuple[str, ...] | None = None, exclude_dirs: tuple[str, ...] = ()) -> str`
- Produces: `fingerprint_items(items: Mapping[str, str]) -> str`
- Produces: `BuildCache.load(cache_dir: Path) -> BuildCache`
- Produces: `BuildCache.should_skip(stage_name: str, fingerprint: str, context: StageContext, output_check: Callable[[StageContext], bool] | None) -> CacheDecision`
- Produces: `BuildCache.record_success(stage_name: str, fingerprint: str, outputs: list[str]) -> None`
- Produces: `BuildCache.save() -> Path`
- Produces: `clean_cache(cache_dir: Path) -> None`

## Steps

### Step 1: Write failing cache tests

Create `rst2md/tests/test_build_release_cache.py`:

```python
from pathlib import Path

from godot_rag_build.cache import BuildCache, clean_cache
from godot_rag_build.fingerprints import fingerprint_file, fingerprint_items, fingerprint_tree
from godot_rag_build.runner import CommandRunner
from godot_rag_build.stages import StageContext


def test_file_fingerprint_changes_with_content(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("one", encoding="utf-8")
    first = fingerprint_file(path)

    path.write_text("two", encoding="utf-8")
    second = fingerprint_file(path)

    assert first != second


def test_tree_fingerprint_uses_stable_order(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "b.py").write_text("b", encoding="utf-8")
    (root / "a.py").write_text("a", encoding="utf-8")

    first = fingerprint_tree(root, include_suffixes=(".py",))
    second = fingerprint_tree(root, include_suffixes=(".py",))

    assert first == second


def test_options_change_fingerprint():
    no_wiki = fingerprint_items({"with_wiki": "false", "godot_docs_head": "abc"})
    with_wiki = fingerprint_items({"with_wiki": "true", "godot_docs_head": "abc"})

    assert no_wiki != with_wiki


def test_cache_skips_only_when_fingerprint_and_outputs_match(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    output = tmp_path / "dist/pkg.whl"
    output.parent.mkdir()
    output.write_text("wheel", encoding="utf-8")

    cache = BuildCache.load(cache_dir)
    cache.record_success("wheel", "abc", [str(output)])
    cache.save()
    loaded = BuildCache.load(cache_dir)
    ctx = StageContext(tmp_path, cache_dir, CommandRunner(), {}, {})

    decision = loaded.should_skip("wheel", "abc", ctx, lambda _ctx: output.exists())

    assert decision.skip is True
    assert decision.reason == "fingerprint match"
    assert decision.outputs == [str(output)]


def test_cache_miss_when_output_check_fails(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    cache = BuildCache.load(cache_dir)
    cache.record_success("rag-db", "abc", [str(tmp_path / "missing.sqlite")])
    cache.save()
    ctx = StageContext(tmp_path, cache_dir, CommandRunner(), {}, {})

    decision = BuildCache.load(cache_dir).should_skip("rag-db", "abc", ctx, lambda _ctx: False)

    assert decision.skip is False
    assert decision.reason == "outputs missing"


def test_clean_cache_removes_cache_dir(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    cache_dir.mkdir(parents=True)
    (cache_dir / "manifest.json").write_text("{}", encoding="utf-8")

    clean_cache(cache_dir)

    assert not cache_dir.exists()
```

### Step 2: Run tests to verify they fail

```bash
rtk uv run pytest rst2md/tests/test_build_release_cache.py -q
```

Expected: FAIL because cache and fingerprint modules do not exist.

### Step 3: Implement stable fingerprints

Create `godot_rag_build/fingerprints.py`:

```python
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
```

### Step 4: Implement manifest cache

Create `godot_rag_build/cache.py`:

```python
from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from godot_rag_build.stages import StageContext


@dataclass(frozen=True)
class CacheDecision:
    skip: bool
    reason: str
    outputs: list[str]


class BuildCache:
    def __init__(self, cache_dir: Path, entries: dict[str, dict[str, object]] | None = None):
        self.cache_dir = cache_dir
        self.entries = entries or {}

    @classmethod
    def load(cls, cache_dir: Path) -> "BuildCache":
        manifest = cache_dir / "manifest.json"
        if not manifest.exists():
            return cls(cache_dir)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return cls(cache_dir, dict(data.get("stages", {})))

    def should_skip(
        self,
        stage_name: str,
        fingerprint: str,
        context: StageContext,
        output_check: Callable[[StageContext], bool] | None,
    ) -> CacheDecision:
        entry = self.entries.get(stage_name)
        if not entry:
            return CacheDecision(False, "manifest missing", [])
        if entry.get("fingerprint") != fingerprint:
            return CacheDecision(False, "fingerprint changed", list(entry.get("outputs", [])))
        outputs = list(entry.get("outputs", []))
        if output_check and not output_check(context):
            return CacheDecision(False, "outputs missing", outputs)
        for output in outputs:
            if not Path(output).exists():
                return CacheDecision(False, "outputs missing", outputs)
        return CacheDecision(True, "fingerprint match", outputs)

    def record_success(self, stage_name: str, fingerprint: str, outputs: list[str]) -> None:
        self.entries[stage_name] = {"fingerprint": fingerprint, "outputs": outputs}

    def save(self) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / "manifest.json"
        path.write_text(
            json.dumps({"stages": self.entries}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path


def clean_cache(cache_dir: Path) -> None:
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
```

### Step 5: Run cache tests

```bash
rtk uv run pytest rst2md/tests/test_build_release_cache.py -q
```

Expected: PASS.

### Step 6: Commit Task 3

```bash
rtk git status --short
rtk git add godot_rag_build/fingerprints.py godot_rag_build/cache.py rst2md/tests/test_build_release_cache.py
rtk git commit -m "feat: add release build cache manifest"
```

## Global Constraints

- 缓存只在 manifest 指纹完全匹配、影响选项匹配、期望输出存在且 output check 通过时使用；任何不确定都必须运行阶段。
- `.cache/build-release/manifest.json` 保存可复用缓存状态。
- `clean-cache` 移除整个 `.cache/build-release` 目录。
- 每个实现任务完成后运行该任务列出的测试命令并提交。
