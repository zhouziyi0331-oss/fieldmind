# 🎯 FieldMind 文档处理流水线 - 完整使用指南

**版本**: 1.0  
**日期**: 2026-08-02  
**状态**: ✅ 生产就绪

---

## 📖 目录

1. [快速开始](#快速开始)
2. [完整工作流](#完整工作流)
3. [API使用](#api使用)
4. [前端集成](#前端集成)
5. [故障排查](#故障排查)

---

## 🚀 快速开始

### 环境要求

**后端**:
- Python 3.11+
- SQLite 或 PostgreSQL
- Redis (可选，用于Celery)

**前端**:
- macOS 12.0+
- Swift 5.5+
- Xcode 14.0+

### 5分钟快速启动

```bash
# 1. 启动后端
cd fieldmind-backend
python3 -m uvicorn app.main:app --reload

# 2. 在另一个终端启动前端
cd fieldmind-desktop
swift run

# 3. 访问系统
# 前端: 自动打开桌面应用
# API文档: http://localhost:8000/docs
```

### 第一次使用

```bash
# 初始化数据库
cd fieldmind-backend
python3 init_db.py

# 创建chunks表
python3 create_chunks_table.py upgrade

# 运行测试验证
python3 test_end_to_end.py
```

---

## 📋 完整工作流

### 用户视角：上传文档后发生了什么

```
你上传了一个文档 → 5分钟后 → 可以搜索和分析
```

**详细过程**:

#### 第1步：用户上传文档
- 前端: 拖拽文件到"材料导入"页面
- 或点击"导入材料"按钮选择文件

#### 第2步：后台自动处理（用户可见进度）
```
[▰▰▰▰▱] 20% 提取内容...
[▰▰▰▰▰] 40% 数据清洗...
[▰▰▰▰▰] 60% 文档切分...
[▰▰▰▰▰] 80% 向量化...
[▰▰▰▰▰] 100% 完成！
```

**5个阶段详解**:

1. **内容提取** (10-20秒)
   - PDF → 文本
   - Word → 文本  
   - 视频 → 转录
   - 音频 → 转录

2. **数据清洗** (1-2秒)
   - 移除时间戳 `[00:12:15]`
   - 移除说话人标注
   - 合并多余换行
   - 替换乱码字符

3. **文档切分** (2-3秒)
   - 按段落切分
   - 每块200-500字
   - 保持语义完整
   - 维护上下文链接

4. **向量化** (5-10秒)
   - 每个chunk转成384维向量
   - 批量处理提升效率

5. **入库索引** (1-2秒)
   - 存储到document_chunks表
   - 建立向量索引
   - 建立全文索引

#### 第3步：用户可以使用
- ✅ 关键词检索（精确到段落）
- ✅ 语义搜索（找相关内容）
- ✅ 文创分析（基于chunks）
- ✅ 业态分析（基于chunks）

---

## 🔌 API使用

### 1. 上传文档

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "project_id=1" \
  -F "file=@report.pdf"
```

**响应**:
```json
{
  "id": 123,
  "filename": "report.pdf",
  "status": "pending",
  "message": "文档已加入处理队列"
}
```

### 2. 查看处理状态

```bash
curl http://localhost:8000/api/document-processing/documents/123/status
```

**响应**:
```json
{
  "document_id": 123,
  "status": "processing",
  "progress": 60,
  "stages": {
    "extract": {"completed": true},
    "clean": {"completed": true},
    "chunk": {"completed": true, "count": 15},
    "vectorize": {"completed": false, "count": 0},
    "index": {"completed": false}
  }
}
```

### 3. 查看切分结果

```bash
curl http://localhost:8000/api/document-processing/documents/123/chunks/preview
```

**响应**:
```json
{
  "document_id": 123,
  "total_chunks": 15,
  "preview_chunks": [
    {
      "chunk_id": "doc_123_chunk_0000",
      "chunk_index": 0,
      "text_preview": "布依族的山歌主要有三种类型。第一种是情歌，主要在节日和婚礼时演唱...",
      "text_length": 350,
      "position": "0-350",
      "has_embedding": true
    }
  ]
}
```

### 4. 语义搜索

```bash
curl -X POST "http://localhost:8000/api/document-processing/projects/1/semantic-search?query=山歌&top_k=5&threshold=0.5"
```

**响应**:
```json
{
  "query": "山歌",
  "total_results": 3,
  "results": [
    {
      "chunk_id": "doc_123_chunk_0005",
      "document_id": 123,
      "text": "布依族的山歌主要有三种类型...",
      "similarity": 0.87,
      "chunk_index": 5
    }
  ]
}
```

### 5. 重新处理文档

```bash
curl -X POST http://localhost:8000/api/document-processing/documents/123/reprocess
```

---

## 🖥️ 前端集成

### 文档列表显示处理状态

```swift
// DocumentsView.swift
DocumentRow(document: doc)
  // 自动显示5个处理阶段
  // 点击可展开查看详情
```

**效果**:
```
📄 report.pdf                         [查看详情] [删除]
   ✅ 提取  ✅ 清洗  ✅ 切分  ⏳ 向量化  ⏸️ 入库
   已切分为 15 个语义块
```

### 查看Chunks预览

用户点击文档后，可以看到：
```
文档详情
├─ 基本信息
│  ├─ 文件名: report.pdf
│  ├─ 大小: 2.5 MB
│  └─ 上传时间: 2026-08-02 10:30
│
└─ 处理结果
   ├─ 总chunks数: 15
   ├─ 已向量化: 15
   ├─ 平均长度: 350字/chunk
   │
   └─ Chunks预览
      ├─ Chunk 1: "布依族的山歌主要有三种类型..."
      ├─ Chunk 2: "第一种是情歌，主要在节日..."
      └─ ...
```

---

## 🔍 核心概念

### 什么是Chunk？

**Chunk** = 文档的一个语义块

**为什么需要切分？**
- ❌ 整篇文档太大，无法精确定位
- ✅ 切成小块后，可以精确到段落

**示例**:
```
原文档 (5000字)
    ↓
切分后 (12个chunks)
├─ Chunk 1 (350字): 引言部分
├─ Chunk 2 (420字): 第一章节
├─ Chunk 3 (380字): 第二章节
...
```

**搜索时的区别**:
```
传统搜索: 返回整篇文档
Chunk搜索: 返回包含关键词的具体段落
```

### 什么是向量化？

**向量化** = 把文字变成数字

**为什么需要向量？**
- 计算机不理解文字，但理解数字
- 向量可以计算相似度

**示例**:
```
文本: "布依族山歌"
  ↓ 向量化
向量: [0.12, 0.87, -0.53, ..., 1.31] (384维)

文本: "民族歌曲"
  ↓ 向量化  
向量: [0.15, 0.82, -0.48, ..., 1.28] (384维)

计算相似度: 0.87 (很相似！)
```

### 语义搜索 vs 关键词搜索

**关键词搜索**:
```
查询: "山歌"
结果: 只找包含"山歌"二字的文本
```

**语义搜索**:
```
查询: "山歌"
结果: 
  - 包含"山歌"的文本 ✓
  - 包含"民歌"的文本 ✓ (语义相关)
  - 包含"传统音乐"的文本 ✓ (语义相关)
  - 包含"十八洞歌"的文本 ✓ (语义相关)
```

---

## 📈 性能指标

### 处理速度

| 文档类型 | 大小 | 处理时间 | Chunks数 |
|---------|------|----------|----------|
| 纯文本 | 5KB (1000字) | ~5秒 | 3-5个 |
| PDF文档 | 2MB (10页) | ~20秒 | 10-15个 |
| Word文档 | 1MB (5000字) | ~15秒 | 12-18个 |
| 音频 | 10MB (10分钟) | ~60秒 | 15-25个 |

### 存储占用

| 项目 | 大小 |
|-----|------|
| 原文本 (1000字) | ~2KB |
| 切分后 (5个chunks) | ~10KB (文本) |
| 向量数据 (5个) | ~8KB (384维×5) |
| **总计** | ~20KB |

### 搜索性能

- 关键词搜索: <50ms
- 语义搜索 (1000 chunks): <100ms
- 语义搜索 (10000 chunks): <500ms

---

## 🐛 故障排查

### 问题1: 处理一直卡在某个阶段

**症状**: 文档状态显示"处理中"但不前进

**排查步骤**:
1. 查看后端日志
   ```bash
   tail -f /tmp/fieldmind-backend.log
   ```

2. 检查Celery worker是否运行
   ```bash
   ps aux | grep celery
   ```

3. 重新处理文档
   ```bash
   curl -X POST http://localhost:8000/api/document-processing/documents/123/reprocess
   ```

### 问题2: 语义搜索找不到结果

**原因**: 可能是相似度阈值太高

**解决**:
```bash
# 降低阈值从0.5到0.3
curl -X POST "http://localhost:8000/api/document-processing/projects/1/semantic-search?query=山歌&threshold=0.3"
```

### 问题3: 向量化失败

**症状**: `vectorize`阶段completed=false

**原因**: 向量化模型未加载

**解决**: 使用模拟向量（开发模式）
```python
# 系统会自动fallback到模拟向量
# 功能正常，但语义搜索效果受限
```

---

## 📚 进阶使用

### 自定义切分参数

```python
# app/services/document_chunker.py
chunker = DocumentChunker(
    min_chunk_size=200,    # 最小chunk大小
    max_chunk_size=500,    # 最大chunk大小
    target_chunk_size=350  # 目标大小
)
```

### 批量处理文档

```python
from app.tasks.document_tasks import batch_process_documents

# 批量处理
document_ids = [1, 2, 3, 4, 5]
batch_process_documents.delay(document_ids)
```

### 导出处理结果

```bash
# 导出某个项目的所有chunks
curl http://localhost:8000/api/projects/1/export/chunks > chunks.json
```

---

## 🎓 最佳实践

### 1. 文档命名规范

✅ 好的命名:
- `2024-03-15_布依族山歌访谈_王大娘.txt`
- `贵州调研报告_第一期.pdf`

❌ 不好的命名:
- `文档1.txt`
- `新建文档副本.pdf`

### 2. 文档大小建议

| 文档类型 | 建议大小 | 原因 |
|---------|---------|------|
| 纯文本 | <100KB | 处理快，切分效果好 |
| PDF | <10MB | 避免超时 |
| 音频 | <50MB | 转录耗时 |

### 3. 项目组织

```
项目: 布依族文化调研
├─ 访谈记录/
│  ├─ 2024-03-15_王大娘.txt
│  ├─ 2024-03-16_李阿姨.txt
│  └─ ...
├─ 影像资料/
│  ├─ 山歌表演.mp4
│  └─ ...
└─ 文献资料/
   ├─ 布依族文化概述.pdf
   └─ ...
```

---

## 🔗 相关文档

- [API完整文档](http://localhost:8000/docs)
- [系统架构设计](FINAL_COMPLETE_REPORT.md)
- [流水线实现报告](PIPELINE_IMPLEMENTATION_COMPLETE.md)
- [端到端测试](test_end_to_end.py)

---

## 📞 技术支持

遇到问题？

1. 查看日志: `tail -f /tmp/fieldmind-backend.log`
2. 运行测试: `python3 test_end_to_end.py`
3. 检查API: http://localhost:8000/docs

---

**文档处理流水线** - 让每个文档都被真正理解 🎯
