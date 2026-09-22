#!/bin/bash

echo "=================================="
echo "FieldMind 文档和临时文件清理"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FIELDMIND_DIR="/Users/alwan/FieldMind"
HOME_DIR="/Users/alwan"

cd "$FIELDMIND_DIR"

echo "将要删除以下文件："
echo ""
echo "=== 重复/过时的文档 ==="
echo "  API_MAP.md"
echo "  FRONTEND_BACKEND_API_MAPPING.md"
echo "  AGENT_SKILL_ARCHITECTURE.md"
echo "  SKILL_AGENT_DESIGN.md"
echo "  WORKFLOW_DESIGN.md"
echo "  CURRENT_STATUS.md"
echo "  VERIFICATION_COMMANDS.md"
echo "  QUICK_START.md"
echo "  USER_MANUAL.md"
echo "  FAQ.md"
echo ""
echo "=== 临时文档 ==="
echo "  components_full_list.txt"
echo "  remaining_components.txt"
echo "  test_timeline_doc.txt"
echo ""
echo "=== 测试脚本 (34个Python + 9个Shell + 9个Swift) ==="
echo "  test_*.py"
echo "  test_*.sh"
echo "  test_*.swift"
echo "  *test*.html"
echo ""
echo "=== 修复脚本 (7个Python + 1个Shell) ==="
echo "  fix_*.py"
echo "  fix_*.sh"
echo ""
echo "=== 清理脚本 (4个) ==="
echo "  cleanup*.sh"
echo ""
echo "=== 其他临时脚本和文件 ==="
echo "  analyze_*.py"
echo "  benchmark_*.py"
echo "  create_*.py"
echo "  debug_*.py"
echo "  diagnose_*.py"
echo "  rebuild_*.py"
echo "  verify_*.py"
echo "  init_database.py"
echo "  code_quality_check.py"
echo "  manual_verify_remaining.py"
echo ""
echo "=== 用户主目录临时文件 ==="
echo "  ~/fix_fieldmind_app.sh"
echo "  ~/merge_fieldmind.sh"
echo "  ~/organize_fieldmind.sh"
echo ""
echo -e "${YELLOW}按 Enter 继续删除，或 Ctrl+C 取消${NC}"
read

echo ""
echo "开始清理..."
echo ""

# 1. 删除重复/过时的文档
echo "清理重复/过时的文档..."
rm -f API_MAP.md \
      FRONTEND_BACKEND_API_MAPPING.md \
      AGENT_SKILL_ARCHITECTURE.md \
      SKILL_AGENT_DESIGN.md \
      WORKFLOW_DESIGN.md \
      CURRENT_STATUS.md \
      VERIFICATION_COMMANDS.md \
      QUICK_START.md \
      USER_MANUAL.md \
      FAQ.md
echo -e "${GREEN}✓${NC} 已删除过时文档"

# 2. 删除临时文档
echo "清理临时文档..."
rm -f components_full_list.txt \
      remaining_components.txt \
      test_timeline_doc.txt
echo -e "${GREEN}✓${NC} 已删除临时文档"

# 3. 删除测试脚本
echo "清理测试脚本..."
rm -f test_*.py test_*.sh test_*.swift *test*.html
echo -e "${GREEN}✓${NC} 已删除测试脚本"

# 4. 删除修复脚本
echo "清理修复脚本..."
rm -f fix_*.py fix_*.sh
echo -e "${GREEN}✓${NC} 已删除修复脚本"

# 5. 删除清理脚本（但保留当前这个）
echo "清理旧的清理脚本..."
rm -f cleanup.sh cleanup_final.sh cleanup_safe.sh COMPLETE_FIX_SCRIPT.sh
echo -e "${GREEN}✓${NC} 已删除旧的清理脚本"

# 6. 删除其他临时Python脚本
echo "清理其他临时脚本..."
rm -f analyze_*.py \
      benchmark_*.py \
      create_*.py \
      debug_*.py \
      diagnose_*.py \
      rebuild_*.py \
      verify_*.py \
      init_database.py \
      code_quality_check.py \
      manual_verify_remaining.py \
      deep_verify_unused_modules.py
echo -e "${GREEN}✓${NC} 已删除临时脚本"

# 7. 删除用户主目录的临时文件
echo "清理用户主目录临时文件..."
rm -f "$HOME_DIR/fix_fieldmind_app.sh" \
      "$HOME_DIR/merge_fieldmind.sh" \
      "$HOME_DIR/organize_fieldmind.sh"
echo -e "${GREEN}✓${NC} 已删除主目录临时文件"

# 8. 清理旧的安装和部署脚本
echo "清理旧的安装/部署脚本..."
rm -f install*.sh \
      auto_install_all.sh \
      continue_install.sh \
      quick_install_remaining.sh \
      setup_isolated_envs.sh \
      create_ios_project.sh \
      create_web_project.sh \
      create_asgi_middleware.py \
      deploy*.sh \
      run_backend.sh \
      start_services.sh \
      start_system.sh \
      stop_system.sh \
      monitor.sh \
      system_status.sh \
      check_status.sh \
      diagnose_data_calls.sh \
      diagnostic_script.sh \
      demo_test.sh \
      final_report.sh \
      test_new_features.sh \
      quick_start.sh \
      quick_test.sh \
      run_all_tests.sh \
      test_auth_api.sh \
      test_api.sh \
      test_apis.sh \
      test_connection.sh \
      test_api_endpoints.sh \
      test_deployment.py \
      test_monitoring_system.py
echo -e "${GREEN}✓${NC} 已删除旧的安装/部署脚本"

# 9. 删除旧的HTML测试文件
echo "清理HTML测试文件..."
rm -f fieldmind_desktop_v2.html \
      fieldmind_working.html \
      debug_injector.html
echo -e "${GREEN}✓${NC} 已删除HTML测试文件"

echo ""
echo "=================================="
echo -e "${GREEN}清理完成！${NC}"
echo "=================================="
echo ""
echo "保留的核心文档："
echo "  ✓ README.md - 项目说明"
echo "  ✓ ARCHITECTURE.md - 系统架构"
echo "  ✓ API_REFERENCE.md - API文档"
echo "  ✓ CHANGELOG.md - 更新日志"
echo "  ✓ CONTRIBUTING.md - 贡献指南"
echo ""
echo "保留的核心脚本："
echo "  ✓ 启动FieldMind.command - 启动脚本"
echo "  ✓ 停止FieldMind.command - 停止脚本"
echo "  ✓ start.sh - 简单启动脚本"
echo "  ✓ stop.sh - 简单停止脚本"
echo "  ✓ manage.sh - 管理脚本"
echo ""
echo "项目现在更干净整洁了！"
echo ""
