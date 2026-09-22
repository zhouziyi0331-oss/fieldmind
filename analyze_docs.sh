#!/bin/bash

echo "=================================="
echo "FieldMind 文档清理分析报告"
echo "=================================="
echo ""

cd /Users/alwan/FieldMind

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== 1. 重复/过时的 API 文档 ===${NC}"
echo ""
echo "API_MAP.md (937B, Jul 30) - 简单的API映射"
echo "API_REFERENCE.md (13K, Aug 3) - 详细的API文档"
echo "FRONTEND_BACKEND_API_MAPPING.md (18K, Jul 30) - 前后端API映射"
echo ""
echo -e "${YELLOW}建议：保留 API_REFERENCE.md，删除 API_MAP.md 和 FRONTEND_BACKEND_API_MAPPING.md${NC}"
echo ""

echo -e "${BLUE}=== 2. 重复的架构文档 ===${NC}"
echo ""
echo "ARCHITECTURE.md (14K, Jul 30) - 系统架构"
echo "AGENT_SKILL_ARCHITECTURE.md (12K, Aug 13) - Agent/Skill架构"
echo "SKILL_AGENT_DESIGN.md (11K, Aug 13) - Agent/Skill设计"
echo "WORKFLOW_DESIGN.md (17K, Jul 30) - 工作流设计"
echo ""
echo -e "${YELLOW}建议：保留 ARCHITECTURE.md，其他是特定功能设计（可能过时）${NC}"
echo ""

echo -e "${BLUE}=== 3. 临时/测试文档 ===${NC}"
echo ""
echo "components_full_list.txt (1.3K, Jul 30) - 组件列表"
echo "remaining_components.txt (857B, Jul 30) - 剩余组件"
echo "test_timeline_doc.txt (1.4K, Jul 31) - 测试时间线"
echo "CURRENT_STATUS.md (5.4K, Aug 2) - 当前状态（已过时）"
echo "VERIFICATION_COMMANDS.md (7.8K, Aug 6) - 验证命令"
echo ""
echo -e "${YELLOW}建议：全部删除，这些是开发过程中的临时记录${NC}"
echo ""

echo -e "${BLUE}=== 4. 过时的用户文档 ===${NC}"
echo ""
echo "QUICK_START.md (1.6K, Jul 31) - 快速开始"
echo "USER_MANUAL.md (12K, Aug 3) - 用户手册"
echo "FAQ.md (10K, Aug 3) - 常见问题"
echo ""
echo -e "${YELLOW}建议：内容可能过时，需要检查后决定${NC}"
echo ""

echo -e "${BLUE}=== 5. 有用的文档（保留） ===${NC}"
echo ""
echo "README.md (2.8K, Aug 9) - 项目说明 ✓"
echo "CHANGELOG.md (6.4K, Aug 3) - 更新日志 ✓"
echo "CONTRIBUTING.md (8.3K, Aug 3) - 贡献指南 ✓"
echo ""

echo ""
echo -e "${BLUE}=== 6. 根目录散落的测试脚本 ===${NC}"
echo ""
ls -lh /Users/alwan/FieldMind/*test*.py 2>/dev/null | wc -l | xargs echo "Python测试脚本数量："
ls -lh /Users/alwan/FieldMind/*test*.sh 2>/dev/null | wc -l | xargs echo "Shell测试脚本数量："
ls -lh /Users/alwan/FieldMind/*test*.swift 2>/dev/null | wc -l | xargs echo "Swift测试脚本数量："
echo ""
echo -e "${YELLOW}建议：这些测试脚本大部分是一次性的，可以移到 archive/ 或删除${NC}"
echo ""

echo -e "${BLUE}=== 7. 一次性修复脚本 ===${NC}"
echo ""
ls -1 /Users/alwan/FieldMind/fix_*.py 2>/dev/null | wc -l | xargs echo "修复脚本数量："
ls -1 /Users/alwan/FieldMind/fix_*.sh 2>/dev/null | wc -l | xargs echo "修复Shell脚本数量："
ls -1 /Users/alwan/FieldMind/*clean*.sh 2>/dev/null | wc -l | xargs echo "清理脚本数量："
echo ""
echo -e "${YELLOW}建议：这些都是一次性的修复脚本，问题已解决，可以删除${NC}"
echo ""

echo -e "${BLUE}=== 8. 用户主目录下的临时文件 ===${NC}"
echo ""
ls -lh /Users/alwan/fix_fieldmind_app.sh 2>/dev/null
ls -lh /Users/alwan/merge_fieldmind.sh 2>/dev/null
ls -lh /Users/alwan/organize_fieldmind.sh 2>/dev/null
echo ""
echo -e "${YELLOW}建议：这些是临时脚本，可以删除${NC}"
echo ""

echo ""
echo "=================================="
echo "清理建议总结"
echo "=================================="
echo ""
echo "可以安全删除的文件类型："
echo "1. 重复的API文档（保留最完整的）"
echo "2. 过时的架构设计文档（特定功能的，不是核心的）"
echo "3. 所有临时测试脚本和文件列表"
echo "4. 所有一次性修复脚本"
echo "5. 根目录下的临时清理脚本"
echo ""
echo "建议保留："
echo "- README.md"
echo "- ARCHITECTURE.md"
echo "- API_REFERENCE.md"
echo "- CHANGELOG.md"
echo "- CONTRIBUTING.md"
echo ""
echo "如果确认要清理，运行："
echo "  ./cleanup_docs.sh"
echo ""
