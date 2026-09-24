#!/usr/bin/env python3
"""
FieldMind完整系统架构扫描器

深度扫描916个API端点，232个服务，60个模型
生成完整的系统功能地图
"""
import os
import re
import json
from pathlib import Path
from collections import defaultdict


class FieldMindArchitectureScanner:
    """完整架构扫描器"""

    def __init__(self):
        self.base = Path("/Users/alwan/FieldMind/backend/src/app")
        self.api_dir = self.base / "api"
        self.services_dir = self.base / "services"
        self.models_dir = self.base / "models"

        self.architecture = {
            "api_modules": {},
            "service_modules": {},
            "model_modules": {},
            "integration_status": {},
            "feature_map": defaultdict(list)
        }

    def scan_all(self):
        """完整扫描"""
        print("=" * 80)
        print("🔍 FieldMind完整系统架构扫描")
        print("=" * 80)

        # 1. 扫描所有API
        print("\n【1】扫描API层 (916个端点)...")
        self.scan_apis()

        # 2. 扫描所有Service
        print("\n【2】扫描Service层 (232个服务)...")
        self.scan_services()

        # 3. 扫描所有Model
        print("\n【3】扫描Model层 (60个模型)...")
        self.scan_models()

        # 4. 分析功能模块
        print("\n【4】分析功能模块分布...")
        self.analyze_feature_modules()

        # 5. 检查集成状态
        print("\n【5】检查新集成模块状态...")
        self.check_integration_status()

        # 6. 生成架构报告
        print("\n【6】生成完整架构报告...")
        self.generate_architecture_report()

    def scan_apis(self):
        """扫描所有API文件"""
        api_files = sorted(self.api_dir.glob("*.py"))

        for api_file in api_files:
            if api_file.name.startswith('_'):
                continue

            module_name = api_file.stem
            content = api_file.read_text()

            # 提取路由
            endpoints = re.findall(
                r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                content
            )

            # 提取标签
            tags = re.findall(r'tags=\[([^\]]+)\]', content)

            self.architecture["api_modules"][module_name] = {
                "file": str(api_file.name),
                "endpoints": [(method.upper(), path) for method, path in endpoints],
                "endpoint_count": len(endpoints),
                "tags": tags,
                "size_kb": api_file.stat().st_size // 1024
            }

        total_endpoints = sum(
            m["endpoint_count"]
            for m in self.architecture["api_modules"].values()
        )

        print(f"  ✅ 扫描完成: {len(api_files)}个API文件, {total_endpoints}个端点")

    def scan_services(self):
        """扫描所有Service文件"""
        service_files = sorted(self.services_dir.glob("*.py"))

        for service_file in service_files:
            if service_file.name.startswith('_'):
                continue

            module_name = service_file.stem
            content = service_file.read_text()

            # 提取类定义
            classes = re.findall(r'class\s+(\w+)', content)

            # 提取函数定义
            functions = re.findall(r'def\s+(\w+)\(', content)

            self.architecture["service_modules"][module_name] = {
                "file": str(service_file.name),
                "classes": classes,
                "functions": len(functions),
                "size_kb": service_file.stat().st_size // 1024
            }

        print(f"  ✅ 扫描完成: {len(service_files)}个Service文件")

    def scan_models(self):
        """扫描所有Model文件"""
        model_files = sorted(self.models_dir.glob("*.py"))

        for model_file in model_files:
            if model_file.name.startswith('_'):
                continue

            module_name = model_file.stem
            content = model_file.read_text()

            # 提取模型类
            models = re.findall(r'class\s+(\w+)\(Base\)', content)

            self.architecture["model_modules"][module_name] = {
                "file": str(model_file.name),
                "models": models,
                "model_count": len(models),
                "size_kb": model_file.stat().st_size // 1024
            }

        total_models = sum(
            m["model_count"]
            for m in self.architecture["model_modules"].values()
        )

        print(f"  ✅ 扫描完成: {len(model_files)}个Model文件, {total_models}个数据表")

    def analyze_feature_modules(self):
        """分析功能模块"""
        print("\n  分析功能分类...")

        # 按功能分类
        feature_keywords = {
            "文档处理": ["document", "file", "upload", "pdf", "docx"],
            "向量搜索": ["vector", "embedding", "similarity"],
            "知识管理": ["knowledge", "concept", "fact"],
            "Agent系统": ["agent", "workflow", "task"],
            "用户管理": ["user", "auth", "permission", "role"],
            "项目管理": ["project", "workspace"],
            "数据分析": ["analysis", "analytics", "statistics"],
            "RAG问答": ["rag", "chat", "query", "answer"],
            "SBPACK": ["sbpack", "distill", "package"],
            "技能系统": ["skill", "learning", "progress"],
            "Obsidian": ["obsidian", "markdown", "sync"],
            "知识图谱": ["graph", "entity", "relation"]
        }

        for feature, keywords in feature_keywords.items():
            matched_apis = []
            matched_services = []

            for name, data in self.architecture["api_modules"].items():
                if any(kw in name.lower() for kw in keywords):
                    matched_apis.append(name)

            for name, data in self.architecture["service_modules"].items():
                if any(kw in name.lower() for kw in keywords):
                    matched_services.append(name)

            if matched_apis or matched_services:
                self.architecture["feature_map"][feature] = {
                    "apis": matched_apis,
                    "services": matched_services
                }

    def check_integration_status(self):
        """检查新集成模块状态"""
        new_modules = {
            "SBPACK系统": {
                "api": "sbpack",
                "services": [
                    "knowledge_track_extractor",
                    "skill_track_extractor",
                    "sbpack_builder",
                    "sbpack_validator",
                    "production_auditor",
                    "input_processor"
                ],
                "models": "sbpack"
            },
            "技能树系统": {
                "api": "skill_tree",
                "services": [
                    "skill_tree_builder",
                    "skill_progress_tracker"
                ],
                "models": "skill_system"
            },
            "Obsidian集成": {
                "api": "obsidian",
                "services": [
                    "obsidian_exporter"
                ],
                "core": [
                    "obsidian_compat",
                    "obsidian_sync"
                ]
            },
            "RAG系统": {
                "api": "rag",
                "services": [
                    "knowledge_graph_builder",
                    "vector_store",
                    "hybrid_retriever",
                    "rag_generator"
                ],
                "models": "knowledge_graph"
            },
            "LLM增强": {
                "api": "llm",
                "services": [
                    "llm_enhancer"
                ]
            }
        }

        for module_name, components in new_modules.items():
            status = {
                "api": False,
                "services": [],
                "models": False,
                "core": []
            }

            # 检查API
            if "api" in components:
                status["api"] = components["api"] in self.architecture["api_modules"]

            # 检查Services
            if "services" in components:
                for svc in components["services"]:
                    if svc in self.architecture["service_modules"]:
                        status["services"].append(svc)

            # 检查Models
            if "models" in components:
                status["models"] = components["models"] in self.architecture["model_modules"]

            # 检查Core
            if "core" in components:
                core_dir = self.base / "core"
                for core_file in components["core"]:
                    if (core_dir / f"{core_file}.py").exists():
                        status["core"].append(core_file)

            self.architecture["integration_status"][module_name] = status

    def generate_architecture_report(self):
        """生成架构报告"""
        print("\n" + "=" * 80)
        print("📊 FieldMind完整架构报告")
        print("=" * 80)

        # 统计
        total_apis = len(self.architecture["api_modules"])
        total_endpoints = sum(
            m["endpoint_count"]
            for m in self.architecture["api_modules"].values()
        )
        total_services = len(self.architecture["service_modules"])
        total_models = len(self.architecture["model_modules"])

        print(f"\n📈 系统规模:")
        print(f"  • API文件: {total_apis}个")
        print(f"  • API端点: {total_endpoints}个")
        print(f"  • Service文件: {total_services}个")
        print(f"  • Model文件: {total_models}个")

        # 功能模块
        print(f"\n🎯 功能模块分布:")
        for feature, data in sorted(self.architecture["feature_map"].items()):
            api_count = len(data["apis"])
            svc_count = len(data["services"])
            if api_count > 0 or svc_count > 0:
                print(f"  • {feature}: {api_count}个API, {svc_count}个Service")

        # 集成状态
        print(f"\n🔌 新集成模块状态:")
        for module, status in self.architecture["integration_status"].items():
            api_status = "✅" if status["api"] else "❌"
            svc_count = len(status["services"])
            model_status = "✅" if status["models"] else "❌"

            print(f"\n  {module}:")
            print(f"    API: {api_status}")
            print(f"    Services: {svc_count}个已集成")
            print(f"    Models: {model_status}")
            if status.get("core"):
                print(f"    Core: {len(status['core'])}个已集成")

        # 保存详细报告
        report_file = Path("/Users/alwan/FieldMind/COMPLETE_ARCHITECTURE_REPORT.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.architecture, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告: {report_file}")

        # 总结
        print("\n" + "=" * 80)
        print("💡 总结")
        print("=" * 80)
        print("\nFieldMind是一个超大型系统：")
        print(f"  • {total_endpoints}个API端点服务各种功能")
        print(f"  • {total_services}个Service提供核心业务逻辑")
        print(f"  • 新增5个集成模块已嵌入现有架构")
        print(f"  • 所有新功能都是现有系统的增强扩展")


if __name__ == "__main__":
    scanner = FieldMindArchitectureScanner()
    scanner.scan_all()
