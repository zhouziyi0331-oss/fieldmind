# FieldMind Backend 快速启动指南

## 前置要求

- Python 3.9+
- PostgreSQL 14+
- 已安装 pip 和 virtualenv

## 1. 环境配置

### 1.1 创建虚拟环境

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 1.2 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3 配置环境变量

创建 `.env` 文件：

```bash
# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/fieldmind

# 向量化服务
VECTOR_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384

# 长记忆配置
LONG_MEMORY_ENABLED=true
SHORT_TERM_MESSAGE_COUNT=5
MID_TERM_DAYS=7
LONG_TERM_TOP_K=10
RELEVANCE_THRESHOLD=0.7

# 深度思考配置
EXTENDED_THINKING_MODEL=claude-3-7-sonnet-20250219
THINKING_BUDGET_TOKENS=10000

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 2. 数据库初始化

```bash
# 创建数据库
createdb fieldmind

# 运行迁移
alembic upgrade head
```

## 3. 启动服务

### 3.1 开发模式（带自动重载）

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.2 生产模式

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 4. 验证服务

### 4.1 健康检查

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 4.2 API文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 5. 测试增强对话功能

### 5.1 基础对话测试

```bash
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "message": "解释一下量子计算的基本原理",
    "project_id": 1,
    "use_long_memory": true,
    "use_deep_thinking": false
  }'
```

### 5.2 深度思考模式测试

```bash
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-002",
    "message": "设计一个高并发的分布式系统架构",
    "project_id": 1,
    "use_long_memory": true,
    "use_deep_thinking": true
  }'
```

### 5.3 技能模式测试

```bash
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-003",
    "message": "分析这段代码的性能瓶颈",
    "project_id": 1,
    "use_long_memory": true,
    "skill_config": {
      "skill_name": "code_review",
      "workflow_prompt": "你是一位资深代码审查专家，专注于性能优化和最佳实践..."
    }
  }'
```

### 5.4 记忆搜索测试

```bash
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "量子计算",
    "project_id": 1,
    "top_k": 5
  }'
```

### 5.5 流式响应测试

```bash
curl -X POST http://localhost:8000/api/v1/chat/enhanced/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-004",
    "message": "详细讲解机器学习的基本概念",
    "project_id": 1,
    "use_long_memory": true
  }'
```

## 6. 向量数据库初始化

### 6.1 导入文档到向量库

```bash
curl -X POST http://localhost:8000/api/v1/documents/vectorize \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "document_ids": [1, 2, 3]
  }'
```

### 6.2 批量向量化

```bash
curl -X POST http://localhost:8000/api/v1/vectorization/batch \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "force_reindex": false
  }'
```

## 7. 记忆统计查询

```bash
curl http://localhost:8000/api/v1/memory/statistics?project_id=1
```

预期响应：
```json
{
  "short_term_count": 5,
  "mid_term_count": 23,
  "long_term_count": 156,
  "total_vectors": 184,
  "avg_relevance_score": 0.82
}
```

## 8. 监控与日志

### 8.1 查看实时日志

```bash
tail -f logs/fieldmind.log
```

### 8.2 性能监控

使用 `/api/v1/metrics` 端点查看性能指标：

```bash
curl http://localhost:8000/api/v1/metrics
```

## 9. 常见问题

### Q: Anthropic API 调用失败
**A:** 检查 `.env` 中的 `ANTHROPIC_API_KEY` 是否正确，并确认账户有足够余额。

### Q: 向量化速度慢
**A:** 首次加载 `sentence-transformers` 模型需要下载，约 90MB。后续调用会使用缓存。

### Q: 数据库连接失败
**A:** 确认 PostgreSQL 服务运行中，并检查 `DATABASE_URL` 配置。

### Q: 记忆检索结果为空
**A:** 确保已执行文档向量化步骤，并检查 `RELEVANCE_THRESHOLD` 是否过高。

## 10. 下一步

1. **配置技能模板** - 在 `app/config/skills.yaml` 中定义领域专用技能
2. **优化记忆策略** - 根据实际使用调整记忆配置参数
3. **集成前端应用** - 启动 FieldMind macOS 应用进行完整测试
4. **生产部署** - 配置 Nginx、SSL 证书、负载均衡等

## 技术支持

- 文档: `/Users/alwan/Desktop/FieldMindApp/LONG_MEMORY_COMPLETE.md`
- API 参考: http://localhost:8000/docs
- 架构说明: `/Users/alwan/Desktop/FieldMindApp/LONG_MEMORY_IMPLEMENTATION.md`
