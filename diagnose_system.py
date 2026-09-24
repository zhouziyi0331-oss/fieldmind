#!/usr/bin/env python3
"""
FieldMind完整系统诊断工具

深度扫描整个程序，检查所有问题：
1. 程序实例数量
2. 数据断联和空数据
3. 工作流完整性
4. 边界和合规性
5. 前后端API连接
6. 逻辑错误和Bug
7. 缺失功能
"""
import os
import sys
import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class FieldMindDiagnostics:
    """FieldMind系统诊断器"""

    def __init__(self, base_dir: str = "/Users/alwan/FieldMind"):
        self.base_dir = Path(base_dir)
        self.backend_dir = self.base_dir / "backend" / "src"
        self.frontend_dir = self.base_dir / "frontend"
        self.app_dir = self.backend_dir / "app"

        # 诊断结果
        self.results = {
            "programs_found": [],
            "data_issues": [],
            "workflow_issues": [],
            "boundary_issues": [],
            "api_disconnects": [],
            "logic_errors": [],
            "missing_features": []
        }

    def run_full_diagnostics(self):
        """运行完整诊断"""
        print("=" * 80)
        print("🔍 FieldMind 完整系统诊断")
        print("=" * 80)

        # 1. 检测程序实例
        print("\n【检查1】扫描程序实例...")
        self.check_program_instances()

        # 2. 检查数据断联
        print("\n【检查2】检查数据连接...")
        self.check_data_connections()

        # 3. 检查工作流
        print("\n【检查3】检查工作流完整性...")
        self.check_workflows()

        # 4. 检查边界和合规
        print("\n【检查4】检查边界和合规性...")
        self.check_boundaries()

        # 5. 检查API连接
        print("\n【检查5】检查前后端API连接...")
        self.check_api_connections()

        # 6. 检查逻辑错误
        print("\n【检查6】检查逻辑错误和Bug...")
        self.check_logic_errors()

        # 7. 分析缺失功能
        print("\n【检查7】分析缺失功能...")
        self.check_missing_features()

        # 生成报告
        print("\n" + "=" * 80)
        self.generate_report()

    def check_program_instances(self):
        """检查1: 扫描所有程序实例"""
        print("\n  扫描FieldMind程序实例...")

        # 查找所有main.py和启动文件
        main_files = []

        for root, dirs, files in os.walk(self.base_dir):
            # 跳过node_modules, venv等
            dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git']]

            for file in files:
                if file in ['main.py', 'app.py', 'server.py', 'index.js', 'index.tsx']:
                    full_path = Path(root) / file
                    main_files.append(str(full_path))

        print(f"  找到 {len(main_files)} 个程序入口文件:")
        for f in main_files:
            rel_path = Path(f).relative_to(self.base_dir)
            print(f"    • {rel_path}")
            self.results["programs_found"].append(str(rel_path))

        # 检查是否有多个后端实例
        backend_mains = [f for f in main_files if 'backend' in f and f.endswith('.py')]
        if len(backend_mains) > 1:
            print(f"\n  ⚠️ 警告: 发现 {len(backend_mains)} 个后端主程序")
            self.results["logic_errors"].append({
                "type": "multiple_backends",
                "files": backend_mains,
                "severity": "high"
            })

    def check_data_connections(self):
        """检查2: 数据断联和空数据"""
        print("\n  检查数据库连接和模型...")

        # 扫描所有模型文件
        models_dir = self.app_dir / "models"
        if not models_dir.exists():
            print("  ❌ models目录不存在！")
            return

        model_files = list(models_dir.glob("*.py"))
        print(f"  找到 {len(model_files)} 个模型文件")

        # 分析模型定义
        models_defined = set()
        models_with_relations = set()
        orphan_models = []

        for model_file in model_files:
            if model_file.name.startswith('_'):
                continue

            content = model_file.read_text()

            # 查找模型定义
            model_classes = re.findall(r'class\s+(\w+)\(Base\)', content)
            models_defined.update(model_classes)

            # 查找关系定义
            if 'relationship' in content or 'ForeignKey' in content:
                models_with_relations.update(model_classes)

        print(f"  定义的模型: {len(models_defined)}")
        print(f"  有关系的模型: {len(models_with_relations)}")

        # 检查孤立模型
        orphan_models = models_defined - models_with_relations
        if orphan_models:
            print(f"\n  ⚠️ 发现 {len(orphan_models)} 个孤立模型（无关系）:")
            for model in list(orphan_models)[:5]:
                print(f"    • {model}")

            self.results["data_issues"].append({
                "type": "orphan_models",
                "count": len(orphan_models),
                "models": list(orphan_models)
            })

        # 检查数据库连接配置
        db_file = self.app_dir / "database.py"
        if db_file.exists():
            content = db_file.read_text()
            if 'SQLALCHEMY_DATABASE_URL' not in content and 'engine' not in content:
                print("  ⚠️ 数据库连接配置可能不完整")
                self.results["data_issues"].append({
                    "type": "db_config_incomplete",
                    "file": str(db_file)
                })

    def check_workflows(self):
        """检查3: 工作流完整性"""
        print("\n  检查工作流状态...")

        # 扫描服务层
        services_dir = self.app_dir / "services"
        if not services_dir.exists():
            print("  ❌ services目录不存在！")
            return

        service_files = list(services_dir.glob("*.py"))
        print(f"  找到 {len(service_files)} 个服务文件")

        # 分析服务依赖
        service_dependencies = defaultdict(set)
        service_outputs = defaultdict(set)

        for service_file in service_files:
            if service_file.name.startswith('_'):
                continue

            service_name = service_file.stem
            content = service_file.read_text()

            # 查找导入的其他服务
            imports = re.findall(r'from app\.services\.(\w+) import', content)
            service_dependencies[service_name].update(imports)

            # 查找返回类型
            returns = re.findall(r'-> (Dict|List|Optional|[\w]+):', content)
            service_outputs[service_name].update(returns)

        # 检查循环依赖
        print(f"\n  检查服务依赖...")
        circular_deps = self._find_circular_dependencies(service_dependencies)
        if circular_deps:
            print(f"  ⚠️ 发现循环依赖: {len(circular_deps)}个")
            for cycle in circular_deps[:3]:
                print(f"    • {' -> '.join(cycle)}")

            self.results["workflow_issues"].append({
                "type": "circular_dependencies",
                "count": len(circular_deps),
                "cycles": circular_deps
            })

        # 检查工作流封装
        workflow_patterns = [
            "KnowledgeGraphBuilder",
            "VectorStore",
            "RAGGenerator",
            "SkillTreeBuilder",
            "ObsidianSyncEngine"
        ]

        missing_workflows = []
        for pattern in workflow_patterns:
            found = False
            for service_file in service_files:
                if pattern.lower() in service_file.stem.lower():
                    found = True
                    break
            if not found:
                missing_workflows.append(pattern)

        if missing_workflows:
            print(f"\n  ⚠️ 缺失工作流组件: {len(missing_workflows)}个")
            for wf in missing_workflows:
                print(f"    • {wf}")

            self.results["workflow_issues"].append({
                "type": "missing_workflow_components",
                "components": missing_workflows
            })

    def check_boundaries(self):
        """检查4: 边界和合规性"""
        print("\n  检查API边界和数据验证...")

        # 扫描API文件
        api_dir = self.app_dir / "api"
        if not api_dir.exists():
            print("  ❌ api目录不存在！")
            return

        api_files = list(api_dir.glob("*.py"))
        print(f"  找到 {len(api_files)} 个API文件")

        # 检查请求验证
        apis_without_validation = []
        apis_without_error_handling = []

        for api_file in api_files:
            if api_file.name.startswith('_'):
                continue

            content = api_file.read_text()

            # 检查Pydantic模型
            has_validation = 'BaseModel' in content or 'Schema' in content

            # 检查错误处理
            has_error_handling = 'HTTPException' in content or 'try:' in content

            if not has_validation:
                apis_without_validation.append(api_file.stem)

            if not has_error_handling:
                apis_without_error_handling.append(api_file.stem)

        if apis_without_validation:
            print(f"\n  ⚠️ {len(apis_without_validation)}个API缺少输入验证:")
            for api in apis_without_validation[:5]:
                print(f"    • {api}.py")

            self.results["boundary_issues"].append({
                "type": "missing_validation",
                "apis": apis_without_validation
            })

        if apis_without_error_handling:
            print(f"\n  ⚠️ {len(apis_without_error_handling)}个API缺少错误处理:")
            for api in apis_without_error_handling[:5]:
                print(f"    • {api}.py")

            self.results["boundary_issues"].append({
                "type": "missing_error_handling",
                "apis": apis_without_error_handling
            })

    def check_api_connections(self):
        """检查5: 前后端API连接"""
        print("\n  检查前后端API连接...")

        # 扫描后端API端点
        backend_endpoints = self._scan_backend_endpoints()
        print(f"  后端API端点: {len(backend_endpoints)}")

        # 扫描前端API调用
        frontend_calls = self._scan_frontend_api_calls()
        print(f"  前端API调用: {len(frontend_calls)}")

        # 找出未连接的API
        backend_only = set(backend_endpoints) - set(frontend_calls)
        frontend_only = set(frontend_calls) - set(backend_endpoints)

        if backend_only:
            print(f"\n  ⚠️ {len(backend_only)}个后端API未被前端调用:")
            for api in list(backend_only)[:10]:
                print(f"    • {api}")

            self.results["api_disconnects"].append({
                "type": "unused_backend_apis",
                "count": len(backend_only),
                "apis": list(backend_only)
            })

        if frontend_only:
            print(f"\n  ⚠️ {len(frontend_only)}个前端调用的API不存在:")
            for api in list(frontend_only)[:10]:
                print(f"    • {api}")

            self.results["api_disconnects"].append({
                "type": "missing_backend_apis",
                "count": len(frontend_only),
                "apis": list(frontend_only)
            })

    def check_logic_errors(self):
        """检查6: 逻辑错误和Bug"""
        print("\n  检查潜在逻辑错误...")

        # 扫描所有Python文件
        py_files = list(self.app_dir.rglob("*.py"))
        print(f"  扫描 {len(py_files)} 个Python文件...")

        # 检查常见问题
        issues = {
            "bare_except": [],
            "missing_await": [],
            "unused_imports": [],
            "todos": []
        }

        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue

            try:
                content = py_file.read_text()

                # 检查裸except
                if re.search(r'except\s*:', content):
                    issues["bare_except"].append(str(py_file.relative_to(self.app_dir)))

                # 检查缺少await
                async_funcs = re.findall(r'async def\s+(\w+)', content)
                for func in async_funcs:
                    pattern = rf'{func}\([^)]*\)(?!\s*await)'
                    if re.search(pattern, content):
                        issues["missing_await"].append(f"{py_file.stem}.{func}")

                # 检查TODO
                todos = re.findall(r'#\s*TODO:?\s*(.+)', content)
                if todos:
                    issues["todos"].extend([(str(py_file.relative_to(self.app_dir)), t) for t in todos])

            except Exception as e:
                pass

        # 报告问题
        if issues["bare_except"]:
            print(f"\n  ⚠️ 发现 {len(issues['bare_except'])} 个裸except（应该指定异常类型）")
            self.results["logic_errors"].append({
                "type": "bare_except",
                "count": len(issues["bare_except"])
            })

        if issues["missing_await"]:
            print(f"\n  ⚠️ 可能缺少await: {len(issues['missing_await'])}处")
            self.results["logic_errors"].append({
                "type": "missing_await",
                "count": len(issues["missing_await"])
            })

        if issues["todos"]:
            print(f"\n  📝 发现 {len(issues['todos'])} 个TODO标记")
            for file, todo in issues["todos"][:5]:
                print(f"    • {file}: {todo[:60]}")

    def check_missing_features(self):
        """检查7: 缺失功能"""
        print("\n  分析缺失功能和待完善项...")

        # 必需的功能组件
        required_features = {
            "authentication": ["auth", "login", "token"],
            "authorization": ["permission", "role", "access"],
            "logging": ["logger", "log"],
            "testing": ["test_", "pytest"],
            "documentation": ["swagger", "openapi", "docs"],
            "monitoring": ["metrics", "health", "status"],
            "caching": ["cache", "redis"],
            "rate_limiting": ["rate_limit", "throttle"],
            "file_upload": ["upload", "multipart"],
            "search": ["search", "query"]
        }

        missing = []
        for feature, keywords in required_features.items():
            found = False
            for keyword in keywords:
                # 搜索服务和API
                service_files = list((self.app_dir / "services").glob(f"*{keyword}*.py"))
                api_files = list((self.app_dir / "api").glob(f"*{keyword}*.py"))

                if service_files or api_files:
                    found = True
                    break

            if not found:
                missing.append(feature)
                print(f"  ⚠️ 缺少功能: {feature}")

        if missing:
            self.results["missing_features"] = missing

    def _scan_backend_endpoints(self) -> List[str]:
        """扫描后端API端点"""
        endpoints = []
        api_dir = self.app_dir / "api"

        if not api_dir.exists():
            return endpoints

        for api_file in api_dir.glob("*.py"):
            try:
                content = api_file.read_text()

                # 查找路由定义
                routes = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
                for method, path in routes:
                    endpoints.append(f"{method.upper()} {path}")

            except Exception:
                pass

        return endpoints

    def _scan_frontend_api_calls(self) -> List[str]:
        """扫描前端API调用"""
        calls = []

        if not self.frontend_dir.exists():
            return calls

        for tsx_file in self.frontend_dir.rglob("*.tsx"):
            try:
                content = tsx_file.read_text()

                # 查找axios或fetch调用
                api_calls = re.findall(r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
                for method, url in api_calls:
                    calls.append(f"{method.upper()} {url}")

                fetch_calls = re.findall(r'fetch\(["\']([^"\']+)["\'],\s*{\s*method:\s*["\'](\w+)', content)
                for url, method in fetch_calls:
                    calls.append(f"{method.upper()} {url}")

            except Exception:
                pass

        return calls

    def _find_circular_dependencies(self, deps: Dict) -> List[List[str]]:
        """查找循环依赖"""
        cycles = []

        def visit(node, path, visited):
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in deps.get(node, []):
                visit(neighbor, path[:], visited)

        visited = set()
        for node in deps:
            visit(node, [], visited)

        return cycles

    def generate_report(self):
        """生成诊断报告"""
        print("\n📊 诊断报告")
        print("=" * 80)

        # 统计
        total_issues = sum([
            len(self.results["data_issues"]),
            len(self.results["workflow_issues"]),
            len(self.results["boundary_issues"]),
            len(self.results["api_disconnects"]),
            len(self.results["logic_errors"])
        ])

        print(f"\n总计发现 {total_issues} 类问题:")
        print(f"  • 数据问题: {len(self.results['data_issues'])}")
        print(f"  • 工作流问题: {len(self.results['workflow_issues'])}")
        print(f"  • 边界问题: {len(self.results['boundary_issues'])}")
        print(f"  • API断联: {len(self.results['api_disconnects'])}")
        print(f"  • 逻辑错误: {len(self.results['logic_errors'])}")
        print(f"  • 缺失功能: {len(self.results['missing_features'])}")

        # 保存详细报告
        report_file = self.base_dir / "DIAGNOSTICS_REPORT.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存: {report_file}")

        # 优先级建议
        print("\n🎯 修复优先级建议:")
        print("  1. 修复API断联（前后端通信）")
        print("  2. 添加数据验证和错误处理")
        print("  3. 解决循环依赖")
        print("  4. 补充缺失功能")
        print("  5. 清理TODO和未使用代码")


if __name__ == "__main__":
    diagnostics = FieldMindDiagnostics()
    diagnostics.run_full_diagnostics()
