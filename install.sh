#!/bin/bash
# FieldMind 完整安装脚本
# 安装22个核心和推荐组件

set -e  # 遇到错误立即退出

echo "=========================================="
echo "FieldMind 田野调查知识管理系统 - 安装脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python环境
echo -e "${BLUE}[1/4] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python 3.8+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查Node.js环境
echo -e "${BLUE}[2/4] 检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}警告: 未找到Node.js，前端组件将无法安装${NC}"
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js版本: $NODE_VERSION${NC}"
fi

# 创建Python虚拟环境
echo -e "${BLUE}[3/4] 创建Python虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
else
    echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
fi

# 激活虚拟环境
source venv/bin/activate

# 升级pip
echo -e "${BLUE}[4/4] 升级pip...${NC}"
pip install --upgrade pip wheel setuptools
echo -e "${GREEN}✓ pip已升级${NC}"

echo ""
echo "=========================================="
echo "开始克隆和安装22个组件..."
echo "=========================================="
echo ""

# 创建目录结构
mkdir -p repos
mkdir -p logs
cd repos

# 安装进度计数
TOTAL=22
CURRENT=0

# ============================================
# 🔴 必装核心 (14个)
# ============================================

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🔴 必装核心组件 (14个)${NC}"
echo -e "${BLUE}============================================${NC}"

# 1. Microsoft GraphRAG
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Microsoft GraphRAG - 图谱增强RAG${NC}"
if [ ! -d "graphrag" ]; then
    git clone https://github.com/microsoft/graphrag.git 2>&1 | tee ../logs/graphrag.log
    cd graphrag
    pip install -e . 2>&1 | tee -a ../logs/graphrag.log
    cd ..
    echo -e "${GREEN}✓ GraphRAG 安装完成${NC}"
else
    echo -e "${GREEN}✓ GraphRAG 已存在，跳过${NC}"
fi
echo ""

# 2. RAGFlow
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] RAGFlow - 完整RAG引擎${NC}"
if [ ! -d "ragflow" ]; then
    git clone https://github.com/infiniflow/ragflow.git 2>&1 | tee ../logs/ragflow.log
    cd ragflow
    pip install -r requirements.txt 2>&1 | tee -a ../logs/ragflow.log
    cd ..
    echo -e "${GREEN}✓ RAGFlow 安装完成${NC}"
else
    echo -e "${GREEN}✓ RAGFlow 已存在，跳过${NC}"
fi
echo ""

# 3. Khoj
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Khoj - AI知识助手${NC}"
if [ ! -d "khoj" ]; then
    git clone https://github.com/khoj-ai/khoj.git 2>&1 | tee ../logs/khoj.log
    cd khoj
    pip install -e . 2>&1 | tee -a ../logs/khoj.log
    cd ..
    echo -e "${GREEN}✓ Khoj 安装完成${NC}"
else
    echo -e "${GREEN}✓ Khoj 已存在，跳过${NC}"
fi
echo ""

# 4. Graphiti
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Graphiti - 时序知识图谱${NC}"
if [ ! -d "graphiti" ]; then
    git clone https://github.com/getzep/graphiti.git 2>&1 | tee ../logs/graphiti.log
    cd graphiti
    pip install -e . 2>&1 | tee -a ../logs/graphiti.log
    cd ..
    echo -e "${GREEN}✓ Graphiti 安装完成${NC}"
else
    echo -e "${GREEN}✓ Graphiti 已存在，跳过${NC}"
fi
echo ""

# 5. HanLP
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] HanLP - 中文NLP核心${NC}"
pip install hanlp 2>&1 | tee ../logs/hanlp.log
echo -e "${GREEN}✓ HanLP 安装完成${NC}"
echo ""

# 6. DuckDB
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] DuckDB - 嵌入式分析数据库${NC}"
pip install duckdb 2>&1 | tee ../logs/duckdb.log
echo -e "${GREEN}✓ DuckDB 安装完成${NC}"
echo ""

# 7. Neo4j-KGBuilder
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Neo4j-KGBuilder - 知识图谱构建${NC}"
if [ ! -d "Neo4j-KGBuilder" ]; then
    git clone https://github.com/bigdante/Neo4j-KGBuilder.git 2>&1 | tee ../logs/kgbuilder.log
    cd Neo4j-KGBuilder
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt 2>&1 | tee -a ../logs/kgbuilder.log
    fi
    cd ..
    echo -e "${GREEN}✓ Neo4j-KGBuilder 安装完成${NC}"
else
    echo -e "${GREEN}✓ Neo4j-KGBuilder 已存在，跳过${NC}"
fi
echo ""

# 8. Mem0
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Mem0 - AI记忆层${NC}"
pip install mem0ai 2>&1 | tee ../logs/mem0.log
echo -e "${GREEN}✓ Mem0 安装完成${NC}"
echo ""

# 9. PDF-Guru
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] PDF-Guru - 中文PDF处理${NC}"
if [ ! -d "PDF-Guru" ]; then
    git clone https://github.com/kevin2li/PDF-Guru.git 2>&1 | tee ../logs/pdfguru.log
    cd PDF-Guru
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt 2>&1 | tee -a ../logs/pdfguru.log
    fi
    cd ..
    echo -e "${GREEN}✓ PDF-Guru 安装完成${NC}"
else
    echo -e "${GREEN}✓ PDF-Guru 已存在，跳过${NC}"
fi
echo ""

# 10. BetterRAG
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] BetterRAG - RAG知识库${NC}"
if [ ! -d "BetterRAG" ]; then
    git clone https://github.com/HKUDS/BetterRAG.git 2>&1 | tee ../logs/betterrag.log
    cd BetterRAG
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt 2>&1 | tee -a ../logs/betterrag.log
    fi
    cd ..
    echo -e "${GREEN}✓ BetterRAG 安装完成${NC}"
else
    echo -e "${GREEN}✓ BetterRAG 已存在，跳过${NC}"
fi
echo ""

# 11. Pillow
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Pillow - 图像处理${NC}"
pip install Pillow 2>&1 | tee ../logs/pillow.log
echo -e "${GREEN}✓ Pillow 安装完成${NC}"
echo ""

# 12. ExifReader (JavaScript)
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] ExifReader - 照片元数据${NC}"
if command -v npm &> /dev/null; then
    npm install exifreader 2>&1 | tee ../logs/exifreader.log
    echo -e "${GREEN}✓ ExifReader 安装完成${NC}"
else
    echo -e "${RED}⚠ ExifReader 跳过 (需要npm)${NC}"
fi
echo ""

# 13. mind-map
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] mind-map - 思维导图可视化${NC}"
if [ ! -d "mind-map" ]; then
    git clone https://github.com/wanglin2/mind-map.git 2>&1 | tee ../logs/mindmap.log
    echo -e "${GREEN}✓ mind-map 克隆完成${NC}"
else
    echo -e "${GREEN}✓ mind-map 已存在，跳过${NC}"
fi
echo ""

# 14. pyhanlp
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] pyhanlp - HanLP Python版${NC}"
pip install pyhanlp 2>&1 | tee ../logs/pyhanlp.log
echo -e "${GREEN}✓ pyhanlp 安装完成${NC}"
echo ""

# ============================================
# 🟡 强烈推荐 (8个)
# ============================================

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🟡 强烈推荐组件 (8个)${NC}"
echo -e "${BLUE}============================================${NC}"

# 15. LightRAG
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] LightRAG - 轻量级RAG${NC}"
if [ ! -d "LightRAG" ]; then
    git clone https://github.com/HKUDS/LightRAG.git 2>&1 | tee ../logs/lightrag.log
    cd LightRAG
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt 2>&1 | tee -a ../logs/lightrag.log
    fi
    cd ..
    echo -e "${GREEN}✓ LightRAG 安装完成${NC}"
else
    echo -e "${GREEN}✓ LightRAG 已存在，跳过${NC}"
fi
echo ""

# 16. Quivr
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Quivr - 第二大脑${NC}"
if [ ! -d "quivr" ]; then
    git clone https://github.com/QuivrHQ/quivr.git 2>&1 | tee ../logs/quivr.log
    echo -e "${GREEN}✓ Quivr 克隆完成 (需要单独Docker部署)${NC}"
else
    echo -e "${GREEN}✓ Quivr 已存在，跳过${NC}"
fi
echo ""

# 17. Cognee
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Cognee - 认知AI框架${NC}"
if [ ! -d "cognee" ]; then
    git clone https://github.com/topoteretes/cognee.git 2>&1 | tee ../logs/cognee.log
    cd cognee
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt 2>&1 | tee -a ../logs/cognee.log
    fi
    cd ..
    echo -e "${GREEN}✓ Cognee 安装完成${NC}"
else
    echo -e "${GREEN}✓ Cognee 已存在，跳过${NC}"
fi
echo ""

# 18. Firecrawl
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Firecrawl - Web爬虫${NC}"
if [ ! -d "firecrawl" ]; then
    git clone https://github.com/mendableai/firecrawl.git 2>&1 | tee ../logs/firecrawl.log
    cd firecrawl
    pip install firecrawl-py 2>&1 | tee -a ../logs/firecrawl.log
    cd ..
    echo -e "${GREEN}✓ Firecrawl 安装完成${NC}"
else
    echo -e "${GREEN}✓ Firecrawl 已存在，跳过${NC}"
fi
echo ""

# 19. Crawl4AI
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] Crawl4AI - AI爬虫${NC}"
if [ ! -d "crawl4ai" ]; then
    git clone https://github.com/unclecode/crawl4ai.git 2>&1 | tee ../logs/crawl4ai.log
    cd crawl4ai
    pip install crawl4ai 2>&1 | tee -a ../logs/crawl4ai.log
    cd ..
    echo -e "${GREEN}✓ Crawl4AI 安装完成${NC}"
else
    echo -e "${GREEN}✓ Crawl4AI 已存在，跳过${NC}"
fi
echo ""

# 20. funNLP
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] funNLP - 中文NLP工具集${NC}"
if [ ! -d "funNLP" ]; then
    git clone https://github.com/fighting41love/funNLP.git 2>&1 | tee ../logs/funnlp.log
    echo -e "${GREEN}✓ funNLP 克隆完成 (资源库)${NC}"
else
    echo -e "${GREEN}✓ funNLP 已存在，跳过${NC}"
fi
echo ""

# 21. awesome-pretrained-chinese-nlp-models
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] awesome-pretrained-chinese-nlp-models - 中文预训练模型${NC}"
if [ ! -d "awesome-pretrained-chinese-nlp-models" ]; then
    git clone https://github.com/lonePatient/awesome-pretrained-chinese-nlp-models.git 2>&1 | tee ../logs/chinese-nlp-models.log
    echo -e "${GREEN}✓ awesome-pretrained-chinese-nlp-models 克隆完成 (资源库)${NC}"
else
    echo -e "${GREEN}✓ awesome-pretrained-chinese-nlp-models 已存在，跳过${NC}"
fi
echo ""

# 22. dialect-preservation-fieldwork-minutes
CURRENT=$((CURRENT+1))
echo -e "${BLUE}[$CURRENT/$TOTAL] dialect-preservation-fieldwork-minutes - 田野调查参考${NC}"
if [ ! -d "dialect-preservation-fieldwork-minutes" ]; then
    git clone https://github.com/qzxtu/dialect-preservation-fieldwork-minutes.git 2>&1 | tee ../logs/fieldwork.log
    echo -e "${GREEN}✓ dialect-preservation-fieldwork-minutes 克隆完成 (参考实现)${NC}"
else
    echo -e "${GREEN}✓ dialect-preservation-fieldwork-minutes 已存在，跳过${NC}"
fi
echo ""

# ============================================
# 安装完成总结
# ============================================

cd ..

echo ""
echo "=========================================="
echo -e "${GREEN}✓ 安装完成！${NC}"
echo "=========================================="
echo ""
echo "📦 已安装组件："
echo "  🔴 必装核心: 14个"
echo "  🟡 强烈推荐: 8个"
echo "  📊 总计: 22个"
echo ""
echo "📁 安装位置："
echo "  工作目录: $(pwd)"
echo "  仓库目录: $(pwd)/repos"
echo "  日志目录: $(pwd)/logs"
echo "  虚拟环境: $(pwd)/venv"
echo ""
echo "🚀 下一步："
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 查看安装日志: ls -lh logs/"
echo "  3. 测试Python导入: python3 test_imports.py"
echo ""
echo "💡 提示："
echo "  - 某些组件需要额外配置（API密钥等）"
echo "  - 查看各组件的README了解详细使用方法"
echo "  - 所有日志已保存到 logs/ 目录"
echo ""
