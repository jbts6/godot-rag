# Task 5: Publish Gates And Package Index Checks

## Task Description

**Files:**
- Create: `godot_rag_build/publish.py`
- Modify: `godot_rag_build/cli.py`
- Test: `rst2md/tests/test_build_release_publish.py`

**Interfaces:**
- Consumes: `BuildOptions`, `run_build`, `CommandRunner`, `BuildReport`.
- Produces: `PublishOptions(target: Literal["pypi", "testpypi"], no_bump: bool = False, with_wiki: bool = False, cache_dir: Path = Path(".cache/build-release"), root: Path = Path("."), runner: CommandRunner | None = None)`.
- Produces: `check_worktree_clean(root: Path, runner: CommandRunner) -> None`.
- Produces: `package_version_exists(package: str, version: str, target: str, opener=urlopen) -> bool`.
- Produces: `run_publish(options: PublishOptions) -> BuildReport`.

## Steps

See plan file `docs/superpowers/plans/2026-06-28-build-efficiency.md` Task 5 section (approximately lines 1306-1553) for the full implementation code.

### Key Implementation Notes

1. `check_worktree_clean` runs `git status --porcelain` and raises if output is non-empty
2. `package_version_exists` checks PyPI/TestPyPI JSON API for existing version
3. `run_publish` ordering: worktree check → full build → tests → diagnostics → version check → upload
4. `publish` must NOT expose `--skip-tests`
5. `_failed_publish_report` helper creates FAIL reports with publish_error in artifacts
6. Upload uses `uv run --with twine python -m twine upload`

### Test Commands

Step 2: `rtk uv run pytest rst2md/tests/test_build_release_publish.py -q` (verify fail)
Step 4: `rtk uv run pytest rst2md/tests/test_build_release_publish.py -q` (verify pass)
Step 5: `rtk uv run pytest rst2md/tests/test_build_release_cli.py::test_publish_help_has_no_skip_tests -q`

### Commit

```bash
rtk git add godot_rag_build/publish.py godot_rag_build/cli.py rst2md/tests/test_build_release_publish.py rst2md/tests/test_build_release_cli.py
rtk git commit -m "feat: add gated release publishing"
```

## Global Constraints

- `publish` 必须执行完整 build、tests、release diagnostics、目标 index 版本存在检查，然后才允许 upload
- `publish` 不得提供 `--skip-tests` 或同义跳过测试参数
- report 不得记录 token、password、credential
- 每个实现任务完成后运行测试并提交
