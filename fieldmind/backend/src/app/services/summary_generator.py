"""
文档缩影生成服务
File Summary Generator Service

功能：
1. 从现有数据（document_chunks、extra_data）生成文档缩影
2. 自动提取关键词、实体、主题、事件
3. 生成一句话摘要和完整摘要
4. 计算关联文档（基于关键词重叠）
5. 保存到 file_summaries 表

作者: FieldMind Team
创建时间: 2024-09-14
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import logging

from app.models.project import ProjectDocument
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class FileSummaryGenerator:
    """文档缩影生成器"""

    def __init__(self, db: Session):
        self.db = db

    def generate_summary(self, document_id: int) -> Dict[str, Any]:
        """
        生成文档缩影

        流程：
        1. 从 project_documents 获取基本信息
        2. 从 document_chunks 聚合量化指标、维度标签、时空上下文
        3. 从 extra_data 提取关键词（jieba分词结果）
        4. 从 topic_clusters 提取主题（如果有）
        5. 从 entities 表提取实体（如果有）
        6. 从 events 表提取事件（如果有）
        7. 生成一句话摘要和完整摘要
        8. 计算关联文档（基于关键词重叠）
        9. 构造缩影数据结构

        Args:
            document_id: 文档ID

        Returns:
            缩影数据字典

        Raises:
            ValueError: 文档不存在
        """

        logger.info(f"🔄 开始生成文档 {document_id} 的缩影")

        # 1. 获取文档基本信息
        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            raise ValueError(f"Document {document_id} not found")

        logger.info(f"📄 文档信息: {doc.original_filename} ({doc.file_type})")

        # 2. 从 document_chunks 聚合数据
        chunks_data = self._aggregate_chunks_data(document_id)
        logger.info(f"📦 Chunks数据: {chunks_data['chunk_count']}块, {chunks_data['word_count']}字")

        # 3. 提取关键词（从 extra_data）
        top_keywords = self._extract_keywords(doc)
        logger.info(f"🏷️ 提取了 {len(top_keywords)} 个关键词")

        # 4. 提取主题
        top_topics = self._extract_topics(document_id)
        logger.info(f"📊 提取了 {len(top_topics)} 个主题")

        # 5. 提取实体
        top_entities = self._extract_entities(document_id)
        logger.info(f"👤 提取了 {len(top_entities)} 个实体")

        # 6. 提取事件
        top_events = self._extract_events(document_id)
        logger.info(f"⏰ 提取了 {len(top_events)} 个事件")

        # 7. 生成一句话摘要
        one_line_summary = self._generate_one_line_summary(
            doc, top_keywords, top_topics, top_entities, chunks_data
        )
        logger.info(f"📝 一句话摘要: {one_line_summary}")

        # 8. 生成完整摘要
        full_summary = self._generate_full_summary(
            doc, chunks_data, top_keywords, top_topics, top_entities, top_events
        )
        logger.info(f"📋 完整摘要生成完成 ({len(full_summary)}字)")

        # 9. 计算关联文档
        related_docs = self._find_related_documents(document_id, doc.project_id, top_keywords)
        logger.info(f"🔗 找到 {len(related_docs)} 个关联文档")

        # 10. 构造缩影数据
        summary_data = {
            'document_id': document_id,
            'project_id': doc.project_id,
            'one_line_summary': one_line_summary,
            'full_summary': full_summary,
            'top_keywords': json.dumps(top_keywords, ensure_ascii=False),
            'top_entities': json.dumps(top_entities, ensure_ascii=False),
            'top_topics': json.dumps(top_topics, ensure_ascii=False),
            'top_events': json.dumps(top_events, ensure_ascii=False),
            'word_count': chunks_data['word_count'],
            'chunk_count': chunks_data['chunk_count'],
            'avg_chunk_length': chunks_data['avg_chunk_length'],
            'primary_dimension': chunks_data['primary_dimension'],
            'secondary_dimensions': json.dumps(chunks_data['secondary_dimensions'], ensure_ascii=False),
            'time_start': chunks_data['time_start'],
            'time_end': chunks_data['time_end'],
            'spatial_context': chunks_data['spatial_context'],
            'related_documents': json.dumps(related_docs, ensure_ascii=False),
            'status': 'done',
            'generated_at': datetime.utcnow().isoformat()
        }

        logger.info(f"✅ 文档 {document_id} 缩影生成完成")

        return summary_data

    def _aggregate_chunks_data(self, document_id: int) -> Dict[str, Any]:
        """
        从 document_chunks 聚合数据

        聚合内容：
        - 量化指标：总字数、分块数、平均长度
        - 维度标签：主要维度、次要维度
        - 时空上下文：时间范围、空间上下文
        - 情感分析：情绪极性、主观性（新增）
        """

        # 查询所有 chunks
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()

        if not chunks:
            logger.warning(f"文档 {document_id} 没有 chunks，返回空数据")
            return {
                'word_count': 0,
                'chunk_count': 0,
                'avg_chunk_length': 0,
                'primary_dimension': '未分类',
                'secondary_dimensions': [],
                'time_start': None,
                'time_end': None,
                'spatial_context': None,
                'emotion_polarity': 0.0,
                'subjectivity': 0.5
            }

        # 计算量化指标
        word_count = sum(chunk.text_length or 0 for chunk in chunks)
        chunk_count = len(chunks)
        avg_chunk_length = word_count / chunk_count if chunk_count > 0 else 0

        # 聚合维度标签（统计出现次数）
        dimension_freq = {}
        for chunk in chunks:
            if chunk.primary_domain:
                dimension_freq[chunk.primary_domain] = dimension_freq.get(chunk.primary_domain, 0) + 1

        # 主要维度：出现次数最多的
        primary_dimension = max(dimension_freq, key=dimension_freq.get) if dimension_freq else '未分类'

        # 次要维度：其他出现的维度（取前3个）
        secondary_dimensions = [dim for dim in dimension_freq if dim != primary_dimension][:3]

        # 提取时间范围（取第一个和最后一个）
        time_contexts = [chunk.temporal_context for chunk in chunks if chunk.temporal_context]
        time_start = time_contexts[0] if time_contexts else None
        time_end = time_contexts[-1] if len(time_contexts) > 1 else time_start

        # 提取空间上下文（取第一个）
        spatial_contexts = [chunk.spatial_context for chunk in chunks if chunk.spatial_context]
        spatial_context = spatial_contexts[0] if spatial_contexts else None

        # 情感分析（新增）
        emotion_polarity, subjectivity = self._analyze_sentiment(chunks)

        return {
            'word_count': word_count,
            'chunk_count': chunk_count,
            'avg_chunk_length': round(avg_chunk_length, 2),
            'primary_dimension': primary_dimension,
            'secondary_dimensions': secondary_dimensions,
            'time_start': time_start,
            'time_end': time_end,
            'spatial_context': spatial_context,
            'emotion_polarity': emotion_polarity,
            'subjectivity': subjectivity
        }

    def _analyze_sentiment(self, chunks: List[DocumentChunk]) -> tuple[float, float]:
        """
        情感分析（新增）

        分析文档的情绪极性和主观性

        返回：
        - emotion_polarity: 情绪极性（-1到1，负面到正面）
        - subjectivity: 主观性（0到1，客观到主观）
        """

        try:
            # 尝试使用 SnowNLP 进行中文情感分析
            from snownlp import SnowNLP

            sentiments = []
            for chunk in chunks[:10]:  # 只分析前10个 chunk，避免性能问题
                if chunk.text and len(chunk.text) > 10:
                    try:
                        s = SnowNLP(chunk.text)
                        # SnowNLP 返回 0-1 的正面概率，转换为 -1 到 1
                        polarity = (s.sentiments - 0.5) * 2
                        sentiments.append(polarity)
                    except Exception as e:
                        logger.debug(f"单个 chunk 情感分析失败: {e}")
                        continue

            if sentiments:
                # 平均情绪极性
                emotion_polarity = sum(sentiments) / len(sentiments)
                emotion_polarity = round(emotion_polarity, 2)

                # 主观性：基于情绪极性的绝对值
                # 极性越强（接近 -1 或 1），主观性越高
                subjectivity = round(abs(emotion_polarity), 2)

                logger.info(f"情感分析完成: polarity={emotion_polarity}, subjectivity={subjectivity}")

                return emotion_polarity, subjectivity

        except ImportError:
            logger.debug("未安装 snownlp 库，跳过情感分析")
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")

        # 默认值：中性情绪，中等主观性
        return 0.0, 0.5

    def _extract_keywords(self, doc: ProjectDocument) -> List[Dict]:
        """
        从 extra_data 提取关键词（jieba分词结果）

        返回格式: [{"word":"山歌","rank":1,"count":34}, ...]
        """

        if not doc.extra_data:
            return []

        keywords = doc.extra_data.get('keywords', [])

        if not keywords:
            return []

        # 取 Top 8，转换格式
        top_keywords = []
        for i, kw in enumerate(keywords[:8]):
            if isinstance(kw, str):
                # 简单字符串格式
                top_keywords.append({
                    'word': kw,
                    'rank': i + 1
                })
            elif isinstance(kw, dict):
                # 字典格式（可能包含 tfidf、count 等）
                top_keywords.append({
                    'word': kw.get('word', kw.get('keyword', '')),
                    'rank': i + 1,
                    'tfidf': kw.get('tfidf', kw.get('weight', 0)),
                    'count': kw.get('count', 0)
                })

        return top_keywords

    def _extract_topics(self, document_id: int) -> List[Dict]:
        """
        从 topic_clusters 表提取主题（如果有）

        返回格式: [{"topic_id":1,"topic_name":"非遗传承","weight":0.76}, ...]
        """

        try:
            # 检查 topic_clusters 表是否存在
            result = self.db.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='topic_clusters'
            """)).fetchone()

            if not result:
                logger.debug("topic_clusters 表不存在")
                return []

            # 查询主题（按权重排序，取前3个）
            topics = self.db.execute(text("""
                SELECT topic_id, topic_name, weight
                FROM topic_clusters
                WHERE document_id = :document_id
                ORDER BY weight DESC
                LIMIT 3
            """), {'document_id': document_id}).fetchall()

            return [
                {
                    'topic_id': row[0],
                    'topic_name': row[1],
                    'weight': round(float(row[2]), 2) if row[2] else 0
                }
                for row in topics
            ]

        except Exception as e:
            logger.warning(f"提取主题失败: {e}")
            return []

    def _extract_entities(self, document_id: int) -> List[Dict]:
        """
        从 entities 表提取实体（如果有）

        返回格式: [{"name":"王大爷","type":"person","mention_count":15}, ...]
        """

        try:
            # 检查 entities 表是否存在
            result = self.db.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='entities'
            """)).fetchone()

            if not result:
                logger.debug("entities 表不存在")
                return []

            # 查询实体（按提及次数排序，取前5个）
            entities = self.db.execute(text("""
                SELECT name, entity_type, mention_count
                FROM entities
                WHERE document_id = :document_id
                ORDER BY mention_count DESC
                LIMIT 5
            """), {'document_id': document_id}).fetchall()

            return [
                {
                    'name': row[0],
                    'type': row[1],
                    'mention_count': row[2]
                }
                for row in entities
            ]

        except Exception as e:
            logger.warning(f"提取实体失败: {e}")
            return []

    def _extract_events(self, document_id: int) -> List[Dict]:
        """
        从 events 表提取事件（如果有）

        返回格式: [{"name":"山歌培训班停办","date":"2023.06","event_type":"社会"}, ...]
        """

        try:
            # 检查 events 表是否存在
            result = self.db.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='events'
            """)).fetchone()

            if not result:
                logger.debug("events 表不存在")
                return []

            # 查询事件（取前3个）
            events = self.db.execute(text("""
                SELECT event_type, temporal_expression, description
                FROM events
                WHERE document_id = :document_id
                LIMIT 3
            """), {'document_id': document_id}).fetchall()

            return [
                {
                    'name': row[0] or '未命名事件',
                    'date': row[1],
                    'description': row[2]
                }
                for row in events
            ]

        except Exception as e:
            logger.warning(f"提取事件失败: {e}")
            return []

    def _generate_one_line_summary(
        self,
        doc: ProjectDocument,
        keywords: List[Dict],
        topics: List[Dict],
        entities: List[Dict],
        chunks_data: Dict
    ) -> str:
        """
        生成一句话摘要（模板法 + LLM 增强）

        策略：
        1. 优先尝试使用 LLM 生成自然摘要
        2. LLM 失败时回退到模板法
        """

        # 尝试使用 LLM 生成摘要
        try:
            llm_summary = self._generate_llm_summary(doc, keywords, topics, entities, chunks_data)
            if llm_summary and len(llm_summary) > 10:
                logger.info(f"使用 LLM 生成一句话摘要")
                return llm_summary
        except Exception as e:
            logger.warning(f"LLM 生成摘要失败，回退到模板法: {e}")

        # 回退到模板法
        # 提取关键信息
        top_keywords_str = "、".join([kw['word'] for kw in keywords[:3]])
        top_topics_str = "、".join([t['topic_name'] for t in topics[:2]]) if topics else None
        top_entities_str = "、".join([e['name'] for e in entities[:2]]) if entities else None

        # 策略1：主题 + 关键词
        if top_topics_str:
            summary = f"本文档主要讨论{top_topics_str}"
            if top_keywords_str:
                summary += f"，关键词包括{top_keywords_str}"
        # 策略2：实体 + 关键词
        elif top_entities_str and top_keywords_str:
            summary = f"本文档主要涉及{top_entities_str}，关键主题包括{top_keywords_str}"
        # 策略3：关键词
        elif top_keywords_str:
            summary = f"本文档主要涉及{top_keywords_str}"
        # 策略4：基本信息
        else:
            summary = f"{doc.original_filename}（{chunks_data['word_count']}字）"

        # 添加维度信息
        if chunks_data['primary_dimension'] != '未分类':
            summary += f"，归类为{chunks_data['primary_dimension']}"

        # 添加句号
        if not summary.endswith('。'):
            summary += "。"

        return summary

    def _generate_llm_summary(
        self,
        doc: ProjectDocument,
        keywords: List[Dict],
        topics: List[Dict],
        entities: List[Dict],
        chunks_data: Dict
    ) -> Optional[str]:
        """
        使用 LLM 生成一句话摘要

        使用 OpenAI API 或其他 LLM 服务生成更自然的摘要
        """

        # 构造提示词
        prompt_parts = [
            f"请为以下文档生成一句话摘要（不超过50字）：",
            f"文档名称：{doc.original_filename}",
            f"文件类型：{doc.file_type}",
        ]

        if keywords:
            kw_str = "、".join([kw['word'] for kw in keywords[:5]])
            prompt_parts.append(f"关键词：{kw_str}")

        if topics:
            topic_str = "、".join([t['topic_name'] for t in topics])
            prompt_parts.append(f"主题：{topic_str}")

        if entities:
            entity_str = "、".join([e['name'] for e in entities])
            prompt_parts.append(f"实体：{entity_str}")

        prompt_parts.append(f"维度：{chunks_data['primary_dimension']}")

        # 获取第一个 chunk 的内容作为上下文
        first_chunk = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).order_by(DocumentChunk.chunk_index).first()

        if first_chunk and first_chunk.text:
            # 取前500字作为上下文
            context = first_chunk.text[:500]
            prompt_parts.append(f"\n文档开头内容：\n{context}")

        prompt = "\n".join(prompt_parts)

        # 调用 LLM API
        try:
            # 检查是否配置了 OpenAI API Key
            import os
            api_key = os.getenv('OPENAI_API_KEY')

            if not api_key:
                logger.debug("未配置 OPENAI_API_KEY，跳过 LLM 摘要生成")
                return None

            # 调用 OpenAI API
            import openai
            openai.api_key = api_key

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的文档摘要助手，擅长用简洁的语言概括文档核心内容。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            summary = response.choices[0].message.content.strip()

            # 验证摘要质量
            if len(summary) > 100:
                summary = summary[:100] + "..."

            return summary

        except ImportError:
            logger.debug("未安装 openai 库，跳过 LLM 摘要生成")
            return None
        except Exception as e:
            logger.warning(f"LLM API 调用失败: {e}")
            return None

    def _generate_full_summary(
        self,
        doc: ProjectDocument,
        chunks_data: Dict,
        keywords: List[Dict],
        topics: List[Dict],
        entities: List[Dict],
        events: List[Dict]
    ) -> str:
        """
        生成完整摘要（200-500字）

        结构：
        1. 基本信息（文件名、类型、字数）
        2. 关键词
        3. 核心主题
        4. 涉及实体
        5. 重要事件
        6. 维度分类
        7. 时空上下文
        """

        summary_parts = []

        # 1. 基本信息
        summary_parts.append(f"**文档名称**：{doc.original_filename}")
        summary_parts.append(f"**文件类型**：{doc.file_type or '未知'}")
        summary_parts.append(f"**总字数**：{chunks_data['word_count']}字")
        summary_parts.append(f"**分块数**：{chunks_data['chunk_count']}块")

        # 2. 关键词
        if keywords:
            kw_list = [kw['word'] for kw in keywords[:8]]
            kw_str = "、".join(kw_list)
            summary_parts.append(f"\n**关键词**：{kw_str}")

        # 3. 主题
        if topics:
            topic_list = [f"{t['topic_name']}({t['weight']})" for t in topics]
            topic_str = "、".join(topic_list)
            summary_parts.append(f"\n**核心主题**：{topic_str}")

        # 4. 实体
        if entities:
            entity_list = [e['name'] for e in entities]
            entity_str = "、".join(entity_list)
            summary_parts.append(f"\n**涉及实体**：{entity_str}")

        # 5. 事件
        if events:
            event_list = [e['name'] for e in events]
            event_str = "、".join(event_list)
            summary_parts.append(f"\n**重要事件**：{event_str}")

        # 6. 维度
        if chunks_data['primary_dimension'] != '未分类':
            dim_str = chunks_data['primary_dimension']
            if chunks_data['secondary_dimensions']:
                dim_str += f"（次要：{' '.join(chunks_data['secondary_dimensions'])}）"
            summary_parts.append(f"\n**维度分类**：{dim_str}")

        # 7. 时空上下文
        if chunks_data['time_start'] or chunks_data['spatial_context']:
            context_parts = []
            if chunks_data['time_start']:
                time_str = chunks_data['time_start']
                if chunks_data['time_end'] and chunks_data['time_end'] != chunks_data['time_start']:
                    time_str += f" - {chunks_data['time_end']}"
                context_parts.append(f"时间：{time_str}")
            if chunks_data['spatial_context']:
                context_parts.append(f"地点：{chunks_data['spatial_context']}")
            summary_parts.append(f"\n**时空上下文**：{' | '.join(context_parts)}")

        return "\n".join(summary_parts)

    def _find_related_documents(
        self,
        document_id: int,
        project_id: int,
        keywords: List[Dict],
        limit: int = 3
    ) -> List[Dict]:
        """
        计算关联文档（向量相似度 + 关键词重叠）

        策略：
        1. 优先使用向量相似度（如果 ChromaDB 可用）
        2. 回退到关键词重叠度计算

        返回格式: [{"document_id":2,"title":"山歌表演","similarity":0.89,"overlap_keywords":5}, ...]
        """

        # 策略1：尝试使用向量相似度
        try:
            vector_results = self._find_related_by_vector(document_id, project_id, limit)
            if vector_results:
                logger.info(f"使用向量相似度计算关联文档，找到 {len(vector_results)} 个")
                return vector_results
        except Exception as e:
            logger.debug(f"向量相似度计算失败，回退到关键词重叠: {e}")

        # 策略2：回退到关键词重叠度
        return self._find_related_by_keywords(document_id, project_id, keywords, limit)

    def _find_related_by_vector(
        self,
        document_id: int,
        project_id: int,
        limit: int = 3
    ) -> List[Dict]:
        """
        使用向量相似度计算关联文档（新增）

        使用 ChromaDB 或 document_chunks 表中的 embedding 字段
        """

        # 获取当前文档的向量表示
        doc_chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding.isnot(None)
        ).all()

        if not doc_chunks:
            logger.debug(f"文档 {document_id} 没有向量表示")
            return []

        # 计算文档级向量（所有 chunk 向量的平均）
        import json
        import numpy as np

        doc_vectors = []
        for chunk in doc_chunks:
            try:
                if isinstance(chunk.embedding, str):
                    vector = json.loads(chunk.embedding)
                else:
                    vector = chunk.embedding

                if vector and isinstance(vector, list):
                    doc_vectors.append(vector)
            except Exception as e:
                logger.debug(f"解析向量失败: {e}")
                continue

        if not doc_vectors:
            return []

        # 平均向量
        doc_vector = np.mean(doc_vectors, axis=0)

        # 查询同项目下其他文档的向量
        other_docs = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.id != document_id
        ).all()

        similarities = []

        for other_doc in other_docs:
            # 获取该文档的向量
            other_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == other_doc.id,
                DocumentChunk.embedding.isnot(None)
            ).all()

            if not other_chunks:
                continue

            other_vectors = []
            for chunk in other_chunks:
                try:
                    if isinstance(chunk.embedding, str):
                        vector = json.loads(chunk.embedding)
                    else:
                        vector = chunk.embedding

                    if vector and isinstance(vector, list):
                        other_vectors.append(vector)
                except:
                    continue

            if not other_vectors:
                continue

            # 平均向量
            other_vector = np.mean(other_vectors, axis=0)

            # 计算余弦相似度
            similarity = self._cosine_similarity(doc_vector, other_vector)

            if similarity > 0.5:  # 相似度阈值
                similarities.append({
                    'document_id': other_doc.id,
                    'title': other_doc.original_filename,
                    'similarity': round(float(similarity), 2),
                    'overlap_keywords': 0  # 向量方法不计算关键词重叠
                })

        # 按相似度排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return similarities[:limit]

    def _cosine_similarity(self, vec1, vec2) -> float:
        """计算余弦相似度"""
        import numpy as np

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _find_related_by_keywords(
        self,
        document_id: int,
        project_id: int,
        keywords: List[Dict],
        limit: int = 3
    ) -> List[Dict]:
        """
        基于关键词重叠度计算关联文档（回退方法）
        """

        if not keywords:
            return []

        # 提取关键词列表
        keyword_words = [kw['word'] for kw in keywords[:5]]

        try:
            # 查询同项目下其他文档
            docs = self.db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.id != document_id,
                ProjectDocument.extra_data.isnot(None)
            ).all()

            related = []

            for doc in docs:
                # 获取该文档的关键词
                doc_keywords = doc.extra_data.get('keywords', [])

                # 提取关键词文本
                doc_keyword_words = []
                for kw in doc_keywords[:10]:
                    if isinstance(kw, str):
                        doc_keyword_words.append(kw)
                    elif isinstance(kw, dict):
                        word = kw.get('word', kw.get('keyword', ''))
                        if word:
                            doc_keyword_words.append(word)

                # 计算重叠度
                overlap = len(set(keyword_words) & set(doc_keyword_words))

                if overlap > 0:
                    similarity = overlap / len(keyword_words)
                    related.append({
                        'document_id': doc.id,
                        'title': doc.original_filename,
                        'similarity': round(similarity, 2),
                        'overlap_keywords': overlap
                    })

            # 按相似度排序
            related.sort(key=lambda x: x['similarity'], reverse=True)

            return related[:limit]

        except Exception as e:
            logger.warning(f"计算关联文档失败: {e}")
            return []


def save_summary(db: Session, summary_data: Dict[str, Any]):
    """
    保存缩影到数据库

    使用 INSERT OR REPLACE 实现 UPSERT（如果已存在则更新）

    Args:
        db: 数据库会话
        summary_data: 缩影数据字典
    """

    try:
        db.execute(text("""
            INSERT OR REPLACE INTO file_summaries (
                document_id, project_id, one_line_summary, full_summary,
                top_keywords, top_entities, top_topics, top_events,
                word_count, chunk_count, avg_chunk_length,
                primary_dimension, secondary_dimensions,
                time_start, time_end, spatial_context,
                related_documents, status, generated_at,
                updated_at
            ) VALUES (
                :document_id, :project_id, :one_line_summary, :full_summary,
                :top_keywords, :top_entities, :top_topics, :top_events,
                :word_count, :chunk_count, :avg_chunk_length,
                :primary_dimension, :secondary_dimensions,
                :time_start, :time_end, :spatial_context,
                :related_documents, :status, :generated_at,
                datetime('now')
            )
        """), summary_data)

        db.commit()
        logger.info(f"✅ 缩影已保存到数据库: document_id={summary_data['document_id']}")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 保存缩影失败: {e}", exc_info=True)
        raise


def regenerate_summary(db: Session, document_id: int) -> Dict[str, Any]:
    """
    重新生成文档缩影

    用于：
    1. 缩影生成失败后重试
    2. 文档内容更新后重新生成
    3. 用户手动触发重新生成

    Args:
        db: 数据库会话
        document_id: 文档ID

    Returns:
        缩影数据字典
    """

    logger.info(f"🔄 重新生成文档 {document_id} 的缩影")

    generator = FileSummaryGenerator(db)
    summary_data = generator.generate_summary(document_id)
    save_summary(db, summary_data)

    logger.info(f"✅ 文档 {document_id} 缩影重新生成完成")

    return summary_data
