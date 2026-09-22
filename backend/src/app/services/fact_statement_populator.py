"""
Fact Statements填充器
在现有Pipeline中同步填充结构化事实表

集成点：document_processing_pipeline_complete.py
在向量化完成后，同步填充fact_statements
"""

import json

from sqlalchemy.orm import Session
from typing import List, Dict, Any
import jieba.posseg as pseg
import logging

logger = logging.getLogger(__name__)


class FactStatementPopulator:
    """事实陈述填充器 - 将chunks转换为结构化记录"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def populate(self, document_id: int, project_id: int, chunks: List[Dict], metadata: Dict = None) -> int:
        """
        将chunks填充到fact_statements表

        Args:
            document_id: 文档ID
            project_id: 项目ID
            chunks: 切分后的chunks列表
            metadata: 额外元数据

        Returns:
            成功插入的记录数
        """
        from app.models.project import ProjectDocument
        from sqlalchemy import text

        # 获取文档信息
        doc = self.db.query(ProjectDocument).get(document_id)
        if not doc:
            logger.error(f"文档{document_id}不存在")
            return 0

        source_file = doc.filename
        inserted_count = 0

        self.db.execute(
            text("DELETE FROM fact_statements WHERE document_id = :document_id"),
            {"document_id": document_id},
        )

        for i, chunk in enumerate(chunks):
            try:
                chunk_text = chunk.get('text', '')
                if not chunk_text:
                    continue

                # 提取结构化信息
                fact_data = self._extract_structured_data(
                    text=chunk_text,
                    chunk_index=i,
                    chunk_metadata=chunk.get('metadata', {})
                )

                # 插入到fact_statements表
                self.db.execute(text("""
                    INSERT INTO fact_statements (
                        fid, source_fid, derived_from_chain,
                        project_id, document_id, statement_text,
                        statement_type, start_sec, end_sec,
                        entity_names, event_summary, keywords,
                        confidence_score, created_at
                    ) VALUES (
                        :fid, :source_fid, :derived_from_chain,
                        :project_id, :document_id, :statement_text,
                        :statement_type, :start_sec, :end_sec,
                        :entity_names, :event_summary, :keywords,
                        :confidence_score, datetime('now')
                    )
                """), {
                    'fid': f"fact_{document_id}_{i}",
                    'source_fid': f"document_{document_id}",
                    'derived_from_chain': json.dumps(
                        ["project_document", document_id, "chunk", i],
                        ensure_ascii=False,
                    ),
                    'document_id': document_id,
                    'project_id': project_id,
                    'statement_text': fact_data['clean_text'],
                    'statement_type': fact_data['sentence_type'],
                    'start_sec': fact_data['start_sec'],
                    'end_sec': fact_data['end_sec'],
                    'entity_names': json.dumps(
                        fact_data['entity_names'].split(",")
                        if fact_data['entity_names'] else [],
                        ensure_ascii=False,
                    ),
                    'event_summary': fact_data['topic_tag'],
                    'keywords': json.dumps(
                        fact_data['keywords'].split(",")
                        if fact_data['keywords'] else [],
                        ensure_ascii=False,
                    ),
                    'confidence_score': fact_data['confidence_score']
                })

                inserted_count += 1

            except Exception as e:
                logger.error(f"插入fact_statement失败 (chunk {i}): {e}")
                continue

        # 提交
        try:
            self.db.commit()
            logger.info(f"✅ 成功插入{inserted_count}条fact_statements记录")
        except Exception as e:
            logger.error(f"❌ 提交fact_statements失败: {e}")
            self.db.rollback()
            return 0

        return inserted_count

    def _extract_structured_data(self, text: str, chunk_index: int, chunk_metadata: Dict) -> Dict:
        """提取结构化数据"""

        # 1. 清洗文本
        clean_text = self._clean_text(text)

        # 2. 主题分类
        topic_tag = self._classify_topic(clean_text)

        # 3. 提取实体
        entities = self._extract_entities(clean_text)

        # 4. 提取关键词
        keywords = self._extract_keywords(clean_text)

        # 5. 句子类型
        sentence_type = self._detect_sentence_type(clean_text)

        # 6. 说话人（从metadata中提取，如果有）
        speaker = chunk_metadata.get('speaker')

        # 7. 时间信息（音频）
        start_sec = chunk_metadata.get('start_sec')
        end_sec = chunk_metadata.get('end_sec')

        # 8. 计算置信度评分（反幻觉锁3）
        confidence_score = self._calculate_confidence(clean_text, entities, keywords, chunk_metadata)

        return {
            'clean_text': clean_text,
            'topic_tag': topic_tag,
            'entity_names': ','.join(entities) if entities else None,
            'keywords': ','.join(keywords[:10]) if keywords else None,  # 只保留前10个
            'sentence_type': sentence_type,
            'speaker': speaker,
            'start_sec': start_sec,
            'end_sec': end_sec,
            'confidence_score': confidence_score
        }

    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        # 简单清洗，去除多余空格
        import re
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _classify_topic(self, text: str) -> str:
        """主题分类"""
        # 使用简单的关键词匹配
        topic_keywords = {
            '衣': ['衣服', '服装', '纺织', '刺绣', '布料', '穿', '织'],
            '食': ['吃', '食物', '饮食', '做饭', '烹饪', '菜', '肉', '粮食', '杀猪', '酒', '宴'],
            '住': ['房子', '建房', '住宅', '院子', '装修', '祠堂', '村舍'],
            '行': ['路', '交通', '出行', '车', '走', '桥', '道路'],
            '社交': ['婚礼', '丧事', '祭祀', '节日', '聚会', '拜访', '亲戚'],
            '经济': ['钱', '收入', '支出', '买', '卖', '生意', '工资'],
            '信仰': ['神', '庙', '祭祀', '迷信', '风水', '祖先'],
        }

        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return topic

        return '其他'

    def _extract_entities(self, text: str) -> List[str]:
        """提取人名/地名"""
        entities = []
        words = pseg.cut(text)

        for word in words:
            if word.flag in ['nr', 'ns']:  # 人名、地名
                entities.append(word.word)

        return list(set(entities))  # 去重

    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_k)
        return keywords

    def _detect_sentence_type(self, text: str) -> str:
        """检测句子类型"""
        if '？' in text or '?' in text:
            return '疑问句'
        elif '！' in text or '!' in text:
            return '感叹句'
        else:
            return '陈述句'

    def _calculate_confidence(self, text: str, entities: List[str], keywords: List[str], metadata: Dict) -> float:
        """
        计算置信度评分（反幻觉锁3）

        评分维度：
        1. 文本完整性（0-0.3分）：长度适中、标点完整
        2. 信息密度（0-0.3分）：实体和关键词丰富度
        3. 来源可靠性（0-0.2分）：有说话人、时间戳等
        4. 语言质量（0-0.2分）：无乱码、无重复

        Returns:
            置信度评分 (0-1)，1为最高
        """
        score = 0.0

        # 1. 文本完整性评分（0-0.3）
        text_length = len(text)
        if 20 <= text_length <= 500:  # 合理长度范围
            score += 0.2
        elif text_length > 10:
            score += 0.1

        # 有完整标点
        if any(p in text for p in ['。', '！', '？', '.', '!', '?']):
            score += 0.1

        # 2. 信息密度评分（0-0.3）
        if entities and len(entities) > 0:
            score += min(0.15, len(entities) * 0.05)  # 每个实体+0.05，最多0.15

        if keywords and len(keywords) > 0:
            score += min(0.15, len(keywords) * 0.03)  # 每个关键词+0.03，最多0.15

        # 3. 来源可靠性评分（0-0.2）
        if metadata.get('speaker'):
            score += 0.1  # 有说话人

        if metadata.get('start_sec') is not None:
            score += 0.1  # 有时间戳

        # 4. 语言质量评分（0-0.2）
        # 检查是否有乱码（连续特殊字符）
        import re
        if not re.search(r'[^一-龥a-zA-Z0-9]{5,}', text):
            score += 0.1

        # 检查是否有过度重复
        words = list(text)
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.5:  # 重复率不高
                score += 0.1

        # 确保分数在 0-1 范围内
        return min(1.0, max(0.0, score))


if __name__ == "__main__":
    # 测试
    from app.core.database import SessionLocal

    print("=" * 70)
    print("🧪 Fact Statements填充器测试")
    print("=" * 70)

    db = SessionLocal()
    populator = FactStatementPopulator(db)

    # 模拟chunks
    test_chunks = [
        {
            'text': '王大爷说，杀猪菜是我们村的传统美食。',
            'metadata': {
                'start_sec': 10.5,
                'end_sec': 15.2,
                'speaker': '王大爷'
            }
        },
        {
            'text': '李婶补充说，现在年轻人都不会做了。',
            'metadata': {
                'start_sec': 15.5,
                'end_sec': 20.1,
                'speaker': '李婶'
            }
        }
    ]

    # 填充（使用测试文档ID=1）
    count = populator.populate(
        document_id=1,
        project_id=1,
        chunks=test_chunks
    )

    print(f"\n✅ 成功插入 {count} 条记录")

    # 验证
    from sqlalchemy import text
    result = db.execute(text("SELECT COUNT(*) FROM fact_statements")).scalar()
    print(f"fact_statements表当前记录数: {result}")

    # 查询示例
    print("\n📊 查询示例:")
    results = db.execute(text("""
        SELECT topic_tag, COUNT(*) as count
        FROM fact_statements
        WHERE project_id = 1
        GROUP BY topic_tag
    """)).fetchall()

    for row in results:
        print(f"  {row[0]}: {row[1]}次")

    db.close()

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
