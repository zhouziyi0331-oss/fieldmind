#!/usr/bin/env python3
"""
数据一致性校验脚本
检查 SQLite(fact_statements) 和 ChromaDB(向量) 之间的数据一致性
"""
import sys
import os

# 添加父目录到路径以便导入app模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.fact_statement import FactStatement
from app.core.rag_engine import rag_engine
from app.core.database import get_fact_db_session
from typing import List, Dict


def check_sqlite_stats() -> Dict:
    """检查SQLite中的fact_statements统计"""
    print("\n📊 检查 SQLite (fact_statements)...")

    db = next(get_fact_db_session())

    try:
        total_facts = db.query(FactStatement).count()

        # 按项目分组统计
        facts_by_project = db.query(
            FactStatement.project_id,
            func.count(FactStatement.id).label('count')
        ).group_by(FactStatement.project_id).all()

        # 带时间戳的陈述
        facts_with_timestamp = db.query(FactStatement).filter(
            FactStatement.start_sec.isnot(None)
        ).count()

        # 带向量ID的陈述
        facts_with_vector_id = db.query(FactStatement).filter(
            FactStatement.vector_id.isnot(None),
            FactStatement.vector_id != ''
        ).count()

        print(f"  ✅ 总陈述数: {total_facts}")
        print(f"  ✅ 带时间戳: {facts_with_timestamp} ({facts_with_timestamp/total_facts*100:.1f}%)" if total_facts > 0 else "")
        print(f"  ✅ 带向量ID: {facts_with_vector_id} ({facts_with_vector_id/total_facts*100:.1f}%)" if total_facts > 0 else "")
        print(f"\n  按项目分布:")
        for project_id, count in facts_by_project:
            print(f"    项目 {project_id}: {count} 条")

        return {
            'total_facts': total_facts,
            'facts_with_timestamp': facts_with_timestamp,
            'facts_with_vector_id': facts_with_vector_id,
            'by_project': dict(facts_by_project)
        }

    finally:
        db.close()


def check_chromadb_stats() -> Dict:
    """检查ChromaDB中的向量统计"""
    print("\n🔍 检查 ChromaDB (向量存储)...")

    try:
        collection = rag_engine.vector_store

        # 获取总向量数
        total_vectors = collection.count()

        # 按项目分组（通过metadata）
        all_data = collection.get(include=["metadatas"])

        vectors_by_project = {}
        for metadata in all_data['metadatas']:
            project_id = metadata.get('project_id')
            if project_id:
                vectors_by_project[project_id] = vectors_by_project.get(project_id, 0) + 1

        print(f"  ✅ 总向量数: {total_vectors}")
        print(f"\n  按项目分布:")
        for project_id, count in vectors_by_project.items():
            print(f"    项目 {project_id}: {count} 个向量")

        return {
            'total_vectors': total_vectors,
            'by_project': vectors_by_project
        }

    except Exception as e:
        print(f"  ❌ ChromaDB查询失败: {e}")
        return {
            'total_vectors': 0,
            'by_project': {},
            'error': str(e)
        }


def find_missing_vectors(sqlite_stats: Dict, chromadb_stats: Dict) -> List[int]:
    """找出缺失向量的项目"""
    print("\n🔎 检测数据不一致...")

    missing_projects = []
    inconsistent_projects = []

    for project_id, fact_count in sqlite_stats['by_project'].items():
        vector_count = chromadb_stats['by_project'].get(project_id, 0)

        if vector_count == 0:
            missing_projects.append(project_id)
            print(f"  ⚠️  项目 {project_id}: {fact_count} 条fact，但 0 个向量（完全缺失）")
        elif vector_count < fact_count:
            inconsistent_projects.append(project_id)
            diff = fact_count - vector_count
            print(f"  ⚠️  项目 {project_id}: {fact_count} 条fact，但只有 {vector_count} 个向量（缺失 {diff} 个）")
        else:
            print(f"  ✅ 项目 {project_id}: {fact_count} 条fact，{vector_count} 个向量（一致）")

    return missing_projects + inconsistent_projects


def suggest_fix(inconsistent_projects: List[int]):
    """提供修复建议"""
    if not inconsistent_projects:
        print("\n🎉 所有数据一致，无需修复！")
        return

    print("\n🔧 修复建议:")
    print(f"  发现 {len(inconsistent_projects)} 个项目存在不一致")
    print(f"\n  运行以下命令重新生成向量:")
    print(f"    python scripts/reindex_vectors.py --projects {','.join(map(str, inconsistent_projects))}")
    print(f"\n  或重新处理这些项目的文档:")
    for project_id in inconsistent_projects:
        print(f"    python scripts/reprocess_project.py --project-id {project_id}")


def main():
    print("=" * 60)
    print("🔍 FieldMind 数据一致性校验")
    print("=" * 60)

    # 检查SQLite
    sqlite_stats = check_sqlite_stats()

    # 检查ChromaDB
    chromadb_stats = check_chromadb_stats()

    # 对比差异
    inconsistent_projects = find_missing_vectors(sqlite_stats, chromadb_stats)

    # 提供修复建议
    suggest_fix(inconsistent_projects)

    print("\n" + "=" * 60)
    print("✅ 校验完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
