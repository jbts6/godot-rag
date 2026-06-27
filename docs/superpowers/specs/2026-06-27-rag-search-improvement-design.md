---
comet_change: rag-search-improvement
role: technical-design
canonical_spec: openspec
date: 2026-06-27
status: draft
archived-with: 2026-06-27-rag-search-improvement
status: final
---

# Design Doc: RAG 搜索质量提升

## 概述

对 godot-rag 的搜索系统做 3 阶段改进：符号匹配模糊化、BM25 校准、chunk 图谱、FTS 查询优化、分数体系统一。

## 1. 符号 normalize 增强

### 现状

`normalize_symbol()` 只做 `lowercase + strip "()"`，无法处理：
- `addChild` vs `add_child`（camelCase vs snake_case）
- `_add_child` vs `add_child`（前缀下划线）

### 设计

新增 `_canonical_form()` 函数：

```python
def _canonical_form(name: str) -> str:
    name = name.rstrip("()")
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)  # camelCase → camel_case
    name = name.lower()
    name = name.replace("_", "").replace(".", "")
    return name
```

`normalize_symbol()` 改为调用 `_canonical_form()`。

**影响范围**:
- `rst2md/rag/symbols.py`: 修改 `normalize_symbol()`
- `rst2md/rag/store.py`: 查询时对 `query` 做同样 canonical 化

**向后兼容**: canonical form 是更宽松的匹配，不会让之前能匹配的查询失效。

### 测试

```python
assert _canonical_form("add_child") == "addchild"
assert _canonical_form("addChild") == "addchild"
assert _canonical_form("_add_child") == "addchild"
assert _canonical_form("Node.add_child") == "nodeaddchild"
assert _canonical_form("GDExtension") == "gdextension"
```

## 2. BM25 分数映射校准

### 现状

```python
fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.1)))
```

问题：`* 0.1` 系数导致大多数结果分数挤在 30-40 区间，长文档 BM25 值天然偏高被过度惩罚。

### 设计

调整系数为 `* 0.01`，拉宽分数分布：

```python
fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
```

新分布：
- BM25=1 → 39.6（之前 36.4）
- BM25=10 → 28.6（之前 20.0）
- BM25=50 → 8.0（之前 6.7）
- BM25=100 → 2.9（之前 3.6）

**影响范围**: `rst2md/rag/store.py` 中 FTS 分数计算。

## 3. Chunk 图谱

### 表结构

```sql
CREATE TABLE IF NOT EXISTS chunk_relations (
  source_id INTEGER NOT NULL REFERENCES chunks(id),
  target_id INTEGER NOT NULL REFERENCES chunks(id),
  relation  TEXT NOT NULL,  -- 'parent' | 'inherits' | 'references' | 'see_also'
  weight    REAL DEFAULT 1.0,
  PRIMARY KEY (source_id, target_id, relation)
);
CREATE INDEX idx_relations_source ON chunk_relations(source_id);
CREATE INDEX idx_relations_target ON chunk_relations(target_id);
```

### 建图逻辑

在 `build_database()` 中，所有 chunk 插入完成后、FTS 同步前执行建图。

#### 3.1 parent 关系

**数据流**: chunker 在生成 member chunk 时，记录其所属 class 的 symbol 名。

```python
# chunker.py: _chunk_class_document() 中
chunks.append(Chunk(
    ...,
    parent_symbol=class_name,  # 新增字段
))
```

```python
# store.py: build_database() 建图时
for chunk in chunks:
    if chunk.parent_symbol:
        # 查找 parent chunk 的 id
        parent_id = symbol_to_chunk_id[chunk.parent_symbol]
        conn.execute(
            "INSERT OR IGNORE INTO chunk_relations VALUES (?, ?, 'parent', 1.0)",
            (chunk_id, parent_id)
        )
```

#### 3.2 inherits 关系

从 class_summary chunk 的正文中提取继承链：

```python
# 正则: \*\*Inherits:\*\* `XXX` **<** `YYY` **<** `ZZZ`
INHERITS_RE = re.compile(r'\*\*Inherits:\*\*(.+)')

def _extract_inherits(text: str) -> List[str]:
    match = INHERITS_RE.search(text)
    if not match:
        return []
    # 提取所有 `ClassName` 引用
    return re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`', match.group(1))
```

建图时，对每个 class chunk，找到其继承链中每个类的 chunk，建立 `inherits` 关系。

#### 3.3 references 关系

对 chunk 文本中出现的符号名做交叉引用：

```python
# 构建所有已知符号的集合
all_symbols = {sym.normalized_name: sym for sym in symbols}

# 对每个 chunk，扫描文本中出现的符号名
for chunk_id, text in chunk_texts:
    tokens = re.findall(r'[A-Za-z_][A-Za-z0-9_.]+', text)
    for token in tokens:
        normalized = _canonical_form(token)
        if normalized in all_symbols and normalized != current_symbol:
            target_id = all_symbols[normalized].chunk_id
            conn.execute(
                "INSERT OR IGNORE INTO chunk_relations VALUES (?, ?, 'references', 0.5)",
                (chunk_id, target_id)
            )
```

#### 3.4 see_also 关系

同一 heading 下的连续 chunks 互相关联：

```python
# 同 heading、同 doc_type 的相邻 chunks
prev_id = None
for chunk in heading_group:
    if prev_id:
        conn.execute(
            "INSERT OR IGNORE INTO chunk_relations VALUES (?, ?, 'see_also', 0.3)",
            (prev_id, chunk_id)
        )
    prev_id = chunk_id
```

## 4. 图谱遍历查询

### 接口扩展

```python
def search_database(
    db_path, query, limit=8, doc_types=None, addon=None,
    expand_graph=True,  # 新参数
) -> List[SearchResult]:
```

### 遍历逻辑

```python
# 1. 现有 4 层匹配 → 主结果集 (results dict)
# 2. 如果 expand_graph=True:
top_k = min(3, len(results))  # 对 top-3 做扩展
for result in results[:top_k]:
    # 查询关联 chunks
    related = conn.execute("""
        SELECT c.*, r.relation, r.weight
        FROM chunk_relations r
        JOIN chunks c ON c.id = r.target_id
        WHERE r.source_id = ?
        ORDER BY r.weight DESC
        LIMIT 5
    """, (result.id,)).fetchall()
    
    for rel in related:
        if rel['id'] not in results:
            results[rel['id']] = _make_result(
                rel,
                score=result['score'] * rel['weight'] * 0.5,  # 衰减
                relation_type=rel['relation'],
                distance=1,
            )
```

### SearchResult 扩展

```python
@dataclass(frozen=True)
class SearchResult:
    # 现有字段...
    relation_type: str = ''   # '' | 'parent' | 'inherits' | 'references' | 'see_also'
    distance: int = 0         # 0=主结果, 1=一跳关联
```

## 5. FTS 查询分词优化

### 现状

```python
"Node.add_child" → '"Node.add_child"'  # 整串匹配，FTS5 找不到
```

### 设计

对含 `.` 的查询拆 token：

```python
def _smart_tokenize(query: str) -> str:
    # "Node.add_child" → '"Node" AND "add" AND "child"'
    tokens = re.split(r'[._]', query)
    fts_tokens = []
    for t in tokens:
        if not t:
            continue
        if any(c in _FTS5_SPECIAL for c in t):
            fts_tokens.append(f'"{t.replace(chr(34), chr(34)+chr(34))}"')
        else:
            fts_tokens.append(t)
    return " AND ".join(fts_tokens) if fts_tokens else query
```

在 `search_database()` 的 FTS 查询部分，对原始 query 先尝试 `_smart_tokenize`，如果 FTS5 报错则回退到 `_escape_fts5`。

## 6. 分数体系统一

### 问题

符号层(100/80/40)和 FTS 层(0-40)有断层，FTS 最高分(40)刚好等于符号最低分(40)。

### 设计

保持现有分层不变，但图谱引入后，关联结果用衰减公式：

```
关联分数 = 主结果分数 × relation_weight × 0.5
```

其中 `relation_weight`:
- parent: 1.0
- inherits: 0.8
- references: 0.5
- see_also: 0.3

这确保关联结果不会超过主结果，但仍然排在有意义的位置。

## 实施顺序

1. Phase 1: symbols.py normalize + store.py BM25 公式 → 独立可测
2. Phase 2: models.py 新增字段 + chunker.py parent_symbol + store.py 建图
3. Phase 3: store.py 图谱遍历 + FTS 分词 + CLI 扩展
