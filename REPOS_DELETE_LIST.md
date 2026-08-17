# 建议删除的第三方项目清单

**生成时间**: 2026-08-09  
**当前 repos/ 总大小**: 约 890M

---

## ❌ 建议删除的项目（8个，约 379M）

### 1. **ragflow** (109M) - RAG 框架重复
- **原因**: 功能与现有 RAG 系统重复
- **说明**: FieldMind 已经有完整的 RAG 实现（Milvus + 向量检索）
- **可删除**: ✅ 是

### 2. **rawgraphs-app** (15M) - 图表工具，非核心
- **原因**: 数据可视化工具，与 FieldMind 核心功能无关
- **说明**: 前端已有 Chart.js，不需要额外的图表库
- **可删除**: ✅ 是

### 3. **nvd3** (7.7M) - 图表库重复
- **原因**: D3.js 图表库，功能重复
- **说明**: 前端已有 Chart.js，不需要额外的 D3 封装
- **可删除**: ✅ 是

### 4. **pyhanlp** (880K) - HanLP Python 绑定，有 HanLP 就够
- **原因**: 如果已有 HanLP (5.4M)，不需要重复的 Python 绑定
- **说明**: HanLP 本身就支持 Python
- **可删除**: ✅ 是

### 5. **gecco** (868K) - 爬虫框架重复
- **原因**: 已有 crawl4ai (29M) 和 firecrawl (53M)
- **说明**: 功能重复，保留更强大的 crawl4ai
- **可删除**: ✅ 是

### 6. **duckdb** (4K) - 仅占位符
- **原因**: 只有 4KB，可能是空目录或文档
- **说明**: 如需 DuckDB，应该用 pip 安装，不需要源码
- **可删除**: ✅ 是

### 7. **Pillow** (4K) - 仅占位符
- **原因**: 只有 4KB，Pillow 应该通过 pip 安装
- **说明**: Python 图像库，不需要源码
- **可删除**: ✅ 是

### 8. **codebase-memory-mcp** (0B) - 空目录
- **原因**: 空目录
- **可删除**: ✅ 是

---

## 🤔 可选删除（参考资料，245M）

这些是**文档/资源类**项目，不是代码库：

### 9. **awesome-knowledge-graph** (185M) - 学习资料
- **类型**: 知识图谱学习资源合集
- **价值**: 参考价值，但不是功能代码
- **建议**: 如果不需要学习资料，可以删除
- **可删除**: 🟡 可选

### 10. **funNLP** (160M) - NLP 工具资源合集
- **类型**: 中文 NLP 工具和资源列表
- **价值**: 参考价值，但不是功能代码
- **建议**: 如果不需要学习资料，可以删除
- **可删除**: 🟡 可选

### 11. **awesome-pretrained-chinese-nlp-models** (764K) - 模型列表
- **类型**: 预训练模型列表和文档
- **价值**: 参考价值
- **建议**: 可删除
- **可删除**: 🟡 可选

### 12. **dialect-preservation-fieldwork-minutes** (4K) - 会议记录
- **类型**: 可能是田野考察会议记录
- **价值**: 不清楚
- **建议**: 检查后决定
- **可删除**: 🟡 可选

---

## 📊 删除统计

### 方案 A: 仅删除明确无用的（推荐）
```
删除 8 个项目:
- ragflow (109M)
- rawgraphs-app (15M)
- nvd3 (7.7M)
- pyhanlp (880K)
- gecco (868K)
- duckdb (4K)
- Pillow (4K)
- codebase-memory-mcp (0B)

总释放: ~133M
```

### 方案 B: 包含参考资料
```
删除 12 个项目:
- 方案 A 的 8 个 (133M)
- awesome-knowledge-graph (185M)
- funNLP (160M)
- awesome-pretrained-chinese-nlp-models (764K)
- dialect-preservation-fieldwork-minutes (4K)

总释放: ~479M
```

---

## 🎯 我的推荐

### 推荐：方案 A（删除 8 个，释放 133M）

**立即删除这 8 个项目**：

```bash
cd ~/FieldMind/repos

# 删除功能重复的项目
rm -rf ragflow          # 109M - RAG 重复
rm -rf rawgraphs-app    # 15M - 图表工具
rm -rf nvd3             # 7.7M - 图表库重复
rm -rf pyhanlp          # 880K - HanLP 重复
rm -rf gecco            # 868K - 爬虫重复

# 删除占位符/空目录
rm -rf duckdb           # 4K - 占位符
rm -rf Pillow           # 4K - 占位符
rm -rf codebase-memory-mcp  # 0B - 空目录

echo "✅ 已释放约 133MB"
```

### 可选：方案 B（额外删除学习资料，再释放 346M）

如果你**不需要这些学习资料**，可以继续删除：

```bash
cd ~/FieldMind/repos

# 删除学习资料（可选）
rm -rf awesome-knowledge-graph              # 185M
rm -rf funNLP                               # 160M
rm -rf awesome-pretrained-chinese-nlp-models # 764K
rm -rf dialect-preservation-fieldwork-minutes # 4K

echo "✅ 额外释放约 346MB"
```

---

## ⚠️ 保留的重要项目（28个）

这些**必须保留**，是 FieldMind 的核心功能：

### 🔴 已集成或即将集成（11个）
1. **crawl4ai** (29M) - ✅ 已部分集成
2. **mem0** (36M) - ✅ 已集成
3. **mind-map** (21M) - ✅ 已部分集成
4. **cognee** (96M) - 🔜 即将集成
5. **graphrag** (19M) - 🔜 即将集成
6. **khoj** (83M) - 🔜 即将集成
7. **firecrawl** (53M) - 🔜 爬虫增强
8. **graphiti** (22M) - 🔜 图谱可视化
9. **LightRAG** (22M) - 🔜 RAG 优化
10. **neo4j-knowledge-graph-builder** (18M) - 🔜 图谱工具
11. **Neo4j-KGBuilder** (3.7M) - 🔜 图谱工具

### 🟡 工具类（6个）
12. **HanLP** (5.4M) - 中文 NLP
13. **markitdown** (24M) - 文档转换
14. **PDF-Guru** (1.8M) - PDF 处理
15. **browser-use** (9M) - 浏览器自动化
16. **markdown-nice** (1.8M) - Markdown 编辑
17. **exif-reader** (1.3M) - EXIF 读取

### 🟢 备选（1个）
18. **quivr** (11M) - RAG 系统（功能强大但可能重复）
19. **file-transfer-go** (2.2M) - 文件传输

---

## 🚀 执行建议

**第一步：立即删除方案 A（8个项目）**

```bash
cd ~/FieldMind/repos && rm -rf ragflow rawgraphs-app nvd3 pyhanlp gecco duckdb Pillow codebase-memory-mcp
```

**第二步：评估学习资料**

检查这些目录的内容：
```bash
ls -la awesome-knowledge-graph/
ls -la funNLP/
```

如果确认是学习资料，可以删除。

**第三步：验证**

```bash
cd ~/FieldMind/repos
du -sh .
ls -la
```

---

## 你想怎么做？

1. **方案 A** - 删除 8 个明确无用的（释放 133M）✅ 推荐
2. **方案 B** - 同时删除学习资料（释放 479M）
3. **手动选择** - 告诉我具体删哪些
4. **先看看内容** - 我帮你检查这些目录里有什么

请告诉我你的选择！
