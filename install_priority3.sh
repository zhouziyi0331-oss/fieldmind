#!/bin/bash
# 优先级3：可选增强组件

echo "========================================"
echo "📦 开始安装优先级3组件..."
echo "========================================"

# 激活虚拟环境
source /Users/alwan/FieldMind-Rebuild/venv/bin/activate

# 主题建模和文本分析
echo -e "\n🔍 安装主题建模工具..."
pip install gensim bertopic -i https://pypi.tuna.tsinghua.edu.cn/simple

# 搜索引擎增强
echo -e "\n🔎 安装Elasticsearch客户端..."
pip install elasticsearch -i https://pypi.tuna.tsinghua.edu.cn/simple

# 多Agent系统
echo -e "\n🤖 安装AutoGen..."
pip install pyautogen -i https://pypi.tuna.tsinghua.edu.cn/simple

echo -e "\n========================================"
echo "✅ 优先级3组件安装完成！"
echo "========================================"
