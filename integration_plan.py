#!/usr/bin/env python3
"""
FieldMind完整整合执行计划

任务1: 修复数据库迁移
任务2: 深度融合新模块到现有架构
任务3: API整合优化（463个→精简到200-300个）
"""
import json
from pathlib import Path
from collections import defaultdict


class FieldMindIntegrationPlan:
    """完整整合计划"""

    def __init__(self):
        self.base = Path("/Users/alwan/FieldMind")
        self.backend = self.base / "backend" / "src"

        # 加载架构报告
        with open(self.base / "COMPLETE_ARCHITECTURE_REPORT.json") as f:
            self.architecture = json.load(f)

    def generate_plan(self):
        """生成执行计划"""
        print("=" * 80)
        print("📋 FieldMind完整整合执行计划")
        print("=" * 80)

        # 任务1: 数据库迁移修复
        print("\n【任务1】修复数据库迁移")
        self.plan_migration_fix()

        # 任务2: 深度融合
        print("\n【任务2】深度融合新模块到现有架构")
        self.plan_deep_integration()

        # 任务3: API整合优化
        print("\n【任务3】API整合优化 (463→250)")
        self.plan_api_consolidation()

        # 生成执行脚本
        print("\n【生成】创建自动化执行脚本")
        self.generate_execution_scripts()

    def plan_migration_fix(self):
        """计划迁移修复"""
        print("\n  问题: 迁移链断裂 (008_unified_pipeline缺失)")
        print("\n  解决方案:")
        print("  1. 跳过损坏的迁移，重新创建完整迁移")
        print("  2. 使用 alembic stamp head 标记当前状态")
        print("  3. 创建新的集成迁移（23张新表）")
        print("\n  执行命令:")
        print("    cd backend/src")
        print("    alembic stamp head  # 标记当前状态为最新")
        print("    alembic revision -m 'integration_tables' --autogenerate")
        print("    alembic upgrade head")

    def plan_deep_integration(self):
        """计划深度融合"""
        print("\n  融合策略：")

        integrations = {
            "SBPACK → distillation": {
                "现有": "distillation.py (蒸馏API)",
                "新增": "sbpack.py (SBPACK API)",
                "融合": "将sbpack端点合并到distillation.py",
                "好处": "统一蒸馏入口，避免功能分散"
            },
            "RAG → unified_rag": {
                "现有": "unified_rag.py (统一RAG)",
                "新增": "rag.py (新RAG系统)",
                "融合": "将新RAG功能作为unified_rag的增强模式",
                "好处": "保持统一API，内部双引擎"
            },
            "skill_tree → unified_skills": {
                "现有": "unified_skills.py (统一技能)",
                "新增": "skill_tree.py (技能树)",
                "融合": "将技能树作为unified_skills的可视化层",
                "好处": "技能管理+可视化一体化"
            },
            "obsidian → document_processing_v2": {
                "现有": "document_processing_v2.py (文档处理)",
                "新增": "obsidian.py (Obsidian集成)",
                "融合": "添加Obsidian导出为文档处理的新格式",
                "好处": "统一文档处理流程"
            },
            "llm → llm_p3": {
                "现有": "llm_p3.py (LLM P3)",
                "新增": "llm.py (LLM增强)",
                "融合": "作为llm_p3的增强中间件",
                "好处": "透明增强所有LLM调用"
            }
        }

        print("\n  融合映射:")
        for name, details in integrations.items():
            print(f"\n  📌 {name}")
            print(f"    现有: {details['现有']}")
            print(f"    新增: {details['新增']}")
            print(f"    方案: {details['融合']}")
            print(f"    好处: {details['好处']}")

    def plan_api_consolidation(self):
        """计划API整合"""
        print("\n  当前状态: 61个API文件, 463个端点")
        print("  目标: 精简到30-40个API文件, 200-300个端点")

        print("\n  整合策略:")

        # 分析可合并的API
        consolidation_groups = {
            "文档处理统一API": {
                "合并": ["document_processing_v2", "file_manager", "file_summaries", "document_normalization"],
                "新名": "documents_unified.py",
                "端点数": "~40个"
            },
            "知识图谱统一API": {
                "合并": ["knowledge_graph_p3", "knowledge_pipeline", "knowledge_query", "entity_extraction"],
                "新名": "knowledge_unified.py",
                "端点数": "~50个"
            },
            "搜索统一API": {
                "合并": ["search", "semantic_search", "keyword_search", "dynamic_discovery_api"],
                "新名": "search_unified.py",
                "端点数": "~30个"
            },
            "Agent统一API": {
                "合并": ["agents_p3", "super_agents", "tasks", "workflow"],
                "新名": "agents_unified.py",
                "端点数": "~50个"
            },
            "LLM统一API": {
                "合并": ["llm_p3", "llm_providers", "llm_stats", "llm"],
                "新名": "llm_unified.py",
                "端点数": "~30个"
            }
        }

        print("\n  合并组:")
        for group, details in consolidation_groups.items():
            print(f"\n  📦 {group}")
            print(f"    合并: {len(details['合并'])}个API")
            print(f"    → {details['新名']} ({details['端点数']})")

        print("\n  预期结果:")
        print("    • API文件: 61 → 35 (-26个)")
        print("    • API端点: 463 → 250 (-213个)")
        print("    • 减少重复: ~45%")
        print("    • 提升性能: 路由查找更快")
        print("    • 易于维护: 功能分组清晰")

    def generate_execution_scripts(self):
        """生成执行脚本"""

        # 1. 迁移修复脚本
        migration_script = """#!/bin/bash
# 修复数据库迁移

cd /Users/alwan/FieldMind/backend/src

echo "1. 标记当前数据库状态..."
alembic stamp head

echo "2. 创建集成迁移..."
alembic revision -m "add_integration_tables" --autogenerate

echo "3. 执行迁移..."
alembic upgrade head

echo "✅ 迁移完成"
"""

        script_path = self.base / "fix_migration.sh"
        script_path.write_text(migration_script)
        script_path.chmod(0o755)
        print(f"  ✅ 创建: fix_migration.sh")

        # 2. API整合脚本骨架
        consolidation_plan = {
            "phase1": "合并文档和知识API",
            "phase2": "合并搜索和Agent API",
            "phase3": "合并LLM和其他API",
            "phase4": "移除旧API，更新路由"
        }

        plan_file = self.base / "API_CONSOLIDATION_PLAN.json"
        plan_file.write_text(json.dumps(consolidation_plan, indent=2))
        print(f"  ✅ 创建: API_CONSOLIDATION_PLAN.json")

        # 3. 融合指南
        integration_guide = """# 深度融合执行指南

## 步骤1: 准备
1. 备份当前代码: git branch backup-before-integration
2. 确保测试通过: pytest tests/
3. 记录当前API列表

## 步骤2: 融合SBPACK到distillation
- 将sbpack.py的端点迁移到distillation.py
- 保持向后兼容（重定向旧端点）
- 更新文档

## 步骤3: 融合RAG到unified_rag
- 在unified_rag.py中添加"enhanced"模式
- 使用新RAG引擎作为可选后端
- A/B测试两种模式

## 步骤4: 其他模块类似处理

## 步骤5: 测试验证
- 端到端测试
- 性能对比
- 逐步切换
"""

        guide_file = self.base / "DEEP_INTEGRATION_GUIDE.md"
        guide_file.write_text(integration_guide)
        print(f"  ✅ 创建: DEEP_INTEGRATION_GUIDE.md")

        print("\n" + "=" * 80)
        print("📋 执行顺序")
        print("=" * 80)
        print("\n1. 先执行数据库迁移:")
        print("   ./fix_migration.sh")
        print("\n2. 验证系统启动:")
        print("   cd backend/src && python -m uvicorn app.main:app --reload")
        print("\n3. 然后开始深度融合:")
        print("   按照 DEEP_INTEGRATION_GUIDE.md 逐步执行")
        print("\n4. 最后API整合:")
        print("   按照 API_CONSOLIDATION_PLAN.json 分阶段执行")


if __name__ == "__main__":
    planner = FieldMindIntegrationPlan()
    planner.generate_plan()
