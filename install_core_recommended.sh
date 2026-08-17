#!/bin/bash

source venv/bin/activate

REPOS_DIR="repos"
INSTALLED_COUNT=$(find "$REPOS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | xargs)

declare -a COMPONENTS=(
    "browser-use|https://github.com/browser-use/browser-use.git|浏览器自动化"
    "letta-code|https://github.com/letta-ai/letta-code.git|Letta AI代码"
    "codebase-memory-mcp|https://github.com/DeusData/codebase-memory-mcp.git|代码库记忆MCP"
    "deer-flow|https://github.com/bytedance/deer-flow.git|字节工作流引擎"
    "HyperAgents|https://github.com/facebookresearch/HyperAgents.git|Meta超级Agent"
    "gecco|https://github.com/xtuhcy/gecco.git|Java爬虫框架"
    "awesome-knowledge-graph|https://github.com/husthuke/awesome-knowledge-graph.git|知识图谱资源"
)

TOTAL=${#COMPONENTS[@]}
CURRENT=0

for component in "${COMPONENTS[@]}"; do
    IFS='|' read -r NAME URL DESC <<< "$component"
    CURRENT=$((CURRENT + 1))
    
    echo ""
    echo "========================================"
    echo "正在安装: [$CURRENT/$TOTAL] $NAME - $DESC"
    echo "========================================"
    echo ""
    
    cd "$REPOS_DIR" || exit 1
    
    if [ -d "$NAME" ]; then
        echo "⏭️  已存在，跳过: $NAME"
        continue
    fi
    
    echo "📦 克隆仓库（浅克隆）..."
    if git clone --depth 1 "$URL" 2>&1; then
        echo ""
        echo "✅ 克隆成功"
        echo ""
        
        cd "$NAME" || continue
        
        # 尝试安装
        if [ -f "pyproject.toml" ]; then
            echo "📝 发现 pyproject.toml，正在安装..."
            pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 部分依赖安装失败"
        elif [ -f "requirements.txt" ]; then
            echo "📝 发现 requirements.txt，正在安装依赖..."
            pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 部分依赖安装失败"
        elif [ -f "setup.py" ]; then
            echo "📝 发现 setup.py，正在安装..."
            pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 部分依赖安装失败"
        else
            echo "ℹ️ 无安装文件，仅克隆代码"
        fi
        
        cd ..
        echo ""
        echo "✅ [$CURRENT/$TOTAL] $NAME - $DESC 安装完成"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
    else
        echo ""
        echo "❌ 克隆失败: $NAME"
        echo ""
        
        # 创建跳过标记
        mkdir -p "$NAME"
        cd "$NAME"
        touch .skip
        echo "# $NAME

跳过：网络错误或克隆失败" > README.md
        cd ..
    fi
    
    cd /Users/alwan/FieldMind-Rebuild
    
    # 添加延迟避免网络问题
    if [ $CURRENT -lt $TOTAL ]; then
        sleep 2
    fi
done

echo ""
echo "========================================"
echo "🎉 核心+强烈推荐组件安装完成！"
echo "========================================"
echo "总计: $TOTAL 个组件"
echo ""

