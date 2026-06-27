## Why

当前搜索只有 FTS5 词法搜索 + 符号索引，无法处理语义相似但词法不同的查询（如 "how to make a button" 无法匹配 "how to create a button"）。此外，Godot 文档中有 190 个有效的 `See also` 交叉引用未被利用。

## What Changes

- 新增 `see_also` 关系类型，从文档中的 `See also \`xxx\`` 格式提取引用（846 个匹配中约 190 个能匹配到已注册符号，其余为全局函数/常量，不在本次范围）
- 引入 sqlite-vec + model2vec 实现向量语义搜索
- 实现 FTS5 + 向量双路召回，RRF 融合排序

## Capabilities

### New Capabilities
- `semantic-search`: 向量语义搜索能力，包括向量生成、存储、检索和 RRF 融合排序
- `see-also-relations`: 从 Godot 文档中提取 `See also` 引用，建立 see_also 关系

### Modified Capabilities

## Impact

- `rst2md/rag/store.py`: 新增 `see_also` 关系构建逻辑、向量表 schema、RRF 搜索函数
- `pyproject.toml`: 新增 `sqlite-vec`、`model2vec` 依赖
- 数据库 schema: 新增 `vec_chunks` 虚拟表
