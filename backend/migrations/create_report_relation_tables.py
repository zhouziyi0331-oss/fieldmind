"""
创建报告关系相关表
包括: report_relations, report_entities, report_entity_relations, report_network_nodes, report_network_edges
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from app.core.database import engine, Base
from app.models.report_relation import (
    ReportRelation,
    ReportEntity,
    ReportEntityRelation,
    ReportNetworkNode,
    ReportNetworkEdge
)

def create_tables():
    """创建报告关系相关表"""
    print("开始创建报告关系相关表...")

    try:
        # 创建表
        Base.metadata.create_all(
            engine,
            tables=[
                ReportRelation.__table__,
                ReportEntity.__table__,
                ReportEntityRelation.__table__,
                ReportNetworkNode.__table__,
                ReportNetworkEdge.__table__
            ]
        )

        print("✅ 报告关系表创建成功！")
        print("\n创建的表:")
        print("  1. report_relations - 报告关系表")
        print("  2. report_entities - 报告实体表")
        print("  3. report_entity_relations - 报告实体关系表")
        print("  4. report_network_nodes - 报告网络节点表")
        print("  5. report_network_edges - 报告网络边表")

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        raise

if __name__ == "__main__":
    create_tables()
