#!/bin/bash

echo "=== Phase 7 库克隆状态检查 ==="
echo "检查时间: $(date)"
echo ""

LIBS_DIR="external_libs"

# 必须安装的库（9个）
REQUIRED_LIBS=(
    "sentence-transformers"
    "unstructured"
    "PaddleOCR"
    "FunASR"
    "HanLP"
    "pyannote-audio"
    "ragas"
    "deepeval"
    "celery"
)

# 推荐安装的库（3个）
RECOMMENDED_LIBS=(
    "noScribe"
    "hamilton"
    "langchain"
)

# 已克隆的库（延后Phase 8）
DEFERRED_LIBS=(
    "AutoRAG"
    "KAG"
    "n8n"
    "ImageBind"
)

check_status() {
    local category=$1
    shift
    local libs=("$@")
    local success=0
    local total=${#libs[@]}

    echo "=== $category ==="
    for lib in "${libs[@]}"; do
        if [ -d "$LIBS_DIR/$lib" ]; then
            echo "✅ $lib"
            ((success++))
        else
            echo "❌ $lib - 未克隆"
        fi
    done
    echo "进度: $success/$total"
    echo ""
}

check_status "必须库 (9个)" "${REQUIRED_LIBS[@]}"
check_status "推荐库 (3个)" "${RECOMMENDED_LIBS[@]}"
check_status "已有库 (延后Phase 8)" "${DEFERRED_LIBS[@]}"

echo "=== 总览 ==="
echo "external_libs/ 目录中的所有库:"
ls -d "$LIBS_DIR"/*/ 2>/dev/null | xargs -n1 basename | sort
echo ""
echo "总数: $(ls -d "$LIBS_DIR"/*/ 2>/dev/null | wc -l | tr -d ' ')"
