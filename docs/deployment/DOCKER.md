# FieldMind Docker 部署指南

## 🚀 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+

### 一键启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd fieldmind

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要配置（特别是 ANTHROPIC_API_KEY）

# 3. 启动服务
chmod +x start.sh
./start.sh
```

服务将在以下端口启动：
- **前端**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474

---

## 📦 服务架构

```
┌─────────────┐
│   Nginx     │  前端静态文件 + API代理
│   (80)      │
└──────┬──────┘
       │
       ↓ /api/*
┌─────────────┐
│  FastAPI    │  后端API服务
│  (8000)     │
└──────┬──────┘
       │
       ├──→ PostgreSQL (5432)  主数据库
       ├──→ Redis (6379)        缓存 + 任务队列
       └──→ Neo4j (7687)        知识图谱
```

---

## 🔧 Docker Compose 服务

### 服务列表

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `frontend` | node:18 + nginx | 80 | React前端 |
| `backend` | python:3.11 | 8000 | FastAPI后端 |
| `db` | postgres:15 | 5432 | PostgreSQL数据库 |
| `redis` | redis:7 | 6379 | Redis缓存 |
| `neo4j` | neo4j:5.14 | 7474, 7687 | Neo4j图数据库 |

### 启动所有服务

```bash
docker-compose up -d
```

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 停止服务

```bash
docker-compose down
```

### 停止并删除数据卷

```bash
docker-compose down -v
```

---

## 🔑 环境变量配置

关键配置项（`.env`文件）：

```bash
# 必需配置
SECRET_KEY=<至少32字符的随机字符串>
JWT_SECRET_KEY=<至少32字符的随机字符串>
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 数据库配置（Docker环境）
DATABASE_URL=postgresql://fieldmind:fieldmind_password@db:5432/fieldmind
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=fieldmind_password
REDIS_URL=redis://redis:6379/0
```

生成随机密钥：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🗄️ 数据持久化

数据存储在Docker卷中：

```bash
# 查看卷
docker volume ls | grep fieldmind

# 备份数据库
docker-compose exec db pg_dump -U fieldmind fieldmind > backup.sql

# 恢复数据库
docker-compose exec -T db psql -U fieldmind fieldmind < backup.sql
```

---

## 🐛 故障排查

### 后端无法启动

```bash
# 查看详细日志
docker-compose logs backend

# 进入容器调试
docker-compose exec backend bash
```

### 数据库连接失败

```bash
# 检查数据库健康状态
docker-compose ps db

# 测试数据库连接
docker-compose exec db psql -U fieldmind -c "SELECT 1"
```

### Neo4j连接失败

```bash
# 检查Neo4j状态
docker-compose logs neo4j

# 访问Neo4j浏览器
open http://localhost:7474
# 用户名: neo4j
# 密码: fieldmind_password
```

---

## 🔄 开发模式

如果需要在开发时实时更新代码：

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  backend:
    volumes:
      - ./app:/app/app
      - ./main_simple.py:/app/main_simple.py
    command: uvicorn main_simple:app --host 0.0.0.0 --port 8000 --reload
```

然后：
```bash
docker-compose up -d
```

---

## 📊 性能优化

### 生产环境建议

1. **使用多worker**
   ```yaml
   backend:
     command: gunicorn main_simple:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

2. **限制资源**
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 4G
   ```

3. **启用健康检查**（已包含在docker-compose.yml中）

---

## 🔐 安全建议

1. ✅ 修改所有默认密码
2. ✅ 使用强随机SECRET_KEY
3. ✅ 不要提交.env文件到git
4. ✅ 生产环境使用HTTPS
5. ✅ 限制数据库端口仅内部访问
6. ✅ 定期备份数据

---

## 📚 更多命令

```bash
# 重启特定服务
docker-compose restart backend

# 查看资源占用
docker stats

# 清理未使用的镜像
docker system prune -a

# 更新镜像
docker-compose pull
docker-compose up -d --build
```
