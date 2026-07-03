from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from godot_rag_build.cache import BuildCache
from godot_rag_build.fingerprints import fingerprint_file, fingerprint_items, fingerprint_tree
from godot_rag_build.reporting import BuildReport, print_summary, write_last_run
from godot_rag_build.runner import CommandRunner
from godot_rag_build.stages import StageContext, StageError, StageSpec, StageStatus, run_stages


@dataclass(frozen=True)
class BuildOptions:
    no_bump: bool = False
    with_wiki: bool = False
    cache_dir: Path = Path(".cache/build-release")
    root: Path = Path(".")
    runner: CommandRunner | None = None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def resolve_godot_version(root: Path) -> str:
    conf = root / "godot-docs/conf.py"
    text = conf.read_text(encoding="utf-8")
    match = re.search(r'godot_version.*"([0-9]+\.[0-9]+)"', text)
    if not match:
        raise StageError("unable to extract Godot version from godot-docs/conf.py")
    return match.group(1)


def _read_package_version(pyproject: Path) -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise StageError("pyproject.toml missing version")
    return match.group(1)


def resolve_package_version(root: Path, godot_version: str, no_bump: bool) -> str:
    pyproject = root / "pyproject.toml"
    current = _read_package_version(pyproject)
    if no_bump:
        return current
    base = f"{godot_version}.0"
    match = re.match(rf"^{re.escape(base)}(?:\.post(\d+))?$", current)
    next_post = int(match.group(1) or 0) + 1 if match else 1
    version = f"{base}.post{next_post}"
    text = re.sub(r'^version\s*=.*$', f'version = "{version}"', pyproject.read_text(encoding="utf-8"), count=1, flags=re.MULTILINE)
    pyproject.write_text(text, encoding="utf-8")
    return version


def _rewrite_imports(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("from rag.", "from godot_rag.rag.")
    text = text.replace("import rag.", "import godot_rag.rag.")
    path.write_text(text, encoding="utf-8")


def assemble_package_tree(root: Path) -> list[str]:
    package_root = root / "godot_rag"
    rag_out = package_root / "rag"
    if rag_out.exists():
        shutil.rmtree(rag_out)
    rag_out.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").touch()

    for source in sorted((root / "rst2md/rag").glob("*.py")):
        target = rag_out / source.name
        shutil.copy2(source, target)
        _rewrite_imports(target)

    for source in sorted((root / "rst2md/rag").glob("*.json")):
        target = rag_out / source.name
        shutil.copy2(source, target)

    addon_source = root / "rst2md/rag/addon_configs"
    addon_target = rag_out / "addon_configs"
    if addon_source.exists():
        shutil.copytree(addon_source, addon_target)
        for py_file in sorted(addon_target.glob("*.py")):
            _rewrite_imports(py_file)

    return [path.relative_to(root).as_posix() for path in sorted(rag_out.rglob("*")) if path.is_file()]


def _env_with_pythonpath(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "rst2md"
    return env


def _run_cmd(ctx: StageContext, args: list[str]) -> None:
    ctx.runner.run(args, cwd=ctx.root, env=_env_with_pythonpath(ctx.root))


def _submodule_commit_hash(ctx: StageContext, submodule: str) -> str:
    try:
        result = ctx.runner.run(
            ["git", "-C", submodule, "rev-parse", "HEAD"],
            cwd=ctx.root, capture_output=True, check=True,
        )
        return result.stdout.strip()
    except (RuntimeError, OSError):
        return "unknown"


def _tool_version(ctx: StageContext, args: list[str]) -> str:
    try:
        result = ctx.runner.run(args, cwd=ctx.root, capture_output=True, check=False)
    except (RuntimeError, OSError) as exc:
        return f"unavailable:{' '.join(args)}:{exc}"
    output = (result.stdout or result.stderr).strip()
    return output or f"returncode:{result.returncode}"


def _stage_submodule(ctx: StageContext) -> list[str]:
    _run_cmd(ctx, ["git", "submodule", "update", "--init", "--depth", "1", "godot-docs"])
    if not (ctx.root / "godot-docs/classes").is_dir():
        raise StageError("godot-docs/classes is missing after submodule update")
    return ["godot-docs"]


def _stage_version(ctx: StageContext) -> list[str]:
    godot_version = resolve_godot_version(ctx.root)
    package_version = resolve_package_version(ctx.root, godot_version, bool(ctx.options["no_bump"]))
    ctx.artifacts["godot_version"] = godot_version
    ctx.artifacts["package_version"] = package_version
    return ["pyproject.toml"]


def _stage_docs_md(ctx: StageContext) -> list[str]:
    target = ctx.root / "godot_rag/docs-md"
    if target.exists():
        shutil.rmtree(target)
    (ctx.root / "godot_rag").mkdir(exist_ok=True)
    _run_cmd(ctx, ["uv", "run", "python3", "rst2md/rst2md_batch.py", "-i", "godot-docs", "-o", "godot_rag/docs-md"])
    return ["godot_rag/docs-md"]


def _wiki_dir(ctx: StageContext) -> Path:
    """Return the wiki directory — prefer submodule over cloned copy."""
    submodule = ctx.root / "addons/scene_manager_wiki"
    if submodule.is_dir() and any(submodule.glob("*.md")):
        return submodule
    return ctx.root / "addons/scene_manager/docs_wiki"


def _stage_wiki(ctx: StageContext) -> list[str]:
    if not ctx.options["with_wiki"]:
        return []
    # If submodule already provides wiki content, skip clone/copy.
    submodule = ctx.root / "addons/scene_manager_wiki"
    if submodule.is_dir() and any(submodule.glob("*.md")):
        return ["addons/scene_manager_wiki"]
    cache = ctx.root / ".cache/addon-wikis/scene_manager"
    if (cache / ".git").exists():
        ctx.runner.run(["git", "-C", str(cache.relative_to(ctx.root)), "pull", "--ff-only"], cwd=ctx.root, check=False)
    else:
        (ctx.root / ".cache/addon-wikis").mkdir(parents=True, exist_ok=True)
        ctx.runner.run(["git", "clone", "--depth", "1", "https://github.com/glass-brick/Scene-Manager.wiki.git", str(cache.relative_to(ctx.root))], cwd=ctx.root)
    target = ctx.root / "addons/scene_manager/docs_wiki"
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        shutil.copytree(cache, target)
    if (target / ".git").exists():
        shutil.rmtree(target / ".git")
    return ["addons/scene_manager/docs_wiki"]


def _stage_rag_db(ctx: StageContext) -> list[str]:
    (ctx.root / "godot_rag/rag").mkdir(parents=True, exist_ok=True)
    _run_cmd(ctx, ["uv", "run", "python3", "-m", "rag.cli", "build", "--docs", "godot_rag/docs-md", "--db", "godot_rag/rag/godot_docs.sqlite", "--addons", "addons"])
    return ["godot_rag/rag/godot_docs.sqlite"]


def _stage_diagnostics(ctx: StageContext) -> list[str]:
    _run_cmd(ctx, ["uv", "run", "python3", "-m", "rag.cli", "diagnostics", "--db", "godot_rag/rag/godot_docs.sqlite"])
    result = ctx.runner.run(["git", "check-ignore", "-q", "godot_rag/rag/godot_docs.sqlite"], cwd=ctx.root, check=False)
    if result.returncode != 0:
        raise StageError("godot_rag/rag/godot_docs.sqlite must be git ignored")
    return []


def _stage_cleanup_wiki(ctx: StageContext) -> list[str]:
    if ctx.options["with_wiki"]:
        # Only clean up cloned copy, never the submodule.
        cloned = ctx.root / "addons/scene_manager/docs_wiki"
        if cloned.exists():
            shutil.rmtree(cloned)
    return []


def _stage_package_tree(ctx: StageContext) -> list[str]:
    return assemble_package_tree(ctx.root)


def _stage_readme(ctx: StageContext) -> list[str]:
    ctx.runner.run(["uv", "run", "python3", "scripts/merge_readme.py"], cwd=ctx.root)
    return ["README_PYPI.md"]


def _stage_wheel(ctx: StageContext) -> list[str]:
    ctx.runner.run(["uv", "build", "--wheel"], cwd=ctx.root)
    version = ctx.artifacts.get("package_version", _read_package_version(ctx.root / "pyproject.toml"))
    wheel = f"dist/godot_rag-{version}-py3-none-any.whl"
    if not (ctx.root / wheel).exists():
        raise StageError(f"expected wheel not found: {wheel}")
    ctx.artifacts["wheel"] = wheel
    return [wheel]


def _stage_twine_check(ctx: StageContext) -> list[str]:
    wheel = ctx.artifacts["wheel"]
    ctx.runner.run(["uv", "run", "--with", "twine", "python", "-m", "twine", "check", wheel], cwd=ctx.root)
    return [wheel]


def _fingerprint_docs_md(ctx: StageContext) -> str:
    return fingerprint_items({
        "godot_docs": _submodule_commit_hash(ctx, "godot-docs"),
        "rst2md": fingerprint_tree(ctx.root / "rst2md", include_suffixes=(".py", ".json", ".yaml", ".yml")),
        "pandoc_version": _tool_version(ctx, ["pandoc", "--version"]),
    })


def _fingerprint_wiki(ctx: StageContext) -> str:
    if not ctx.options["with_wiki"]:
        return fingerprint_items({"wiki_cache": "disabled"})
    wiki_source = _wiki_dir(ctx)
    return fingerprint_items({
        "wiki_cache": fingerprint_tree(wiki_source, exclude_dirs=(".git",)) if wiki_source.exists() else "missing",
    })


def _fingerprint_rag_db(ctx: StageContext) -> str:
    wiki_source = _wiki_dir(ctx)
    return fingerprint_items({
        "with_wiki": str(ctx.options["with_wiki"]).lower(),
        "godot_docs": _submodule_commit_hash(ctx, "godot-docs"),
        "rst2md": fingerprint_tree(ctx.root / "rst2md", include_suffixes=(".py", ".json", ".yaml", ".yml")),
        "wiki_cache": fingerprint_tree(wiki_source, exclude_dirs=(".git",)) if wiki_source.exists() else "missing",
        "addons": fingerprint_tree(ctx.root / "addons", include_suffixes=(".md", ".rst", ".gd", ".cs", ".json", ".yaml", ".yml", ".cfg"), exclude_dirs=(".git", ".godot", "__pycache__")),
        "addon_configs": fingerprint_tree(ctx.root / "rst2md/rag/addon_configs", include_suffixes=(".py", ".json", ".yaml", ".yml")),
    })


def _fingerprint_package_tree(ctx: StageContext) -> str:
    return fingerprint_items({
        "rag_source": fingerprint_tree(ctx.root / "rst2md/rag", include_suffixes=(".py", ".json", ".yaml", ".yml")),
        "addon_configs": fingerprint_tree(ctx.root / "rst2md/rag/addon_configs", include_suffixes=(".py", ".json", ".yaml", ".yml")),
        "build_tool": fingerprint_tree(ctx.root / "godot_rag_build", include_suffixes=(".py",)),
    })


def _fingerprint_readme(ctx: StageContext) -> str:
    return fingerprint_items({
        "merge_readme": fingerprint_file(ctx.root / "scripts/merge_readme.py"),
        "readme": fingerprint_file(ctx.root / "README.md"),
        "readme_zh": fingerprint_file(ctx.root / "README_zh.md"),
    })


def create_build_stages(options: BuildOptions) -> list[StageSpec]:
    return [
        StageSpec("submodule", _stage_submodule),
        StageSpec("version", _stage_version, dependencies=("submodule",)),
        StageSpec("docs-md", _stage_docs_md, cacheable=True, fingerprint=_fingerprint_docs_md, output_check=lambda ctx: (ctx.root / "godot_rag/docs-md").exists(), dependencies=("version",)),
        StageSpec("wiki", _stage_wiki, cacheable=True, fingerprint=_fingerprint_wiki, output_check=lambda ctx: (not ctx.options["with_wiki"]) or _wiki_dir(ctx).exists(), dependencies=("docs-md",)),
        StageSpec("rag-db", _stage_rag_db, cacheable=True, fingerprint=_fingerprint_rag_db, output_check=lambda ctx: (ctx.root / "godot_rag/rag/godot_docs.sqlite").exists(), dependencies=("wiki",)),
        StageSpec("diagnostics", _stage_diagnostics, dependencies=("rag-db",)),
        StageSpec("cleanup-wiki", _stage_cleanup_wiki, dependencies=("diagnostics",)),
        StageSpec("package-tree", _stage_package_tree, cacheable=True, fingerprint=_fingerprint_package_tree, output_check=lambda ctx: (ctx.root / "godot_rag/rag").exists(), dependencies=("cleanup-wiki",)),
        StageSpec("readme", _stage_readme, cacheable=True, fingerprint=_fingerprint_readme, output_check=lambda ctx: (ctx.root / "README_PYPI.md").exists(), dependencies=("package-tree",)),
        StageSpec("wheel", _stage_wheel, dependencies=("readme",)),
        StageSpec("twine-check", _stage_twine_check, dependencies=("wheel",)),
    ]


def run_build(options: BuildOptions) -> BuildReport:
    root = options.root.resolve()
    runner = options.runner or CommandRunner()
    cache_dir = options.cache_dir if options.cache_dir.is_absolute() else root / options.cache_dir
    cache = BuildCache.load(cache_dir)
    ctx = StageContext(
        root=root,
        cache_dir=cache_dir,
        runner=runner,
        options={"no_bump": options.no_bump, "with_wiki": options.with_wiki},
        artifacts={},
    )
    started = _utc_now()
    results = run_stages(create_build_stages(options), ctx, cache)
    cache.save()
    overall = "FAIL" if any(result.status is StageStatus.FAIL for result in results) else "OK"
    report = BuildReport(
        command="build",
        options={"no_bump": options.no_bump, "with_wiki": options.with_wiki},
        overall_status=overall,
        started_at=started,
        ended_at=_utc_now(),
        stages=results,
        artifacts=ctx.artifacts,
    )
    write_last_run(report, cache_dir)
    print_summary(report)
    return report
