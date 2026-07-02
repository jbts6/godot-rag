import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir():
    """提供临时目录"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_docs(tmp_dir):
    """创建示例文档结构"""
    docs = tmp_dir / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)

    # 创建示例类文件
    (classes / "class_node.md").write_text(
        "# Node\n\nBase class.\n\n## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child.\n",
        encoding="utf-8",
    )
    return docs


@pytest.fixture
def sample_db(sample_docs, tmp_dir):
    """创建示例数据库"""
    from rag.store import build_database

    db_path = tmp_dir / "test.sqlite"
    build_database(sample_docs, db_path)
    return db_path