#!/usr/bin/env python3
"""模块对比验证框架"""
import re
from pathlib import Path
from typing import Dict, List, Set

class EndpointInfo:
    def __init__(self, method: str, path: str, function: str, line: int):
        self.method = method
        self.path = path
        self.function = function
        self.line = line
    
    def __repr__(self):
        return f"{self.method} {self.path} -> {self.function}() [line {self.line}]"

def extract_endpoints(file_path: Path) -> List[EndpointInfo]:
    """提取文件中的所有端点"""
    endpoints = []
    
    if not file_path.exists():
        return endpoints
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 查找所有路由装饰器
    route_pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    
    for i, line in enumerate(lines, 1):
        match = re.search(route_pattern, line)
        if match:
            method = match.group(1).upper()
            path = match.group(2)
            
            # 查找对应的函数名
            func_name = "unknown"
            for j in range(i, min(i+5, len(lines))):
                func_match = re.match(r'(async\s+)?def\s+(\w+)', lines[j])
                if func_match:
                    func_name = func_match.group(2)
                    break
            
            endpoints.append(EndpointInfo(method, path, func_name, i))
    
    return endpoints

def compare_modules(old_modules: List[Path], unified_module: Path) -> Dict:
    """对比旧模块和统一模块"""
    result = {
        'unified_module': unified_module.name,
        'old_modules': [m.name for m in old_modules],
        'old_endpoints': [],
        'unified_endpoints': [],
        'missing_endpoints': [],
        'new_endpoints': [],
        'matched_endpoints': [],
    }
    
    # 提取旧模块的所有端点
    old_endpoints_map = {}
    for old_module in old_modules:
        endpoints = extract_endpoints(old_module)
        result['old_endpoints'].extend(endpoints)
        for ep in endpoints:
            key = f"{ep.method} {ep.path}"
            old_endpoints_map[key] = ep
    
    # 提取统一模块的端点
    unified_endpoints = extract_endpoints(unified_module)
    result['unified_endpoints'] = unified_endpoints
    
    unified_keys = {f"{ep.method} {ep.path}" for ep in unified_endpoints}
    old_keys = set(old_endpoints_map.keys())
    
    # 识别缺失和新增的端点
    # 注意：路径可能不完全相同，需要模糊匹配
    for old_key in old_keys:
        matched = False
        for unified_key in unified_keys:
            # 简单匹配：如果路径主要部分相同
            old_path = old_key.split()[1]
            unified_path = unified_key.split()[1]
            
            # 提取路径的关键部分
            old_parts = set(old_path.split('/'))
            unified_parts = set(unified_path.split('/'))
            
            # 如果有50%以上的重叠，认为是匹配的
            overlap = len(old_parts & unified_parts)
            if overlap > 0 and overlap >= len(old_parts) * 0.5:
                matched = True
                result['matched_endpoints'].append({
                    'old': old_key,
                    'unified': unified_key
                })
                break
        
        if not matched:
            result['missing_endpoints'].append(old_endpoints_map[old_key])
    
    # 识别新增的端点
    for unified_key in unified_keys:
        matched = False
        for old_key in old_keys:
            old_path = old_key.split()[1]
            unified_path = unified_key.split()[1]
            old_parts = set(old_path.split('/'))
            unified_parts = set(unified_path.split('/'))
            overlap = len(old_parts & unified_parts)
            if overlap > 0 and overlap >= len(old_parts) * 0.5:
                matched = True
                break
        
        if not matched:
            # 找到对应的端点对象
            for ep in unified_endpoints:
                if f"{ep.method} {ep.path}" == unified_key:
                    result['new_endpoints'].append(ep)
                    break
    
    return result

def print_comparison_report(result: Dict):
    """打印对比报告"""
    print("="*80)
    print(f"📊 模块对比报告: {result['unified_module']}")
    print("="*80)
    
    print(f"\n📦 对应的旧模块 ({len(result['old_modules'])}个):")
    for module in result['old_modules']:
        print(f"   - {module}")
    
    print(f"\n📈 端点统计:")
    print(f"   旧模块端点总数: {len(result['old_endpoints'])}")
    print(f"   统一模块端点数: {len(result['unified_endpoints'])}")
    print(f"   匹配的端点: {len(result['matched_endpoints'])}")
    print(f"   缺失的端点: {len(result['missing_endpoints'])}")
    print(f"   新增的端点: {len(result['new_endpoints'])}")
    
    if result['missing_endpoints']:
        print(f"\n⚠️  缺失的端点 ({len(result['missing_endpoints'])}个):")
        for ep in result['missing_endpoints']:
            print(f"   ❌ {ep}")
    
    if result['new_endpoints']:
        print(f"\n✨ 新增的端点 ({len(result['new_endpoints'])}个):")
        for ep in result['new_endpoints']:
            print(f"   ✓ {ep}")
    
    # 计算完成度
    if len(result['old_endpoints']) > 0:
        coverage = (len(result['matched_endpoints']) / len(result['old_endpoints'])) * 100
        print(f"\n📊 功能覆盖率: {coverage:.1f}%")
        
        if coverage >= 90:
            print("   ✅ 优秀：基本完整")
        elif coverage >= 70:
            print("   ⚠️  良好：有一些缺失")
        elif coverage >= 50:
            print("   ⚠️  一般：缺失较多")
        else:
            print("   ❌ 较差：大量缺失")
    
    print()

# 保存函数供后续使用
__all__ = ['extract_endpoints', 'compare_modules', 'print_comparison_report']

