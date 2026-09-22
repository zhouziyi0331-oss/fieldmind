#!/usr/bin/env python3
"""提取所有API端点"""
import re
import os
from pathlib import Path

api_files = []
api_dir = Path("src/app/api")

# 收集所有API文件
for file in api_dir.rglob("*.py"):
    if file.name != "__init__.py":
        api_files.append(file)

print(f"📊 发现 {len(api_files)} 个API文件\n")

all_endpoints = []

for file in sorted(api_files):
    try:
        content = file.read_text(encoding='utf-8')
        
        # 查找路由装饰器
        pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        
        if matches:
            module = str(file.relative_to("src/app/api"))
            for method, path in matches:
                all_endpoints.append({
                    'module': module,
                    'method': method.upper(),
                    'path': path
                })
    except Exception as e:
        print(f"❌ 处理失败: {file} - {e}")

print(f"✅ 总共找到 {len(all_endpoints)} 个API端点\n")

# 按模块分组
by_module = {}
for ep in all_endpoints:
    module = ep['module']
    if module not in by_module:
        by_module[module] = []
    by_module[module].append(ep)

# 输出统计
print("="*80)
print("按模块统计:")
print("="*80)
for module in sorted(by_module.keys()):
    endpoints = by_module[module]
    print(f"\n📁 {module} ({len(endpoints)} 个端点)")
    for ep in endpoints[:5]:  # 显示前5个
        print(f"   {ep['method']:6} {ep['path']}")
    if len(endpoints) > 5:
        print(f"   ... 还有 {len(endpoints)-5} 个端点")

print(f"\n\n总计: {len(api_files)} 个模块, {len(all_endpoints)} 个端点")
