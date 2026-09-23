#!/usr/bin/env python3
"""分析剩余模块的端点"""
import re
from pathlib import Path

# 报告生成模块
report_modules = [
    "src/app/api/export_summaries.py",
    "src/app/api/v1/reports.py",
]

# 导入导出模块
io_modules = [
    "src/app/api/v1/import_data.py",
    "src/app/api/v1/export.py",
]

# 工具模块
tool_modules = [
    "src/app/api/ocr.py",
    "src/app/api/audio.py",
]

all_modules = {
    "报告生成": report_modules,
    "导入导出": io_modules,
    "工具模块": tool_modules
}

for category, modules in all_modules.items():
    print("="*80)
    print(f"{category}模块分析")
    print("="*80)
    
    total_endpoints = 0
    
    for module_path in modules:
        module_name = Path(module_path).stem
        parent = Path(module_path).parent.name
        full_name = f"{parent}/{module_name}" if parent != "api" else module_name
        
        if not Path(module_path).exists():
            print(f"\n❌ {full_name}: 文件不存在")
            continue
        
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取端点
        pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        
        endpoints = []
        for method, path in matches:
            endpoints.append(f"{method.upper():6} {path}")
        
        total_endpoints += len(endpoints)
        
        print(f"\n📁 {full_name} ({len(endpoints)}个端点)")
        for ep in endpoints[:8]:
            print(f"   {ep}")
        if len(endpoints) > 8:
            print(f"   ... 还有 {len(endpoints)-8} 个端点")
    
    print(f"\n小计: {total_endpoints} 个端点\n")

