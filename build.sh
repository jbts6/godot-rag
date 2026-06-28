#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<EOF
用法: $0 [选项]

选项:
  --no-bump      构建时不递增 pyproject.toml 版本
  --publish      构建并发布到 PyPI
  --test-pypi    构建并发布到 TestPyPI
  --with-wiki    拉取 Scene Manager wiki 文档并纳入 RAG 构建
  -h, --help     显示帮助

新入口:
  uv run godot-rag-build build
  uv run godot-rag-build publish --target pypi
EOF
}

NO_BUMP=0
WITH_WIKI=0
PUBLISH_TARGET=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-bump)
            NO_BUMP=1
            ;;
        --with-wiki)
            WITH_WIKI=1
            ;;
        --publish|publish)
            if [ -n "$PUBLISH_TARGET" ]; then
                echo "错误: --publish 和 --test-pypi 不能同时使用" >&2
                exit 1
            fi
            PUBLISH_TARGET="pypi"
            ;;
        --test-pypi)
            if [ -n "$PUBLISH_TARGET" ]; then
                echo "错误: --publish 和 --test-pypi 不能同时使用" >&2
                exit 1
            fi
            PUBLISH_TARGET="testpypi"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "错误: 未知参数 $1" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

CMD=(uv run godot-rag-build)
if [ -n "$PUBLISH_TARGET" ]; then
    CMD+=(publish --target "$PUBLISH_TARGET")
else
    CMD+=(build)
fi
if [ "$NO_BUMP" -eq 1 ]; then
    CMD+=(--no-bump)
fi
if [ "$WITH_WIKI" -eq 1 ]; then
    CMD+=(--with-wiki)
fi

if [ "${GODOT_RAG_BUILD_WRAPPER_DRY_RUN:-0}" = "1" ]; then
    printf '%s' "${CMD[0]}"
    for arg in "${CMD[@]:1}"; do
        printf ' %s' "$arg"
    done
    printf '\n'
    exit 0
fi

exec "${CMD[@]}"
