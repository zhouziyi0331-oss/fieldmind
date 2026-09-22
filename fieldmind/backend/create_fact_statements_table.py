"""
创建结构化事实表 - Fact Statements Table
让数据真正可统计、可分析

核心原则：
1. 每个语义单元（句子/段落）一条记录
2. 包含所有可统计的维度
3. 支持SQL聚合查询
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.core.database import engine, Base
from sqlalchemy import Column, Integer, String, Text, Float, ARRAY, DateTime, Index
from datetime import datetime

print("=" * 70)
print("🗄️  创建结构化事实表")
print("=" * 70)

# 定义fact_statements表
from sqlalchemy.ext.declarative import declarative_base

class FactStatement(Base):
    """
    结构化事实表 - 每一条陈述的结构化记录

    用途：
    - SQL聚合统计（COUNT/GROUP BY）
    - 精确查询（WHERE topic_tag='食'）
    - 数据分析（不是向量检索）
    """
    __tablename__ = 'fact_statements'

    id = Column(Integer, primary_key=True, index=True)

    # 来源信息
    source_file = Column(String(255), nullable=False, index=True)  # 文件名
    document_id = Column(Integer, nullable=False, index=True)      # 文档ID
    project_id = Column(Integer, nullable=False, index=True)       # 项目ID

    # 说话人/作者
    speaker = Column(String(100), nullable=True, index=True)       # 说话人

    # 时间信息
    start_sec = Column(Float, nullable=True)                       # 音频开始时间（秒）
    end_sec = Column(Float, nullable=True)                         # 音频结束时间（秒）

    # 文本内容
    original_text = Column(Text, nullable=False)                   # 原始文本
    clean_text = Column(Text, nullable=False)                      # 清洗后文本

    # 结构化标签（核心：让数据可统计）
    topic_tag = Column(String(50), nullable=True, index=True)      # 主题标签：衣/食/住/行/经济/社会

    # 实体（使用逗号分隔字符串，SQLite不支持ARRAY）
    entity_names = Column(Text, nullable=True)                     # 人名/地名，逗号分隔
    keywords = Column(Text, nullable=True)                         # 关键词，逗号分隔

    # 句子类型
    sentence_type = Column(String(20), nullable=True)              # 陈述句/疑问句/感叹句

    # 元数据
    chunk_index = Column(Integer, nullable=True)                   # 在文档中的位置
    word_count = Column(Integer, default=0)                        # 字数

    # 置信度评分（反幻觉锁3）
    confidence_score = Column(Float, default=0.8)                  # 置信度评分 (0-1)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<FactStatement(id={self.id}, topic={self.topic_tag}, speaker={self.speaker})>"


# 创建索引（加速查询）
Index('idx_fact_project_topic', FactStatement.project_id, FactStatement.topic_tag)
Index('idx_fact_speaker', FactStatement.speaker)
Index('idx_fact_document', FactStatement.document_id)

try:
    # 创建表
    print("\n📝 创建 fact_statements 表...")
    FactStatement.__table__.create(bind=engine, checkfirst=True)
    print("✅ 表创建成功")

    # 验证
    from sqlalchemy import inspect
    inspector = inspect(engine)

    if 'fact_statements' in inspector.get_table_names():
        print("\n✅ fact_statements 表已存在")

        # 显示表结构
        columns = inspector.get_columns('fact_statements')
        print("\n📋 表结构:")
        for col in columns:
            print(f"   {col['name']:20s} {str(col['type']):20s}")

        # 显示索引
        indexes = inspector.get_indexes('fact_statements')
        if indexes:
            print("\n🔍 索引:")
            for idx in indexes:
                print(f"   {idx['name']}: {idx['column_names']}")
    else:
        print("❌ 表创建失败")

except Exception as e:
    print(f"❌ 创建表失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ 结构化事实表创建完成")
print("=" * 70)

print("""
📊 使用示例:

# 统计各主题的频次
SELECT topic_tag, COUNT(*)
FROM fact_statements
WHERE project_id = 1
GROUP BY topic_tag
ORDER BY COUNT(*) DESC;

# 统计某人的发言次数
SELECT COUNT(*)
FROM fact_statements
WHERE speaker = '王大爷';

# 查询某主题的所有陈述
SELECT clean_text, speaker, start_sec
FROM fact_statements
WHERE topic_tag = '食'
ORDER BY start_sec;

# 时间线分析
SELECT
  CAST(start_sec/60 AS INT) as minute,
  COUNT(*) as statements_count
FROM fact_statements
WHERE document_id = 40
GROUP BY minute
ORDER BY minute;
""")
