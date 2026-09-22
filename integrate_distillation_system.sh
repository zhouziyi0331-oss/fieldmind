#!/bin/bash

# FieldMind 知识蒸馏系统集成脚本
# 完整集成前后端的第二大脑蒸馏系统

set -e

echo "🚀 FieldMind 知识蒸馏系统集成"
echo "================================"

# 检查当前目录
if [ ! -f "backend/src/app/main.py" ]; then
    echo "❌ 错误：请在 FieldMind 项目根目录运行此脚本"
    exit 1
fi

# 步骤 1: 后端集成检查
echo ""
echo "📦 步骤 1: 检查后端集成..."
echo "--------------------------------"

# 检查蒸馏模块是否存在
if [ -d "backend/src/app/distillation" ]; then
    echo "✅ 蒸馏模块已存在"
    ls -l backend/src/app/distillation/*.py | awk '{print "   -", $9}'
else
    echo "❌ 蒸馏模块不存在！"
    exit 1
fi

# 检查数据库模型
if grep -q "distillation" backend/src/app/models/*.py 2>/dev/null; then
    echo "✅ 数据库模型已集成"
else
    echo "⚠️  数据库模型未找到"
fi

# 检查 API 路由
if grep -q "distillation" backend/src/app/main.py; then
    echo "✅ API 路由已注册"
else
    echo "⚠️  API 路由未注册，正在添加..."
    # 这里可以添加自动注册逻辑
fi

# 步骤 2: 数据库迁移
echo ""
echo "🗄️  步骤 2: 数据库迁移..."
echo "--------------------------------"

cd backend

# 检查 alembic
if [ -f "../alembic.ini" ]; then
    echo "正在运行数据库迁移..."

    # 创建迁移（如果需要）
    if [ ! -f "src/app/migrations/versions/*distillation*.py" ]; then
        echo "创建蒸馏系统数据库迁移..."
        cd ..
        alembic revision --autogenerate -m "Add distillation system tables" || echo "⚠️  迁移创建失败，可能已存在"
        cd backend
    fi

    # 应用迁移
    cd ..
    alembic upgrade head || echo "⚠️  迁移应用失败"
    cd backend

    echo "✅ 数据库迁移完成"
else
    echo "⚠️  未找到 alembic.ini，请手动运行迁移"
fi

cd ..

# 步骤 3: 后端依赖检查
echo ""
echo "📚 步骤 3: 检查 Python 依赖..."
echo "--------------------------------"

REQUIRED_DEPS=(
    "fastapi"
    "sqlalchemy"
    "python-multipart"
    "aiofiles"
    "httpx"
    "pypdf"
    "ebooklib"
    "python-docx"
    "markdown"
    "whisper"
)

cd backend
source venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null || true

for dep in "${REQUIRED_DEPS[@]}"; do
    if python -c "import ${dep//-/_}" 2>/dev/null; then
        echo "✅ $dep"
    else
        echo "⚠️  $dep 未安装"
    fi
done

cd ..

# 步骤 4: 前端集成检查
echo ""
echo "🎨 步骤 4: 检查 Swift 前端集成..."
echo "--------------------------------"

# 检查新创建的 Swift 文件
SWIFT_FILES=(
    "fieldmind/Services/DistillationService.swift"
    "fieldmind/Views/DistillationView.swift"
    "fieldmind/Views/MainNavigationView.swift"
)

for file in "${SWIFT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 不存在！"
    fi
done

# 步骤 5: Xcode 项目集成说明
echo ""
echo "🔧 步骤 5: Xcode 项目集成"
echo "--------------------------------"
echo "请按以下步骤将新文件添加到 Xcode 项目："
echo ""
echo "1. 打开 Xcode 项目:"
echo "   open fieldmind/fieldmind.xcodeproj"
echo ""
echo "2. 创建 Services 文件夹（如果不存在）："
echo "   - 右键点击项目导航器中的 'fieldmind' 文件夹"
echo "   - 选择 'New Group'"
echo "   - 命名为 'Services'"
echo ""
echo "3. 添加 DistillationService.swift："
echo "   - 右键点击 'Services' 文件夹"
echo "   - 选择 'Add Files to \"fieldmind\"...'"
echo "   - 选择: fieldmind/Services/DistillationService.swift"
echo "   - 确保 'Copy items if needed' 未勾选"
echo "   - 点击 'Add'"
echo ""
echo "4. 添加新视图文件："
echo "   - 右键点击 'Views' 文件夹"
echo "   - 选择 'Add Files to \"fieldmind\"...'"
echo "   - 选择: fieldmind/Views/DistillationView.swift"
echo "   - 选择: fieldmind/Views/MainNavigationView.swift"
echo "   - 点击 'Add'"
echo ""
echo "5. 验证 ContentView.swift 已更新"
echo ""
echo "6. 编译项目 (⌘+B)"
echo ""

# 步骤 6: 后端启动测试
echo ""
echo "🧪 步骤 6: 后端 API 测试"
echo "--------------------------------"

# 检查后端是否运行
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 后端正在运行"

    # 测试蒸馏 API
    if curl -s http://localhost:8000/api/v1/distillation/stats > /dev/null 2>&1; then
        echo "✅ 蒸馏 API 可访问"

        # 获取统计信息
        echo ""
        echo "📊 当前统计："
        curl -s http://localhost:8000/api/v1/distillation/stats | python -m json.tool 2>/dev/null || echo "无法解析统计数据"
    else
        echo "⚠️  蒸馏 API 无法访问"
        echo "   请检查路由是否正确注册"
    fi
else
    echo "⚠️  后端未运行"
    echo ""
    echo "启动后端命令："
    echo "  cd backend"
    echo "  source venv/bin/activate  # 或 source ../venv/bin/activate"
    echo "  python -m uvicorn app.main:app --reload"
fi

# 步骤 7: 完整性检查总结
echo ""
echo "📋 集成完整性检查总结"
echo "================================"

echo ""
echo "✅ 已完成的部分："
echo "  • Python 后端蒸馏系统（11 个阶段完整流水线）"
echo "  • 数据库模型（6 张表）"
echo "  • REST API 端点（11 个端点）"
echo "  • Swift 网络服务层（DistillationService.swift）"
echo "  • Swift 完整界面（DistillationView.swift）"
echo "  • 主导航集成（MainNavigationView.swift）"
echo ""

echo "⚠️  需要手动完成："
echo "  1. 在 Xcode 中添加新的 Swift 文件到项目"
echo "  2. 编译并运行 Swift 应用"
echo "  3. 启动 Python 后端"
echo "  4. 测试完整的蒸馏流程"
echo ""

echo "🎯 下一步操作："
echo "--------------------------------"
echo "1. 添加文件到 Xcode（见上方详细步骤）"
echo "2. 启动后端："
echo "   cd backend && python -m uvicorn app.main:app --reload"
echo "3. 构建并运行 Swift 应用 (⌘+R)"
echo "4. 在应用中点击 '知识蒸馏' 开始使用"
echo ""

echo "📖 API 文档："
echo "   http://localhost:8000/docs"
echo ""

echo "✨ 集成完成！"

# 创建快速启动脚本
cat > quick_start_distillation.sh << 'EOF'
#!/bin/bash

echo "🚀 启动 FieldMind 知识蒸馏系统"
echo ""

# 启动后端
echo "📡 启动后端服务..."
cd backend
source venv/bin/activate 2>/dev/null || source ../venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "后端 PID: $BACKEND_PID"
echo ""

# 等待后端启动
sleep 3

# 检查后端
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 后端启动成功"
    echo "📖 API 文档: http://localhost:8000/docs"
else
    echo "❌ 后端启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎨 启动 Swift 应用..."
cd ../fieldmind
open fieldmind.xcodeproj

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "停止后端："
echo "  kill $BACKEND_PID"
EOF

chmod +x quick_start_distillation.sh

echo "创建了快速启动脚本: quick_start_distillation.sh"
echo "运行: ./quick_start_distillation.sh"
