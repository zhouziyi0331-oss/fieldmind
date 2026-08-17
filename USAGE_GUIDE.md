# FieldMind 项目隔离系统 - 使用指南

## 🎉 系统状态

✅ **后端核心功能已完成并测试通过**

所有测试项目：
- ✅ 数据模型导入
- ✅ 数据库初始化
- ✅ 项目创建
- ✅ 文档上传
- ✅ 三层记忆系统
- ✅ 对话会话
- ✅ 知识脉络层级

## 🚀 快速开始

### 1. 启动后端服务器

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
./start.sh
```

服务器将在 http://localhost:8000 启动

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 2. 测试项目系统

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 test_project_system.py
```

这将创建一个测试项目，包含文档、记忆、对话和知识脉络。

## 📚 API 使用示例

### 创建项目

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "杭州西溪湿地调查",
    "description": "2024年秋季田野调查项目"
  }'
```

响应：
```json
{
  "id": 1,
  "name": "杭州西溪湿地调查",
  "description": "2024年秋季田野调查项目",
  "document_count": 0,
  "context_count": 0,
  "chat_session_count": 0,
  "status": "active",
  "created_at": "2024-07-30T10:00:00"
}
```

### 列出所有项目

```bash
curl http://localhost:8000/api/v1/projects/
```

### 获取项目详情

```bash
curl http://localhost:8000/api/v1/projects/1
```

### 上传文档到项目

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/documents/upload \
  -F "file=@interview_notes.txt"
```

### 创建知识脉络

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/contexts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "社会关系网络",
    "description": "分析村落中的社会关系结构",
    "level": 1,
    "keywords": ["社会关系", "网络", "结构"]
  }'
```

### 创建对话会话

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/chat-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "访谈分析对话",
    "document_ids": [1, 2, 3],
    "config": {
      "use_long_memory": true,
      "use_deep_thinking": true,
      "skill_name": "fxt-differential"
    }
  }'
```

### 发送对话消息

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/chat-sessions/1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请使用差序格局理论分析文档中的社会关系",
    "use_long_memory": true,
    "use_deep_thinking": true,
    "framework": "fxt-differential"
  }'
```

响应包含：
```json
{
  "id": 1,
  "role": "assistant",
  "content": "根据差序格局理论分析...",
  "thinking_process": "思考过程：首先...",
  "sources": [
    {
      "document_id": 1,
      "relevance_score": 0.95
    }
  ],
  "extra_data": {
    "model": "claude-3-7-sonnet-20250219",
    "input_tokens": 1200,
    "output_tokens": 800
  }
}
```

### 获取项目数据看板

```bash
curl http://localhost:8000/api/v1/projects/1/dashboard
```

### 查看项目记忆

```bash
curl http://localhost:8000/api/v1/projects/1/memories?memory_type=long_term
```

## 🏗️ 系统架构

### 项目隔离

每个项目是完全独立的研究单元：

```
Project (项目)
├── Documents (文档)
│   ├── 文本内容
│   ├── 向量索引
│   └── 实体/关键词
├── Contexts (知识脉络)
│   ├── Level 1 (主题)
│   ├── Level 2 (子主题)
│   └── Level 3 (细节)
├── Chat Sessions (对话会话)
│   ├── 配置 (长记忆/深度思考)
│   └── Messages (消息历史)
└── Memories (三层记忆)
    ├── Short-term (短期)
    ├── Mid-term (中期)
    └── Long-term (长期)
```

### 三层记忆系统

```
📝 Short-term Memory (短期记忆)
   - 最近 7 天的对话和文档
   - 快速访问
   - 定期清理

🧠 Mid-term Memory (中期记忆)
   - 1 个月内的重要概念
   - 访问次数 ≥ 5 自动提升
   - 中等保留期

💎 Long-term Memory (长期记忆)
   - 核心知识和概念
   - 访问次数 ≥ 10 自动提升
   - 永久保存
```

### 增强对话流程

```
用户消息
    ↓
检索长记忆 (三层)
    ↓
检索相关文档 (RAG)
    ↓
应用分析框架 (差序格局/仪式过程/熟人社会)
    ↓
调用 Claude API
    ├── 标准模式: claude-3-5-sonnet
    └── 深度思考: claude-3-7-sonnet (扩展思考)
    ↓
返回回复 + 思考过程 + 来源引用
    ↓
自动提取记忆
```

## 📊 支持的分析框架

### 1. 差序格局 (fxt-differential)

费孝通的经典理论，分析中国社会关系的层次结构：
- 核心圈层：家庭、亲属
- 次级圈层：朋友、熟人
- 外围圈层：陌生人

### 2. 仪式过程 (fxt-ritual)

Victor Turner 的仪式分析框架：
- 分离阶段
- 过渡阶段（边缘状态）
- 整合阶段

### 3. 熟人社会 (fxt-acquaintance)

分析熟人关系网络：
- 信任基础：血缘、地缘、业缘
- 互惠机制：人情往来
- 社会资本

## 🔧 配置

### 环境变量

创建 `.env` 文件：

```env
# 数据库
DATABASE_URL=sqlite:///./fieldmind.db

# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# 上传目录
UPLOAD_DIR=/tmp/fieldmind_uploads

# 服务器
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 项目配置示例

```json
{
  "default_language": "zh",
  "analysis_frameworks": [
    "fxt-differential",
    "fxt-ritual"
  ],
  "auto_vectorization": true,
  "auto_entity_extraction": true,
  "memory_config": {
    "short_term_days": 7,
    "mid_term_days": 30,
    "consolidation_threshold": 5
  }
}
```

### 对话会话配置

```json
{
  "use_long_memory": true,
  "use_deep_thinking": true,
  "skill_name": "fxt-differential",
  "memory_search_depth": 10,
  "framework": "fxt-differential"
}
```

## 📝 数据库模式

查看完整的数据库模式：

```bash
sqlite3 fieldmind.db
.schema projects
.schema project_documents
.schema project_contexts
.schema project_chat_sessions
.schema project_chat_messages
.schema project_memories
```

## 🧪 测试

运行完整测试套件：

```bash
python3 test_project_system.py
```

测试包括：
1. 数据模型导入
2. 数据库初始化
3. 项目 CRUD
4. 文档上传
5. 三层记忆系统
6. 对话会话
7. 知识脉络层级

## 📦 依赖

主要依赖：
- FastAPI
- SQLAlchemy
- Pydantic
- Anthropic (Claude API)
- Uvicorn

查看 `requirements.txt` 获取完整列表。

## 🐛 故障排除

### 数据库错误

```bash
# 删除并重新创建数据库
rm fieldmind.db
python3 -c "from app.core.database import init_db; init_db()"
```

### API Key 未设置

确保设置了环境变量：
```bash
export ANTHROPIC_API_KEY=your_key_here
```

或在 `.env` 文件中配置。

### 导入错误

确保在正确的目录：
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
```

## 🎯 下一步

### 后端

- [ ] 集成 ChromaDB/FAISS 向量检索
- [ ] 实现文档处理管道（PDF、DOCX）
- [ ] 添加后台任务队列（Celery）
- [ ] 实现用户权限系统

### 前端

- [ ] 更新 APIService.swift 使用新的项目 API
- [ ] 实现真正的项目切换逻辑
- [ ] 创建文档上传界面
- [ ] 实现增强对话界面（长记忆、深度思考）
- [ ] 可视化知识脉络
- [ ] 数据看板展示

## 📖 相关文档

- [项目隔离后端摘要](PROJECT_ISOLATION_BACKEND_SUMMARY.md)
- [API 文档](http://localhost:8000/docs) (启动服务器后访问)

## 💡 提示

1. **项目隔离**：每个项目的数据完全独立，删除项目会删除所有关联数据
2. **记忆管理**：系统自动管理三层记忆，高频访问的记忆会自动提升
3. **深度思考**：使用 `use_deep_thinking: true` 可以看到 AI 的思考过程
4. **框架分析**：选择合适的分析框架可以获得更专业的分析结果

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

---

**版本**: 1.0.0  
**最后更新**: 2026-07-30  
**状态**: ✅ 后端核心功能完成
