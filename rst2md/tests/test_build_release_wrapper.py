import os
import subprocess


def run_wrapper(*args):
    env = {**os.environ, "GODOT_RAG_BUILD_WRAPPER_DRY_RUN": "1"}
    result = subprocess.run(["bash", "build.sh", *args], env=env, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def test_build_sh_syntax_is_valid():
    subprocess.run(["bash", "-n", "build.sh"], check=True)


def test_wrapper_delegates_default_build():
    assert run_wrapper() == "uv run godot-rag-build build"


def test_wrapper_preserves_no_bump_and_wiki():
    assert run_wrapper("--no-bump", "--with-wiki") == "uv run godot-rag-build build --no-bump --with-wiki"


def test_wrapper_maps_publish_target():
    assert run_wrapper("--publish", "--with-wiki") == "uv run godot-rag-build publish --target pypi --with-wiki"


def test_wrapper_maps_test_pypi_target():
    assert run_wrapper("--test-pypi", "--no-bump") == "uv run godot-rag-build publish --target testpypi --no-bump"
