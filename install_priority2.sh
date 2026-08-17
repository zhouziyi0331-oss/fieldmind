#!/bin/bash

echo "========================================
🚀 安装优先级2增强功能组件
========================================
"

# AI框架
echo "
🤖 1/4 安装AI框架 (langchain, spacy)..."
pip install langchain langchain-openai langchain-anthropic spacy -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
📊 2/4 安装可视化工具..."
pip install folium geopy plotly networkx pyvis -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
🔍 3/4 安装搜索引擎..."
pip install whoosh -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
📄 4/4 安装PDF增强工具..."
pip install pdfplumber PyMuPDF -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
========================================
✅ 优先级2组件安装完成！
========================================
"

