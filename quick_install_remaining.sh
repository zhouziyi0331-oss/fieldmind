#!/bin/bash

source ../venv/bin/activate

# 剩余5个组件
declare -a COMPONENTS=(
    "codebase-memory-mcp|https://github.com/DeusData/codebase-memory-mcp.git"
    "deer-flow|https://github.com/bytedance/deer-flow.git"
    "HyperAgents|https://github.com/facebookresearch/HyperAgents.git"
    "gecco|https://github.com/xtuhcy/gecco.git"
    "awesome-knowledge-graph|https://github.com/husthuke/awesome-knowledge-graph.git"
)

for comp in "${COMPONENTS[@]}"; do
    IFS='|' read -r NAME URL <<< "$comp"
    
    echo ""
    echo "▶ 克隆: $NAME"
    
    timeout 90 git clone --depth 1 "$URL" && echo "  ✅ $NAME" || {
        echo "  ❌ $NAME 失败，标记跳过"
        mkdir -p "$NAME"
        touch "$NAME/.skip"
        echo "跳过：网络超时" > "$NAME/README.md"
    }
    
    sleep 2
done

echo ""
echo "完成！"

