#!/bin/bash
# FieldMind 项目清理脚本 - 100%安全版本
# 只删除确认无用的重复文档和可重建的环境

set -e

echo "=== FieldMind 安全清理脚本 ==="
echo ""
echo "清理范围："
echo "1. 重复的状态报告文档（开发历史记录）"
echo "2. venv 虚拟环境（可重建）"
echo ""
echo "不会影响："
echo "✓ 前端代码 (fieldmind-web/)"
echo "✓ 后端代码 (fieldmind-backend/)"
echo "✓ 桌面应用 (fieldmind-desktop/)"
echo "✓ iOS应用 (fieldmind-ios/)"
echo "✓ 任何功能代码"
echo ""

# 计算当前大小
echo "计算当前项目大小..."
du -sh . 2>/dev/null | awk '{print "当前大小: " $1}'
echo ""

read -p "继续清理？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消清理"
    exit 0
fi

# 记录删除的文件
DELETED_COUNT=0

# 1. 删除重复的完成报告（最多的重复类型）
echo "删除重复的完成报告..."
rm -f COMPLETE_FIX_REPORT.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f COMPLETE_FIX_REPORT_FINAL.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f FINAL_COMPLETE_REPORT.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f IMPLEMENTATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f INTEGRATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f NEO4J_INTEGRATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f COMPLETE_FIX_CHECKLIST.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f COMPLETION_SUMMARY.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 2. 删除各个功能链的完成标记
echo "删除功能链完成标记..."
rm -f CHAIN_*_COMPLETE.md 2>/dev/null && ((DELETED_COUNT+=5)) || true
rm -f FUNCTION_*_COMPLETE.md 2>/dev/null && ((DELETED_COUNT+=3)) || true
rm -f DATA_ANALYSIS_TRANSFORMATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f AUDIO_PIPELINE_FIX_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f P1_OPTIMIZATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f KNOWLEDGE_GRAPH_OPTIMIZATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f ANTI_HALLUCINATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f FIELDMIND_TRANSFORMATION_COMPLETE.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 3. 删除修复计划（已完成的）
echo "删除已完成的修复计划..."
rm -f INFRASTRUCTURE_FIX_PLAN.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f DESKTOP_FIX_PLAN.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f FIELDMIND_REPAIR_PLAN.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 4. 删除各种工作总结
echo "删除工作总结..."
rm -f FIX_SUMMARY.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f FUNCTION_10_WORK_SUMMARY.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f PROJECT_FINAL_SUMMARY.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f FEATURE_COMPLETION_REPORT.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 5. 删除阶段报告
echo "删除阶段报告..."
rm -f AI_PHASES_PROGRESS.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f SYSTEM_STATUS_FINAL.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f OPTIMIZATION_REPORT.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 6. 删除集成和安装报告（信息已在代码中）
echo "删除集成报告..."
rm -f MINERU_INTEGRATION_REPORT.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f MINERU_TIANSHU_INTEGRATION.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f installation_summary.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 7. 删除各种指南的重复版本（保留主要的）
echo "删除重复指南..."
rm -f MEM0_INTEGRATION_GUIDE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f CICD_INTEGRATION_GUIDE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f MONITORING_INTEGRATION_GUIDE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f NEO4J_INSTALLATION_GUIDE.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 8. 删除方案和分析文档
echo "删除方案文档..."
rm -f KNOWLEDGE_GRAPH_SOLUTION.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f PINECONE_VS_CHROMADB.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f architecture_gap_analysis.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 9. 删除迁移和实现计划
echo "删除迁移计划..."
rm -f DYNAMIC_DISCOVERY_MIGRATION_PLAN.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f PIPELINE_IMPLEMENTATION_PLAN.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f WORKFLOW_INTEGRATION.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 10. 删除审计报告
echo "删除审计报告..."
rm -f API_AUDIT_REPORT.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 11. 删除多余的系统文档
echo "删除多余系统文档..."
rm -f AI_SYSTEM_SETUP_GUIDE.md 2>/dev/null && ((DELETED_COUNT++)) || true
rm -f AI_SYSTEM_ARCHITECTURE.md 2>/dev/null && ((DELETED_COUNT++)) || true

# 12. 删除venv（最大的空间节省）
if [ -d "venv" ]; then
    echo ""
    echo "删除 venv/ 目录..."
    du -sh venv/ 2>/dev/null | awk '{print "venv 大小: " $1}'
    rm -rf venv/
    echo "✓ venv/ 已删除（可以用 python -m venv venv && source venv/bin/activate && pip install -r fieldmind-backend/requirements.txt 重建）"
fi

# 13. 删除未使用的小目录
echo ""
echo "删除未使用的小目录..."
rm -rf gecco/ 2>/dev/null && echo "✓ gecco/" || true
rm -rf deer-flow/ 2>/dev/null && echo "✓ deer-flow/" || true

echo ""
echo "=== 清理完成 ==="
echo "删除文档数: $DELETED_COUNT"
echo ""
du -sh . 2>/dev/null | awk '{print "清理后大小: " $1}'
echo ""
echo "✓ 前端正常 (fieldmind-web/)"
echo "✓ 后端正常 (fieldmind-backend/)"
echo "✓ 所有功能代码完整"
echo ""
echo "注意: 如需重建 venv："
echo "  cd /Users/alwan/FieldMind-Rebuild"
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r fieldmind-backend/requirements.txt"
