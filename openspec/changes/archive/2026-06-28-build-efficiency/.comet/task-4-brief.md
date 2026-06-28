# Task 4: Local Build Orchestration

## Task Description

**Files:**
- Create: `godot_rag_build/orchestrator.py`
- Modify: `godot_rag_build/cli.py`
- Test: `rst2md/tests/test_build_release_orchestrator.py`

**Interfaces:**
- Consumes: `BuildCache`, `StageSpec`, `StageContext`, `BuildReport`, `CommandRunner`.
- Produces: `BuildOptions(no_bump: bool = False, with_wiki: bool = False, cache_dir: Path = Path(".cache/build-release"), root: Path = Path("."), runner: CommandRunner | None = None)`.
- Produces: `resolve_godot_version(root: Path) -> str`.
- Produces: `resolve_package_version(root: Path, godot_version: str, no_bump: bool) -> str`.
- Produces: `assemble_package_tree(root: Path) -> list[str]`.
- Produces: `create_build_stages(options: BuildOptions) -> list[StageSpec]`.
- Produces: `run_build(options: BuildOptions) -> BuildReport`.
- Produces: `run_release_diagnostics(db_path: Path) -> int`.

## Steps

See plan file `docs/superpowers/plans/2026-06-28-build-efficiency.md` Task 4 section (lines 908-1304) for the full implementation code including:
- Test file with FakeRunner
- Version resolution helpers
- Package assembly with import rewriting
- Stage implementations (submodule, version, docs-md, wiki, rag-db, diagnostics, cleanup-wiki, package-tree, readme, wheel, twine-check)
- Fingerprinting and run_build

### Key Implementation Notes

1. `FakeRunner` in tests intercepts subprocess calls and returns canned responses
2. `write_minimal_build_tree` creates a minimal project structure for testing
3. `_rewrite_imports` replaces `from rag.` with `from godot_rag.rag.` in copied files
4. Stages have dependencies: submodule → version → docs-md → wiki → rag-db → diagnostics → cleanup-wiki → package-tree → readme → wheel → twine-check
5. `resolve_package_version` bumps the `.postN` suffix unless `--no-bump`
6. Wiki stage clones Scene Manager wiki and cleans `.git` directory
7. `run_release_diagnostics` runs `rag.cli diagnostics` and validates git-ignore

### Test Commands

Step 2: `rtk uv run pytest rst2md/tests/test_build_release_orchestrator.py -q` (verify fail)
Step 7: `rtk uv run pytest rst2md/tests/test_build_release_orchestrator.py -q` (verify pass)

### Commit

```bash
rtk git add godot_rag_build/orchestrator.py godot_rag_build/cli.py rst2md/tests/test_build_release_orchestrator.py
rtk git commit -m "feat: port local release build orchestration"
```

## Global Constraints

- 本 change 只优化本地 release build
- 缓存只在 manifest 指纹完全匹配时使用
- `--with-wiki` 必须进入受影响阶段指纹
- `build.sh` 不得保留主构建逻辑（Task 6 处理）
- 每个实现任务完成后运行测试并提交
