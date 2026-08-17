#!/bin/bash
# FieldMind 快速启动脚本

set -e

echo "================================================"
echo "FieldMind 系统快速启动"
echo "================================================"

# 检查Python虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查必需的Python包
echo ""
echo "📦 检查依赖包..."
pip install -q python-jose[cryptography] passlib[bcrypt] python-multipart psycopg2-binary 2>/dev/null || true

# 检查PostgreSQL
echo ""
echo "🔍 检查PostgreSQL..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "⚠️  PostgreSQL未运行，正在启动..."
    brew services start postgresql@14 || brew services start postgresql
    sleep 2
fi

# 检查Redis
echo ""
echo "🔍 检查Redis..."
if ! redis-cli ping >/dev/null 2>&1; then
    echo "⚠️  Redis未运行，正在启动..."
    brew services start redis
    sleep 1
fi

# 初始化数据库（如果需要）
echo ""
echo "📊 初始化数据库..."
cd fieldmind-backend
python init_db.py

echo ""
echo "================================================"
echo "✅ 准备完成！"
echo "================================================"
echo ""
echo "现在可以启动服务："
echo ""
echo "1. 启动后端 (终端1):"
echo "   cd fieldmind-backend"
echo "   python -m app.main"
echo ""
echo "2. 启动Celery Worker (终端2):"
echo "   cd fieldmind-backend"
echo "   celery -A app.celery_app worker -l info"
echo ""
echo "3. 访问API文档:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. 默认管理员账户:"
echo "   邮箱: admin@fieldmind.com"
echo "   密码: admin123"
echo ""
