# Brainstorm Summary

- Change: semantic-search
- Date: 2026-06-27

## 确认的技术方案

1. **向量生成**：使用 model2vec (potion-base-8M, 256 维) 批量生成向量，每批 1000 个，显示进度
2. **see_also 关系**：正则 `See also \`([^`]+)\`` 提取引用，只匹配已注册符号（约 190 个有效）
3. **RRF 融合**：FTS5 + 向量两路融合，k=60，融合后执行 graph expansion
4. **向量存储**：sqlite-vec 虚拟表 `vec_chunks`，chunk_id 主键，embedding float[256]

## 关键取舍与风险

- **向量生成性能**：28231 个 chunk 分 28 批处理，预计需要较长时间 → 分批处理，显示进度
- **model2vec 模型**：首次加载需要下载 → 缓存到本地
- **向量维度固定**：256 维可能限制表达能力 → 后续可升级模型

## 测试策略

- see_also 关系构建：验证构建后 chunk_relations 表中 see_also 数量 ≥ 100
- 向量搜索：验证搜索 "how to make a button" 能返回语义相关结果
- RRF 融合：验证融合结果优于单路搜索

## Spec Patch

无
