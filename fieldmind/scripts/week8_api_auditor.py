#!/usr/bin/env python3
"""
Week 8-9 Day 1: API 审计与分析

功能：
1. 扫描所有 API 端点
2. 分析 API 使用情况
3. 识别冗余和重复端点
4. 生成整合建议
"""

import os
import re
import json
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from datetime import datetime


class APIAuditor:
    """API 审计器"""

    def __init__(self, backend_dir: str, output_dir: str):
        self.backend_dir = backend_dir
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/api_audit", exist_ok=True)

    def scan_api_endpoints(self) -> List[Dict]:
        """扫描所有 API 端点"""
        print("🔍 扫描 API 端点...")

        endpoints = []

        # 扫描路由文件
        routes_files = self._find_route_files()
        print(f"   找到 {len(routes_files)} 个路由文件")

        for file_path in routes_files:
            file_endpoints = self._parse_route_file(file_path)
            endpoints.extend(file_endpoints)

        print(f"   ✓ 发现 {len(endpoints)} 个端点")

        return endpoints

    def _find_route_files(self) -> List[str]:
        """查找路由文件"""
        route_files = []

        # 常见路由文件模式
        patterns = [
            '**/routes.py',
            '**/router.py',
            '**/api.py',
            '**/*_routes.py',
            '**/*_router.py',
            '**/*_api.py',
        ]

        for root, dirs, files in os.walk(self.backend_dir):
            for file in files:
                if file.endswith(('_routes.py', '_router.py', '_api.py', 'routes.py', 'router.py', 'api.py')):
                    route_files.append(os.path.join(root, file))

        return route_files

    def _parse_route_file(self, file_path: str) -> List[Dict]:
        """解析路由文件"""
        endpoints = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取 Flask/FastAPI 路由
            # Flask: @app.route('/path', methods=['GET'])
            # FastAPI: @router.get('/path')

            # Flask 路由
            flask_routes = re.findall(
                r'@(?:app|bp|blueprint|router)\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods\s*=\s*\[(.*?)\])?\)',
                content
            )

            for path, methods in flask_routes:
                methods_list = [m.strip('\'" ') for m in methods.split(',')] if methods else ['GET']
                for method in methods_list:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'file': os.path.relpath(file_path, self.backend_dir),
                        'framework': 'flask',
                    })

            # FastAPI 路由
            fastapi_patterns = [
                (r'@router\.get\([\'"]([^\'"]+)[\'"]\)', 'GET'),
                (r'@router\.post\([\'"]([^\'"]+)[\'"]\)', 'POST'),
                (r'@router\.put\([\'"]([^\'"]+)[\'"]\)', 'PUT'),
                (r'@router\.delete\([\'"]([^\'"]+)[\'"]\)', 'DELETE'),
                (r'@router\.patch\([\'"]([^\'"]+)[\'"]\)', 'PATCH'),
                (r'@app\.get\([\'"]([^\'"]+)[\'"]\)', 'GET'),
                (r'@app\.post\([\'"]([^\'"]+)[\'"]\)', 'POST'),
                (r'@app\.put\([\'"]([^\'"]+)[\'"]\)', 'PUT'),
                (r'@app\.delete\([\'"]([^\'"]+)[\'"]\)', 'DELETE'),
            ]

            for pattern, method in fastapi_patterns:
                paths = re.findall(pattern, content)
                for path in paths:
                    endpoints.append({
                        'path': path,
                        'method': method,
                        'file': os.path.relpath(file_path, self.backend_dir),
                        'framework': 'fastapi',
                    })

        except Exception as e:
            print(f"   ⚠️  解析失败 {file_path}: {e}")

        return endpoints

    def analyze_endpoints(self, endpoints: List[Dict]) -> Dict:
        """分析端点"""
        print("\n📊 分析端点...")

        analysis = {
            'total_endpoints': len(endpoints),
            'by_method': defaultdict(int),
            'by_framework': defaultdict(int),
            'by_resource': defaultdict(list),
            'path_patterns': defaultdict(list),
        }

        for endpoint in endpoints:
            method = endpoint['method']
            framework = endpoint['framework']
            path = endpoint['path']

            analysis['by_method'][method] += 1
            analysis['by_framework'][framework] += 1

            # 提取资源名称
            resource = self._extract_resource(path)
            analysis['by_resource'][resource].append(endpoint)

            # 提取路径模式
            pattern = self._extract_pattern(path)
            analysis['path_patterns'][pattern].append(endpoint)

        # 转换 defaultdict
        analysis['by_method'] = dict(analysis['by_method'])
        analysis['by_framework'] = dict(analysis['by_framework'])
        analysis['by_resource'] = dict(analysis['by_resource'])
        analysis['path_patterns'] = dict(analysis['path_patterns'])

        print(f"   ✓ 总端点: {analysis['total_endpoints']}")
        print(f"   按方法:")
        for method, count in sorted(analysis['by_method'].items()):
            print(f"     - {method}: {count}")

        return analysis

    def _extract_resource(self, path: str) -> str:
        """提取资源名称"""
        # 移除查询参数
        path = path.split('?')[0]

        # 提取第一个路径段作为资源
        parts = [p for p in path.split('/') if p and not p.startswith('{') and not p.startswith('<')]

        if parts:
            return parts[0]

        return 'root'

    def _extract_pattern(self, path: str) -> str:
        """提取路径模式"""
        # 替换参数为占位符
        pattern = re.sub(r'\{[^}]+\}', '{id}', path)  # FastAPI
        pattern = re.sub(r'<[^>]+>', '<id>', pattern)  # Flask
        return pattern

    def identify_redundancies(self, endpoints: List[Dict], analysis: Dict) -> Dict:
        """识别冗余端点"""
        print("\n🔎 识别冗余端点...")

        redundancies = {
            'duplicate_paths': [],
            'similar_patterns': [],
            'overlapping_resources': [],
        }

        # 1. 完全重复的路径
        path_method_map = defaultdict(list)
        for endpoint in endpoints:
            key = f"{endpoint['method']}:{endpoint['path']}"
            path_method_map[key].append(endpoint)

        for key, eps in path_method_map.items():
            if len(eps) > 1:
                redundancies['duplicate_paths'].append({
                    'key': key,
                    'count': len(eps),
                    'endpoints': eps,
                })

        # 2. 相似的路径模式
        patterns = analysis['path_patterns']
        for pattern, eps in patterns.items():
            if len(eps) > 3:  # 同一模式有太多端点
                redundancies['similar_patterns'].append({
                    'pattern': pattern,
                    'count': len(eps),
                    'endpoints': eps[:5],  # 只显示前5个
                })

        # 3. 重叠的资源
        resources = analysis['by_resource']
        for resource, eps in resources.items():
            if len(eps) > 10:  # 单个资源端点过多
                redundancies['overlapping_resources'].append({
                    'resource': resource,
                    'count': len(eps),
                    'methods': list(set(e['method'] for e in eps)),
                })

        print(f"   ✓ 重复路径: {len(redundancies['duplicate_paths'])}")
        print(f"   ✓ 相似模式: {len(redundancies['similar_patterns'])}")
        print(f"   ✓ 重叠资源: {len(redundancies['overlapping_resources'])}")

        return redundancies

    def generate_consolidation_plan(self, endpoints: List[Dict], analysis: Dict, redundancies: Dict) -> Dict:
        """生成整合计划"""
        print("\n📋 生成整合计划...")

        plan = {
            'current_state': {
                'total_endpoints': len(endpoints),
                'by_method': analysis['by_method'],
                'by_framework': analysis['by_framework'],
            },
            'target_state': {},
            'consolidation_actions': [],
            'estimated_reduction': 0,
        }

        # 1. 处理重复路径
        for dup in redundancies['duplicate_paths']:
            plan['consolidation_actions'].append({
                'type': 'merge_duplicates',
                'path': dup['key'],
                'current_count': dup['count'],
                'target_count': 1,
                'savings': dup['count'] - 1,
                'action': f"合并 {dup['count']} 个重复端点到单一实现",
            })

        # 2. 整合相似模式
        for similar in redundancies['similar_patterns']:
            if similar['count'] > 5:
                plan['consolidation_actions'].append({
                    'type': 'consolidate_pattern',
                    'pattern': similar['pattern'],
                    'current_count': similar['count'],
                    'target_count': max(3, similar['count'] // 2),
                    'savings': similar['count'] - max(3, similar['count'] // 2),
                    'action': f"整合相似端点，减少冗余实现",
                })

        # 3. 优化资源端点
        for overlap in redundancies['overlapping_resources']:
            if overlap['count'] > 15:
                plan['consolidation_actions'].append({
                    'type': 'optimize_resource',
                    'resource': overlap['resource'],
                    'current_count': overlap['count'],
                    'target_count': min(10, overlap['count']),
                    'savings': max(0, overlap['count'] - 10),
                    'action': f"优化资源端点，使用 RESTful 标准",
                })

        # 计算总节省
        plan['estimated_reduction'] = sum(
            action.get('savings', 0)
            for action in plan['consolidation_actions']
        )

        plan['target_state'] = {
            'total_endpoints': len(endpoints) - plan['estimated_reduction'],
            'reduction_rate': round(plan['estimated_reduction'] / len(endpoints) * 100, 1) if endpoints else 0,
        }

        print(f"   ✓ 整合操作: {len(plan['consolidation_actions'])}")
        print(f"   ✓ 预计减少: {plan['estimated_reduction']} 个端点")
        print(f"   ✓ 减少率: {plan['target_state']['reduction_rate']}%")

        return plan

    def generate_api_catalog(self, endpoints: List[Dict], analysis: Dict) -> Dict:
        """生成 API 目录"""
        print("\n📚 生成 API 目录...")

        catalog = {
            'generated_at': datetime.now().isoformat(),
            'total_endpoints': len(endpoints),
            'summary': {
                'by_method': analysis['by_method'],
                'by_framework': analysis['by_framework'],
                'by_resource': {k: len(v) for k, v in analysis['by_resource'].items()},
            },
            'resources': {},
        }

        # 按资源组织端点
        for resource, eps in analysis['by_resource'].items():
            catalog['resources'][resource] = {
                'total_endpoints': len(eps),
                'methods': list(set(e['method'] for e in eps)),
                'endpoints': [
                    {
                        'path': e['path'],
                        'method': e['method'],
                        'file': e['file'],
                    }
                    for e in sorted(eps, key=lambda x: (x['path'], x['method']))
                ],
            }

        # 保存目录
        catalog_file = f"{self.output_dir}/api_audit/api_catalog.json"
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {catalog_file}")

        return catalog

    def generate_audit_report(self, endpoints: List[Dict], analysis: Dict, redundancies: Dict, plan: Dict):
        """生成审计报告"""
        print("\n📄 生成审计报告...")

        report = f"""# FieldMind API 审计报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、总体概况

### 端点统计
- **总端点数**: {len(endpoints)}
- **目标端点数**: {plan['target_state']['total_endpoints']}
- **预计减少**: {plan['estimated_reduction']} ({plan['target_state']['reduction_rate']}%)

### 按方法分布
"""

        for method, count in sorted(analysis['by_method'].items(), key=lambda x: x[1], reverse=True):
            report += f"- **{method}**: {count} ({round(count/len(endpoints)*100, 1)}%)\n"

        report += f"""
### 按框架分布
"""

        for framework, count in analysis['by_framework'].items():
            report += f"- **{framework}**: {count}\n"

        report += f"""
---

## 二、冗余分析

### 重复路径
发现 **{len(redundancies['duplicate_paths'])}** 组完全重复的端点

"""

        if redundancies['duplicate_paths']:
            report += "| 路径 | 重复次数 | 文件 |\n"
            report += "|------|---------|------|\n"
            for dup in redundancies['duplicate_paths'][:10]:
                files = ', '.join(set(e['file'] for e in dup['endpoints']))
                report += f"| `{dup['key']}` | {dup['count']} | {files} |\n"

        report += f"""
### 相似模式
发现 **{len(redundancies['similar_patterns'])}** 组相似的路径模式

"""

        if redundancies['similar_patterns']:
            report += "| 模式 | 端点数 |\n"
            report += "|------|-------|\n"
            for similar in redundancies['similar_patterns'][:10]:
                report += f"| `{similar['pattern']}` | {similar['count']} |\n"

        report += f"""
### 资源端点过多
发现 **{len(redundancies['overlapping_resources'])}** 个资源的端点数量过多

"""

        if redundancies['overlapping_resources']:
            report += "| 资源 | 端点数 | 方法 |\n"
            report += "|------|-------|------|\n"
            for overlap in redundancies['overlapping_resources']:
                methods = ', '.join(overlap['methods'])
                report += f"| `{overlap['resource']}` | {overlap['count']} | {methods} |\n"

        report += f"""
---

## 三、整合计划

### 整合操作
计划执行 **{len(plan['consolidation_actions'])}** 项整合操作

"""

        action_types = defaultdict(int)
        for action in plan['consolidation_actions']:
            action_types[action['type']] += 1

        for action_type, count in action_types.items():
            type_names = {
                'merge_duplicates': '合并重复端点',
                'consolidate_pattern': '整合相似模式',
                'optimize_resource': '优化资源端点',
            }
            report += f"- **{type_names.get(action_type, action_type)}**: {count} 项\n"

        report += """
### 详细操作清单

"""

        for i, action in enumerate(plan['consolidation_actions'][:20], 1):
            report += f"""
#### {i}. {action.get('path') or action.get('pattern') or action.get('resource')}
- **类型**: {action['type']}
- **当前**: {action['current_count']} 个端点
- **目标**: {action['target_count']} 个端点
- **节省**: {action['savings']} 个端点
- **操作**: {action['action']}
"""

        report += f"""
---

## 四、资源分布

### Top 10 资源（按端点数）

"""

        sorted_resources = sorted(
            analysis['by_resource'].items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]

        report += "| 资源 | 端点数 | 方法 |\n"
        report += "|------|-------|------|\n"

        for resource, eps in sorted_resources:
            methods = ', '.join(sorted(set(e['method'] for e in eps)))
            report += f"| `{resource}` | {len(eps)} | {methods} |\n"

        report += f"""
---

## 五、建议

### 短期（1-2周）
1. **合并重复端点**: 优先处理完全重复的 {len(redundancies['duplicate_paths'])} 组端点
2. **统一命名规范**: 建立清晰的 API 命名标准
3. **文档完善**: 为所有端点补充文档说明

### 中期（1个月）
1. **RESTful 改造**: 按 REST 标准重构资源端点
2. **版本管理**: 引入 API 版本控制（v1, v2）
3. **权限统一**: 统一认证授权机制

### 长期（3个月+）
1. **GraphQL**: 考虑引入 GraphQL 减少端点数量
2. **微服务拆分**: 按业务域拆分 API
3. **自动化测试**: 为所有端点添加测试用例

---

## 六、风险评估

### 高风险操作
- 合并端点可能影响现有客户端
- 建议使用版本控制和废弃警告

### 中风险操作
- 路径重命名需要更新所有调用方
- 建议保留别名一段时间

### 低风险操作
- 文档完善和测试补充
- 可以立即开始

---

**FieldMind API 整合项目**
Week 8-9 Day 1 审计报告
"""

        report_file = f"{self.output_dir}/api_audit/audit_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"   ✓ 保存到: {report_file}")

        return report_file

    def run(self):
        """执行完整审计"""
        print("=" * 70)
        print("Week 8-9 Day 1: API 审计与分析")
        print("=" * 70)

        # 1. 扫描端点
        endpoints = self.scan_api_endpoints()

        # 2. 分析端点
        analysis = self.analyze_endpoints(endpoints)

        # 3. 识别冗余
        redundancies = self.identify_redundancies(endpoints, analysis)

        # 4. 生成整合计划
        plan = self.generate_consolidation_plan(endpoints, analysis, redundancies)

        # 5. 生成 API 目录
        catalog = self.generate_api_catalog(endpoints, analysis)

        # 6. 生成审计报告
        report_file = self.generate_audit_report(endpoints, analysis, redundancies, plan)

        # 7. 保存原始数据
        data_file = f"{self.output_dir}/api_audit/endpoints_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'endpoints': endpoints,
                'analysis': analysis,
                'redundancies': redundancies,
                'plan': plan,
            }, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 70)
        print("API 审计完成")
        print("=" * 70)

        print(f"\n📊 审计结果:")
        print(f"  发现端点: {len(endpoints)}")
        print(f"  重复路径: {len(redundancies['duplicate_paths'])}")
        print(f"  相似模式: {len(redundancies['similar_patterns'])}")
        print(f"  预计减少: {plan['estimated_reduction']} ({plan['target_state']['reduction_rate']}%)")

        print(f"\n📁 输出文件:")
        print(f"  - API 目录: {self.output_dir}/api_audit/api_catalog.json")
        print(f"  - 审计报告: {report_file}")
        print(f"  - 原始数据: {data_file}")

        return {
            'endpoints': endpoints,
            'analysis': analysis,
            'redundancies': redundancies,
            'plan': plan,
            'catalog': catalog,
        }


def main():
    backend_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/backend"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind"

    auditor = APIAuditor(backend_dir, output_dir)
    result = auditor.run()

    print("\n✅ API 审计完成！")


if __name__ == "__main__":
    main()
