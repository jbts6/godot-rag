---
comet_change: semantic-search
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-27-semantic-search
status: final
---

# 语义搜索设计

## 概述

为 godot-rag 添加向量语义搜索能力，实现 FTS5 + 向量双路召回，RRF 融合排序。同时提取文档中的 `See also` 交叉引用，建立 see_also 关系。

## 技术方案

### 1. 向量生成

**组件**：model2vec (potion-base-8M)

**规格**：
- 向量维度：256
- 批处理大小：1000 个/批
- 进度显示：每 5 批输出一次

**实现**：
```python
def generate_embeddings(chunks: List[dict], batch_size: int = 1000) -> List[List[float]]:
    model = StaticModel.from_pretrained("minishlab/potion-base-8M")
    embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c['text'] for c in batch]
        batch_embeddings = model.encode(texts)
        embeddings.extend(batch_embeddings.tolist())
        
        if (i // batch_size) % 5 == 0:
            print(f"Generating embeddings... ({i+len(batch)}/{len(chunks)})")
    
    return embeddings
```

### 2. 向量存储

**组件**：sqlite-vec

**Schema**：
```sql
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[256]
);
```

**写入**：
```python
for i, embedding in enumerate(embeddings):
    conn.execute(
        "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
        (chunk_ids[i], str(embedding))
    )
```

### 3. see_also 关系提取

**正则**：`See also \`([^`]+)\``

**过滤条件**：
- 匹配到已注册符号（`sym_to_id`）
- 排除自引用

**权重**：0.6（介于 references 0.5 和 inherits 0.8 之间）

**实现**：
```python
SEE_ALSO_RE = re.compile(r'See also `([^`]+)`')

for row in rows:
    chunk_id, path, doc_type, chunk_type, symbol, parent_symbol, text = row
    matches = SEE_ALSO_RE.findall(text)
    for match in matches:
        target_norm = normalize_symbol(match)
        if target_norm and target_norm in sym_to_id and target_norm != normalize_symbol(symbol):
            target_id = sym_to_id[target_norm]
            conn.execute(
                "INSERT OR IGNORE INTO chunk_relations (source_id, target_id, relation, weight) VALUES (?, ?, 'see_also', 0.6)",
                (chunk_id, target_id)
            )
```

### 4. 向量搜索

**组件**：sqlite-vec KNN 查询

**实现**：
```python
def vector_search(conn, query_embedding: List[float], limit: int = 10) -> List[dict]:
    results = conn.execute("""
        SELECT chunk_id, distance
        FROM vec_chunks
        WHERE embedding MATCH ? AND k = ?
        ORDER BY distance
    """, (str(query_embedding), limit)).fetchall()
    
    return [{'id': row[0], 'distance': row[1]} for row in results]
```

### 5. RRF 融合排序

**公式**：`score = 1 / (k + rank)`，k=60

**融合范围**：FTS5 结果 + 向量结果，两路融合

**实现**：
```python
def rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]:
    scores = {}
    
    for rank, result in enumerate(fts_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)
    
    for rank, result in enumerate(vec_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)
    
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    results = []
    for chunk_id in sorted_ids:
        result = next((r for r in fts_results if r['id'] == chunk_id), None)
        if result is None:
            result = next((r for r in vec_results if r['id'] == chunk_id), None)
        if result:
            result['rrf_score'] = scores[chunk_id]
            results.append(result)
    
    return results
```

### 6. 搜索流程

```
用户查询
    ↓
┌───────────┬───────────┐
│  FTS5 搜索 │ 向量搜索   │
└─────┬─────┴─────┬─────┘
      │           │
      ▼           ▼
   FTS5 结果   向量结果
      │           │
      └─────┬─────┘
            ▼
      RRF 融合排序
            │
            ▼
    Graph Expansion
            │
            ▼
       最终结果
```

**集成**：
```python
def search_database(db_path: Path, query: str, limit: int = 8, ...) -> List[SearchResult]:
    with get_connection(db_path) as conn:
        # 1. FTS5 搜索
        fts_results = fts_search(conn, query, limit=limit*3)
        
        # 2. 向量搜索
        query_embedding = model.encode([query])[0]
        vec_results = vector_search(conn, query_embedding, limit=limit*3)
        
        # 3. RRF 融合
        fused_results = rrf_fusion(fts_results, vec_results)
        
        # 4. Graph expansion（融合后）
        if expand_graph:
            top_k = min(3, len(fused_results))
            expanded = graph_expand(conn, fused_results[:top_k])
            fused_results.extend(expanded)
        
        # 5. 排序并返回
        fused_results.sort(key=lambda x: x['rrf_score'], reverse=True)
        return fused_results[:limit]
```

## 数据库 Schema 变更

```sql
-- 新增向量表
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[256]
);

-- chunk_relations 表新增 see_also 类型
-- INSERT INTO chunk_relations (source_id, target_id, relation, weight)
-- VALUES (?, ?, 'see_also', 0.6);
```

## 依赖变更

```toml
[project]
dependencies = [
    # ... 现有依赖 ...
    "sqlite-vec>=0.1.9",
    "model2vec>=0.8.2",
]
```

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 向量生成性能 | 构建时间增加 | 分批处理，显示进度 |
| 模型首次加载 | 首次搜索延迟 | 缓存模型到本地 |
| 向量维度固定 | 表达能力受限 | 后续可升级模型 |

## 测试策略

1. **see_also 关系构建**：验证构建后 chunk_relations 表中 see_also 数量 ≥ 100
2. **向量搜索**：验证搜索 "how to make a button" 能返回语义相关结果
3. **RRF 融合**：验证融合结果优于单路搜索
4. **单元测试**：编写 see_also 关系构建、向量搜索、RRF 融合的单元测试
