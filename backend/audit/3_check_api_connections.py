#!/usr/bin/env python3
"""检查前端调用的 API 是否在后端存在"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(".")

def extract_frontend_api_calls():
    """从所有前端文件中提取 fetch/axios 调用的 API 路径"""
    api_calls = set()

    patterns = [
        r'fetch\([\'"`](/api/[^\'"`]+)[\'"`]',
        r'axios\.\w+\([\'"`](/api/[^\'"`]+)[\'"`]',
        r'\.get\([\'"`](/api/[^\'"`]+)[\'"`]',
        r'\.post\([\'"`](/api/[^\'"`]+)[\'"`]',
    ]

    for ext in ['*.html', '*.js', '*.ts', '*.jsx', '*.tsx', '*.vue']:
        for f in PROJECT_ROOT.rglob(ext):
            if 'node_modules' in str(f) or '.git' in str(f) or 'venv' in str(f):
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                for pattern in patterns:
                    for match in re.findall(pattern, content):
                        # 去掉查询参数
                        api_path = match.split('?')[0]
                        # 去掉路径参数
                        api_path = re.sub(r'/\d+', '/{id}', api_path)
                        api_calls.add((api_path, str(f)))
            except:
                pass

    return api_calls

def extract_backend_routes():
    """从后端文件中提取所有注册的路由"""
    routes = set()

    patterns = [
        r'@app\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
        r'@router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
        r'\.add_api_route\([\'"`]([^\'"`]+)[\'"`]',
    ]

    # 找router前缀
    prefix_pattern = r'app\.include_router\([^)]*prefix=[\'"`]([^\'"`]+)[\'"`]'

    for ext in ['*.py']:
        for f in PROJECT_ROOT.rglob(ext):
            if 'venv' in str(f) or '.git' in str(f) or 'node_modules' in str(f):
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                for pattern in patterns:
                    for match in re.findall(pattern, content):
                        if isinstance(match, tuple):
                            route = match[-1]
                        else:
                            route = match
                        # 规范化
                        route = route.rstrip('/')
                        routes.add(route)

                # 查找router前缀
                for prefix in re.findall(prefix_pattern, content):
                    routes.add(prefix)
            except:
                pass

    return routes

def main():
    print("🔍 检查 API 断联...\n")

    print("正在扫描前端调用...")
    api_calls = extract_frontend_api_calls()
    print(f"   找到 {len(api_calls)} 个前端 API 调用\n")

    print("正在扫描后端路由...")
    backend_routes = extract_backend_routes()
    print(f"   找到 {len(backend_routes)} 个后端路由\n")

    # 检查断联
    disconnected = []
    for api_path, source_file in api_calls:
        # 查找是否有匹配的后端路由
        matched = False
        for route in backend_routes:
            if route in api_path or api_path in route:
                matched = True
                break
            # 处理路径参数 {id} vs :id
            route_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', route)
            route_pattern = re.sub(r':[^/]+', r'[^/]+', route_pattern)
            if re.match(route_pattern, api_path):
                matched = True
                break

        if not matched:
            disconnected.append((api_path, source_file))

    print("=" * 60)
    if disconnected:
        print(f"\n❌ 发现 {len(disconnected)} 个前端调用但后端无对应路由：\n")
        for api_path, source in disconnected[:30]:
            print(f"   {api_path}")
            print(f"      来源: {source}")
        if len(disconnected) > 30:
            print(f"   ... 还有 {len(disconnected) - 30} 个")
    else:
        print("\n✅ 前端所有调用都有对应的后端路由")

    # 检查孤儿路由
    print("\n" + "=" * 60)
    orphan_routes = []
    for route in backend_routes:
        found = False
        for api_path, _ in api_calls:
            if route in api_path or api_path in route:
                found = True
                break
        if not found:
            orphan_routes.append(route)

    if orphan_routes:
        print(f"\n⚠️ 发现 {len(orphan_routes)} 个后端路由未被前端调用：\n")
        for route in orphan_routes[:30]:
            print(f"   {route}")
        if len(orphan_routes) > 30:
            print(f"   ... 还有 {len(orphan_routes) - 30} 个")
    else:
        print("\n✅ 后端所有路由都被前端调用")

if __name__ == "__main__":
    main()
