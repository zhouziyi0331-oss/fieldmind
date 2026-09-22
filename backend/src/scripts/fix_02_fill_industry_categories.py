#!/usr/bin/env python3
"""
填充行业分类数据

修复：industry_categories表为空导致行业分类功能无法使用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid
import json
from datetime import datetime
import sqlite3

# 基础行业分类数据
INDUSTRY_CATEGORIES = [
    {
        "category_id": "agriculture",
        "name": "农业",
        "description": "农业、林业、畜牧业、渔业相关领域"
    },
    {
        "category_id": "manufacturing",
        "name": "制造业",
        "description": "生产制造、加工业、装备制造等"
    },
    {
        "category_id": "technology",
        "name": "科技",
        "description": "信息技术、互联网、人工智能、软件开发等"
    },
    {
        "category_id": "finance",
        "name": "金融",
        "description": "银行、保险、证券、投资等金融服务"
    },
    {
        "category_id": "education",
        "name": "教育",
        "description": "学校教育、职业培训、在线教育等"
    },
    {
        "category_id": "healthcare",
        "name": "医疗健康",
        "description": "医疗服务、医药、健康管理等"
    },
    {
        "category_id": "culture",
        "name": "文化",
        "description": "文化遗产、艺术、传媒、娱乐等"
    },
    {
        "category_id": "tourism",
        "name": "旅游",
        "description": "旅游服务、酒店、景区等"
    },
    {
        "category_id": "retail",
        "name": "零售",
        "description": "商业、批发零售、电子商务等"
    },
    {
        "category_id": "real_estate",
        "name": "房地产",
        "description": "房地产开发、物业管理等"
    },
    {
        "category_id": "transportation",
        "name": "交通运输",
        "description": "物流、运输、仓储等"
    },
    {
        "category_id": "energy",
        "name": "能源",
        "description": "电力、石油、天然气、新能源等"
    },
    {
        "category_id": "government",
        "name": "政府/公共服务",
        "description": "政府机构、公共服务、社会组织等"
    },
    {
        "category_id": "other",
        "name": "其他",
        "description": "其他未分类行业"
    }
]


def fill_industry_categories():
    """填充行业分类数据"""
    print("="*60)
    print("填充行业分类数据")
    print("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM industry_categories")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"⚠️ 已有 {existing_count} 个分类，跳过填充")
        conn.close()
        return

    # 插入分类数据
    inserted = 0
    for category in INDUSTRY_CATEGORIES:
        category_id_db = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO industry_categories
            (id, category_id, name, description, document_count, entity_count,
             overview, detailed_analysis, statistics, trends, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            category_id_db,
            category['category_id'],
            category['name'],
            category['description'],
            0,  # document_count
            0,  # entity_count
            json.dumps({}),  # overview
            json.dumps({}),  # detailed_analysis
            json.dumps({}),  # statistics
            json.dumps({}),  # trends
            datetime.utcnow(),
            datetime.utcnow()
        ))
        inserted += 1

    conn.commit()
    conn.close()

    print(f"✅ 已插入 {inserted} 个行业分类")


def verify_categories():
    """验证分类数据"""
    print("\n" + "="*60)
    print("验证分类数据")
    print("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT category_id, name, description FROM industry_categories")
    categories = cursor.fetchall()

    if categories:
        print(f"\n当前分类列表（共{len(categories)}个）:")
        for category_id, name, description in categories:
            print(f"  - [{category_id}] {name}")
            print(f"    {description}")
    else:
        print("❌ 分类表仍为空")

    conn.close()


if __name__ == "__main__":
    fill_industry_categories()
    verify_categories()

    print("\n" + "="*60)
    print("✅ 问题 #2 修复完成")
    print("="*60)
