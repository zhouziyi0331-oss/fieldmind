"""
扩展 files 和 chunks 表，添加全量元数据和指标字段
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from app.core.database import engine


def extend_files_table():
    """扩展 files 表，添加元数据字段"""

    print("\n" + "="*60)
    print("扩展 files 表")
    print("="*60)

    fields_to_add = [
        # 文件级元数据
        ("file_hash", "VARCHAR(64)", "文件MD5哈希（去重用）"),
        ("total_words", "INT", "总字数"),
        ("total_sentences", "INT", "总句数"),
        ("total_paragraphs", "INT", "总段落数"),
        ("speaker_count", "INT", "说话人数量（音频）"),
        ("language", "VARCHAR(20)", "语言检测结果"),

        # 采集环境
        ("collection_device", "VARCHAR(100)", "采集设备"),
        ("collection_location", "VARCHAR(200)", "采集地点"),
        ("collector_name", "VARCHAR(100)", "采集人"),
        ("batch_id", "VARCHAR(50)", "采集批次号"),

        # 处理追踪
        ("processing_started", "DATETIME", "处理开始时间"),
        ("processing_ended", "DATETIME", "处理结束时间"),
        ("processing_duration", "DECIMAL(10,2)", "处理耗时（秒）"),
    ]

    with engine.connect() as conn:
        for field_name, field_type, comment in fields_to_add:
            try:
                sql = f"""
                    ALTER TABLE documents
                    ADD COLUMN {field_name} {field_type} COMMENT '{comment}'
                """
                conn.execute(text(sql))
                print(f"✓ 添加字段: {field_name}")
            except Exception as e:
                if "Duplicate column" in str(e):
                    print(f"⚠ 字段 {field_name} 已存在")
                else:
                    print(f"❌ 添加 {field_name} 失败: {e}")

        conn.commit()

    print("\n✅ files 表扩展完成")


def extend_chunks_table():
    """扩展 chunks 表，添加全量指标字段"""

    print("\n" + "="*60)
    print("扩展 chunks 表")
    print("="*60)

    fields_to_add = [
        # 结构性指标
        ("word_count", "INT", "字数（M001）"),
        ("sentence_count", "INT", "句数（M002）"),
        ("avg_sentence_length", "DECIMAL(6,2)", "平均句长（M003）"),

        # 情绪性指标
        ("emotion_polarity", "DECIMAL(4,3)", "情感极性值 [-1,1]（M011）"),
        ("emotion_strength", "DECIMAL(4,3)", "情绪强度 [0,1]（M012）"),
        ("subjectivity", "DECIMAL(4,3)", "主观性 [0,1]（M013）"),

        # 语言风格指标
        ("emotion_word_density", "DECIMAL(4,3)", "情绪词密度（M021）"),
        ("exclamation_count", "INT", "感叹号数量（M022）"),
        ("question_ratio", "DECIMAL(4,3)", "疑问句比例（M023）"),
        ("tone_strength", "DECIMAL(4,3)", "语气强度（M024）"),
        ("modal_verb_count", "INT", "情态动词数量（M025）"),

        # 内容类指标
        ("keyword_count", "INT", "关键词数量（M031）"),
        ("keywords_json", "TEXT", "关键词列表（JSON）"),
        ("entity_count", "INT", "实体数量（M032）"),
        ("topic_consistency", "DECIMAL(4,3)", "主题一致性（M033）"),
        ("topic_label", "VARCHAR(100)", "主题标签"),

        # 质量类指标
        ("quality_score", "DECIMAL(4,3)", "文本质量评分（M041）"),
        ("duplicate_ratio", "DECIMAL(4,3)", "重复率（M042）"),
        ("grammar_error_count", "INT", "语法错误数（M043）"),

        # 时间类指标（音频/视频）
        ("duration_seconds", "DECIMAL(8,2)", "时间跨度（M051）"),
        ("speech_rate", "DECIMAL(6,2)", "语速 字/秒（M052）"),
    ]

    with engine.connect() as conn:
        for field_name, field_type, comment in fields_to_add:
            try:
                sql = f"""
                    ALTER TABLE document_chunks
                    ADD COLUMN {field_name} {field_type} COMMENT '{comment}'
                """
                conn.execute(text(sql))
                print(f"✓ 添加字段: {field_name}")
            except Exception as e:
                if "Duplicate column" in str(e):
                    print(f"⚠ 字段 {field_name} 已存在")
                else:
                    print(f"❌ 添加 {field_name} 失败: {e}")

        conn.commit()

    print("\n✅ chunks 表扩展完成")


def create_indexes():
    """创建必要的索引"""

    print("\n" + "="*60)
    print("创建索引")
    print("="*60)

    indexes = [
        ("idx_files_hash", "documents", "file_hash"),
        ("idx_files_batch", "documents", "batch_id"),
        ("idx_chunks_emotion", "document_chunks", "emotion_polarity"),
        ("idx_chunks_quality", "document_chunks", "quality_score"),
    ]

    with engine.connect() as conn:
        for idx_name, table_name, column_name in indexes:
            try:
                sql = f"CREATE INDEX {idx_name} ON {table_name}({column_name})"
                conn.execute(text(sql))
                print(f"✓ 创建索引: {idx_name}")
            except Exception as e:
                if "Duplicate key" in str(e) or "already exists" in str(e):
                    print(f"⚠ 索引 {idx_name} 已存在")
                else:
                    print(f"❌ 创建索引 {idx_name} 失败: {e}")

        conn.commit()

    print("\n✅ 索引创建完成")


def main():
    """执行所有扩展"""

    print("="*60)
    print("数据治理：扩展数据表")
    print("="*60)

    try:
        # 1. 扩展 files 表
        extend_files_table()

        # 2. 扩展 chunks 表
        extend_chunks_table()

        # 3. 创建索引
        create_indexes()

        print("\n" + "="*60)
        print("✅ 数据表扩展完成")
        print("="*60)
        print("\n新增字段统计:")
        print("  - files 表: 13 个元数据字段")
        print("  - chunks 表: 21 个指标字段")
        print("  - 索引: 4 个")

    except Exception as e:
        print(f"\n❌ 扩展失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
