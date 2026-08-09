# FieldMind 系统完整部署指南

## 系统概述

FieldMind 是一个完整的田野调查智能分析系统，包含：
- **后端**: FastAPI + PostgreSQL + Celery（Python）
- **前端（Web）**: HTML + CSS + JavaScript 单页应用
- **前端（macOS）**: Swift + SwiftUI 原生应用

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      FieldMind 系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  Web 前端     │         │  macOS 应用   │                 │
│  │  (浏览器)     │         │  (原生 App)   │                 │
│  └───────┬──────┘         └───────┬──────┘                 │
│          │                         │                         │
│          └─────────┬───────────────┘                        │
│                    │                                         │
│              ┌─────▼─────┐                                  │
│              │  RESTful  │                                  │
│              │    API    │                                  │
│              └─────┬─────┘                                  │
│                    │                                         │
│         ┌──────────┼──────────┐                            │
│         │          │          │                             │
│    ┌────▼───┐ ┌───▼────┐ ┌──▼───┐                        │
│    │FastAPI │ │Celery  │ │Redis │                         │
│    │Backend │ │Worker  │ │Queue │                         │
│    └────┬───┘ └───┬────┘ └──────┘                        │
│         │         │                                         │
│    ┌────▼─────────▼────┐                                   │
│    │   PostgreSQL DB    │                                   │
│    └────────────────────┘                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 部署步骤

### 第一步：后端部署

#### 1.1 环境准备

```bash
# 安装 Python 依赖
cd ~/FieldMind-Rebuild
pip install -r requirements.txt

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 1.2 数据库配置

```bash
# 安装 PostgreSQL (如果使用)
brew install postgresql

# 启动 PostgreSQL
brew services start postgresql

# 创建数据库
createdb fieldmind

# 或者使用 SQLite (开发环境)
# 无需额外配置，自动创建 data/fieldmind.db
```

#### 1.3 环境变量配置

创建 `.env` 文件：
```bash
DATABASE_URL=postgresql://user:password@localhost/fieldmind
# 或使用 SQLite
# DATABASE_URL=sqlite:///./data/fieldmind.db

SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
REDIS_URL=redis://localhost:6379/0
```

#### 1.4 启动后端服务

```bash
# 使用快速启动脚本
./quick_start.sh

# 或手动启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端将运行在: `http://localhost:8000`

### 第二步：Web 前端部署

#### 2.1 启动 Web 服务器

```bash
cd ~/FieldMind-Rebuild/frontend
python3 -m http.server 8080
```

#### 2.2 访问 Web 应用

打开浏览器访问: `http://localhost:8080`

### 第三步：macOS 应用编译

#### 3.1 编译应用

```bash
cd ~/Desktop/FieldMindApp

# 调试模式编译
swift build

# 发布模式编译
swift build -c release
```

#### 3.2 运行应用

```bash
# 直接运行
swift run

# 或使用编译后的二进制
.build/debug/FieldMind
```

#### 3.3 创建 .app 包（可选）

使用 Xcode 打开并构建：
```bash
open Package.swift
```

然后在 Xcode 中：
1. Product → Archive
2. Distribute App → Copy App
3. 选择保存位置

## 完整的启动顺序

### 推荐启动顺序

1. **启动数据库** (PostgreSQL/SQLite)
2. **启动 Redis** (如果使用 Celery)
   ```bash
   brew services start redis
   ```
3. **启动后端服务**
   ```bash
   cd ~/FieldMind-Rebuild
   ./quick_start.sh
   ```
4. **启动前端** (选择一个)
   - Web 前端: `cd frontend && python3 -m http.server 8080`
   - macOS 应用: `cd ~/Desktop/FieldMindApp && swift run`

### 一键启动脚本

创建 `start_all.sh`:
```bash
#!/bin/bash

echo "🚀 启动 FieldMind 完整系统..."

# 启动 Redis
echo "📦 启动 Redis..."
brew services start redis

# 启动后端
echo "🔧 启动后端服务..."
cd ~/FieldMind-Rebuild
./quick_start.sh &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动 Web 前端
echo "🌐 启动 Web 前端..."
cd ~/FieldMind-Rebuild/frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!

echo "✅ 系统启动完成！"
echo ""
echo "后端 API: http://localhost:8000"
echo "Web 前端: http://localhost:8080"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "macOS 应用启动命令:"
echo "  cd ~/Desktop/FieldMindApp && swift run"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
```

## 系统验证

### 验证后端

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 查看 API 文档
open http://localhost:8000/docs
```

### 验证前端

```bash
# Web 前端
open http://localhost:8080

# macOS 应用
cd ~/Desktop/FieldMindApp
swift run
```

### 测试完整流程

1. 打开前端（Web 或 macOS）
2. 使用 `demo` / `demo123` 登录
3. 创建一个测试项目
4. 上传一个测试文档
5. 查看文档处理状态
6. 创建对话会话
7. 发送测试消息

## 性能配置

### 后端优化

编辑 `app/main.py`:
```python
# 生产环境配置
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # 工作进程数
        log_level="info"
    )
```

### 数据库优化

PostgreSQL 配置 (`postgresql.conf`):
```
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
```

### Celery 配置

启动多个 Worker:
```bash
celery -A app.celery_config worker --loglevel=info --concurrency=4
```

## 监控和日志

### 日志位置

- 后端日志: `logs/app.log`
- Celery 日志: `logs/celery.log`
- 前端日志: 浏览器控制台
- macOS 应用日志: 系统控制台

### 监控命令

```bash
# 查看后端日志
tail -f logs/app.log

# 查看 Celery 任务
celery -A app.celery_config inspect active

# 查看数据库连接
psql -d fieldmind -c "SELECT * FROM pg_stat_activity;"
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000
   lsof -i :8080
   
   # 终止进程
   kill -9 <PID>
   ```

2. **数据库连接失败**
   ```bash
   # 检查 PostgreSQL 状态
   brew services list
   
   # 重启 PostgreSQL
   brew services restart postgresql
   ```

3. **依赖安装失败**
   ```bash
   # 清理 pip 缓存
   pip cache purge
   
   # 重新安装
   pip install --no-cache-dir -r requirements.txt
   ```

4. **Swift 编译错误**
   ```bash
   # 清理构建缓存
   cd ~/Desktop/FieldMindApp
   swift package clean
   
   # 更新依赖
   swift package update
   
   # 重新编译
   swift build
   ```

### 性能问题

1. **后端响应慢**
   - 检查数据库查询是否优化
   - 增加 Celery Worker 数量
   - 使用 Redis 缓存

2. **文档处理慢**
   - 检查 Celery Worker 状态
   - 增加 Worker 并发数
   - 优化文档处理算法

3. **前端加载慢**
   - 使用 CDN 加载库文件
   - 压缩 CSS/JS 文件
   - 启用浏览器缓存

## 生产环境部署

### 使用 Docker 部署

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fieldmind
      POSTGRES_USER: fieldmind
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./data:/app/data
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://fieldmind:password@postgres/fieldmind
      REDIS_URL: redis://redis:6379/0

  celery:
    build: .
    command: celery -A app.celery_config worker --loglevel=info
    volumes:
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://fieldmind:password@postgres/fieldmind
      REDIS_URL: redis://redis:6379/0

volumes:
  postgres_data:
```

启动：
```bash
docker-compose up -d
```

### 使用 Nginx 反向代理

创建 `/etc/nginx/sites-available/fieldmind`:
```nginx
server {
    listen 80;
    server_name fieldmind.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 备份和恢复

### 数据库备份

```bash
# PostgreSQL 备份
pg_dump fieldmind > backup_$(date +%Y%m%d).sql

# 恢复
psql fieldmind < backup_20260730.sql
```

### 文件备份

```bash
# 备份数据目录
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/

# 恢复
tar -xzf data_backup_20260730.tar.gz
```

## 安全建议

1. **修改默认密码**
   - 更改演示账号密码
   - 使用强密码策略

2. **启用 HTTPS**
   - 使用 Let's Encrypt 证书
   - 配置 SSL/TLS

3. **API 限流**
   - 使用 Rate Limiting
   - 防止暴力攻击

4. **数据加密**
   - 数据库连接加密
   - 敏感数据字段加密

## 维护计划

- **每日**: 检查日志，监控性能
- **每周**: 数据库备份，清理临时文件
- **每月**: 更新依赖，安全补丁
- **每季度**: 系统升级，性能优化

## 技术支持

如有问题，请查看：
- 项目文档: `README.md`
- API 文档: `http://localhost:8000/docs`
- 问题反馈: GitHub Issues
