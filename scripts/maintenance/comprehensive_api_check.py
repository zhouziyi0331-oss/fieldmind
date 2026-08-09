#!/usr/bin/env python3
"""
全面的前后端API连接性检查
检查所有前端API调用是否与后端匹配
"""

import os
import re
import json
from pathlib import Path
from typing import Set, Dict, List, Tuple
from collections import defaultdict

FRONTEND_DIR = "/Users/alwan/FieldMind-Rebuild/fieldmind-web/src"
BACKEND_DIR = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/app"

def extract_all_api_calls_from_file(filepath: str) -> List[Dict]:
    """从单个文件中提取所有API调用"""
    calls = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return calls

    # 多种API调用模式
    patterns = [
        # fetch with template literal
        (r"fetch\s*\(\s*`([^`]+)`", 'template'),
        # fetch with string
        (r"fetch\s*\(\s*['\"]([^'\"]+)['\"]", 'string'),
        # fetch with variable + string
        (r"fetch\s*\(\s*\$\{[^}]+\}\s*\+\s*['\"]([^'\"]+)['\"]", 'concat'),
        # axios methods
        (r"axios\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", 'axios'),
        (r"axios\.(get|post|put|delete|patch)\s*\(\s*`([^`]+)`", 'axios_template'),
        # api instance
        (r"api\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", 'api'),
        (r"api\.(get|post|put|delete|patch)\s*\(\s*`([^`]+)`", 'api_template'),
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern, pattern_type in patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                groups = match.groups()

                # 提取URL和方法
                if 'axios' in pattern_type or 'api' in pattern_type:
                    method = groups[0].upper()
                    url = groups[1]
                else:
                    method = 'GET'  # fetch默认GET
                    url = groups[0]

                # 跳过外部URL
                if url.startswith('http://') or url.startswith('https://'):
                    continue

                calls.append({
                    'file': filepath,
                    'line': line_num,
                    'method': method,
                    'url': url,
                    'raw': line.strip(),
                    'type': pattern_type
                })

    return calls

def extract_all_frontend_calls() -> List[Dict]:
    """扫描所有前端文件"""
    all_calls = []

    for root, dirs, files in os.walk(FRONTEND_DIR):
        if 'node_modules' in root or 'dist' in root or 'build' in root:
            continue

        for file in files:
            if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                filepath = os.path.join(root, file)
                calls = extract_all_api_calls_from_file(filepath)
                all_calls.extend(calls)

    return all_calls

def extract_backend_routes() -> Dict[str, List[Dict]]:
    """提取所有后端路由，包括前缀"""
    routes = defaultdict(list)

    # 从main.py读取路由注册信息
    main_py = os.path.join(BACKEND_DIR, 'main.py')
    prefix_map = {}  # router_name -> prefix

    try:
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            # 匹配 app.include_router(xxx.router, prefix="/api/xxx")
            router_includes = re.findall(
                r'app\.include_router\s*\(\s*([a-z_]+)\.router\s*,\s*prefix\s*=\s*["\']([^"\']+)["\']',
                content
            )
            for router_name, prefix in router_includes:
                prefix_map[router_name] = prefix
    except:
        pass

    # 扫描所有API文件
    api_dir = os.path.join(BACKEND_DIR, 'api')
    for root, dirs, files in os.walk(api_dir):
        for file in files:
            if not file.endswith('.py'):
                continue

            filepath = os.path.join(root, file)
            module_name = file.replace('.py', '')

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找路由装饰器
                route_pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
                matches = re.finditer(route_pattern, content, re.MULTILINE)

                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)

                    # 尝试找到这个router的前缀
                    prefix = prefix_map.get(module_name, '')
                    full_path = prefix + path if prefix else path

                    routes[module_name].append({
                        'method': method,
                        'path': path,
                        'full_path': full_path,
                        'file': filepath
                    })
            except:
                pass

    return routes

def normalize_path(path: str) -> str:
    """标准化路径用于匹配"""
    # 移除查询参数
    path = path.split('?')[0]
    # 移除末尾斜杠
    path = path.rstrip('/')
    # 替换各种参数格式为统一占位符
    path = re.sub(r'\{[^}]+\}', '{param}', path)  # {id}
    path = re.sub(r'\$\{[^}]+\}', '{param}', path)  # ${id}
    path = re.sub(r'/\d+', '/{param}', path)  # /123
    return path

def main():
    print("=" * 100)
    print("全面API连接性检查")
    print("=" * 100)
    print()

    # 1. 提取前端调用
    print("📱 扫描前端API调用...")
    frontend_calls = extract_all_frontend_calls()
    print(f"   找到 {len(frontend_calls)} 个API调用")
    print()

    # 2. 提取后端路由
    print("🔧 扫描后端API路由...")
    backend_routes = extract_backend_routes()
    total_routes = sum(len(routes) for routes in backend_routes.values())
    print(f"   找到 {total_routes} 个后端路由")
    print()

    # 3. 构建后端路由集合（用于快速查找）
    backend_paths = set()
    backend_full_routes = []
    for module, routes in backend_routes.items():
        for route in routes:
            full_key = f"{route['method']} {route['full_path']}"
            backend_paths.add(full_key)
            backend_full_routes.append({
                'method': route['method'],
                'path': route['full_path'],
                'normalized': normalize_path(route['full_path']),
                'module': module
            })

    # 4. 分析每个前端调用
    print("=" * 100)
    print("详细分析")
    print("=" * 100)
    print()

    matched = []
    unmatched = []

    for call in frontend_calls:
        url = call['url']
        method = call['method']
        normalized_call = normalize_path(url)

        # 尝试匹配
        found = False
        matched_route = None

        for route in backend_full_routes:
            if method == route['method'] and normalized_call == route['normalized']:
                found = True
                matched_route = route
                break

        if found:
            matched.append({
                'call': call,
                'route': matched_route
            })
        else:
            unmatched.append(call)

    # 5. 显示未匹配的调用
    print(f"⚠️  未匹配的前端API调用：{len(unmatched)} 个")
    print("-" * 100)

    if unmatched:
        # 按文件分组
        by_file = defaultdict(list)
        for call in unmatched:
            rel_path = os.path.relpath(call['file'], FRONTEND_DIR)
            by_file[rel_path].append(call)

        for file, calls in sorted(by_file.items()):
            print(f"\n📄 {file}")
            for call in calls:
                print(f"   行 {call['line']:4d}: {call['method']:6s} {call['url']}")
                print(f"            {call['raw'][:80]}")
    else:
        print("   ✅ 所有前端API调用都匹配到后端路由")

    print("\n" + "=" * 100)
    print(f"✅ 已匹配：{len(matched)} 个")
    print(f"❌ 未匹配：{len(unmatched)} 个")
    print(f"📊 总计：{len(frontend_calls)} 个前端API调用")
    print("=" * 100)

if __name__ == "__main__":
    main()
