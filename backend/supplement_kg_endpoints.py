#!/usr/bin/env python3
"""提取知识图谱模块缺失端点的代码"""
from pathlib import Path
import re

# 读取旧模块
old_kg_path = Path("archive/old_modules/knowledge_graph.py")
with open(old_kg_path, 'r', encoding='utf-8') as f:
    old_content = f.read()
    old_lines = old_content.split('\n')

# 需要提取的端点及其行号范围
endpoints_to_extract = [
    {
        'name': 'get_entity_detail',
        'start_line': 155,
        'decorator': '@router.get("/entities/{entity_id}"',
    },
    {
        'name': 'delete_entity',
        'start_line': 295,
        'decorator': '@router.delete("/entities/{entity_id}/"',
    },
    {
        'name': 'get_entity_evidences',
        'start_line': 160,
        'decorator': '@router.get("/entities/{entity_id}/evidences/"',
    },
    {
        'name': 'get_category_evidences',
        'start_line': 222,
        'decorator': '@router.get("/categories/{category}/evidences/"',
    },
    {
        'name': 'get_category_stats',
        'start_line': 272,
        'decorator': '@router.get("/categories/stats"',
    },
    {
        'name': 'delete_evidence',
        'start_line': 363,
        'decorator': '@router.delete("/evidences/{evidence_id}/"',
    },
    {
        'name': 'get_document_entities',
        'start_line': 439,
        'decorator': '@router.get("/documents/{document_id}/entities/"',
    },
]

print("="*80)
print("📋 提取知识图谱模块缺失端点的代码")
print("="*80)

for endpoint in endpoints_to_extract:
    print(f"\n{'='*80}")
    print(f"端点: {endpoint['name']}")
    print(f"装饰器: {endpoint['decorator']}")
    print(f"起始行: {endpoint['start_line']}")
    print('='*80)
    
    # 从指定行开始提取，直到遇到下一个路由装饰器或函数定义
    start_idx = endpoint['start_line'] - 1
    code_lines = []
    
    # 找到装饰器开始
    found_decorator = False
    for i in range(max(0, start_idx - 10), start_idx + 5):
        if '@router.' in old_lines[i]:
            start_idx = i
            found_decorator = True
            break
    
    if not found_decorator:
        print(f"⚠️  未找到装饰器，跳过")
        continue
    
    # 提取代码直到下一个装饰器或文件结束
    in_function = False
    indent_level = 0
    
    for i in range(start_idx, len(old_lines)):
        line = old_lines[i]
        
        # 如果遇到下一个路由装饰器，停止
        if i > start_idx and '@router.' in line:
            break
        
        # 如果遇到新的函数定义（且不是当前函数）
        if in_function and re.match(r'^(async\s+)?def\s+\w+', line):
            break
        
        # 如果是def行，标记进入函数
        if 'def ' in line:
            in_function = True
            indent_level = len(line) - len(line.lstrip())
        
        # 如果已在函数内，检查缩进是否回到函数外
        if in_function and line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and i > start_idx + 5:
                # 缩进回到函数外，停止
                break
        
        code_lines.append(line)
    
    # 打印提取的代码
    code = '\n'.join(code_lines)
    print(code)
    print()

