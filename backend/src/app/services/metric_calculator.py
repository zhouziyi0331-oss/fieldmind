"""
指标计算服务
根据指标字典计算所有量化指标
"""

import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logging import logger
from app.core.database import get_db_session
from app.models.document_chunk import DocumentChunk
from sqlalchemy import text


class MetricCalculator:
    """指标计算器"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.metric_cache = {}  # 缓存已加载的指标定义

    def calculate_all_metrics(
        self,
        chunk_id: str,
        chunk_text: str,
        trigger: str = "auto",
        db=None
    ) -> Dict[str, Any]:
        """
        计算chunk的所有指标

        Args:
            chunk_id: chunk ID
            chunk_text: 文本内容
            trigger: 触发源
            db: 数据库会话（可选，如果不传则创建新会话）

        Returns:
            Dict: 计算结果
        """
        start_time = time.time()

        logger.info(f"[指标计算] 开始: chunk_id={chunk_id}")

        results = {}

        # 结构性指标
        results.update(self._calculate_structural_metrics(chunk_text))

        # 情绪性指标
        results.update(self._calculate_emotion_metrics(chunk_text))

        # 语言风格指标
        results.update(self._calculate_style_metrics(chunk_text))

        # 内容类指标
        results.update(self._calculate_content_metrics(chunk_text))

        # 质量类指标
        results.update(self._calculate_quality_metrics(chunk_text))

        # 记录到计算历史
        self._save_calculation_history(
            chunk_id=chunk_id,
            results=results,
            trigger=trigger,
            execution_time=int((time.time() - start_time) * 1000),
            db=db
        )

        logger.info(
            f"[指标计算] 完成: {len(results)} 个指标, "
            f"耗时 {time.time() - start_time:.2f}s"
        )

        return results

    def _calculate_structural_metrics(self, text: str) -> Dict[str, Any]:
        """计算结构性指标"""
        metrics = {}

        # M001: 字数
        words = [c for c in text if c.isalnum()]
        metrics['word_count'] = len(words)

        # M002: 句数
        sentences = re.split(r'[。！？!?.]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        metrics['sentence_count'] = len(sentences)

        # M003: 平均句长
        if metrics['sentence_count'] > 0:
            metrics['avg_sentence_length'] = metrics['word_count'] / metrics['sentence_count']
        else:
            metrics['avg_sentence_length'] = 0

        return metrics

    def _calculate_emotion_metrics(self, text: str) -> Dict[str, Any]:
        """计算情绪性指标"""
        metrics = {}

        # M011: 情感极性值（简化版，使用规则）
        # TODO: 集成 SnowNLP 或 Erlangshen-RoBERTa
        positive_words = ['好', '喜欢', '高兴', '开心', '满意', '感谢', '棒', '优秀']
        negative_words = ['不好', '讨厌', '难过', '失望', '糟糕', '差', '痛苦', '困难']

        pos_count = sum(text.count(w) for w in positive_words)
        neg_count = sum(text.count(w) for w in negative_words)

        total = pos_count + neg_count
        if total > 0:
            metrics['emotion_polarity'] = (pos_count - neg_count) / total
        else:
            metrics['emotion_polarity'] = 0.0

        # M012: 情绪强度
        emotion_word_count = pos_count + neg_count
        word_count = len([c for c in text if c.isalnum()])
        emotion_density = emotion_word_count / word_count if word_count > 0 else 0
        metrics['emotion_strength'] = abs(metrics['emotion_polarity']) * emotion_density

        # M013: 主观性（第一人称代词比例）
        first_person = ['我', '我们', '咱', '咱们', '本人']
        first_person_count = sum(text.count(w) for w in first_person)
        metrics['subjectivity'] = min(first_person_count / 10, 1.0)  # 归一化

        return metrics

    def _calculate_style_metrics(self, text: str) -> Dict[str, Any]:
        """计算语言风格指标"""
        metrics = {}

        # M021: 情绪词密度
        emotion_words = ['好', '喜欢', '高兴', '开心', '不好', '讨厌', '难过', '失望']
        emotion_count = sum(text.count(w) for w in emotion_words)
        word_count = len([c for c in text if c.isalnum()])
        metrics['emotion_word_density'] = emotion_count / word_count if word_count > 0 else 0

        # M022: 感叹号数量
        metrics['exclamation_count'] = text.count('！') + text.count('!')

        # M023: 疑问句比例
        question_count = text.count('？') + text.count('?')
        sentence_count = len(re.split(r'[。！？!?.]+', text))
        metrics['question_ratio'] = question_count / sentence_count if sentence_count > 0 else 0

        # M024: 语气强度
        tone_words = ['的确', '确实', '非常', '很', '特别', '真的', '绝对']
        tone_count = sum(text.count(w) for w in tone_words)
        metrics['tone_strength'] = min(tone_count / 5, 1.0)

        # M025: 情态动词数量
        modal_verbs = ['可能', '应该', '必须', '会', '能', '要', '想']
        metrics['modal_verb_count'] = sum(text.count(w) for w in modal_verbs)

        return metrics

    def _calculate_content_metrics(self, text: str) -> Dict[str, Any]:
        """计算内容类指标"""
        metrics = {}

        # M031: 关键词数量（简化版）
        # TODO: 集成 TF-IDF 或 TextRank
        import jieba
        # 兼容没有公开 lcut 的旧版 jieba。
        words = list(jieba.lcut(text)) if hasattr(jieba, "lcut") else list(jieba.cut(text))
        # 过滤停用词
        stopwords = {'的', '是', '在', '了', '和', '有', '我', '你', '他', '她', '它'}
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        metrics['keyword_count'] = min(len(set(keywords)), 20)

        # M032: 实体数量（规则提取）
        from app.services.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        entities = extractor.extract(text)
        metrics['entity_count'] = len(entities)

        # M033: 主题一致性（默认值，需要主题模型）
        metrics['topic_consistency'] = 0.5

        return metrics

    def _calculate_quality_metrics(self, text: str) -> Dict[str, Any]:
        """计算质量类指标"""
        metrics = {}

        # M041: 文本质量评分（简化版）
        # 基于：长度、标点、重复率
        score = 0.5

        # 长度合理性
        if 50 < len(text) < 500:
            score += 0.2

        # 标点使用
        punctuation_ratio = len([c for c in text if c in '，。！？；：']) / len(text)
        if 0.05 < punctuation_ratio < 0.15:
            score += 0.2

        metrics['quality_score'] = min(score, 1.0)

        # M042: 重复率
        words = text.split()
        if words:
            unique_words = set(words)
            metrics['duplicate_ratio'] = 1 - (len(unique_words) / len(words))
        else:
            metrics['duplicate_ratio'] = 0.0

        # M043: 语法错误数（简化版）
        # TODO: 集成语法检查工具
        metrics['grammar_error_count'] = 0

        return metrics

    def _save_calculation_history(
        self,
        chunk_id: str,
        results: Dict[str, Any],
        trigger: str,
        execution_time: int,
        db=None
    ):
        """保存计算历史"""
        # 判断是否需要自己管理会话
        should_close = False
        if db is None:
            db = get_db_session()
            should_close = True

        try:
            # 映射指标名到指标ID
            metric_mapping = {
                'word_count': 'M001',
                'sentence_count': 'M002',
                'avg_sentence_length': 'M003',
                'emotion_polarity': 'M011',
                'emotion_strength': 'M012',
                'subjectivity': 'M013',
                'emotion_word_density': 'M021',
                'exclamation_count': 'M022',
                'question_ratio': 'M023',
                'tone_strength': 'M024',
                'modal_verb_count': 'M025',
                'keyword_count': 'M031',
                'entity_count': 'M032',
                'topic_consistency': 'M033',
                'quality_score': 'M041',
                'duplicate_ratio': 'M042',
                'grammar_error_count': 'M043',
            }

            for metric_name, metric_value in results.items():
                metric_id = metric_mapping.get(metric_name)
                if metric_id:
                    sql = text("""
                        INSERT INTO metric_calculation_history (
                            chunk_id, metric_id, metric_value,
                            calculation_timestamp, calculation_trigger,
                            algorithm_version, execution_time_ms
                        ) VALUES (
                            :chunk_id, :metric_id, :metric_value,
                            :calc_time, :trigger, :version, :exec_time
                        )
                    """)

                    db.execute(sql, {
                        "chunk_id": chunk_id,
                        "metric_id": metric_id,
                        "metric_value": str(metric_value),
                        "calc_time": datetime.utcnow(),
                        "trigger": trigger,
                        "version": "v1.0",
                        "exec_time": execution_time
                    })

            # 只有自己创建的会话才commit
            if should_close:
                db.commit()

        except Exception as e:
            # 只有自己创建的会话才rollback
            if should_close:
                db.rollback()
            logger.error(f"保存计算历史失败: {e}")
            # 重新抛出异常，让编排器感知错误
            raise

        finally:
            # 只有自己创建的会话才close
            if should_close:
                db.close()


# 便捷函数
def calculate_chunk_metrics(chunk_id: str, chunk_text: str, db=None) -> Dict[str, Any]:
    """计算chunk的所有指标"""
    calculator = MetricCalculator()
    return calculator.calculate_all_metrics(chunk_id, chunk_text, db=db)
