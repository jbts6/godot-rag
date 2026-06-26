#!/bin/bash
# 构建 Godot RAG 发布包
#
# 目录结构：
#   rst2md/rag/     — 源码（唯一）
#   godot_rag/      — 构建产物（.gitignore）

set -e

PUBLISH=0
if [ "${1:-}" = "--publish" ] || [ "${1:-}" = "publish" ]; then
    PUBLISH=1
elif [ -n "${1:-}" ]; then
    echo "用法: $0 [--publish]"
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

# 构建 RAG 数据库（含 addons）
echo "2. 构建 RAG 数据库..."
mkdir -p godot_rag/rag
PYTHONPATH=rst2md uv run python3 -m rag.cli build \
    --docs godot_rag/docs-md \
    --db godot_rag/rag/godot_docs.sqlite \
    --addons addons

# 组装 RAG 包（源码复制 + import 改写）
echo "3. 组装 RAG 包..."
touch godot_rag/__init__.py
cp rst2md/rag/*.py godot_rag/rag/
python3 -c "
import glob, sys
for f in glob.glob(sys.argv[1] + '/*.py'):
    t = open(f).read().replace('from rag.', 'from godot_rag.rag.')
    open(f, 'w').write(t)
" godot_rag/rag

# 构建 wheel
echo "4. 构建 wheel..."
uv build --wheel

if [ "$PUBLISH" -eq 1 ]; then
    echo "5. 发布到 PyPI..."
    uvx twine upload dist/*
fi

echo ""
echo "=== 构建完成 ==="
echo "版本: ${PKG_VERSION}"
echo "Wheel: dist/godot_rag-${PKG_VERSION}-py3-none-any.whl"
echo ""
echo "发布: ./build.sh --publish"
echo "认证: TWINE_USERNAME=__token__ TWINE_PASSWORD=<token> ./build.sh --publish"
echo "安装: uv pip install godot-rag"
echo "测试: godot-rag search Timer --limit 3"
