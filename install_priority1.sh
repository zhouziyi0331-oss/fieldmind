#!/bin/bash

echo "========================================
🚀 安装优先级1核心组件
========================================
"

# 音视频处理
echo "
📹 1/5 安装音视频处理库..."
pip install openai-whisper opencv-python pydub librosa soundfile -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
💾 2/5 安装向量数据库..."
pip install chromadb faiss-cpu sentence-transformers -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
🗄️ 3/5 安装数据库驱动..."
pip install sqlalchemy psycopg2-binary neo4j -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
🔐 4/5 安装加密库..."
pip install cryptography -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
✂️ 5/5 安装中文分词..."
pip install jieba -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "
========================================
✅ 优先级1组件安装完成！
========================================
"

