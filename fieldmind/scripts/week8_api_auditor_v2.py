#!/usr/bin/env python3
"""
Week 8-9 Day 1: API 审计与分析 (改进版)

功能：
1. 全面扫描所有 API 端点（Flask, FastAPI, Blueprint）
2. 分析 API 使用情况
3. 识别冗余和重复端点
4. 生成整合建议
"""

import os
import re
import json
import ast
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from datetime import datetime


class ImprovedAPIAuditor:
    """改进的 API 审计器"""

    def __init__(self, backend_dir: str, output_dir: str):
        self.backend_dir = backend_dir
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/api_audit", exist_ok=True)

    def scan_api_endpoints(self) -> List[Dict]:
        """扫描所有 API 端点"""
        print("🔍 全面扫描 API 端点...")

        endpoints = []

        # 扫描所有 Python 文件
        py_files = self._find_all_python_files()
        print(f"   扫描 {len(py_files)} 个 Python 文件...")

        for file_path in py_files:
            file_endpoints = self._parse_file_comprehensive(file_path)
            endpoints.extend(file_endpoints)

        print(f"   ✓ 发现 {len(endpoints)} 个端点")

        # 去重
        unique_endpoints = self._deduplicate_endpoints(endpoints)
        print(f"   ✓ 去重后 {len(unique_endpoints)} 个端点")

        return unique_endpoints

    def _find_all_python_files(self) -> List[str]:
        """查找所有 Python 文件"""
        py_files = []

        for root, dirs, files in os.walk(self.backend_dir):
            # 跳过虚拟环境和缓存目录
            dirs[:] = [d for d in dirs if d not in ['venv', 'env', '__pycache__', '.git', 'node_modules']]

            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))

        return py_files

    def _parse_file_comprehensive(self, file_path: str) -> List[Dict]:
        """全面解析文件中的所有路由"""
        endpoints = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            rel_path = os.path.relpath(file_path, self.backend_dir)

            # 1. Flask 路由: @app.route, @bp.route, @blueprint.route
            flask_patterns = [
                r'@(?:app|bp|blueprint|router|api)\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods\s*=\s*\[(.*?)\])?\)',
            ]

            for pattern in flask_patterns:
                matches = re.findall(pattern, content)
                for path, methods in matches:
                    methods_list = []
                    if methods:
                        # 提取方法列表
                        methods_list = re.findall(r'[\'"](\w+)[\'"]', methods)
                    else:
                        methods_list = ['GET']

                    for method in methods_list:
                        endpoints.append({
                            'path': path,
                            'method': method.upper(),
                            'file': rel_path,
                            'framework': 'flask',
                        })

            # 2. FastAPI 路由: @router.get, @app.post, etc.
            fastapi_methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']
            for method in fastapi_methods:
                patterns = [
                    rf'@(?:router|app|api)\.{method}\([\'"]([^\'"]+)[\'"]\)',
                ]
                for pattern in patterns:
                    paths = re.findall(pattern, content)
                    for path in paths:
                        endpoints.append({
                            'path': path,
                            'method': method.upper(),
                            'file': rel_path,
                            'framework': 'fastapi',
                        })

            # 3. 函数定义形式: def get_users(), def post_user(), etc.
            func_patterns = [
                r'def\s+(get|post|put|delete|patch)_([a-zA-Z_]+)\s*\(',
            ]

            for pattern in func_patterns:
                matches = re.findall(pattern, content)
                for method, resource in matches:
                    # 推测路径
                    path = f"/{resource}"
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'file': rel_path,
                        'framework': 'inferred',
                    })

            # 4. APIRouter 注册: router.add_route
            add_route_pattern = r'(?:router|app)\.add_route\([\'"]([^\'"]+)[\'"],\s*.*?,\s*methods\s*=\s*\[(.*?)\]'
            matches = re.findall(add_route_pattern, content)
            for path, methods in matches:
                methods_list = re.findall(r'[\'"](\w+)[\'"]', methods)
                for method in methods_list:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'file': rel_path,
                        'framework': 'fastapi',
                    })

            # 5. Blueprint 注册
            bp_pattern = r'app\.register_blueprint\(([^,]+)(?:,\s*url_prefix\s*=\s*[\'"]([^\'"]+)[\'"])?\)'
            bp_matches = re.findall(bp_pattern, content)
            # 记录 blueprint 前缀（需要跨文件分析，这里先标记）

        except Exception as e:
            pass  # 静默处理错误

        return endpoints

    def _deduplicate_endpoints(self, endpoints: List[Dict]) -> List[Dict]:
        """去重端点"""
        seen = set()
        unique = []

        for endpoint in endpoints:
            key = (endpoint['path'], endpoint['method'], endpoint['file'])
            if key not in seen:
                seen.add(key)
                unique.append(endpoint)

        return unique

    def analyze_endpoints(self, endpoints: List[Dict]) -> Dict:
        """分析端点"""
        print("\n📊 分析端点...")

        analysis = {
            'total_endpoints': len(endpoints),
            'by_method': defaultdict(int),
            'by_framework': defaultdict(int),
            'by_resource': defaultdict(list),
            'path_patterns': defaultdict(list),
            'by_file': defaultdict(list),
        }

        for endpoint in endpoints:
            method = endpoint['method']
            framework = endpoint['framework']
            path = endpoint['path']
            file = endpoint['file']

            analysis['by_method'][method] += 1
            analysis['by_framework'][framework] += 1
            analysis['by_file'][file].append(endpoint)

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
        analysis['by_file'] = dict(analysis['by_file'])

        print(f"   ✓ 总端点: {analysis['total_endpoints']}")
        print(f"   按方法:")
        for method, count in sorted(analysis['by_method'].items(), key=lambda x: x[1], reverse=True):
            print(f"     - {method}: {count}")
        print(f"   按框架:")
        for framework, count in analysis['by_framework'].items():
            print(f"     - {framework}: {count}")

        return analysis

    def _extract_resource(self, path: str) -> str:
        """提取资源名称"""
        # 移除查询参数
        path = path.split('?')[0]

        # 提取第一个非参数路径段
        parts = [p for p in path.split('/') if p and not p.startswith('{') and not p.startswith('<') and not p.startswith(':')]

        if parts:
            return parts[0]

        return 'root'

    def _extract_pattern(self, path: str) -> str:
        """提取路径模式"""
        # 替换所有参数为统一占位符
        pattern = re.sub(r'\{[^}]+\}', '{id}', path)  # FastAPI: {user_id}
        pattern = re.sub(r'<[^>]+:[^>]+>', '<id>', pattern)  # Flask: <int:user_id>
        pattern = re.sub(r'<[^>]+>', '<id>', pattern)  # Flask: <user_id>
        pattern = re.sub(r':[a-zA-Z_]+', ':id', pattern)  # Express-style: :user_id
        return pattern

    def identify_redundancies(self, endpoints: List[Dict], analysis: Dict) -> Dict:
        """识别冗余端点"""
        print("\n🔎 识别冗余端点...")

        redundancies = {
            'duplicate_paths': [],
            'similar_patterns': [],
            'overlapping_resources': [],
            'method_inconsistencies': [],
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

        # 2. 相似的路径模式（同一模式有多个实现）
        patterns = analysis['path_patterns']
        for pattern, eps in patterns.items():
            if len(eps) > 5:  # 阈值：同一模式超过5个端点
                redundancies['similar_patterns'].append({
                    'pattern': pattern,
                    'count': len(eps),
                    'endpoints': eps[:10],  # 只显示前10个
                })

        # 3. 资源端点过多
        resources = analysis['by_resource']
        for resource, eps in resources.items():
            if len(eps) > 15:  # 阈值：单个资源超过15个端点
                redundancies['overlapping_resources'].append({
                    'resource': resource,
                    'count': len(eps),
                    'methods': list(set(e['method'] for e in eps)),
                })

        # 4. RESTful 不一致（同一资源有非标准方法组合）
        for resource, eps in resources.items():
            methods = set(e['method'] for e in eps)
            # RESTful 标准: GET, POST, PUT, DELETE, PATCH
            non_standard = methods - {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'}
            if non_standard:
                redundancies['method_inconsistencies'].append({
                    'resource': resource,
                    'non_standard_methods': list(non_standard),
                })

        print(f"   ✓ 重复路径: {len(redundancies['duplicate_paths'])}")
        print(f"   ✓ 相似模式: {len(redundancies['similar_patterns'])}")
        print(f"   ✓ 重叠资源: {len(redundancies['overlapping_resources'])}")
        print(f"   ✓ 方法不一致: {len(redundancies['method_inconsistencies'])}")

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
                'priority': 'high',
                'action': f"合并 {dup['count']} 个重复端点到单一实现",
                'files': [e['file'] for e in dup['endpoints']],
            })

        # 2. 整合相似模式
        for similar in redundancies['similar_patterns']:
            if similar['count'] > 10:
                target = max(5, similar['count'] // 3)
                plan['consolidation_actions'].append({
                    'type': 'consolidate_pattern',
                    'pattern': similar['pattern'],
                    'current_count': similar['count'],
                    'target_count': target,
                    'savings': similar['count'] - target,
                    'priority': 'medium',
                    'action': f"整合相似端点，统一实现方式",
                })

        # 3. 优化资源端点
        for overlap in redundancies['overlapping_resources']:
            if overlap['count'] > 20:
                target = min(12, overlap['count'])
                plan['consolidation_actions'].append({
                    'type': 'optimize_resource',
                    'resource': overlap['resource'],
                    'current_count': overlap['count'],
                    'target_count': target,
                    'savings': max(0, overlap['count'] - 12),
                    'priority': 'medium',
                    'action': f"按 RESTful 标准重构，减少冗余",
                })

        # 4. 标准化方法
        for inconsistency in redundancies['method_inconsistencies']:
            plan['consolidation_actions'].append({
                'type': 'standardize_methods',
                'resource': inconsistency['resource'],
                'non_standard': inconsistency['non_standard_methods'],
                'savings': 0,
                'priority': 'low',
                'action': f"标准化 HTTP 方法",
            })

        # 计算总节省
        plan['estimated_reduction'] = sum(
            action.get('savings', 0)
            for action in plan['consolidation_actions']
        )

        target_total = len(endpoints) - plan['estimated_reduction']
        plan['target_state'] = {
            'total_endpoints': target_total,
            'reduction_count': plan['estimated_reduction'],
            'reduction_rate': round(plan['estimated_reduction'] / len(endpoints) * 100, 1) if endpoints else 0,
        }

        print(f"   ✓ 整合操作: {len(plan['consolidation_actions'])}")
        print(f"   ✓ 预计减少: {plan['estimated_reduction']} 个端点")
        print(f"   ✓ 减少率: {plan['target_state']['reduction_rate']}%")
        print(f"   ✓ 目标端点数: {target_total}")

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
                'total_files': len(analysis['by_file']),
            },
            'resources': {},
            'files': {},
        }

        # 按资源组织
        for resource, eps in analysis['by_resource'].items():
            catalog['resources'][resource] = {
                'total_endpoints': len(eps),
                'methods': sorted(list(set(e['method'] for e in eps))),
                'endpoints': [
                    {
                        'path': e['path'],
                        'method': e['method'],
                        'file': e['file'],
                        'framework': e['framework'],
                    }
                    for e in sorted(eps, key=lambda x: (x['path'], x['method']))
                ],
            }

        # 按文件组织
        for file, eps in analysis['by_file'].items():
            catalog['files'][file] = {
                'total_endpoints': len(eps),
                'methods': sorted(list(set(e['method'] for e in eps))),
                'resources': sorted(list(set(self._extract_resource(e['path']) for e in eps))),
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
- **当前端点数**: {len(endpoints)}
- **目标端点数**: {plan['target_state']['total_endpoints']}
- **预计减少**: {plan['estimated_reduction']} ({plan['target_state']['reduction_rate']}%)
- **涉及文件数**: {len(analysis['by_file'])}

### 按方法分布
"""

        for method, count in sorted(analysis['by_method'].items(), key=lambda x: x[1], reverse=True):
            pct = round(count/len(endpoints)*100, 1)
            report += f"- **{method}**: {count} ({pct}%)\n"

        report += f"""
### 按框架分布
"""

        for framework, count in sorted(analysis['by_framework'].items(), key=lambda x: x[1], reverse=True):
            pct = round(count/len(endpoints)*100, 1)
            report += f"- **{framework}**: {count} ({pct}%)\n"

        report += f"""
### 按资源分布
共 {len(analysis['by_resource'])} 个资源

Top 20 资源（按端点数）:
"""

        sorted_resources = sorted(analysis['by_resource'].items(), key=lambda x: len(x[1]), reverse=True)[:20]
        for resource, eps in sorted_resources:
            report += f"- **{resource}**: {len(eps)} 个端点\n"

        report += f"""
---

## 二、冗余分析

### 2.1 重复路径
发现 **{len(redundancies['duplicate_paths'])}** 组完全重复的端点

"""

        if redundancies['duplicate_paths']:
            report += "| 路径 | 重复次数 | 文件 |\n"
            report += "|------|---------|------|\n"
            for dup in redundancies['duplicate_paths'][:20]:
                files = ' / '.join(set(e['file'] for e in dup['endpoints']))
                report += f"| `{dup['key']}` | {dup['count']} | {files} |\n"
        else:
            report += "✅ 未发现重复路径\n"

        report += f"""
### 2.2 相似模式
发现 **{len(redundancies['similar_patterns'])}** 组相似的路径模式

"""

        if redundancies['similar_patterns']:
            report += "| 模式 | 端点数 | 建议 |\n"
            report += "|------|-------|------|\n"
            for similar in redundancies['similar_patterns'][:15]:
                report += f"| `{similar['pattern']}` | {similar['count']} | 考虑整合 |\n"
        else:
            report += "✅ 模式分布合理\n"

        report += f"""
### 2.3 资源端点过多
发现 **{len(redundancies['overlapping_resources'])}** 个资源的端点数量过多 (>15)

"""

        if redundancies['overlapping_resources']:
            report += "| 资源 | 端点数 | 方法 |\n"
            report += "|------|-------|------|\n"
            for overlap in redundancies['overlapping_resources']:
                methods = ', '.join(overlap['methods'])
                report += f"| `{overlap['resource']}` | {overlap['count']} | {methods} |\n"
        else:
            report += "✅ 资源端点分布合理\n"

        report += f"""
### 2.4 方法不一致
发现 **{len(redundancies['method_inconsistencies'])}** 个资源使用了非标准 HTTP 方法

"""

        if redundancies['method_inconsistencies']:
            for inconsistency in redundancies['method_inconsistencies'][:10]:
                methods = ', '.join(inconsistency['non_standard_methods'])
                report += f"- **{inconsistency['resource']}**: {methods}\n"
        else:
            report += "✅ 所有资源使用标准 HTTP 方法\n"

        report += f"""
---

## 三、整合计划

### 3.1 整合目标
- **当前**: {len(endpoints)} 个端点
- **目标**: {plan['target_state']['total_endpoints']} 个端点
- **减少**: {plan['estimated_reduction']} 个 ({plan['target_state']['reduction_rate']}%)

### 3.2 整合操作
计划执行 **{len(plan['consolidation_actions'])}** 项整合操作

"""

        action_types = defaultdict(int)
        action_priorities = defaultdict(int)

        for action in plan['consolidation_actions']:
            action_types[action['type']] += 1
            action_priorities[action.get('priority', 'medium')] += 1

        report += "**按类型统计**:\n"
        type_names = {
            'merge_duplicates': '合并重复端点',
            'consolidate_pattern': '整合相似模式',
            'optimize_resource': '优化资源端点',
            'standardize_methods': '标准化方法',
        }
        for action_type, count in sorted(action_types.items(), key=lambda x: x[1], reverse=True):
            type_name = type_names.get(action_type, action_type)
            report += f"- **{type_name}**: {count} 项\n"

        report += "\n**按优先级统计**:\n"
        for priority in ['high', 'medium', 'low']:
            count = action_priorities.get(priority, 0)
            if count > 0:
                report += f"- **{priority.upper()}**: {count} 项\n"

        report += """
### 3.3 详细操作清单

"""

        # 按优先级分组显示
        for priority in ['high', 'medium', 'low']:
            priority_actions = [a for a in plan['consolidation_actions'] if a.get('priority') == priority]
            if priority_actions:
                report += f"#### {priority.upper()} 优先级 ({len(priority_actions)} 项)\n\n"

                for i, action in enumerate(priority_actions[:10], 1):
                    target = action.get('path') or action.get('pattern') or action.get('resource')
                    report += f"""
**{i}. {target}**
- 类型: {type_names.get(action['type'], action['type'])}
- 当前: {action['current_count']} 个端点
"""
                    if action.get('target_count'):
                        report += f"- 目标: {action['target_count']} 个端点\n"
                    if action.get('savings', 0) > 0:
                        report += f"- 节省: {action['savings']} 个端点\n"
                    report += f"- 操作: {action['action']}\n"

                if len(priority_actions) > 10:
                    report += f"\n... 还有 {len(priority_actions) - 10} 项操作\n"

        report += f"""
---

## 四、实施建议

### 4.1 短期（1-2周）- HIGH 优先级
1. **合并重复端点** ({action_priorities.get('high', 0)} 项)
   - 立即处理完全重复的路径
   - 选择最优实现，删除其他版本
   - 更新所有调用方

2. **文档完善**
   - 为所有端点补充 OpenAPI 文档
   - 标注废弃端点

### 4.2 中期（1个月）- MEDIUM 优先级
1. **整合相似模式** ({action_types.get('consolidate_pattern', 0)} 项)
   - 统一实现方式
   - 减少代码重复

2. **RESTful 改造** ({action_types.get('optimize_resource', 0)} 项)
   - 按 REST 标准重构资源端点
   - 统一命名规范

3. **版本管理**
   - 引入 API 版本控制 (/api/v1, /api/v2)
   - 平滑迁移策略

### 4.3 长期（3个月+）- LOW 优先级
1. **标准化方法** ({action_types.get('standardize_methods', 0)} 项)
   - 统一使用标准 HTTP 方法
   - 清理非标准方法

2. **架构优化**
   - 考虑 GraphQL 整合
   - 微服务拆分
   - 网关统一入口

3. **自动化**
   - API 测试覆盖
   - 自动化文档生成
   - 端点监控告警

---

## 五、风险评估

### 高风险操作
- **合并重复端点**: 可能影响现有客户端
  - 缓解措施: 保留别名，添加废弃警告
  - 建议: 使用版本控制

### 中风险操作
- **路径重命名**: 需要更新所有调用方
  - 缓解措施: 保留旧路径3-6个月
  - 建议: 提前通知所有相关方

### 低风险操作
- **文档完善**: 无风险
- **测试补充**: 无风险
- **内部重构**: 对外接口不变

---

## 六、预期收益

### 定量收益
- 端点数量: {len(endpoints)} → {plan['target_state']['total_endpoints']} (-{plan['target_state']['reduction_rate']}%)
- 维护成本: 预计降低 {min(50, plan['target_state']['reduction_rate'] * 1.5):.0f}%
- 测试用例: 预计减少 {min(40, plan['target_state']['reduction_rate']):.0f}%

### 定性收益
- ✅ 代码可维护性提升
- ✅ API 一致性增强
- ✅ 新人上手更容易
- ✅ 文档更清晰
- ✅ 测试覆盖更全面

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
        print("Week 8-9 Day 1: API 审计与分析（改进版）")
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
        print(f"  涉及文件: {len(analysis['by_file'])}")
        print(f"  资源数量: {len(analysis['by_resource'])}")
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

    auditor = ImprovedAPIAuditor(backend_dir, output_dir)
    result = auditor.run()

    print("\n✅ API 审计完成！")


if __name__ == "__main__":
    main()
