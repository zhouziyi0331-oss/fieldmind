#!/usr/bin/env python3
"""
第一周任务2: 数据库结构完整分析
分析所有表的结构、字段、索引、记录数
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
OUTPUT_PATH = "/Users/alwan/Downloads/FieldMind/fieldmind/WEEK1_DATABASE_SCHEMA.md"

def analyze_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema_report = f"""# FieldMind 数据库完整结构分析
生成时间: {datetime.now().isoformat()}
数据库路径: {DB_PATH}

## 概览

- 总表数: {len(tables)}

"""

    # 分析每个表
    for table_name in tables:
        if table_name.startswith('sqlite_') or table_name.startswith('_alembic'):
            continue

        print(f"分析表: {table_name}")

        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        # 获取索引
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()

        schema_report += f"""
## 表: `{table_name}`

- 记录数: **{count}**
- 列数: {len(columns)}
- 索引数: {len(indexes)}

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
"""

        for col in columns:
            cid, name, type_, notnull, default, pk = col
            notnull_str = "✅" if notnull else ""
            pk_str = "🔑" if pk else ""
            default_str = str(default) if default else ""

            schema_report += f"| {cid} | `{name}` | {type_} | {notnull_str} | {default_str} | {pk_str} |\n"

        # 如果记录数 > 0，显示示例数据
        if count > 0 and count <= 5:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            samples = cursor.fetchall()

            if samples:
                schema_report += "\n### 示例数据（前3条）\n\n"
                col_names = [col[1] for col in columns]
                schema_report += "| " + " | ".join(col_names) + " |\n"
                schema_report += "|" + "---|" * len(col_names) + "\n"

                for row in samples:
                    row_str = []
                    for val in row:
                        if val is None:
                            row_str.append("NULL")
                        elif isinstance(val, str) and len(val) > 50:
                            row_str.append(val[:47] + "...")
                        else:
                            row_str.append(str(val))
                    schema_report += "| " + " | ".join(row_str) + " |\n"

        schema_report += "\n---\n"

    conn.close()

    # 写入文件
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(schema_report)

    print(f"\n✅ 数据库结构分析完成")
    print(f"   报告保存到: {OUTPUT_PATH}")

if __name__ == "__main__":
    analyze_database()
