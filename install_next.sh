#!/bin/bash

# FieldMind 改进的逐个安装脚本
# 使用浅克隆加速，每次只安装一个组件

cd /Users/alwan/FieldMind-Rebuild/repos
source ../venv/bin/activate

# 检查已安装的组件
installed_count=$(ls -1 | grep -v "^\." 2>/dev/null | wc -l | tr -d ' ')
echo "已安装组件数: $installed_count/22"
echo ""

# 组件列表
declare -a components=(
    "graphrag|https://github.com/microsoft/graphrag.git|Microsoft GraphRAG"
    "ragflow|https://github.com/infiniflow/ragflow.git|RAGFlow - 完整RAG引擎"
    "khoj|https://github.com/khoj-ai/khoj.git|Khoj - AI助手"
    "graphiti|https://github.com/getzep/graphiti.git|Graphiti - 时序知识图谱"
    "HanLP|https://github.com/hankcs/HanLP.git|HanLP - 中文NLP"
    "duckdb|https://github.com/duckdb/duckdb.git|DuckDB - 分析数据库"
    "neo4j-knowledge-graph-builder|https://github.com/neo4j-labs/llm-graph-builder.git|Neo4j图谱构建器"
    "mem0|https://github.com/mem0ai/mem0.git|Mem0 - 记忆层"
    "PDF-Guru|https://github.com/kevin2li/PDF-Guru.git|PDF-Guru - PDF处理"
    "BetterRAG|https://github.com/HKUDS/BetterRAG.git|BetterRAG - 改进RAG"
    "Pillow|https://github.com/python-pillow/Pillow.git|Pillow - 图像处理"
    "exif-reader|https://github.com/devongovett/exif-reader.git|ExifReader - EXIF读取"
    "mind-map|https://github.com/wanglin2/mind-map.git|思维导图库"
    "pyhanlp|https://github.com/hankcs/pyhanlp.git|PyHanLP - Python封装"
    "LightRAG|https://github.com/HKUST-KnowComp/LightRAG.git|LightRAG - 轻量RAG"
    "quivr|https://github.com/StanGirard/quivr.git|Quivr - 第二大脑"
    "cognee|https://github.com/topoteretes/cognee.git|Cognee - 确定性记忆"
    "firecrawl|https://github.com/mendableai/firecrawl.git|Firecrawl - 网页爬虫"
    "crawl4ai|https://github.com/unclecode/crawl4ai.git|Crawl4AI - AI爬虫"
    "funNLP|https://github.com/fighting41love/funNLP.git|funNLP - 中文NLP工具"
    "awesome-pretrained-chinese-nlp-models|https://github.com/lonePatient/awesome-pretrained-chinese-nlp-models.git|预训练中文模型"
    "dialect-preservation-fieldwork-minutes|https://github.com/Yixuan-Wang/dialect-preservation-fieldwork-minutes.git|方言调查记录"
)

# 找到下一个要安装的组件
for i in "${!components[@]}"; do
    IFS='|' read -r dir_name git_url display_name <<< "${components[$i]}"

    if [ ! -d "$dir_name" ]; then
        echo "========================================"
        echo "正在安装: [$((i+1))/22] $display_name"
        echo "========================================"
        echo ""

        # 使用浅克隆加速
        echo "📦 克隆仓库（浅克隆）..."
        git clone --depth 1 "$git_url" "$dir_name"

        if [ $? -eq 0 ] && [ -d "$dir_name" ]; then
            echo ""
            echo "✅ 克隆成功"

            # 检查是否有 requirements.txt
            if [ -f "$dir_name/requirements.txt" ]; then
                echo ""
                echo "📝 安装Python依赖..."
                cd "$dir_name"
                pip install -r requirements.txt 2>&1 | tee ../logs/${dir_name}.log || echo "⚠️ 部分依赖安装失败"
                cd ..
            elif [ -f "$dir_name/pyproject.toml" ]; then
                echo ""
                echo "📝 安装Python包（pyproject.toml）..."
                cd "$dir_name"
                pip install -e . 2>&1 | tee ../logs/${dir_name}.log || echo "⚠️ 部分依赖安装失败"
                cd ..
            elif [ -f "$dir_name/setup.py" ]; then
                echo ""
                echo "📝 安装Python包（setup.py）..."
                cd "$dir_name"
                pip install -e . 2>&1 | tee ../logs/${dir_name}.log || echo "⚠️ 部分依赖安装失败"
                cd ..
            else
                echo ""
                echo "ℹ️ 无安装文件，仅克隆代码"
                echo "repository cloned (no dependencies)" > ../logs/${dir_name}.log
            fi

            echo ""
            echo "✅ [$((i+1))/22] $display_name 安装完成"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            exit 0
        else
            echo ""
            echo "❌ 克隆失败: $display_name"
            # 清理失败的克隆
            rm -rf "$dir_name"
            exit 1
        fi
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 全部22个组件已安装完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
