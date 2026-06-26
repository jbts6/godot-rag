#!/bin/bash
# 构建 Godot RAG 发布包
#
# 目录结构：
#   rst2md/rag/     — 源码（唯一）
#   godot_rag/      — 构建产物（.gitignore）

set -e

usage() {
    cat <<EOF
用法: $0 [选项]

选项:
  --no-bump      构建时不递增 pyproject.toml 版本
  --publish      构建并发布到 PyPI
  --test-pypi    构建并发布到 TestPyPI
  --with-wiki    拉取 Scene Manager wiki 文档并纳入 RAG 构建
  -h, --help     显示帮助

认证示例:
  TWINE_USERNAME=__token__ TWINE_PASSWORD=<token> $0 --publish
EOF
}

NO_BUMP=0
PUBLISH_TARGET=""
WITH_WIKI=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-bump)
            NO_BUMP=1
            ;;
        --publish|publish)
            if [ -n "$PUBLISH_TARGET" ]; then
                echo "错误: --publish 和 --test-pypi 不能同时使用"
                exit 1
            fi
            PUBLISH_TARGET="pypi"
            ;;
        --test-pypi)
            if [ -n "$PUBLISH_TARGET" ]; then
                echo "错误: --publish 和 --test-pypi 不能同时使用"
                exit 1
            fi
            PUBLISH_TARGET="testpypi"
            ;;
        --with-wiki)
            WITH_WIKI=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "错误: 未知参数 $1"
            usage
            exit 1
            ;;
    esac
    shift
done

if [ -n "$PUBLISH_TARGET" ] && [ -n "$(git status --porcelain)" ]; then
    echo "错误: 发布前工作区必须干净"
    git status --short
    exit 1
fi

echo "=== 构建 Godot RAG ==="

# 更新子模块
echo "检查子模块..."
git submodule update --init --depth 1 godot-docs

# 检查 godot-docs submodule
if [ ! -d "godot-docs/classes" ]; then
    echo "错误: godot-docs submodule 未初始化"
    exit 1
fi

# 从 conf.py 提取 Godot 版本，更新 pyproject.toml
GODOT_VERSION=$(sed -n 's/.*godot_version.*"\([0-9]*\.[0-9]*\)".*/\1/p' godot-docs/conf.py | head -1)
if [ -z "$GODOT_VERSION" ]; then
    echo "错误: 无法从 conf.py 提取 Godot 版本"
    exit 1
fi

if [ "$NO_BUMP" -eq 1 ]; then
    PKG_VERSION=$(python3 -c "
import re
from pathlib import Path

text = Path('pyproject.toml').read_text(encoding='utf-8')
match = re.search(r'^version\\s*=\\s*\"([^\"]+)\"', text, re.MULTILINE)
if not match:
    raise SystemExit('pyproject.toml missing version')
print(match.group(1))
")
else
    # 版本策略: Godot 版本不变时自动递增 postN
    # 4.7.0 → 4.7.0.post1 → 4.7.0.post2 → ...
    # Godot 版本变化时重置为 4.8.0.post1
    PKG_VERSION=$(python3 -c "
import re
from pathlib import Path

godot_ver = '${GODOT_VERSION}'
base = godot_ver + '.0'
text = Path('pyproject.toml').read_text(encoding='utf-8')
match = re.search(r'^version\\s*=\\s*\"([^\"]+)\"', text, re.MULTILINE)
cur = match.group(1) if match else ''

# 匹配当前 Godot 版本的 postN
m = re.match(r'^' + re.escape(base) + r'(?:\\.post(\\d+))?$', cur)
if m:
    n = int(m.group(1) or 0) + 1
else:
    n = 1
print(f'{base}.post{n}')
")

    python3 -c "
import re, sys
p = sys.argv[1]; v = sys.argv[2]
t = open(p).read()
t = re.sub(r'^version = .*$', f'version = \"{v}\"', t, count=1, flags=re.MULTILINE)
open(p, 'w').write(t)
" pyproject.toml "${PKG_VERSION}"
fi
echo "版本: ${PKG_VERSION} (Godot ${GODOT_VERSION})"

# 清理旧的构建产物（保留 docs-md）
rm -rf godot_rag/rag dist

# 转换 Markdown（子模块提交时间晚于 docs-md 修改时间则重新生成）
SUBMODULE_MTIME=$(git -C godot-docs log -1 --format=%ct)
DOCS_MTIME=$(python3 -c "import os,sys; print(int(os.path.getmtime(sys.argv[1]))) if os.path.exists(sys.argv[1]) else print(0)" godot_rag/docs-md)

if [ ! -d "godot_rag/docs-md" ] || [ "$SUBMODULE_MTIME" -gt "$DOCS_MTIME" ]; then
    echo "1. 转换 Markdown...（子模块已更新，重新生成）"
    rm -rf godot_rag/docs-md
    mkdir -p godot_rag
    PYTHONPATH=rst2md uv run python3 rst2md/rst2md_batch.py \
        -i godot-docs \
        -o godot_rag/docs-md
else
    echo "1. 转换 Markdown... 跳过（未过期）"
fi

# 可选：拉取 Scene Manager wiki 文档
if [ "$WITH_WIKI" -eq 1 ]; then
    echo "2a. 拉取 Scene Manager wiki..."
    WIKI_CACHE=".cache/addon-wikis/scene_manager"
    if [ -d "$WIKI_CACHE/.git" ]; then
        git -C "$WIKI_CACHE" pull --ff-only || echo "警告: wiki 更新失败，使用缓存"
    else
        mkdir -p ".cache/addon-wikis"
        git clone --depth 1 https://github.com/glass-brick/Scene-Manager.wiki.git "$WIKI_CACHE"
    fi
    # 复制到 addon 目录供 discovery 发现
    rm -rf addons/scene_manager/docs_wiki
    cp -r "$WIKI_CACHE" addons/scene_manager/docs_wiki
    # 清理 .git 目录（不需要在 addon 内保留）
    rm -rf addons/scene_manager/docs_wiki/.git
    echo "   wiki 已同步到 addons/scene_manager/docs_wiki/"
fi

# 构建 RAG 数据库（含 addons）
echo "2. 构建 RAG 数据库..."
mkdir -p godot_rag/rag
PYTHONPATH=rst2md uv run python3 -m rag.cli build \
    --docs godot_rag/docs-md \
    --db godot_rag/rag/godot_docs.sqlite \
    --addons addons

# 清理 wiki 缓存（已入库，不需要留在子模块内）
if [ "$WITH_WIKI" -eq 1 ]; then
    rm -rf addons/scene_manager/docs_wiki
fi

# 组装 RAG 包（源码复制 + import 改写）
echo "3. 组装 RAG 包..."
touch godot_rag/__init__.py
cp rst2md/rag/*.py godot_rag/rag/
# 复制 addon_configs 模块
cp -r rst2md/rag/addon_configs godot_rag/rag/
python3 -c "
import glob, sys
for f in glob.glob(sys.argv[1] + '/*.py'):
    t = open(f).read().replace('from rag.', 'from godot_rag.rag.')
    open(f, 'w').write(t)
for f in glob.glob(sys.argv[1] + '/addon_configs/*.py'):
    t = open(f).read().replace('from rag.', 'from godot_rag.rag.')
    open(f, 'w').write(t)
" godot_rag/rag

# 合并中英文 README 用于 PyPI 展示
echo "3a. 合并 README..."
python3 scripts/merge_readme.py

# 构建 wheel
echo "4. 构建 wheel..."
uv build --wheel
WHEEL_PATH="dist/godot_rag-${PKG_VERSION}-py3-none-any.whl"
if [ ! -f "$WHEEL_PATH" ]; then
    echo "错误: 未找到当前版本 wheel: $WHEEL_PATH"
    exit 1
fi

echo "5. 检查 wheel..."
uv run --with twine python -m twine check "$WHEEL_PATH"

if [ "$PUBLISH_TARGET" = "pypi" ]; then
    echo "6. 发布到 PyPI..."
    uv run pytest -q
    uv run --with twine python -m twine upload "$WHEEL_PATH"
elif [ "$PUBLISH_TARGET" = "testpypi" ]; then
    echo "6. 发布到 TestPyPI..."
    uv run pytest -q
    uv run --with twine python -m twine upload --repository testpypi "$WHEEL_PATH"
fi

echo ""
echo "=== 构建完成 ==="
echo "版本: ${PKG_VERSION}"
echo "Wheel: ${WHEEL_PATH}"
echo ""
echo "发布: ./build.sh --publish"
echo "TestPyPI: ./build.sh --test-pypi"
echo "认证: TWINE_USERNAME=__token__ TWINE_PASSWORD=<token> ./build.sh --publish"
echo "安装: uv pip install godot-rag"
echo "测试: godot-rag search Timer --limit 3"
