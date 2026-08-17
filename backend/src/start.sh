#!/bin/bash

# FieldMind Backend 快速启动脚本

echo "🚀 启动 FieldMind Backend..."

cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt 2>/dev/null || echo "⚠️  请确保 requirements.txt 存在"

# 检查环境变量
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  警告: ANTHROPIC_API_KEY 未设置"
    echo "   对话功能将不可用"
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
python3 -c "
from app.core.database import init_db
init_db()
print('✅ 数据库初始化完成')
" 2>&1

# 启动服务器
echo ""
echo "🌐 启动 API 服务器..."
echo "📝 API 文档: http://localhost:8000/docs"
echo "🔍 健康检查: http://localhost:8000/health"
echo ""

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
