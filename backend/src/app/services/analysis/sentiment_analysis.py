"""
情感分析服务
分析文档中的情感倾向、情绪强度、情感变化趋势
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from .base_analysis import BaseAnalysisService


class SentimentAnalysisService(BaseAnalysisService):
    """情感分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='sentiment')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        执行情感分析

        Returns:
            {
                'overall_sentiment': {'positive': 0.6, 'neutral': 0.3, 'negative': 0.1},
                'sentiment_by_document': [...],
                'emotional_keywords': [...],
                'sentiment_trend': [...],
                'confidence_score': 0.85
            }
        """
        # 1. 获取项目所有chunks
        chunks = await self._get_project_chunks(project_id, db_session)

        if not chunks:
            return {
                'overall_sentiment': {'positive': 0, 'neutral': 0, 'negative': 0},
                'sentiment_by_document': [],
                'emotional_keywords': [],
                'sentiment_trend': [],
                'confidence_score': 0.0,
                'message': 'No chunks found for analysis'
            }

        # 2. 分析每个chunk的情感
        chunk_sentiments = []
        for chunk in chunks:
            sentiment = await self._analyze_chunk_sentiment(chunk)
            chunk_sentiments.append(sentiment)

        # 3. 聚合整体情感分布
        overall = self._aggregate_sentiments(chunk_sentiments)

        # 4. 提取情感关键词
        emotional_keywords = await self._extract_emotional_keywords(chunks, db_session)

        # 5. 分析情感趋势（按时间排序）
        sentiment_trend = self._calculate_sentiment_trend(chunk_sentiments)

        # 6. 按文档分组
        sentiment_by_document = self._group_by_document(chunk_sentiments)

        return {
            'overall_sentiment': overall,
            'sentiment_by_document': sentiment_by_document,
            'emotional_keywords': emotional_keywords,
            'sentiment_trend': sentiment_trend,
            'confidence_score': self._calculate_confidence(chunk_sentiments),
            'total_chunks_analyzed': len(chunks)
        }

    async def _get_project_chunks(
        self,
        project_id: str,
        db_session: Session
    ) -> List[Dict[str, Any]]:
        """获取项目的所有chunks"""
        query = text("""
            SELECT c.id, c.text AS content, c.document_id, c.chunk_index,
                   c.metadata, d.filename AS document_title,
                   d.created_at AS document_created_at
            FROM document_chunks c
            JOIN project_documents d ON c.document_id = d.id
            WHERE c.project_id = :project_id
            ORDER BY d.created_at, c.chunk_index
        """)

        result = db_session.execute(query, {'project_id': project_id})
        return [dict(row._mapping) for row in result.fetchall()]

    async def _analyze_chunk_sentiment(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个chunk的情感
        这里使用简化的规则方法，实际可接入LLM或专业NLP模型
        """
        content = chunk['content']

        # 简化的情感词典（实际应使用完整词典或模型）
        positive_words = ['好', '优秀', '成功', '增长', '提升', '改善', '创新', '机会', '希望', '积极']
        negative_words = ['差', '失败', '下降', '问题', '风险', '困难', '挑战', '威胁', '担忧', '消极']
        neutral_words = ['平稳', '正常', '维持', '一般', '基本', '常规']

        # 统计词频
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        neutral_count = sum(1 for word in neutral_words if word in content)

        total = positive_count + negative_count + neutral_count
        if total == 0:
            # 无明显情感词，判定为中性
            sentiment_score = {'positive': 0.0, 'neutral': 1.0, 'negative': 0.0}
        else:
            sentiment_score = {
                'positive': positive_count / total,
                'neutral': neutral_count / total,
                'negative': negative_count / total
            }

        # 判断主导情感
        dominant = max(sentiment_score, key=sentiment_score.get)

        return {
            'chunk_id': chunk['id'],
            'document_id': chunk['document_id'],
            'document_title': chunk.get('document_title', ''),
            'chunk_index': chunk['chunk_index'],
            'sentiment_score': sentiment_score,
            'dominant_sentiment': dominant,
            'timestamp': chunk.get('document_created_at')
        }

    def _aggregate_sentiments(self, chunk_sentiments: List[Dict[str, Any]]) -> Dict[str, float]:
        """聚合所有chunk的情感分数"""
        if not chunk_sentiments:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}

        total_positive = sum(cs['sentiment_score']['positive'] for cs in chunk_sentiments)
        total_neutral = sum(cs['sentiment_score']['neutral'] for cs in chunk_sentiments)
        total_negative = sum(cs['sentiment_score']['negative'] for cs in chunk_sentiments)

        count = len(chunk_sentiments)
        return {
            'positive': round(total_positive / count, 3),
            'neutral': round(total_neutral / count, 3),
            'negative': round(total_negative / count, 3)
        }

    async def _extract_emotional_keywords(
        self,
        chunks: List[Dict[str, Any]],
        db_session: Session
    ) -> List[Dict[str, Any]]:
        """提取情感关键词（可从keywords表获取）"""
        if not chunks:
            return []

        positive_words = ['好', '优秀', '成功', '增长', '提升', '改善', '创新', '机会', '希望', '积极']
        negative_words = ['差', '失败', '下降', '问题', '风险', '困难', '挑战', '威胁', '担忧', '消极']
        neutral_words = ['平稳', '正常', '维持', '一般', '基本', '常规']
        counts = []
        for word in positive_words:
            frequency = sum((chunk.get('content') or '').count(word) for chunk in chunks)
            if frequency:
                counts.append({'keyword': word, 'sentiment': 'positive', 'frequency': frequency})
        for word in negative_words:
            frequency = sum((chunk.get('content') or '').count(word) for chunk in chunks)
            if frequency:
                counts.append({'keyword': word, 'sentiment': 'negative', 'frequency': frequency})
        for word in neutral_words:
            frequency = sum((chunk.get('content') or '').count(word) for chunk in chunks)
            if frequency:
                counts.append({'keyword': word, 'sentiment': 'neutral', 'frequency': frequency})
        return sorted(counts, key=lambda item: item['frequency'], reverse=True)[:20]

    def _calculate_sentiment_trend(self, chunk_sentiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算情感趋势（按时间）"""
        if not chunk_sentiments:
            return []
        buckets = min(3, len(chunk_sentiments))
        result = []
        for index in range(buckets):
            start = index * len(chunk_sentiments) // buckets
            end = (index + 1) * len(chunk_sentiments) // buckets
            group = chunk_sentiments[start:end]
            score = self._aggregate_sentiments(group)
            result.append({"period": ["early", "middle", "recent"][index], **score})
        return result

    def _group_by_document(self, chunk_sentiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按文档分组情感分析结果"""
        doc_groups = {}
        for cs in chunk_sentiments:
            doc_id = cs['document_id']
            if doc_id not in doc_groups:
                doc_groups[doc_id] = {
                    'document_id': doc_id,
                    'document_title': cs['document_title'],
                    'chunks': []
                }
            doc_groups[doc_id]['chunks'].append(cs)

        # 计算每个文档的平均情感
        result = []
        for doc_id, group in doc_groups.items():
            sentiments = [c['sentiment_score'] for c in group['chunks']]
            avg_sentiment = self._aggregate_sentiments(group['chunks'])
            result.append({
                'document_id': doc_id,
                'document_title': group['document_title'],
                'chunk_count': len(group['chunks']),
                'average_sentiment': avg_sentiment,
                'dominant_sentiment': max(avg_sentiment, key=avg_sentiment.get)
            })

        return result

    def _calculate_confidence(self, chunk_sentiments: List[Dict[str, Any]]) -> float:
        """计算整体置信度"""
        if not chunk_sentiments:
            return 0.0

        # 简化：基于分析的chunk数量和情感分布的一致性
        count = len(chunk_sentiments)
        if count < 5:
            return 0.5  # 样本太少，置信度低

        # 检查情感分布的方差（方差小说明一致性高）
        sentiments = [cs['sentiment_score'] for cs in chunk_sentiments]
        # 这里简化处理，实际应计算真实方差
        return min(0.85, 0.5 + count * 0.01)
