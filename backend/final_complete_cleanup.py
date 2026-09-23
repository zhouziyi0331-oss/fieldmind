#!/usr/bin/env python3
"""最终完整清理"""
from pathlib import Path
import re

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 所有已删除模块的完整列表
deleted_modules = [
    'conversation', 'skill_generation', 'skill_optimization', 
    'knowledge_graph_p3', 'knowledge_graph_api', 'knowledge_graph_enhanced',
    'document_processing_v2', 'knowledge_graph_v3'
]

# 删除所有包含这些模块的 from...import 行
for module in deleted_modules:
    # 删除 from app.api.v1 import xxx
    content = re.sub(rf'^\s*from app\.api\.v1 import {module}\s*\n', '', content, flags=re.MULTILINE)
    # 删除 from app.api import xxx  
    content = re.sub(rf'^\s*from app\.api import {module}\s*\n', '', content, flags=re.MULTILINE)

# 删除所有包含这些模块的 app.include_router 行
for module in deleted_modules:
    content = re.sub(rf'^\s*app\.include_router\({module}\.router.*?\)\s*\n', '', content, flags=re.MULTILINE)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 最终清理完成！")
