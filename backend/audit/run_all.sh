#!/bin/bash
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         FieldMind 系统全面审计                            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

mkdir -p audit/reports
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "【1/7】扫描所有实例..."
bash audit/1_find_all_instances.sh > audit/reports/1_instances_$TIMESTAMP.txt 2>&1
cat audit/reports/1_instances_$TIMESTAMP.txt

echo ""
echo "【2/7】检查数据完整性..."
python3 audit/2_check_data_integrity.py > audit/reports/2_data_$TIMESTAMP.txt 2>&1
cat audit/reports/2_data_$TIMESTAMP.txt

echo ""
echo "【3/7】检查API断联..."
python3 audit/3_check_api_connections.py > audit/reports/3_api_$TIMESTAMP.txt 2>&1
cat audit/reports/3_api_$TIMESTAMP.txt

echo ""
echo "【4/7】检查工作流..."
python3 audit/4_check_workflow.py > audit/reports/4_workflow_$TIMESTAMP.txt 2>&1
cat audit/reports/4_workflow_$TIMESTAMP.txt

echo ""
echo "【5/7】检查边界合规..."
python3 audit/5_check_boundaries.py > audit/reports/5_boundary_$TIMESTAMP.txt 2>&1
cat audit/reports/5_boundary_$TIMESTAMP.txt

echo ""
echo "【6/7】检查代码bug..."
python3 audit/6_check_bugs.py > audit/reports/6_bugs_$TIMESTAMP.txt 2>&1
cat audit/reports/6_bugs_$TIMESTAMP.txt

echo ""
echo "【7/7】检查功能缺口..."
python3 audit/7_check_gaps.py > audit/reports/7_gaps_$TIMESTAMP.txt 2>&1
cat audit/reports/7_gaps_$TIMESTAMP.txt

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  审计完成！报告保存在 audit/reports/                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "报告文件："
echo "  1. audit/reports/1_instances_$TIMESTAMP.txt"
echo "  2. audit/reports/2_data_$TIMESTAMP.txt"
echo "  3. audit/reports/3_api_$TIMESTAMP.txt"
echo "  4. audit/reports/4_workflow_$TIMESTAMP.txt"
echo "  5. audit/reports/5_boundary_$TIMESTAMP.txt"
echo "  6. audit/reports/6_bugs_$TIMESTAMP.txt"
echo "  7. audit/reports/7_gaps_$TIMESTAMP.txt"
