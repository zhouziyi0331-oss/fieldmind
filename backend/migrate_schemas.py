#!/usr/bin/env python3
"""
Pydantic v2 Schema迁移脚本
将 class Config 迁移到 model_config = ConfigDict
"""
import re
from pathlib import Path

def migrate_simple_config(content: str) -> tuple[str, int]:
    """迁移简单的 from_attributes = True 配置"""
    # 匹配模式：
    # class Config:
    #     from_attributes = True
    pattern = r'(\s+)class Config:\n\1    from_attributes = True\n'
    replacement = r'\1model_config = ConfigDict(from_attributes=True)\n'

    new_content, count = re.subn(pattern, replacement, content)
    return new_content, count

def add_configdict_import(content: str) -> str:
    """添加 ConfigDict 导入"""
    # 检查是否已有导入
    if 'ConfigDict' in content:
        return content

    # 查找 pydantic import 行
    pydantic_import_pattern = r'(from pydantic import [^\n]+)'

    def add_configdict(match):
        imports = match.group(1)
        if 'ConfigDict' not in imports:
            # 在末尾添加 ConfigDict
            imports = imports.rstrip()
            if imports.endswith(')'):
                # 多行导入
                imports = imports[:-1] + ', ConfigDict)'
            else:
                # 单行导入
                imports += ', ConfigDict'
        return imports

    content = re.sub(pydantic_import_pattern, add_configdict, content)
    return content

def migrate_complex_config(content: str) -> tuple[str, int]:
    """迁移包含 json_schema_extra 的配置"""
    # 匹配模式：
    # class Config:
    #     json_schema_extra = {...}
    pattern = r'(\s+)class Config:\n(\1    json_schema_extra = \{[^}]+\})\n'

    def replacement(match):
        indent = match.group(1)
        json_extra = match.group(2).replace('json_schema_extra', 'json_schema_extra')
        return f'{indent}model_config = ConfigDict(\n{json_extra}\n{indent})\n'

    new_content, count = re.subn(pattern, replacement, content)
    return new_content, count

def migrate_file(file_path: Path) -> int:
    """迁移单个文件"""
    if not file_path.exists():
        return 0

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    total_changes = 0

    # Step 1: 添加 ConfigDict 导入
    if 'class Config:' in content:
        content = add_configdict_import(content)

    # Step 2: 迁移复杂配置（包含json_schema_extra）
    content, count = migrate_complex_config(content)
    total_changes += count

    # Step 3: 迁移简单配置（仅from_attributes）
    content, count = migrate_simple_config(content)
    total_changes += count

    # 写回文件
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')

    return total_changes

def main():
    schema_files = [
        'app/schemas/user.py',
        'app/schemas/skill.py',
        'app/schemas/timeline.py',
        'app/schemas/workflow.py',
        'app/schemas/industry.py',
        'app/schemas/scheduler.py',
    ]

    total = 0
    for file_rel in schema_files:
        file_path = Path(file_rel)
        count = migrate_file(file_path)
        if count > 0:
            print(f"✅ {file_rel}: {count} 处Config类已迁移")
            total += count
        else:
            print(f"⏭️  {file_rel}: 无需修改")

    print(f"\n📊 总计: {total} 处Schema Config已迁移到Pydantic v2")

if __name__ == '__main__':
    main()
