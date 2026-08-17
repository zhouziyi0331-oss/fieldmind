#!/bin/bash
# 依赖冲突处理：为khoj和browser-use创建独立虚拟环境

echo "========================================"
echo "🔧 处理依赖冲突 - 创建隔离环境"
echo "========================================"

BASE_DIR="/Users/alwan/FieldMind-Rebuild"
cd $BASE_DIR

# 1. 创建khoj独立环境
echo -e "\n📦 创建khoj独立环境..."
python3 -m venv venv_khoj
source venv_khoj/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
cd repos/khoj
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
deactivate

# 2. 创建browser-use独立环境
echo -e "\n📦 创建browser-use独立环境..."
cd $BASE_DIR
python3 -m venv venv_browser_use
source venv_browser_use/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
cd repos/browser-use
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
deactivate

# 3. 主环境保留通用组件
echo -e "\n✅ 主环境 (venv): 通用组件 + RAG + 可视化"
echo "✅ venv_khoj: khoj专用 (anthropic==0.75.0)"
echo "✅ venv_browser_use: browser-use专用 (anthropic==0.76.0)"

echo -e "\n========================================"
echo "✅ 依赖冲突处理完成！"
echo "========================================"
echo ""
echo "使用方式："
echo "  主环境:          source venv/bin/activate"
echo "  Khoj:           source venv_khoj/bin/activate"
echo "  Browser-use:    source venv_browser_use/bin/activate"
