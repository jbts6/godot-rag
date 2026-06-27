# Brainstorm Summary: RAG 搜索质量提升

## 决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 图谱扩展默认行为 | 默认开启，`--no-expand` 关闭 | 大多数查询需要上下文 |
| canonical form 应用层 | 仅符号层 | FTS 保持原样以保留语义 |

## Phase 1: 符号 normalize 增强

**方案**: 引入 `_canonical_form()` 函数

1. camelCase → 插入 `_` 分隔符
2. 全小写
3. 去掉所有 `_` 和 `.`
4. 去掉尾部 `()`

```
"add_child"      → "addchild"
"addChild"       → "addchild"
"_add_child"     → "addchild"
"Node.add_child" → "nodeaddchild"
```

**改动点**:
- `rst2md/rag/symbols.py`: 新增 `_canonical_form()`，`normalize_symbol` 改用它
- `rst2md/rag/store.py`: 查询时对 query 做同样 canonical 化
- `build_database`: symbols 表的 `normalized_name` 存 canonical form

## Phase 1: BM25 分数映射校准

**方案**: 调整系数 + 可选的统计校准

```python
# 调整前：大多数结果挤在 30-40
fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.1)))

# 调整后：分布更均匀
fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
```

**改动点**:
- `rst2md/rag/store.py`: 修改 FTS 分数公式
- 可选：构建时统计 BM25 值分布存入 metadata 表，查询时用分位数映射

## Phase 2: Chunk 图谱

**表结构**:
```sql
CREATE TABLE IF NOT EXISTS chunk_relations (
  source_id INTEGER NOT NULL REFERENCES chunks(id),
  target_id INTEGER NOT NULL REFERENCES chunks(id),
  relation  TEXT NOT NULL,
  weight    REAL DEFAULT 1.0,
  PRIMARY KEY (source_id, target_id, relation)
);
```

**四种关系**:
| 关系 | 建图方式 | 例子 |
|------|---------|------|
| parent | chunker 附加 `parent_symbol` 字段 | `Node.add_child` → `Node` |
| inherits | 正则提取 class_summary 的 `**Inherits:**` 行 | `Node2D` → `Node` |
| references | chunk 文本中引用的其他符号名 | `add_child` 提到 `remove_child` |
| see_also | 同 heading 下相邻 chunks | 连续 methods |

**建图时机**: `build_database()` 中所有 chunk 插入后、FTS 同步前。

## Phase 3: 检索增强

**图谱遍历**: 命中主结果 top-K 后，通过 `chunk_relations` 查询关联 chunk，`distance=1`。

**分数融合**: 关联结果分数 = 主结果分数 × weight × 0.5（衰减因子）

**返回结果新增字段**: `relation_type`, `distance`

**FTS 分词优化**: 对含 `.` 的查询拆 token，用 AND 连接分别匹配。

## 影响的文件

- `rst2md/rag/symbols.py` — normalize 逻辑
- `rst2md/rag/store.py` — 查询逻辑、分数公式、建图逻辑、图谱遍历
- `rst2md/rag/chunker.py` — 附加 parent_symbol 信息
- `rst2md/rag/models.py` — SearchResult 新增字段
- `rst2md/rag/cli.py` — CLI 新增 `--no-expand` 参数、输出新字段
