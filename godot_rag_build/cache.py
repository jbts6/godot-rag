from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


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
    def load(cls, cache_dir: Path) -> BuildCache:
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
