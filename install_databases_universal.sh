#!/bin/bash
# FieldMind 数据库安装脚本 (无Homebrew版本)

echo "🗄️  FieldMind 数据库安装指南..."
echo ""

cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  检测到系统未安装 Homebrew
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FieldMind 需要以下数据库服务：
1. PostgreSQL 16 (结构化数据存储)
2. Neo4j (知识图谱)
3. Redis (缓存)
4. ChromaDB (向量数据库 - 已通过pip安装 ✅)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
安装方案选择
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

方案 A: 安装 Homebrew (推荐 - macOS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Homebrew 是 macOS 最流行的包管理器，可以一键安装所有依赖。

安装 Homebrew:
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

安装完成后，再次运行本脚本:
  ./install_databases.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
方案 B: Docker 部署 (推荐 - 跨平台)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
使用 Docker 可以快速启动所有数据库服务，无需手动安装。

1. 安装 Docker Desktop:
   https://www.docker.com/products/docker-desktop

2. 创建 docker-compose.yml (已为您生成)

3. 启动所有服务:
   docker-compose up -d

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
方案 C: 手动安装 (适合高级用户)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PostgreSQL 16:
   下载: https://www.postgresql.org/download/
   安装后创建数据库:
     createdb fieldmind

2. Neo4j Community Edition:
   下载: https://neo4j.com/download/
   启动后访问: http://localhost:7474
   默认用户名/密码: neo4j/neo4j (首次登录需修改)

3. Redis:
   下载: https://redis.io/download
   或使用包管理器安装

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
方案 D: 使用 SQLite + 内嵌服务 (最简单)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
适合开发和测试，无需安装额外数据库。

FieldMind 可以使用以下轻量级替代方案:
- PostgreSQL → SQLite (已内置)
- Neo4j → 内存图数据库 (networkx)
- Redis → 内存缓存
- ChromaDB → 本地持久化 (已安装 ✅)

配置 .env 使用 SQLite:
  DATABASE_URL=sqlite:///./fieldmind.db
  # 注释掉 NEO4J_URI 和 REDIS_URL

后端会自动降级到可用的服务。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo ""
echo "🐳 正在为您生成 Docker Compose 配置..."
echo ""

# 创建 docker-compose.yml
cat > docker-compose.yml << 'YAML'
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:16-alpine
    container_name: fieldmind-postgres
    environment:
      POSTGRES_DB: fieldmind
      POSTGRES_USER: fieldmind
      POSTGRES_PASSWORD: fieldmind_password
      POSTGRES_INITDB_ARGS: "-E UTF8 --locale=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fieldmind"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Neo4j 图数据库
  neo4j:
    image: neo4j:5.15-community
    container_name: fieldmind-neo4j
    environment:
      NEO4J_AUTH: neo4j/fieldmind_password
      NEO4J_dbms_memory_pagecache_size: 512M
      NEO4J_dbms_memory_heap_max__size: 1G
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p fieldmind_password 'RETURN 1'"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: fieldmind-redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
    driver: local
  neo4j_data:
    driver: local
  neo4j_logs:
    driver: local
  redis_data:
    driver: local
YAML

echo "✅ 已生成 docker-compose.yml"
echo ""

# 创建简化的 .env 配置
cat > fieldmind-backend/.env.docker << 'ENV'
# FieldMind Backend Configuration (Docker)

# ============ 数据库配置 ============
# PostgreSQL (Docker)
DATABASE_URL=postgresql://fieldmind:fieldmind_password@localhost:5432/fieldmind

# Neo4j (Docker)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fieldmind_password

# Redis (Docker)
REDIS_URL=redis://localhost:6379/0

# ChromaDB (本地持久化)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./chroma_db

# ============ AI 服务配置 ============
# OpenAI API (必需 - 用于 Whisper 和 RAG)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic API (可选 - 用于 Claude 模型)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# ============ 应用配置 ============
# 上传文件存储路径
UPLOAD_DIR=./uploads

# CORS 允许的来源
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# JWT 密钥 (请修改为随机字符串)
JWT_SECRET_KEY=change-this-to-a-random-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ============ Whisper 配置 ============
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# ============ 向量嵌入配置 ============
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DEVICE=cpu
ENV

echo "✅ 已生成 fieldmind-backend/.env.docker 配置模板"
echo ""

cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 使用 Docker 快速启动
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 确保已安装 Docker Desktop
   https://www.docker.com/products/docker-desktop

2. 启动所有数据库服务:
   docker-compose up -d

3. 查看服务状态:
   docker-compose ps

4. 查看日志:
   docker-compose logs -f

5. 停止服务:
   docker-compose down

6. 完全清理 (删除数据):
   docker-compose down -v

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 连接信息 (Docker)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PostgreSQL:
  Host: localhost
  Port: 5432
  Database: fieldmind
  User: fieldmind
  Password: fieldmind_password
  URL: postgresql://fieldmind:fieldmind_password@localhost:5432/fieldmind

Neo4j:
  Web UI: http://localhost:7474
  Bolt: bolt://localhost:7687
  User: neo4j
  Password: fieldmind_password

Redis:
  Host: localhost
  Port: 6379
  URL: redis://localhost:6379/0

ChromaDB:
  本地持久化模式 (无需独立服务)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 下一步操作
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 选择安装方案 (推荐 Docker)

2. 配置 API Keys:
   cp fieldmind-backend/.env.docker fieldmind-backend/.env
   nano fieldmind-backend/.env
   # 填入你的 OPENAI_API_KEY

3. 启动后端:
   ./run_backend.sh

4. 访问 API 文档:
   http://localhost:8000/docs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo ""
echo "💡 提示: 如果只想快速测试，可以使用 SQLite 模式 (无需安装任何数据库)"
echo "   编辑 fieldmind-backend/.env:"
echo "   DATABASE_URL=sqlite:///./fieldmind.db"
echo ""
