"""
数据治理核心表创建脚本
包括：指标字典、血缘关系、质量监控、变更管理
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from app.core.database import engine


def create_governance_tables():
    """创建数据治理表"""

    print("="*60)
    print("创建数据治理核心表")
    print("="*60)

    with engine.connect() as conn:

        # 1. 指标字典表
        print("\n1. 创建指标字典表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS metric_dictionary (
                metric_id VARCHAR(20) PRIMARY KEY,
                metric_name VARCHAR(100) NOT NULL,
                metric_category VARCHAR(50) NOT NULL COMMENT '分类：结构性/情绪性/语言风格/内容类',
                definition TEXT NOT NULL COMMENT '明确定义',
                calculation_rule TEXT NOT NULL COMMENT '计算规则',
                data_type VARCHAR(20) NOT NULL COMMENT '数据类型：float/int/categorical',
                value_range VARCHAR(50) COMMENT '取值范围',
                unit VARCHAR(20) COMMENT '单位',
                source_fields TEXT COMMENT '依赖的原始字段列表（JSON）',
                algorithm_version VARCHAR(20) COMMENT '算法版本',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active' COMMENT 'active/deprecated/draft',
                INDEX idx_category (metric_category),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标字典表'
        """))
        print("✓ 指标字典表创建完成")

        # 2. 血缘模板表
        print("\n2. 创建血缘模板表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lineage_templates (
                lineage_id INT PRIMARY KEY AUTO_INCREMENT,
                parent_metric_id VARCHAR(20) NOT NULL,
                child_metric_id VARCHAR(20) NOT NULL,
                transform_type VARCHAR(50) NOT NULL COMMENT 'transformation/aggregation/derivation',
                transform_description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_metric_id) REFERENCES metric_dictionary(metric_id),
                FOREIGN KEY (child_metric_id) REFERENCES metric_dictionary(metric_id),
                INDEX idx_parent (parent_metric_id),
                INDEX idx_child (child_metric_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='血缘模板表'
        """))
        print("✓ 血缘模板表创建完成")

        # 3. 血缘关系表（字段级）
        print("\n3. 创建血缘关系表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lineage_edges (
                edge_id INT PRIMARY KEY AUTO_INCREMENT,
                project_id INT NOT NULL,
                source_type VARCHAR(20) NOT NULL COMMENT 'file/chunk/metric/report',
                source_id VARCHAR(50) NOT NULL,
                target_type VARCHAR(20) NOT NULL COMMENT 'file/chunk/metric/report',
                target_id VARCHAR(50) NOT NULL,
                transform_type VARCHAR(50) NOT NULL COMMENT 'copy/extract/aggregate/derive/model',
                transform_description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                confidence DECIMAL(3,2) DEFAULT 1.0 COMMENT '血缘置信度',
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                INDEX idx_source (source_type, source_id),
                INDEX idx_target (target_type, target_id),
                INDEX idx_project (project_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='血缘关系表'
        """))
        print("✓ 血缘关系表创建完成")

        # 4. 指标计算历史表
        print("\n4. 创建指标计算历史表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS metric_calculation_history (
                id INT PRIMARY KEY AUTO_INCREMENT,
                chunk_id VARCHAR(50) NOT NULL,
                metric_id VARCHAR(20) NOT NULL,
                metric_value TEXT NOT NULL COMMENT '实际计算值',
                calculation_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                calculation_trigger VARCHAR(100) NOT NULL COMMENT '触发源：agent名称/手动',
                algorithm_version VARCHAR(20),
                execution_time_ms INT COMMENT '计算耗时',
                FOREIGN KEY (metric_id) REFERENCES metric_dictionary(metric_id),
                INDEX idx_chunk (chunk_id),
                INDEX idx_metric (metric_id),
                INDEX idx_timestamp (calculation_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标计算历史表'
        """))
        print("✓ 指标计算历史表创建完成")

        # 5. 数据质量规则表
        print("\n5. 创建数据质量规则表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS quality_rules (
                rule_id INT PRIMARY KEY AUTO_INCREMENT,
                rule_name VARCHAR(100) NOT NULL,
                rule_type VARCHAR(50) NOT NULL COMMENT 'null_check/range_check/pattern_match/unique_check',
                target_table VARCHAR(50) NOT NULL,
                target_column VARCHAR(50) NOT NULL,
                rule_expression TEXT NOT NULL COMMENT 'SQL表达式或检查逻辑',
                severity VARCHAR(20) DEFAULT 'warning' COMMENT 'error/warning/info',
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_target (target_table, target_column),
                INDEX idx_enabled (enabled)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据质量规则表'
        """))
        print("✓ 数据质量规则表创建完成")

        # 6. 质量检查结果表
        print("\n6. 创建质量检查结果表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS quality_check_results (
                result_id INT PRIMARY KEY AUTO_INCREMENT,
                rule_id INT NOT NULL,
                project_id INT NOT NULL,
                check_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                passed BOOLEAN NOT NULL,
                failed_count INT,
                total_count INT,
                error_details TEXT,
                FOREIGN KEY (rule_id) REFERENCES quality_rules(rule_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                INDEX idx_rule (rule_id),
                INDEX idx_project (project_id),
                INDEX idx_timestamp (check_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='质量检查结果表'
        """))
        print("✓ 质量检查结果表创建完成")

        # 7. 变更事件表
        print("\n7. 创建变更事件表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS change_events (
                event_id INT PRIMARY KEY AUTO_INCREMENT,
                target_type VARCHAR(20) NOT NULL COMMENT 'metric/rule/schema',
                target_id VARCHAR(50) NOT NULL,
                change_type VARCHAR(20) NOT NULL COMMENT 'create/update/delete/deprecate',
                change_description TEXT,
                old_value TEXT,
                new_value TEXT,
                initiator VARCHAR(100) COMMENT '变更发起人',
                status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/approved/rejected/applied',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                approved_at DATETIME,
                applied_at DATETIME,
                impact_analysis TEXT COMMENT '影响分析结果（JSON）',
                INDEX idx_target (target_type, target_id),
                INDEX idx_status (status),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='变更事件表'
        """))
        print("✓ 变更事件表创建完成")

        conn.commit()

    print("\n" + "="*60)
    print("✅ 数据治理核心表创建完成")
    print("="*60)


if __name__ == "__main__":
    try:
        create_governance_tables()
    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
