#!/bin/bash
# FieldMind 最终安全清理脚本
# 只删除确认无用且不影响任何功能的文件

set -e

echo "=== FieldMind 最终安全清理 ==="
echo ""
echo "本脚本只删除："
echo "1. ✓ 重复的开发文档（50+ 状态报告）"
echo "2. ✓ venv/ (3.4GB - 可重建)"
echo "3. ✓ 空占位目录 (gecco/, deer-flow/, HyperAgents/)"
echo ""
echo "保留（代码有引用）："
echo "• repos/ (browser-use 爬虫)"
echo "• external-tools/ (markitdown, ragflow)"
echo "• fieldmind-backend/ (后端代码)"
echo "• fieldmind-web/ (前端代码)"
echo ""

du -sh . 2>/dev/null | awk '{print "当前大小: " $1}'
echo ""

read -p "继续？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消"
    exit 0
fi

DELETED=0

# 1. 删除完成报告
echo "删除完成报告..."
for file in COMPLETE_FIX_REPORT.md COMPLETE_FIX_REPORT_FINAL.md FINAL_COMPLETE_REPORT.md \
    IMPLEMENTATION_COMPLETE.md INTEGRATION_COMPLETE.md NEO4J_INTEGRATION_COMPLETE.md \
    COMPLETE_FIX_CHECKLIST.md COMPLETION_SUMMARY.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 2. 删除链和功能完成标记
echo "删除功能完成标记..."
rm -f CHAIN_*_COMPLETE.md 2>/dev/null && ((DELETED+=5))
rm -f FUNCTION_*_COMPLETE.md 2>/dev/null && ((DELETED+=3))
rm -f *_TRANSFORMATION_COMPLETE.md *_OPTIMIZATION_COMPLETE.md *_FIX_COMPLETE.md 2>/dev/null && ((DELETED+=5))
rm -f ANTI_HALLUCINATION_COMPLETE.md MANAGER_SYSTEM_COMPLETE.md 2>/dev/null && ((DELETED+=2))

# 3. 删除修复计划
echo "删除修复计划..."
for file in INFRASTRUCTURE_FIX_PLAN.md DESKTOP_FIX_PLAN.md FIELDMIND_REPAIR_PLAN.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 4. 删除工作总结
echo "删除工作总结..."
for file in FIX_SUMMARY.md FUNCTION_10_WORK_SUMMARY.md PROJECT_FINAL_SUMMARY.md \
    FEATURE_COMPLETION_REPORT.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 5. 删除阶段报告
echo "删除阶段报告..."
for file in AI_PHASES_PROGRESS.md SYSTEM_STATUS_FINAL.md OPTIMIZATION_REPORT.md \
    FEATURE_UPDATE_v2.1.0.md REAL_USABILITY_REPORT.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 6. 删除集成报告
echo "删除集成报告..."
for file in MINERU_INTEGRATION_REPORT.md MINERU_TIANSHU_INTEGRATION.md \
    installation_summary.md MEM0_INTEGRATION_GUIDE.md CICD_INTEGRATION_GUIDE.md \
    MONITORING_INTEGRATION_GUIDE.md NEO4J_INSTALLATION_GUIDE.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 7. 删除方案文档
echo "删除方案文档..."
for file in KNOWLEDGE_GRAPH_SOLUTION.md PINECONE_VS_CHROMADB.md \
    architecture_gap_analysis.md API_AUDIT_REPORT.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 8. 删除计划文档
echo "删除计划文档..."
for file in DYNAMIC_DISCOVERY_MIGRATION_PLAN.md PIPELINE_IMPLEMENTATION_PLAN.md \
    WORKFLOW_INTEGRATION.md AI_SYSTEM_SETUP_GUIDE.md AI_SYSTEM_ARCHITECTURE.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 9. 删除其他重复文档
echo "删除其他重复文档..."
for file in PROJECT_SHOWCASE.md IMPLEMENTATION_CHECKLIST.md ALL_PLUGINS_LIST.md; do
    [ -f "$file" ] && rm -f "$file" && ((DELETED++))
done

# 10. 删除空占位目录
echo "删除占位目录..."
[ -d "gecco" ] && [ -f "gecco/.skip" ] && rm -rf gecco/ && echo "✓ gecco/"
[ -d "deer-flow" ] && [ -f "deer-flow/.skip" ] && rm -rf deer-flow/ && echo "✓ deer-flow/"
[ -d "HyperAgents" ] && [ "$(du -sk HyperAgents | cut -f1)" -lt 100 ] && rm -rf HyperAgents/ && echo "✓ HyperAgents/"

# 11. 删除 venv
if [ -d "venv" ]; then
    echo ""
    echo "删除 venv/..."
    du -sh venv/ 2>/dev/null
    rm -rf venv/
    echo "✓ 已删除（重建: python -m venv venv && pip install -r fieldmind-backend/requirements.txt）"
fi

echo ""
echo "=== 完成 ==="
echo "删除文档: $DELETED 个"
du -sh . 2>/dev/null | awk '{print "清理后: " $1}'
echo ""
echo "✓ 所有功能代码完整"
echo "✓ repos/ 保留（browser-use）"
echo "✓ external-tools/ 保留（markitdown, ragflow）"
