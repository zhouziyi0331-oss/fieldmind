"""
SQLite 数据库迁移脚本 - 文档规范化表

为 SQLite 创建文档规范化相关的表
"""

import sqlite3
import os
from datetime import datetime

# 数据库路径
DB_PATH = "/Users/alwan/FieldMind/backend/src/data/fieldmind.db"

def create_tables():
    """创建文档规范化表"""

    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🚀 开始创建文档规范化表...")

    # =====================================================
    # 表1: 文档规范化日志表
    # =====================================================
    print("📝 创建表: document_normalization_logs")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_normalization_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        file_type VARCHAR(50) NOT NULL,
        normalization_rule VARCHAR(100) NOT NULL,

        original_content_sample TEXT,
        normalized_content_sample TEXT,

        dirty_data_found TEXT,
        dirty_data_handled TEXT,

        completeness_score REAL DEFAULT 0.0,
        completeness_details TEXT,

        confidence REAL DEFAULT 1.0,
        quality_issues TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processing_time_ms INTEGER,

        FOREIGN KEY (file_id) REFERENCES project_documents(id) ON DELETE CASCADE
    )
    """)

    # 创建索引
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_normalization_logs_file_id
    ON document_normalization_logs(file_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_normalization_logs_file_type
    ON document_normalization_logs(file_type)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_normalization_logs_created_at
    ON document_normalization_logs(created_at DESC)
    """)

    # =====================================================
    # 表2: 文件规范化内容表
    # =====================================================
    print("📝 创建表: file_normalized_content")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_normalized_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,

        content_type VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,

        metadata TEXT,
        source_location TEXT,
        extraction_method VARCHAR(100),

        confidence REAL DEFAULT 1.0,
        is_verified INTEGER DEFAULT 0,

        sequence INTEGER DEFAULT 0,
        parent_id INTEGER,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (file_id) REFERENCES project_documents(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES file_normalized_content(id) ON DELETE SET NULL
    )
    """)

    # 创建索引
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_normalized_content_file_id
    ON file_normalized_content(file_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_normalized_content_type
    ON file_normalized_content(content_type)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_normalized_content_sequence
    ON file_normalized_content(file_id, sequence)
    """)

    # =====================================================
    # 表3: 脏数据处理规则配置表
    # =====================================================
    print("📝 创建表: dirty_data_rules")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dirty_data_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        rule_name VARCHAR(100) NOT NULL UNIQUE,
        rule_type VARCHAR(50) NOT NULL,

        applicable_file_types TEXT,
        rule_config TEXT NOT NULL,

        is_enabled INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 0,

        description TEXT,
        examples TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 创建索引
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_dirty_data_rules_enabled
    ON dirty_data_rules(is_enabled)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_dirty_data_rules_type
    ON dirty_data_rules(rule_type)
    """)

    # =====================================================
    # 表4: 文件完整性检查记录表
    # =====================================================
    print("📝 创建表: file_completeness_checks")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_completeness_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,

        check_type VARCHAR(50) NOT NULL,
        is_passed INTEGER NOT NULL,
        score REAL,

        details TEXT,
        issues TEXT,
        recommendations TEXT,

        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (file_id) REFERENCES project_documents(id) ON DELETE CASCADE
    )
    """)

    # 创建索引
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_completeness_checks_file_id
    ON file_completeness_checks(file_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_completeness_checks_type
    ON file_completeness_checks(check_type)
    """)

    # =====================================================
    # 插入默认脏数据处理规则
    # =====================================================
    print("📝 插入默认脏数据处理规则...")

    default_rules = [
        {
            'rule_name': 'remove_filler_words',
            'rule_type': 'preprocessing',
            'applicable_file_types': '["audio", "video"]',
            'rule_config': '{"patterns": ["嗯", "啊", "那个", "这个", "呃"], "action": "remove", "threshold": 0.8}',
            'description': '去除无意义的口头禅',
            'examples': '[{"before": "嗯嗯嗯，那个，我觉得", "after": "我觉得"}]'
        },
        {
            'rule_name': 'fix_ocr_errors',
            'rule_type': 'postprocessing',
            'applicable_file_types': '["document", "image"]',
            'rule_config': '{"replacements": {"0": "○", "l": "I"}, "action": "replace", "threshold": 0.9}',
            'description': '修正常见的OCR识别错误',
            'examples': '[{"before": "这是第l条", "after": "这是第1条"}]'
        },
        {
            'rule_name': 'keep_emotional_words',
            'rule_type': 'preprocessing',
            'applicable_file_types': '["audio", "video"]',
            'rule_config': '{"patterns": ["唉", "哎哟", "哇", "嘿"], "action": "keep_and_tag", "tag": "[情感]"}',
            'description': '保留有情感含义的语气词',
            'examples': '[{"before": "唉，真难啊", "after": "[情感:唉] 真难啊"}]'
        },
        {
            'rule_name': 'recognize_table_units',
            'rule_type': 'postprocessing',
            'applicable_file_types': '["table"]',
            'rule_config': '{"units": ["元", "万元", "亩", "公斤", "吨"], "action": "extract_and_tag"}',
            'description': '识别表格中的单位',
            'examples': '[{"before": "收入 100", "after": "收入 100万元"}]'
        }
    ]

    for rule in default_rules:
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO dirty_data_rules
            (rule_name, rule_type, applicable_file_types, rule_config, description, examples)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rule['rule_name'],
                rule['rule_type'],
                rule['applicable_file_types'],
                rule['rule_config'],
                rule['description'],
                rule['examples']
            ))
        except Exception as e:
            print(f"⚠️ 插入规则 {rule['rule_name']} 失败: {e}")

    # 提交更改
    conn.commit()

    # 验证表是否创建成功
    print("\n✅ 验证表创建情况:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%normalization%' OR name LIKE '%completeness%' OR name LIKE '%dirty_data%'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   ✓ {table[0]}")

    # 统计
    cursor.execute("SELECT COUNT(*) FROM dirty_data_rules")
    rule_count = cursor.fetchone()[0]
    print(f"\n📊 默认规则数量: {rule_count}")

    conn.close()
    print("\n🎉 数据库迁移完成！")

if __name__ == "__main__":
    create_tables()
