#!/bin/bash

source venv/bin/activate

REPOS_DIR="repos"

declare -a REMAINING=(
    "letta-code|https://github.com/letta-ai/letta-code.git|Letta AI代码"
    "codebase-memory-mcp|https://github.com/DeusData/codebase-memory-mcp.git|代码库记忆MCP"
    "deer-flow|https://github.com/bytedance/deer-flow.git|字节工作流引擎"
    "HyperAgents|https://github.com/facebookresearch/HyperAgents.git|Meta超级Agent"
    "gecco|https://github.com/xtuhcy/gecco.git|Java爬虫框架"
    "awesome-knowledge-graph|https://github.com/husthuke/awesome-knowledge-graph.git|知识图谱资源"
)

echo "检查 letta-code 克隆状态..."
cd "$REPOS_DIR/letta-code"

# 等待克隆完成
for i in {1..60}; do
    if [ -f "README.md" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        echo "✅ letta-code 克隆完成"
        break
    fi
    
    SIZE=$(du -sh . | awk '{print $1}')
    echo "等待中... 当前大小: $SIZE (检查 $i/60)"
    sleep 5
done

# 检查是否真的完成
if [ ! -f "README.md" ] && [ ! -f "setup.py" ] && [ ! -f "pyproject.toml" ]; then
    echo "⚠️ letta-code 克隆可能卡住了，跳过安装"
    cd ..
    cd letta-code
    touch .skip
    echo "# letta-code

克隆超时，未完成" > README.md
else
    echo "📝 尝试安装 letta-code..."
    if [ -f "pyproject.toml" ]; then
        pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 安装失败"
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 安装失败"
    else
        echo "ℹ️ 无安装文件"
    fi
fi

cd /Users/alwan/FieldMind-Rebuild

# 继续安装剩余组件
for component in "${REMAINING[@]:1}"; do
    IFS='|' read -r NAME URL DESC <<< "$component"
    
    echo ""
    echo "========================================"
    echo "正在安装: $NAME - $DESC"
    echo "========================================"
    
    cd "$REPOS_DIR" || exit 1
    
    if [ -d "$NAME" ] && [ ! -f "$NAME/.skip" ]; then
        echo "⏭️ 已存在: $NAME"
        cd /Users/alwan/FieldMind-Rebuild
        continue
    fi
    
    echo "📦 克隆仓库（浅克隆）..."
    if timeout 120 git clone --depth 1 "$URL" 2>&1; then
        echo "✅ 克隆成功"
        
        cd "$NAME" || continue
        
        if [ -f "pyproject.toml" ]; then
            echo "📝 安装 pyproject.toml..."
            timeout 180 pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 安装失败"
        elif [ -f "requirements.txt" ]; then
            echo "📝 安装 requirements.txt..."
            timeout 180 pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 安装失败"
        elif [ -f "setup.py" ]; then
            echo "📝 安装 setup.py..."
            timeout 180 pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple || echo "⚠️ 安装失败"
        else
            echo "ℹ️ 无安装文件，仅克隆代码"
        fi
        
        echo "✅ $NAME 完成"
        cd ..
    else
        echo "❌ 克隆失败: $NAME"
        mkdir -p "$NAME"
        echo "跳过" > "$NAME/.skip"
    fi
    
    cd /Users/alwan/FieldMind-Rebuild
    sleep 3
done

echo ""
echo "🎉 安装流程完成！"

