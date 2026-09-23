#!/usr/bin/env python3
"""完整清理所有已删除模块的引用"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 所有已删除模块的标识
deleted_patterns = [
    'knowledge_graph_p3', 'knowledge_graph_v3', 'knowledge_graph_api',
    'knowledge_graph_enhanced', 'knowledge_graph_v2', 'document_processing_v2',
    '.router', '.enhanced', '_v2.', '_v3.', '_p3.', '_old', '_api.'
]

new_lines = []
removed_count = 0

for i, line in enumerate(lines, start=1):
    should_remove = False
    
    # 跳过空行和注释
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        new_lines.append(line)
        continue
    
    # 检查是否包含已删除模块的引用
    for pattern in deleted_patterns:
        if pattern in line:
            # 确保是路由注册或导入语句
            if 'app.include_router' in line or 'from app.api' in line:
                # 不要删除统一模块
                if 'unified_' not in line:
                    should_remove = True
                    print(f"删除第{i}行: {line.strip()[:100]}")
                    removed_count += 1
                    break
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行")
