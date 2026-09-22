# FieldMind 系统当前状态和使用指南

生成时间: 2026-08-19 12:55

---

## ✅ 已修复的问题

### 1. 文档列表API修复
**问题：** API返回的chunk_count全是0，导致前端显示所有文档都未处理

**修复：** 
- 改为直接从`document_chunks`表查询实际chunk数量
- 使用SQL: `SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id`

**结果：**
```
✅ API现在返回正确的chunk_count
✅ 已处理文档: 10个（包括PDF 411 chunks）
⏳ 未处理文档: 7个（主要是音频文件处理失败）
```

### 2. 文档处理流程修复
**问题：** Celery依赖Redis，但Redis未安装，导致文档上传后不会被处理

**修复：** 
- 创建了同步处理模式 `process_document_sync()`
- 绕过Celery，直接在API中处理文档

**结果：**
- 可以手动调用API处理文档
- 处理流程完整：提取 → 清洗 → 分块 → 向量化 → 知识图谱

---

## 📊 当前系统状态

### 服务运行状态
```
✅ 后端API (FastAPI): http://localhost:8000
✅ 前端应用: /Applications/FieldMind.app
❌ Redis: 未安装
❌ Celery Worker: 未运行
```

### 文档处理统计（项目ID 17）
```
总文档数: 17
├── ✅ 已处理: 10个
│   ├── ID 1005: PDF (411 chunks) ← 成功处理大文件！
│   ├── ID 1004: DOCX (5 chunks)
│   ├── ID 1003: TXT (1 chunk)
│   ├── ID 1001: TXT (1 chunk)
│   └── ...
└── ❌ 未处理/失败: 7个
    └── 主要是音频文件 (.wav) - 音频转录功能未配置
```

---

## ⚠️ 已知问题和限制

### 1. word_count字段不准确
**现象：** 
- 万字文档显示11个字
- 一小时录音显示9个字

**原因：**
- `word_count`字段在上传时从文件名或元数据提取
- 文档处理完成后，这个字段没有更新

**影响：**
- 前端显示的字数统计不正确
- **但不影响实际功能** - chunks和向量已正确存储

**临时方案：**
- 使用`chunk_count > 0`判断文档是否已处理
- 忽略word_count字段

**长期修复：**
需要在文档处理完成后更新word_count字段：
```python
# 在process_document_sync()中添加
doc.word_count = len(extracted_text)
db.commit()
```

### 2. 文档上传后不会自动处理
**现象：** 
- 上传文档后，状态停留在"已上传"
- 需要手动调用API才会处理

**原因：**
- 上传API没有自动触发处理流程
- Celery异步处理未启用

**当前解决方案：**
手动调用处理API：
```bash
curl -X POST "http://localhost:8000/api/document-processing/documents/{document_id}/reprocess"
```

**需要的修复：**
在上传API中添加自动处理调用

### 3. 音频文件处理失败
**现象：** 
- 所有`.wav`文件status为"failed"
- 7个音频文件未能处理

**原因：**
- 音频转录需要Whisper服务
- Whisper API可能未配置或服务未启动

**检查：**
```bash
# 查看错误信息
curl "http://localhost:8000/api/documents/list/status?project_id=17" | jq '.[] | select(.file_type=="wav") | {id, filename, error_message}'
```

### 4. 文件管理器前端功能缺失
**问题：**
- 文件列表可能显示，但缺少操作按钮
- 没有"处理文档"、"删除"、"查看详情"等功能
- 前端可能还在调用旧的API路径

**需要的前端修改：**
1. 添加"处理文档"按钮
2. 添加批量处理功能
3. 显示处理进度
4. 更好的错误提示

---

## 🔧 如何使用当前系统

### 1. 查看所有文档状态
```bash
curl "http://localhost:8000/api/documents/list/status?project_id=17" | jq '.'
```

### 2. 手动处理单个文档
```bash
# 替换{document_id}为实际的文档ID
curl -X POST "http://localhost:8000/api/document-processing/documents/{document_id}/reprocess"
```

### 3. 批量处理所有未处理文档
```bash
# 运行批处理脚本
python3 << 'EOF'
import requests
import sqlite3

conn = sqlite3.connect('/Users/alwan/FieldMind/backend/src/data/fieldmind.db')
cursor = conn.cursor()

# 获取未处理的文档
cursor.execute("""
    SELECT id, filename 
    FROM project_documents 
    WHERE project_id = 17 
    AND status != 'failed'
    AND id NOT IN (SELECT DISTINCT document_id FROM document_chunks)
""")

docs = cursor.fetchall()
conn.close()

print(f"找到 {len(docs)} 个未处理文档")

for doc_id, filename in docs:
    print(f"处理文档 {doc_id}: {filename}...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/document-processing/documents/{doc_id}/reprocess",
            timeout=120
        )
        if response.status_code == 200:
            print(f"  ✅ 成功")
        else:
            print(f"  ❌ 失败: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
EOF
```

### 4. 查看文档的chunks
```bash
# 查看文档1004的所有chunks
sqlite3 /Users/alwan/FieldMind/backend/src/data/fieldmind.db << 'SQL'
SELECT 
    id,
    substr(content, 1, 50) as content_preview,
    length(content) as content_length
FROM document_chunks
WHERE document_id = 1004
LIMIT 5;
SQL
```

### 5. 测试语义搜索
```bash
curl -X POST "http://localhost:8000/api/document-processing/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "传播学",
    "project_id": 17,
    "top_k": 5
  }' | jq '.results[0:3]'
```

---

## 🚀 下一步需要完成的工作

### 优先级P0 - 必须修复

#### 1. 修复上传后自动处理
**位置：** `/Users/alwan/FieldMind/backend/src/app/api/v1/projects.py`

找到上传API并添加自动处理：
```python
@router.post("/{project_id}/documents")
async def upload_document(...):
    # ... 现有上传代码 ...
    
    # 添加自动处理
    try:
        from app.tasks.document_tasks import process_document_sync
        process_document_sync(new_document.id, db)
    except Exception as e:
        logger.error(f"自动处理失败: {e}")
        # 不影响上传结果
    
    return new_document
```

#### 2. 更新word_count字段
**位置：** `/Users/alwan/FieldMind/backend/src/app/services/document_processing_pipeline.py`

在处理完成后更新：
```python
# 在process_document()函数的最后
doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
if doc:
    # 统计所有chunks的总字数
    total_words = db.execute(
        text("SELECT SUM(LENGTH(content)) FROM document_chunks WHERE document_id = :doc_id"),
        {"doc_id": document_id}
    ).scalar() or 0
    
    doc.word_count = total_words
    db.commit()
```

#### 3. 前端添加"处理文档"功能
**位置：** 前端Swift代码

需要添加：
- 文档列表右键菜单 → "处理文档"
- 批量选择 + "批量处理"按钮
- 处理进度显示

### 优先级P1 - 重要改进

#### 4. 配置音频转录
检查Whisper配置：
```bash
grep -r "WHISPER\|transcribe" /Users/alwan/FieldMind/backend/src/app/core/config/
```

可能需要：
- 安装Whisper模型
- 配置API密钥
- 或使用本地Whisper服务

#### 5. 启用真正的异步处理
长期方案：
```bash
# 1. 安装Redis
brew install redis
brew services start redis

# 2. 重新启用Celery
# 恢复celery_app.py中的Redis broker配置

# 3. 启动Celery Worker
celery -A app.celery_app worker --loglevel=info
```

#### 6. 添加处理进度显示
在前端添加WebSocket连接，实时显示处理进度

### 优先级P2 - 优化改进

#### 7. 性能优化
- 大文件分批处理
- 并行处理多个文档
- 缓存向量查询结果

#### 8. 错误处理改进
- 更详细的错误信息
- 失败重试机制
- 用户友好的错误提示

#### 9. 文档管理功能
- 删除文档
- 重命名文档
- 文档详情页面
- 下载原文件

---

## 📝 快速启动脚本

创建一个启动脚本：
```bash
cat > /Users/alwan/start_fieldmind.sh << 'SCRIPT'
#!/bin/bash

echo "=== 启动FieldMind系统 ==="

# 1. 启动后端
cd /Users/alwan/FieldMind/backend
export DATABASE_URL="sqlite:////Users/alwan/FieldMind/backend/src/data/fieldmind.db"
export PYTHONPATH=/Users/alwan/FieldMind/backend/src

pkill -f "uvicorn.*app.main" 2>/dev/null
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

echo "✅ 后端API启动中..."
sleep 10

# 2. 启动前端
open /Applications/FieldMind.app

echo "✅ FieldMind应用已启动"
echo ""
echo "📊 系统信息:"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  后端日志: tail -f /tmp/backend.log"
echo ""
echo "✨ 系统已就绪！"
SCRIPT

chmod +x /Users/alwan/start_fieldmind.sh

echo "启动脚本已创建: /Users/alwan/start_fieldmind.sh"
```

使用方法：
```bash
/Users/alwan/start_fieldmind.sh
```

---

## 🐛 故障排查

### 问题：前端显示422错误
**检查：**
```bash
# 1. 确认后端运行
curl http://localhost:8000/health

# 2. 查看后端日志
tail -50 /tmp/backend.log | grep ERROR

# 3. 测试具体API
curl "http://localhost:8000/api/documents/list/status?project_id=17"
```

### 问题：文档处理失败
**检查：**
```bash
# 1. 查看错误信息
curl "http://localhost:8000/api/documents/list/status?project_id=17" | jq '.[] | select(.status=="failed")'

# 2. 查看后端日志
tail -100 /tmp/backend.log | grep -i "error\|exception"

# 3. 手动处理测试
curl -X POST "http://localhost:8000/api/document-processing/documents/1004/reprocess"
```

### 问题：文件管理器加载慢
**优化：**
- 当前API每次都查询chunk_count，对大量文档会慢
- 可以添加缓存或定期更新chunk_count字段到数据库

---

## 📞 总结

### 当前可用功能
✅ 文档上传
✅ 文档处理（手动触发）
✅ 文档列表查询
✅ 语义搜索
✅ 知识图谱

### 需要手动操作的
⚠️ 上传后需要手动处理文档
⚠️ 使用API或脚本批量处理

### 还不能用的
❌ 音频转录
❌ 自动异步处理
❌ 前端文档操作按钮

### 数据正确性
✅ chunks存储正确（已验证）
✅ 向量化正确（可以搜索）
❌ word_count显示不准（不影响使用）
