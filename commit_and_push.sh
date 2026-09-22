#!/bin/bash

#
# commit_and_push.sh
# 提交并推送 FieldMind 统一整合
#

set -e

cd /Users/alwan/FieldMind

echo "📊 检查 Git 状态..."
git status

echo ""
echo "➕ 添加所有更改..."
git add .

echo ""
echo "📝 创建提交..."
git commit -m "统一整合 FieldMind：原生 macOS 应用 + 后端 + 知识库

✨ 新功能
- 统一的 Swift/SwiftUI 主应用
- 自动启动/停止 Python 后端服务
- 集成 Obsidian 风格知识库（笔记、双向链接、知识图谱）
- 完整的知识蒸馏系统界面
- 九大功能模块导航

🏗️ 架构改进
- 迁移 fieldmind-native 所有模块到主 Xcode 项目
- 后端服务生命周期管理（BackendService）
- 知识库文件系统管理（KnowledgeVaultService）
- 统一的应用入口和导航系统

📦 项目结构
- fieldmind/fieldmind/ - Swift 主应用
  - Services/ - 服务层（后端、蒸馏、知识库）
  - Views/ - 视图层（主导航、知识库、蒸馏）
  - ViewModels/ - 视图模型
  - Components/ - 可复用组件
  - Pages/ - 页面模块
  - Network/ - 网络层
  - Core/ - 核心功能
  - DesignSystem/ - 设计系统
- backend/ - Python FastAPI 后端
- obsidian-releases/ - Obsidian 集成

🚀 使用方式
1. 运行构建脚本：./build_unified_app.sh
2. 启动应用：双击 FieldMind.app
3. 后端自动启动，无需手动管理

📚 文档
- UNIFICATION_PLAN.md - 整合方案文档
- DISTILLATION_INTEGRATION_COMPLETE.md - 蒸馏系统文档

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"

echo ""
echo "🔍 显示提交信息..."
git log -1 --stat

echo ""
read -p "是否推送到远程仓库？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 推送到远程仓库..."

    # 检查是否有远程仓库
    if git remote | grep -q "origin"; then
        git push origin main
        echo "✅ 推送完成！"
    else
        echo "⚠️  未配置远程仓库"
        echo ""
        echo "配置远程仓库："
        echo "  git remote add origin <your-repo-url>"
        echo "  git push -u origin main"
    fi
else
    echo "⏭️  跳过推送"
fi

echo ""
echo "✅ Git 操作完成！"
