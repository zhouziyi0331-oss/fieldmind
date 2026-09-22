"""
事实锚点生成器 - Facts Anchor Generator
只生成干燥的数字、列表、时间，绝对不含修饰性形容词

核心原则：
1. 只有数字、名称、时间戳
2. 禁止任何形容词、副词
3. 禁止任何推测性语言
4. 100%从fact_statements表读取数据
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
import logging

logger = logging.getLogger(__name__)


class FactsAnchorGenerator:
    """事实锚点生成器 - 纯数据，无修饰，100%基于fact_statements"""

    def __init__(self, db: Session):
        self.db = db

    def generate_facts(self, project_id: int) -> Dict[str, Any]:
        """
        生成事实锚点 - 只包含可验证的数字和列表

        数据来源：100%从fact_statements表读取

        返回格式：
        {
            "project_id": 1,
            "total_docs": 10,
            "total_statements": 120,
            "total_words": 12450,
            "category_rank": [
                {"name": "食", "count": 45},
                {"name": "衣", "count": 23}
            ],
            "top_speakers": [
                {"name": "王大爷", "count": 15},
                {"name": "李婶", "count": 12}
            ],
            "sentence_types": [...],
            "evidence_samples": [
                {
                    "text": "杀猪菜是传统美食",
                    "source": "document_40",
                    "speaker": "王大爷",
                    "timestamp": 15.2
                }
            ]
        }
        """
        logger.info(f"开始生成facts - 项目{project_id}，数据源：fact_statements表")

        facts = {
            "project_id": project_id,
            "generated_at": None,
            "data_source": "fact_statements"  # 标明数据来源
        }

        # 1. 基础统计 - 从fact_statements读取
        basic_stats = self.db.execute(text("""
            SELECT
                COUNT(*) as total_statements,
                SUM(word_count) as total_words,
                COUNT(DISTINCT document_id) as total_docs
            FROM fact_statements
            WHERE project_id = :project_id
        """), {"project_id": project_id}).first()

        facts['total_statements'] = basic_stats.total_statements or 0
        facts['total_words'] = int(basic_stats.total_words or 0)
        facts['total_docs'] = basic_stats.total_docs or 0

        logger.info(f"  基础统计: {facts['total_statements']}条陈述, {facts['total_words']}字, {facts['total_docs']}个文档")

        # 2. 主题排名（topic_tag字段）
        topic_stats = self.db.execute(text("""
            SELECT
                topic_tag as topic,
                COUNT(*) as count
            FROM fact_statements
            WHERE project_id = :project_id
              AND topic_tag IS NOT NULL
              AND topic_tag != ''
            GROUP BY topic_tag
            ORDER BY count DESC
        """), {"project_id": project_id}).fetchall()

        facts['category_rank'] = [
            {"name": row.topic, "count": row.count}
            for row in topic_stats
        ]

        # 计算百分比
        total_mentions = sum(item['count'] for item in facts['category_rank'])
        if total_mentions > 0:
            for item in facts['category_rank']:
                item['percentage'] = round(item['count'] / total_mentions * 100, 2)

        logger.info(f"  主题分布: {len(facts['category_rank'])}个主题")

        # 3. Top说话人（speaker字段）
        speaker_stats = self.db.execute(text("""
            SELECT
                speaker,
                COUNT(*) as count
            FROM fact_statements
            WHERE project_id = :project_id
              AND speaker IS NOT NULL
              AND speaker != ''
            GROUP BY speaker
            ORDER BY count DESC
            LIMIT 10
        """), {"project_id": project_id}).fetchall()

        facts['top_speakers'] = [
            {"name": row.speaker, "count": row.count}
            for row in speaker_stats
        ]

        logger.info(f"  说话人: {len(facts['top_speakers'])}人")

        # 4. 句子类型分布
        sentence_type_stats = self.db.execute(text("""
            SELECT
                sentence_type,
                COUNT(*) as count
            FROM fact_statements
            WHERE project_id = :project_id
              AND sentence_type IS NOT NULL
            GROUP BY sentence_type
            ORDER BY count DESC
        """), {"project_id": project_id}).fetchall()

        facts['sentence_types'] = [
            {"type": row.sentence_type, "count": row.count}
            for row in sentence_type_stats
        ]

        logger.info(f"  句子类型: {len(facts['sentence_types'])}种")

        # 5. 高频关键词（从keywords字段提取）
        # 由于keywords是逗号分隔的字符串，我们需要先拆分再统计
        keyword_rows = self.db.execute(text("""
            SELECT keywords
            FROM fact_statements
            WHERE project_id = :project_id
              AND keywords IS NOT NULL
              AND keywords != ''
        """), {"project_id": project_id}).fetchall()

        # 统计关键词频率
        keyword_freq = {}
        for row in keyword_rows:
            if row.keywords:
                for kw in row.keywords.split(','):
                    kw = kw.strip()
                    if kw:
                        keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

        # 取Top 20
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        facts['top_keywords'] = [
            {"keyword": kw, "count": count}
            for kw, count in top_keywords
        ]

        logger.info(f"  关键词: {len(facts['top_keywords'])}个高频词")

        # 6. 证据样本（带完整溯源信息）
        # 每个主题取1-2条典型样本
        evidence_samples = []

        for topic_item in facts['category_rank'][:5]:  # 只取前5个主题
            topic = topic_item['name']

            samples = self.db.execute(text("""
                SELECT
                    clean_text,
                    speaker,
                    source_file,
                    document_id,
                    start_sec,
                    topic_tag,
                    keywords
                FROM fact_statements
                WHERE project_id = :project_id
                  AND topic_tag = :topic
                ORDER BY word_count DESC
                LIMIT 2
            """), {"project_id": project_id, "topic": topic}).fetchall()

            for sample in samples:
                evidence_samples.append({
                    "text": sample.clean_text[:100] if sample.clean_text else "",
                    "speaker": sample.speaker,
                    "source_file": sample.source_file,
                    "document_id": sample.document_id,
                    "timestamp": sample.start_sec,
                    "topic": sample.topic_tag,
                    "keywords": sample.keywords.split(',')[:5] if sample.keywords else []
                })

        facts['evidence_samples'] = evidence_samples
        logger.info(f"  证据样本: {len(evidence_samples)}条")

        # 7. 时间戳
        import datetime
        facts['generated_at'] = datetime.datetime.now().isoformat()

        logger.info(f"✅ facts生成完成")

        return facts

    def validate_facts(self, facts: Dict) -> bool:
        """
        验证事实锚点的有效性
        确保所有必需字段都存在且有数据
        """
        # 必需字段
        required_keys = [
            'project_id', 'total_statements', 'total_words',
            'category_rank', 'top_speakers'
        ]

        for key in required_keys:
            if key not in facts:
                logger.error(f"验证失败: 缺少字段 {key}")
                return False

        # 数据量检查
        if facts['total_statements'] == 0:
            logger.warning("验证失败: total_statements为0")
            return False

        logger.info(f"✅ facts验证通过")
        return True


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

    from app.core.database import SessionLocal

    db = SessionLocal()
    generator = FactsAnchorGenerator(db)

    print("=" * 70)
    print("📊 事实锚点生成测试（数据源：fact_statements表）")
    print("=" * 70)

    facts = generator.generate_facts(project_id=1)

    import json
    print(json.dumps(facts, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("验证结果:", "✅ 通过" if generator.validate_facts(facts) else "❌ 失败")
    print("=" * 70)

    db.close()
