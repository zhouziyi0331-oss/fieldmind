#!/bin/bash

echo "=========================================="
echo "🚀 FieldMind 统一系统启动"
echo "=========================================="

PROJECT_ROOT="/Users/alwan/FieldMind"
BACKEND_DIR="$PROJECT_ROOT/backend"
XCODE_PROJECT="$PROJECT_ROOT/fieldmind/fieldmind.xcodeproj"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 检查后端
echo ""
echo "1️⃣  检查后端服务..."
if [ -d "$BACKEND_DIR" ]; then
    echo -e "${GREEN}✅ 后端目录存在${NC}"

    # 检查虚拟环境
    if [ -d "$BACKEND_DIR/venv" ]; then
        echo -e "${GREEN}✅ 虚拟环境已配置${NC}"
    else
        echo -e "${YELLOW}⚠️  虚拟环境未找到，正在创建...${NC}"
        cd "$BACKEND_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi

    # 启动后端
    echo "🔄 启动后端服务..."
    cd "$BACKEND_DIR"
    source venv/bin/activate

    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  端口 8000 已被占用，停止旧进程...${NC}"
        kill $(lsof -t -i:8000)
        sleep 2
    fi

    # 后台启动
    nohup uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    echo -e "${GREEN}✅ 后端已启动 (PID: $BACKEND_PID)${NC}"
    echo "   日志文件: $BACKEND_DIR/backend.log"

    # 等待后端启动
    echo "⏳ 等待后端就绪..."
    for i in {1..10}; do
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 后端健康检查通过${NC}"
            break
        fi
        sleep 1
    done
else
    echo -e "${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

# 2. 检查 Xcode 项目
echo ""
echo "2️⃣  检查 Xcode 项目..."
if [ -d "$XCODE_PROJECT" ]; then
    echo -e "${GREEN}✅ Xcode 项目存在${NC}"

    # 列出关键文件
    echo ""
    echo "📋 核心集成文件状态:"

    files=(
        "fieldmind/fieldmind/Core/UnifiedAppState.swift"
        "fieldmind/fieldmind/Core/DataPipeline/DataPipeline.swift"
        "fieldmind/fieldmind/Services/BackendService.swift"
        "fieldmind/fieldmind/Services/KnowledgeVaultService.swift"
        "fieldmind/fieldmind/Views/KnowledgeVaultView.swift"
        "fieldmind/Services/DistillationService.swift"
        "fieldmind/Views/MainNavigationView.swift"
        "fieldmind/Views/DistillationView.swift"
    )

    for file in "${files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo -e "   ${GREEN}✅${NC} $(basename $file)"
        else
            echo -e "   ${RED}❌${NC} $(basename $file)"
        fi
    done

    # 统计合并文件
    merged_count=$(find "$PROJECT_ROOT/fieldmind/fieldmind" -name "*_Merged.swift" | wc -l)
    echo ""
    echo -e "📊 待审查合并文件: ${YELLOW}$merged_count 个${NC}"

else
    echo -e "${RED}❌ Xcode 项目不存在: $XCODE_PROJECT${NC}"
    exit 1
fi

# 3. 打开 Xcode
echo ""
echo "3️⃣  启动 Xcode..."
echo "   正在打开项目..."
open "$XCODE_PROJECT"
sleep 2
echo -e "${GREEN}✅ Xcode 已启动${NC}"

# 4. 显示后端 API 文档
echo ""
echo "=========================================="
echo "📚 系统信息"
echo "=========================================="
echo "🌐 后端 API: http://127.0.0.1:8000"
echo "📖 API 文档: http://127.0.0.1:8000/docs"
echo "📊 健康检查: http://127.0.0.1:8000/health"
echo ""
echo "📁 日志位置:"
echo "   后端日志: $BACKEND_DIR/backend.log"
echo "   PID 文件: $BACKEND_DIR/backend.pid"
echo ""
echo "🛑 停止服务:"
echo "   kill \$(cat $BACKEND_DIR/backend.pid)"
echo "   或运行: $PROJECT_ROOT/stop_fieldmind.sh"
echo "=========================================="

# 5. 显示下一步操作
echo ""
echo "📋 下一步操作:"
echo ""
echo "1. 在 Xcode 中编译项目 (⌘+B)"
echo "2. 检查是否有编译错误"
echo "3. 审查 48 个 *_Merged.swift 文件:"
echo "   - Services/Unified/ 目录下 25 个"
echo "   - ViewModels/Unified/ 目录下 23 个"
echo "4. 运行应用 (⌘+R)"
echo "5. 测试各个功能模块"
echo ""
echo "⚠️  审查合并文件的步骤:"
echo "   a) 打开每个 *_Merged.swift 文件"
echo "   b) 查看标记为 'NATIVE VERSION' 的代码"
echo "   c) 保留有价值的功能"
echo "   d) 删除重复代码"
echo "   e) 重命名文件去掉 _Merged 后缀"
echo ""
echo "✅ 系统启动完成！"
