#!/bin/bash
# FieldMind 数据库安装脚本

echo "🗄️  安装 FieldMind 所需数据库..."
echo ""

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ 未找到 Homebrew，请先安装: https://brew.sh"
    exit 1
fi

echo "📦 更新 Homebrew..."
brew update

# PostgreSQL
echo ""
echo "1️⃣  安装 PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL 已安装: $(psql --version)"
else
    brew install postgresql@16
    echo "✅ PostgreSQL 安装完成"
fi

# 启动 PostgreSQL
brew services start postgresql@16
echo "   启动服务: brew services start postgresql@16"

# 创建数据库
echo "   创建数据库 fieldmind..."
createdb fieldmind 2>/dev/null && echo "   ✅ 数据库创建成功" || echo "   ⚠️  数据库已存在或创建失败"

# Neo4j
echo ""
echo "2️⃣  安装 Neo4j..."
if command -v neo4j &> /dev/null; then
    echo "✅ Neo4j 已安装: $(neo4j version 2>/dev/null || echo 'version unknown')"
else
    brew install neo4j
    echo "✅ Neo4j 安装完成"
fi

echo "   默认地址: http://localhost:7474"
echo "   默认用户: neo4j / neo4j (首次登录需修改密码)"
echo "   启动服务: brew services start neo4j"
echo "   或者: neo4j console (前台运行)"

# Redis
echo ""
echo "3️⃣  安装 Redis..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis 已安装: $(redis-server --version)"
else
    brew install redis
    echo "✅ Redis 安装完成"
fi

brew services start redis
echo "   启动服务: brew services start redis"

# ChromaDB (Python包已安装，无需额外安装)
echo ""
echo "4️⃣  ChromaDB..."
echo "✅ ChromaDB 已通过 pip 安装"
echo "   可以直接在代码中使用，或启动HTTP服务器:"
echo "   chroma run --host localhost --port 8001"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 数据库安装完成！"
echo ""
echo "📝 连接信息 (更新到 .env 文件):"
echo ""
echo "PostgreSQL:"
echo "  DATABASE_URL=postgresql://$(whoami)@localhost:5432/fieldmind"
echo ""
echo "Neo4j:"
echo "  NEO4J_URI=bolt://localhost:7687"
echo "  NEO4J_USER=neo4j"
echo "  NEO4J_PASSWORD=your_password_here"
echo ""
echo "Redis:"
echo "  REDIS_URL=redis://localhost:6379/0"
echo ""
echo "ChromaDB:"
echo "  CHROMA_HOST=localhost"
echo "  CHROMA_PORT=8000"
echo ""
echo "🚀 下一步:"
echo "  1. 启动 Neo4j: brew services start neo4j"
echo "  2. 访问 http://localhost:7474 设置密码"
echo "  3. 更新 fieldmind-backend/.env 配置"
echo "  4. 运行后端: ./run_backend.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
