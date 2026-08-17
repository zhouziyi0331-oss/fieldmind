# 外部工具集成文档

## 已安装工具

### 1. MarkItDown (已集成 ✅)

**用途**: 文档格式转换，将各种文档格式转换为Markdown

**GitHub**: https://github.com/microsoft/markitdown.git

**安装状态**: ✅ 已安装并集成到后端

**支持格式**:
- PDF (.pdf)
- Word (.docx, .doc)
- PowerPoint (.pptx, .ppt)
- Excel (.xlsx, .xls)
- HTML (.html, .htm)
- 文本格式 (.txt, .md, .csv, .json, .xml)

**集成位置**:
- `/Users/alwan/FieldMind-Rebuild/fieldmind-backend/app/services/document_converter.py` - 文档转换服务
- `/Users/alwan/FieldMind-Rebuild/fieldmind-backend/app/api/v1/project_documents.py` - 项目文档上传API（已更新）

**功能**:
1. 自动将上传的文档转换为Markdown格式
2. 提取文档元数据（标题、文件大小、格式等）
3. 从转换后的内容自动提取记忆条目
4. 支持多种文档格式的统一处理

**使用示例**:
```python
from app.services.document_converter import document_converter

# 转换文档
result = document_converter.convert_file("/path/to/document.pdf")
if result:
    markdown_text = result["text_content"]
    title = result["title"]
    metadata = result["metadata"]
```

---

### 2. RAGFlow (已克隆 ✅)

**用途**: RAG (Retrieval Augmented Generation) 系统，用于长记忆和文档检索

**GitHub**: https://github.com/infiniflow/ragflow.git

**安装状态**: ✅ 已成功克隆，已评估

**版本**: v0.26.4

**克隆位置**: `/Users/alwan/FieldMind-Rebuild/external-tools/ragflow/`

**详细文档**: [RAGFLOW_INTEGRATION_GUIDE.md](RAGFLOW_INTEGRATION_GUIDE.md)

**核心功能**:
1. 深度文档理解和知识提取
2. 模板化智能分块策略
3. 基于引用的回答（减少幻觉）
4. 多种文档格式支持（Word、PDF、Excel、图片等）
5. 向量检索和全文检索
6. Agent工作流和记忆系统
7. Python SDK (ragflow-sdk 0.26.4)

**计划集成方式**:
- **方案A**: 作为独立Docker服务部署（推荐）
- **方案B**: 使用Python SDK直接集成
- **方案C**: 混合方案 - RAGFlow处理复杂文档 + 本地MemoryService处理轻量级操作

**资源要求**:
- CPU >= 4核
- RAM >= 16GB
- 磁盘 >= 50GB
- Docker >= 24.0.0
- Python >= 3.13

**集成优先级**: 高 🔥

**下一步**:
- 本地部署RAGFlow Docker服务进行测试
- 评估文档解析质量
- 实现RAGFlowService包装类
- 与现有MemoryService集成

---

### 3. WeKnora (尝试克隆中)

**用途**: 知识图谱可视化，用于项目知识上下文的可视化

**GitHub**: https://github.com/Tencent/WeKnora.git

**安装状态**: ⏸️ 克隆超时，待重试

**计划用途**:
1. 可视化项目知识上下文层级关系
2. 展示实体和关键词之间的关联网络
3. 支持知识图谱的交互式探索
4. 集成到项目仪表板

**集成优先级**: 中 

---

### 4. Mind-Map (尝试克隆中)

**用途**: 思维导图可视化组件

**GitHub**: https://github.com/wanglin2/mind-map.git

**安装状态**: ⏸️ 克隆超时，待重试

**计划用途**:
1. 可视化项目结构和知识层次
2. 展示聊天对话的思维过程
3. 创建交互式知识地图
4. 集成到前端可视化界面

**集成优先级**: 中

---

## 其他评估的工具（未安装）

### Grist (gristlabs/grist-core)
**原因**: 数据库管理工具，与FieldMind的核心功能重叠度低

### Data-Analysis (WillKoehrsen/Data-Analysis)
**原因**: 示例和教程仓库，非生产级工具

### Apache Superset (apache/superset)
**原因**: 数据可视化平台，体积庞大，可作为备选但非必需

### Kubernetes Dashboard (kubernetes-retired/dashboard)
**原因**: 已废弃项目，且与FieldMind功能无关

### Reveal.js (hakimel/reveal.js)
**原因**: 演示文稿框架，与核心功能关联度低

### ONLYOFFICE DocumentServer (ONLYOFFICE/DocumentServer)
**原因**: 在线Office套件，体积庞大，MarkItDown已满足文档处理需求

### OfficeCLI (iOfficeAI/OfficeCLI)
**原因**: 仓库无法访问或不存在

### Obsidian Skills (kepano/obsidian-skills)
**原因**: Obsidian插件，非独立工具

---

## 集成计划

### 短期（已完成）✅
1. ✅ 安装和集成MarkItDown
2. ✅ 更新文档上传API以使用MarkItDown
3. ✅ 实现文档到Markdown的自动转换
4. ✅ 集成记忆提取功能

### 中期（待完成）
1. 🔄 完成RAGFlow的克隆和评估
2. 🔄 设计RAG系统的集成架构
3. 🔄 实现向量存储和检索API
4. 🔄 完成WeKnora和Mind-Map的克隆
5. 🔄 评估知识图谱可视化方案

### 长期
1. 集成WeKnora进行知识图谱可视化
2. 集成Mind-Map进行思维导图展示
3. 优化文档处理流水线
4. 实现完整的RAG增强对话系统

---

## 技术架构

```
FieldMind 架构
├── 文档处理层
│   └── MarkItDown (已集成) ✅
│       ├── 格式转换
│       ├── 元数据提取
│       └── Markdown生成
│
├── 记忆管理层
│   ├── 三层记忆架构 (已实现) ✅
│   └── RAGFlow (待集成) 🔄
│       ├── 向量存储
│       ├── 语义检索
│       └── 上下文增强
│
└── 可视化层
    ├── WeKnora (待集成) ⏸️
    │   └── 知识图谱
    └── Mind-Map (待集成) ⏸️
        └── 思维导图
```

---

## 性能优化建议

1. **文档处理**: MarkItDown已同步集成，考虑后续添加异步任务队列（Celery）
2. **向量检索**: RAGFlow集成时需要配置独立的向量数据库（如ChromaDB或FAISS）
3. **可视化**: 前端可视化组件应按需加载，避免影响首页加载速度

---

## 维护说明

- 定期检查外部工具的更新和安全补丁
- 监控文档转换的成功率和性能
- 记录集成过程中遇到的问题和解决方案
- 保持文档与实际实现的同步

---

**创建时间**: 2026-07-31  
**最后更新**: 2026-07-31  
**维护者**: FieldMind开发团队
