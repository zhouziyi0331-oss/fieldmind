# FieldMind 完整工作流设计

**创建日期**: 2026-08-02  
**目标**: 建立系统化的工作流，让所有功能关联起来

---

## 🎯 核心理念

**FieldMind 不是功能的堆砌，而是一个完整的工作流系统**

---

## 📊 完整用户旅程

### 阶段 1：项目创建
```
用户进入系统
  ↓
仪表盘（Dashboard）
  ↓ 点击"创建项目"
项目创建弹窗
  ↓ 输入项目名称、描述
后端创建项目 → 返回项目 ID
  ↓ 自动跳转
项目主页（包含：上传区、统计、快捷入口）
```

**前端交互**:
- 创建按钮 → 弹出模态窗口
- 表单验证 → 提交
- 成功提示 → 自动跳转到新项目页

**后端处理**:
- 创建 Project 记录
- 初始化项目目录
- 返回项目详情

---

### 阶段 2：材料上传（核心流程）

```
项目主页 - 上传区
  ↓ 拖拽文件/点击上传
文件上传（带进度条）
  ↓ 上传成功
后端接收文件
  ↓ 立即返回
  ├─ 文档记录创建（状态：processing）
  └─ 触发 Celery 异步任务
      ↓
      异步处理流程：
      ├─ 视频 → FFmpeg 提取音频 → Whisper 转写 → 存储 transcript
      ├─ 音频 → Whisper 转写 → 存储 transcript
      ├─ 文档 → MarkItDown 转换 → 存储 text
      ├─ 图片 → PaddleOCR 提取文字 → 存储 text
      └─ 网页 → Scrapy 抓取 → 存储 text
      ↓
      所有处理完成后：
      ├─ 提取关键词 → keywords 表
      ├─ 生成向量 → ChromaDB
      ├─ 提取实体 → Neo4j 知识图谱
      ├─ 识别时间点 → timeline 表
      └─ 更新文档状态 → completed
      ↓
      WebSocket 通知前端：
      "文档处理完成，请刷新数据"
```

**前端交互**:
1. **拖拽区域**
   - 拖拽文件 → 高亮显示
   - 松开 → 开始上传
   - 显示上传进度条

2. **上传列表**
   - 显示所有上传的文件
   - 实时状态：上传中 → 处理中 → 已完成
   - 点击文件 → 跳转到文档详情页

3. **实时通知**
   - WebSocket 连接
   - 收到"处理完成"消息
   - 自动刷新：统计数据、关键词列表、时间线

**后端处理**:
```python
# 1. 接收上传
@router.post("/upload")
async def upload_document():
    # 保存文件
    # 创建数据库记录（状态：processing）
    # 触发异步任务
    process_document.delay(document_id)
    return {"id": doc.id, "status": "processing"}

# 2. 异步处理任务
@celery_app.task
def process_document(document_id):
    # 根据文件类型调用不同处理器
    if is_video:
        audio = extract_audio(file_path)
        transcript = whisper.transcribe(audio)
        save_transcript(document_id, transcript)
    
    # 后续处理
    extract_keywords(document_id)
    generate_embeddings(document_id)
    extract_entities(document_id)
    extract_timeline(document_id)
    
    # 更新状态
    update_status(document_id, "completed")
    
    # 通知前端
    notify_frontend(project_id, "document_completed", document_id)
```

---

### 阶段 3：数据展示（自动更新）

上传处理完成后，**所有相关页面自动更新**：

#### 3.1 仪表盘（Dashboard）
```
自动更新：
  ├─ 文档数量
  ├─ 总字数
  ├─ 关键词数量
  ├─ 最新上传
  └─ 处理状态
```

#### 3.2 材料导入（Documents）
```
自动更新：
  ├─ 文档列表
  ├─ 状态标识
  └─ 点击文档 → 文档详情弹窗
      ├─ 文件信息
      ├─ 转写文本（如果是视频/音频）
      ├─ 提取的关键词
      └─ 操作：删除、重新处理
```

#### 3.3 关键词检索（KeywordSearch）
```
自动更新：
  ├─ Top 关键词列表（可点击）
  └─ 搜索框可以立即搜到新内容
  
搜索流程：
  输入"布依族" → 点击搜索
    ↓
  后端查询：
    ├─ 查 transcripts 表（视频/音频转写文本）
    ├─ 返回时间戳（00:03:25）
    └─ 返回上下文
    ↓
  前端展示：
    ├─ 视频1: 00:03:25 "布依族的山歌..."
    ├─ 点击"播放" → 弹出视频播放器
    └─ 自动跳转到 00:03:25
```

#### 3.4 编年史（Timeline）
```
自动更新：
  ├─ 从所有文档提取的时间点
  ├─ 按时间排序
  └─ 点击事件 → 跳转到相关文档
```

#### 3.5 关系图谱（Graph）
```
自动更新：
  ├─ 从 Neo4j 读取实体和关系
  ├─ D3.js 可视化
  └─ 点击节点 → 显示相关文档
```

---

### 阶段 4：智能分析（基于真实数据）

#### 4.1 关键词检索
```
前置条件：至少有 1 个文档处理完成

流程：
  输入关键词 → 搜索
    ↓
  后端：
    1. 查询 transcripts 表（视频/音频）
    2. 查询 documents 表（文档）
    3. 返回匹配结果 + 时间戳
    ↓
  前端：
    1. 展示结果列表
    2. 点击"播放" → 打开播放器
    3. 自动跳转到时间点
```

#### 4.2 文创分析
```
前置条件：至少有 5 个文档处理完成

流程：
  输入关键词 → 选择模式 → 开始分析
    ↓
  后端：
    1. 从数据库提取相关文档内容
    2. 构建上下文（最多 10,000 字）
    3. 调用 Claude Opus 5 API
    4. 返回分析结果
    ↓
  前端：
    1. 展示分析结果
    2. 可展开查看详情
    3. 导出报告
```

#### 4.3 业态分析
```
前置条件：至少有 3 个调研文档

流程：
  点击"开始分析"
    ↓
  后端：
    1. 提取所有项目文档
    2. 构建业态分析上下文
    3. 调用 Claude Opus 5 API
    4. 返回分析结果
    ↓
  前端：
    1. 展示现有业态
    2. 展示建议业态
    3. 展示协同效应
    4. 导出报告
```

---

## 🔄 关键工作流

### 工作流 1：文档处理流水线

```python
# Celery 任务链
@celery_app.task
def process_document_pipeline(document_id):
    """完整的文档处理流水线"""
    
    # 第 1 步：基础处理
    content = process_file(document_id)
    
    # 第 2 步：提取关键词
    keywords = extract_keywords(content)
    save_keywords(document_id, keywords)
    
    # 第 3 步：向量化
    embeddings = generate_embeddings(content)
    save_to_chromadb(document_id, embeddings)
    
    # 第 4 步：实体提取
    entities = extract_entities(content)
    save_to_neo4j(document_id, entities)
    
    # 第 5 步：时间线提取
    events = extract_timeline(content)
    save_timeline(document_id, events)
    
    # 第 6 步：更新统计
    update_project_stats(document_id)
    
    # 第 7 步：通知前端
    notify_frontend("document_completed", document_id)
```

### 工作流 2：实时数据同步

```javascript
// 前端 WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/ws')

ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    switch(message.type) {
        case 'document_completed':
            // 刷新文档列表
            refreshDocuments()
            // 刷新统计
            refreshStats()
            // 显示通知
            showNotification('文档处理完成')
            break
            
        case 'processing_progress':
            // 更新进度条
            updateProgress(message.progress)
            break
    }
}
```

### 工作流 3：页面联动

```javascript
// 页面之间的数据流转

// 仪表盘 → 文档详情
function onDocumentClick(documentId) {
    // 弹出详情窗口
    showDocumentDetail(documentId)
}

// 关键词 → 文档定位
function onKeywordClick(keyword) {
    // 跳转到关键词检索页
    navigateTo(`/keyword-search?q=${keyword}`)
}

// 搜索结果 → 视频播放
function onTimestampClick(videoId, timestamp) {
    // 打开视频播放器
    openVideoPlayer(videoId, timestamp)
}

// 知识图谱 → 相关文档
function onEntityClick(entityId) {
    // 显示相关文档侧边栏
    showRelatedDocuments(entityId)
}
```

---

## 🐛 需要修复的 Bug

### Bug 1：上传没反应
**原因**: 前端没有实现拖拽功能  
**修复**: 
```swift
// DocumentsView.swift
.onDrop(of: [.fileURL], isTargeted: $isTargeted) { providers in
    handleDrop(providers)
}
```

### Bug 2：点击按钮没反应
**原因**: 
1. 按钮没有绑定动作
2. 或者绑定了但是方法是空的

**修复**: 检查所有 `Button(action: {})` 确保有实际代码

### Bug 3：数据不更新
**原因**: 缺少 WebSocket 或轮询机制  
**修复**: 实现 WebSocket 实时通知

### Bug 4：页面不跳转
**原因**: 缺少导航逻辑  
**修复**: 实现 NavigationLink 或 `.sheet()` 弹窗

### Bug 5：后端返回模拟数据
**原因**: 
1. Whisper 没真实调用
2. Claude API 降级到模拟数据

**修复**: 
1. 确保 Celery 任务真实执行
2. 移除模拟数据逻辑

---

## ✅ 修复计划

### 第 1 步：后端工作流（2小时）
- [ ] 实现 Celery 异步任务
- [ ] 实现文档处理流水线
- [ ] 实现 WebSocket 通知
- [ ] 移除所有模拟数据

### 第 2 步：前端交互（2小时）
- [ ] 实现文件上传拖拽
- [ ] 实现 WebSocket 连接
- [ ] 实现页面跳转逻辑
- [ ] 实现弹窗交互

### 第 3 步：数据联动（1小时）
- [ ] 仪表盘自动刷新
- [ ] 文档列表实时更新
- [ ] 关键词搜索显示真实数据

### 第 4 步：端到端测试（1小时）
- [ ] 上传视频测试
- [ ] 关键词搜索测试
- [ ] 文创分析测试
- [ ] 完整流程验证

---

**总预计时间**: 6-8 小时  
**优先级**: 🔴 最高
