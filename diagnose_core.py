#!/usr/bin/env python3
"""
FieldMind核心程序精确诊断

只检查backend/和frontend/目录的核心代码
"""
import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict


class FieldMindCoreDiagnostics:
    """FieldMind核心诊断器 - 精确版"""

    def __init__(self, base_dir: str = "/Users/alwan/FieldMind"):
        self.base_dir = Path(base_dir)
        self.backend_dir = self.base_dir / "backend" / "src"
        self.frontend_dir = self.base_dir / "frontend" / "src"

        # 结果
        self.report = {
            "summary": {},
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

    def run(self):
        """运行精确诊断"""
        print("=" * 80)
        print("🎯 FieldMind核心程序精确诊断")
        print("=" * 80)

        print(f"\n📂 扫描目录:")
        print(f"  Backend: {self.backend_dir}")
        print(f"  Frontend: {self.frontend_dir}")

        # 1. 统计核心文件
        self.analyze_structure()

        # 2. 检查主程序
        self.check_main_entry()

        # 3. 检查API完整性
        self.check_api_integrity()

        # 4. 检查模型完整性
        self.check_models_integrity()

        # 5. 检查服务层
        self.check_services_layer()

        # 6. 检查前后端连接
        self.check_frontend_backend()

        # 7. 检查新集成模块
        self.check_integration_modules()

        # 8. 生成报告
        self.generate_final_report()

    def analyze_structure(self):
        """分析目录结构"""
        print("\n【1】分析项目结构...")

        backend_files = {
            "models": list((self.backend_dir / "app" / "models").glob("*.py")) if (self.backend_dir / "app" / "models").exists() else [],
            "services": list((self.backend_dir / "app" / "services").glob("*.py")) if (self.backend_dir / "app" / "services").exists() else [],
            "api": list((self.backend_dir / "app" / "api").glob("*.py")) if (self.backend_dir / "app" / "api").exists() else [],
        }

        print(f"  📊 后端文件统计:")
        print(f"    Models:   {len(backend_files['models'])}")
        print(f"    Services: {len(backend_files['services'])}")
        print(f"    APIs:     {len(backend_files['api'])}")

        self.report["summary"]["backend"] = {
            "models": len(backend_files['models']),
            "services": len(backend_files['services']),
            "apis": len(backend_files['api'])
        }

        # 前端
        if self.frontend_dir.exists():
            tsx_files = list(self.frontend_dir.rglob("*.tsx"))
            print(f"  📊 前端文件统计:")
            print(f"    TSX/JSX: {len(tsx_files)}")
            self.report["summary"]["frontend"] = {"tsx_files": len(tsx_files)}

    def check_main_entry(self):
        """检查主程序入口"""
        print("\n【2】检查主程序入口...")

        main_file = self.backend_dir / "app" / "main.py"

        if not main_file.exists():
            print("  ❌ 找不到main.py！")
            self.report["critical_issues"].append({
                "type": "missing_main",
                "severity": "critical",
                "message": "Main entry point not found"
            })
            return

        print(f"  ✅ 找到main.py ({main_file.stat().st_size // 1024}KB)")

        # 检查路由注册
        content = main_file.read_text()

        # 查找include_router调用
        routers = re.findall(r'app\.include_router\((\w+)\.router', content)
        print(f"  📍 已注册路由: {len(routers)}个")

        # 检查新集成模块是否注册
        integration_modules = ["sbpack", "skill_tree", "obsidian", "rag", "llm"]
        registered = [m for m in integration_modules if m in routers]
        missing = [m for m in integration_modules if m not in routers]

        if registered:
            print(f"  ✅ 已注册新模块: {', '.join(registered)}")

        if missing:
            print(f"  ⚠️ 未注册模块: {', '.join(missing)}")
            self.report["warnings"].append({
                "type": "unregistered_modules",
                "modules": missing,
                "message": "New integration modules not registered in main.py"
            })

    def check_api_integrity(self):
        """检查API完整性"""
        print("\n【3】检查API层完整性...")

        api_dir = self.backend_dir / "app" / "api"
        if not api_dir.exists():
            print("  ❌ API目录不存在！")
            return

        # 检查新增API文件
        new_apis = ["sbpack.py", "skill_tree.py", "obsidian.py", "rag.py", "llm.py"]

        found = []
        missing = []

        for api in new_apis:
            api_path = api_dir / api
            if api_path.exists():
                size = api_path.stat().st_size
                found.append(f"{api} ({size}B)")
            else:
                missing.append(api)

        if found:
            print(f"  ✅ 已存在新API: {len(found)}个")
            for f in found:
                print(f"    • {f}")

        if missing:
            print(f"  ❌ 缺失新API: {len(missing)}个")
            for m in missing:
                print(f"    • {m}")

            self.report["critical_issues"].append({
                "type": "missing_api_files",
                "files": missing,
                "severity": "high"
            })

    def check_models_integrity(self):
        """检查模型完整性"""
        print("\n【4】检查数据模型完整性...")

        models_dir = self.backend_dir / "app" / "models"
        if not models_dir.exists():
            print("  ❌ models目录不存在！")
            return

        # 检查新增模型文件
        new_models = ["sbpack.py", "skill_system.py", "knowledge_graph.py"]

        found = []
        missing = []

        for model in new_models:
            model_path = models_dir / model
            if model_path.exists():
                # 统计模型类数量
                content = model_path.read_text()
                classes = re.findall(r'class\s+(\w+)\(Base\)', content)
                found.append(f"{model} ({len(classes)} tables)")
            else:
                missing.append(model)

        if found:
            print(f"  ✅ 已存在新模型: {len(found)}个")
            for f in found:
                print(f"    • {f}")

        if missing:
            print(f"  ❌ 缺失新模型: {len(missing)}个")
            for m in missing:
                print(f"    • {m}")

            self.report["critical_issues"].append({
                "type": "missing_model_files",
                "files": missing,
                "severity": "high"
            })

    def check_services_layer(self):
        """检查服务层"""
        print("\n【5】检查服务层完整性...")

        services_dir = self.backend_dir / "app" / "services"
        if not services_dir.exists():
            print("  ❌ services目录不存在！")
            return

        # 检查新增服务文件
        new_services = [
            "knowledge_track_extractor.py",
            "skill_track_extractor.py",
            "sbpack_builder.py",
            "sbpack_validator.py",
            "production_auditor.py",
            "input_processor.py",
            "obsidian_exporter.py",
            "llm_enhancer.py",
            "knowledge_graph_builder.py",
            "vector_store.py",
            "hybrid_retriever.py",
            "rag_generator.py",
            "skill_tree_builder.py",
            "skill_progress_tracker.py"
        ]

        found = []
        missing = []

        for service in new_services:
            service_path = services_dir / service
            if service_path.exists():
                size = service_path.stat().st_size // 1024
                found.append(f"{service} ({size}KB)")
            else:
                missing.append(service)

        print(f"  ✅ 已存在服务: {len(found)}/{len(new_services)}")

        if missing:
            print(f"  ❌ 缺失服务: {len(missing)}个")
            for m in missing[:5]:
                print(f"    • {m}")

            self.report["critical_issues"].append({
                "type": "missing_service_files",
                "files": missing,
                "severity": "high"
            })

    def check_frontend_backend(self):
        """检查前后端连接"""
        print("\n【6】检查前后端连接...")

        if not self.frontend_dir.exists():
            print("  ⚠️ 前端目录不存在")
            return

        # 扫描前端组件
        components = [
            "SBPACKManager.tsx",
            "SkillTreeViewer.tsx"
        ]

        found_components = []
        for comp in components:
            comp_files = list(self.frontend_dir.rglob(comp))
            if comp_files:
                found_components.append(comp)

        if found_components:
            print(f"  ✅ 已存在前端组件: {len(found_components)}个")
            for c in found_components:
                print(f"    • {c}")
        else:
            print("  ❌ 未找到新增前端组件")
            self.report["warnings"].append({
                "type": "missing_frontend_components",
                "message": "New frontend components not found"
            })

    def check_integration_modules(self):
        """检查集成模块状态"""
        print("\n【7】检查集成模块状态...")

        # 检查core目录
        core_dir = self.backend_dir / "app" / "core"

        integration_files = [
            "obsidian_compat.py",
            "obsidian_sync.py",
            "integration_config.py",
            "dependencies.py"
        ]

        found = []
        missing = []

        for file in integration_files:
            if core_dir.exists() and (core_dir / file).exists():
                found.append(file)
            else:
                missing.append(file)

        if found:
            print(f"  ✅ 核心集成文件: {len(found)}/{len(integration_files)}")

        if missing:
            print(f"  ⚠️ 缺失集成文件: {len(missing)}个")
            for m in missing:
                print(f"    • {m}")

            self.report["recommendations"].append({
                "type": "create_integration_files",
                "files": missing,
                "action": "Run install_integration.py to create these files"
            })

    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "=" * 80)
        print("📊 诊断报告")
        print("=" * 80)

        # 统计
        critical_count = len(self.report["critical_issues"])
        warning_count = len(self.report["warnings"])

        print(f"\n🔴 严重问题: {critical_count}")
        if critical_count > 0:
            for issue in self.report["critical_issues"]:
                print(f"  • {issue['type']}: {issue.get('message', 'See details')}")

        print(f"\n🟡 警告: {warning_count}")
        if warning_count > 0:
            for warning in self.report["warnings"][:5]:
                print(f"  • {warning['type']}: {warning.get('message', 'See details')}")

        print(f"\n💡 建议: {len(self.report['recommendations'])}")
        if self.report['recommendations']:
            for rec in self.report['recommendations'][:3]:
                print(f"  • {rec['type']}: {rec.get('action', 'See details')}")

        # 保存报告
        report_file = self.base_dir / "CORE_DIAGNOSTICS_REPORT.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告: {report_file}")

        # 下一步行动
        print("\n" + "=" * 80)
        print("🎯 建议行动步骤:")
        print("=" * 80)

        if critical_count > 0:
            print("\n1. 🚨 立即处理严重问题:")
            print("   python install_integration.py  # 创建缺失文件")

        if warning_count > 0:
            print("\n2. ⚠️ 处理警告:")
            print("   - 在main.py中注册新模块路由")
            print("   - 创建缺失的前端组件")

        print("\n3. ✅ 验证集成:")
        print("   cd backend/src")
        print("   python -m pytest tests/")
        print("   python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    diagnostics = FieldMindCoreDiagnostics()
    diagnostics.run()
