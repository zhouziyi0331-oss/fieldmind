#!/bin/bash
# FieldMind 项目清理脚本
# 运行前会创建备份列表，可以随时恢复

set -e

echo "🧹 FieldMind 项目清理工具"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 统计函数
get_size() {
    du -sh "$1" 2>/dev/null | awk '{print $1}'
}

TOTAL_SAVED=0

echo "📊 当前项目大小分析："
echo "- 总大小: $(get_size .)"
echo "- venv: $(get_size venv)"
echo "- fieldmind-backend: $(get_size fieldmind-backend)"
echo "- repos: $(get_size repos)"
echo ""

# ============================================================================
# 第一步：删除重复的文档文件
# ============================================================================
echo "📄 第一步：清理重复的文档文件"
echo "--------------------------------"

# 创建归档目录
mkdir -p docs/archive/{completed,reports,plans}

# 要删除的文档列表
DOCS_TO_DELETE=(
    # 状态报告（保留 CURRENT_STATUS.md）
    "SYSTEM_STATUS_FINAL.md"
    "REPOS_STATUS.md"
    "COMPLETE_STATUS_SUMMARY.md"
    "SYSTEM_READY_REPORT.md"

    # 完成报告（重复太多）
    "COMPLETE_FIX_REPORT.md"
    "COMPLETE_FIX_REPORT_FINAL.md"
    "COMPLETE_FIX_SUMMARY.md"
    "COMPLETE_IMPLEMENTATION_REPORT.md"
    "FINAL_IMPLEMENTATION_REPORT.md"
    "PROJECT_COMPLETION_REPORT.md"
    "IMPLEMENTATION_COMPLETE.md"

    # 集成报告
    "INTEGRATION_COMPLETE.md"
    "FINAL_INTEGRATION_REPORT.md"
    "TOOLS_INTEGRATION_COMPLETE.md"

    # 修复计划（已完成）
    "DESKTOP_FIX_PLAN.md"
    "SYSTEM_FIX_PLAN.md"
    "PRIORITY_FIX_PLAN.md"
    "ORIGINAL_APP_FIX_PLAN.md"
    "INFRASTRUCTURE_FIX_PLAN.md"
    "COMPLETE_FIX_CHECKLIST.md"
    "BUG_FIX_CHECKLIST.md"
    "FIELDMIND_REPAIR_PLAN.md"

    # 功能完成标记
    "MANAGER_SYSTEM_COMPLETE.md"
    "SOURCE_TRACEBACK_COMPLETE.md"
    "PIPELINE_IMPLEMENTATION_COMPLETE.md"
    "DOCUMENT_PIPELINE_COMPLETE.md"
    "ADAPTIVE_INTELLIGENCE_COMPLETE.md"
    "COMPLETE_WORKFLOW_VERIFICATION.md"
    "DYNAMIC_DISCOVERY_MIGRATION_PLAN.md"
    "PIPELINE_IMPLEMENTATION_PLAN.md"
    "DEEP_INTEGRATION_PLAN.md"

    # 测试报告
    "TEST_REPORT_UPDATED.md"
    "DYNAMIC_DISCOVERY_TEST_REPORT.md"
    "TOOL_EXECUTION_REPORT.md"

    # 指南（合并到主指南）
    "MANAGER_USAGE_GUIDE.md"
    "COMPLETE_USER_GUIDE.md"
    "ADAPTIVE_TESTING_GUIDE.md"

    # 特定功能文档
    "BACKEND_FRONTEND_FIXES.md"
    "FRONTEND_FIX_COMPLETE_SUMMARY.md"
    "MINERU_INTEGRATION_REPORT.md"
    "MINERU_DEPLOYMENT_STATUS.md"
    "MINERU_TIANSHU_INTEGRATION.md"

    # 分析报告
    "API_AUDIT_REPORT.md"
    "GAP_ANALYSIS_REPORT.md"
    "REAL_USABILITY_REPORT.md"
    "FIX_SUMMARY.md"

    # AI phases 相关（如果不需要）
    "AI_PHASES_PROGRESS.md"
    "AI_SYSTEM_ARCHITECTURE.md"
    "AI_SYSTEM_SETUP_GUIDE.md"

    # 其他完成文档
    "AUDIO_PIPELINE_FIX_COMPLETE.md"
    "ANTI_HALLUCINATION_COMPLETE.md"
    "DATA_ANALYSIS_TRANSFORMATION_COMPLETE.md"
    "FEATURE_COMPLETION_REPORT.md"
    "FIELDMIND_TRANSFORMATION_COMPLETE.md"
    "FUNCTION_09_FRONTEND_COMPLETE.md"
    "FUNCTION_10_DEPLOYMENT_COMPLETE.md"
    "FUNCTION_10_WORK_SUMMARY.md"
    "FUNCTION_11_MONITORING_COMPLETE.md"
    "KNOWLEDGE_GRAPH_OPTIMIZATION_COMPLETE.md"
    "KNOWLEDGE_GRAPH_SOLUTION.md"
    "NEO4J_INTEGRATION_COMPLETE.md"
    "OPTIMIZATION_REPORT.md"
    "P1_OPTIMIZATION_COMPLETE.md"

    # Chain 相关报告
    "CHAIN_10_SEMANTIC_EMBEDDING_REPORT.md"
    "CHAIN_11_KNOWLEDGE_GRAPH_COMPLETE.md"
    "CHAIN_12_WORKFLOW_COMPLETE.md"
    "CHAIN_13_MEMORY_COMPLETE.md"
    "CHAIN_14_CITATION_COMPLETE.md"
)

DOC_COUNT=0
for doc in "${DOCS_TO_DELETE[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ❌ 删除: $doc"
        rm "$doc"
        ((DOC_COUNT++))
    fi
done

echo -e "${GREEN}✅ 删除了 $DOC_COUNT 个重复文档${NC}"
echo ""

# ============================================================================
# 第二步：删除虚拟环境（可重建）
# ============================================================================
echo "🐍 第二步：删除虚拟环境 (venv/)"
echo "--------------------------------"
if [ -d "venv" ]; then
    VENV_SIZE=$(get_size venv)
    echo "  当前大小: $VENV_SIZE"
    echo "  删除后可用命令重建: python3 -m venv venv"
    rm -rf venv
    echo -e "${GREEN}✅ 已删除 venv/，节省约 $VENV_SIZE${NC}"
else
    echo "  ℹ️  venv/ 不存在，跳过"
fi
echo ""

# ============================================================================
# 第三步：检查并删除重复的后端目录
# ============================================================================
echo "📦 第三步：检查后端目录"
echo "--------------------------------"
if [ -d "fieldmind-backend" ] && [ -d "backend" ]; then
    echo "  ⚠️  发现重复的后端目录:"
    echo "    - fieldmind-backend/: $(get_size fieldmind-backend)"
    echo "    - backend/: $(get_size backend)"
    echo "  建议：手动检查两个目录内容，保留一个删除另一个"
elif [ -d "fieldmind-backend" ]; then
    echo "  ℹ️  只有 fieldmind-backend/ 存在"
else
    echo "  ℹ️  后端目录结构正常"
fi
echo ""

# ============================================================================
# 第四步：清理 repos 目录中未使用的仓库
# ============================================================================
echo "📂 第四步：检查 repos/ 目录"
echo "--------------------------------"
if [ -d "repos" ]; then
    echo "  当前大小: $(get_size repos)"
    echo "  包含的仓库:"
    ls -1 repos/ 2>/dev/null | sed 's/^/    - /'
    echo ""
    echo "  建议：手动检查并删除未使用的外部仓库"
else
    echo "  ℹ️  repos/ 不存在，跳过"
fi
echo ""

# ============================================================================
# 第五步：清理 external-tools 目录
# ============================================================================
echo "🔧 第五步：检查 external-tools/ 目录"
echo "--------------------------------"
if [ -d "external-tools" ]; then
    echo "  当前大小: $(get_size external-tools)"
    echo "  包含的工具:"
    ls -1 external-tools/ 2>/dev/null | sed 's/^/    - /'
    echo ""
    echo "  建议：只保留实际使用的工具"
else
    echo "  ℹ️  external-tools/ 不存在，跳过"
fi
echo ""

# ============================================================================
# 第六步：清理其他小目录
# ============================================================================
echo "🗑️  第六步：清理其他未使用的目录"
echo "--------------------------------"

SMALL_DIRS=(
    "gecco"
    "deer-flow"
    "codebase-memory-mcp"
    "awesome-knowledge-graph"
)

for dir in "${SMALL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ❌ 删除: $dir/ ($(get_size $dir))"
        rm -rf "$dir"
    fi
done
echo -e "${GREEN}✅ 已清理未使用的小目录${NC}"
echo ""

# ============================================================================
# 总结
# ============================================================================
echo "================================"
echo "🎉 清理完成！"
echo ""
echo "📊 新的项目大小: $(get_size .)"
echo ""
echo "💡 下一步建议："
echo "  1. 重建虚拟环境: python3 -m venv venv && source venv/bin/activate"
echo "  2. 安装依赖: pip install -r requirements.txt"
echo "  3. 手动检查并清理:"
echo "     - repos/ 目录（1.8GB）"
echo "     - fieldmind-backend/ 目录（2.7GB）"
echo "     - external-tools/ 目录（203MB）"
echo ""
echo "预计可以再节省 2-4GB 空间"
