"""
量化工具箱统一入口

整合所有特征提取器，提供一站式量化分析接口
"""

import logging
import json
from .structural_features import extract_structural_features
from .emotional_features import extract_emotional_features
from .style_features import extract_style_features
from .content_features import extract_content_features
from .tfidf_extractor import extract_tfidf_keywords_for_chunk

logger = logging.getLogger(__name__)


def quantify_chunk(text: str, all_chunks: list = None, keyword_list: list = None) -> dict:
    """
    量化工具箱的统一入口

    一次调用提取所有量化特征：
    1. 结构性特征（字数、句数、段落数等）
    2. 情绪与情感特征（极性、强度、标签）
    3. 语言风格特征（主观性、语气强度等）
    4. 内容类特征（情绪词密度、关键词密度）
    5. TF-IDF关键词（需要项目上下文）

    Args:
        text: 输入文本
        all_chunks: 项目所有chunk的文本列表（用于TF-IDF计算）
        keyword_list: 自定义关键词列表（用于关键词密度计算）

    Returns:
        包含所有量化特征的字典
    """
    if not text or not text.strip():
        return get_empty_features()

    result = {}

    try:
        # 1. 结构性特征
        logger.debug("提取结构性特征...")
        result.update(extract_structural_features(text))

        # 2. 情绪与情感特征
        logger.debug("提取情绪特征...")
        result.update(extract_emotional_features(text))

        # 3. 语言风格特征
        logger.debug("提取语言风格特征...")
        result.update(extract_style_features(text))

        # 4. 内容类特征
        logger.debug("提取内容类特征...")
        result.update(extract_content_features(text, keyword_list))

        # 5. TF-IDF关键词（需要项目上下文）
        if all_chunks and len(all_chunks) > 1:
            logger.debug("提取TF-IDF关键词...")
            keywords = extract_tfidf_keywords_for_chunk(text, all_chunks, top_k=10)
            result['tfidf_keywords'] = json.dumps(keywords, ensure_ascii=False)
        else:
            result['tfidf_keywords'] = json.dumps([], ensure_ascii=False)

        logger.info(f"量化分析完成，提取了 {len(result)} 个特征")
        return result

    except Exception as e:
        logger.error(f"量化分析失败: {e}")
        return get_empty_features()


def get_empty_features() -> dict:
    """返回空的特征字典（所有字段为默认值）"""
    return {
        # 结构性特征
        'word_count': 0,
        'sentence_count': 0,
        'paragraph_count': 0,
        'avg_word_length': 0.0,
        'avg_sentence_length': 0.0,

        # 情绪与情感特征
        'emotion_polarity': 0.0,
        'emotion_intensity': 0.0,
        'emotion_label': '中性',

        # 语言风格特征
        'subjectivity': 0.5,
        'objectivity': 0.5,
        'tone_strength': 0.0,
        'exclamation_count': 0,
        'modal_verb_count': 0,

        # 内容类特征
        'emotion_word_density': 0.0,
        'keyword_density': 0.0,
        'tfidf_keywords': '[]',
    }


def batch_quantify_chunks(chunks_data: list) -> list:
    """
    批量量化分析

    Args:
        chunks_data: chunk数据列表，每个元素为 {'id': ..., 'text': ...}

    Returns:
        量化结果列表，每个元素为 {'chunk_id': ..., 'features': {...}}
    """
    if not chunks_data:
        return []

    logger.info(f"开始批量量化分析，共 {len(chunks_data)} 个chunks")

    # 提取所有文本用于TF-IDF计算
    all_texts = [chunk['text'] for chunk in chunks_data]

    results = []
    for i, chunk in enumerate(chunks_data):
        try:
            features = quantify_chunk(chunk['text'], all_texts)
            results.append({
                'chunk_id': chunk.get('id'),
                'features': features
            })

            if (i + 1) % 100 == 0:
                logger.info(f"已完成 {i + 1}/{len(chunks_data)} 个chunks")

        except Exception as e:
            logger.error(f"Chunk {chunk.get('id')} 量化失败: {e}")
            results.append({
                'chunk_id': chunk.get('id'),
                'features': get_empty_features()
            })

    logger.info(f"批量量化分析完成，成功 {len(results)} 个")
    return results



# ==================== WorkflowEngine 包装类 ====================

class QuantifierWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_quantify_chunk(self, text: str, _context: dict) -> dict:
        """任务: 量化单个文本块"""
        all_chunks = _context.get('all_chunks')
        keyword_list = _context.get('keyword_list')
        features = quantify_chunk(text, all_chunks, keyword_list)
        return {"features": features}

    def _task_batch_quantify(self, chunks_data: list, _context: dict) -> dict:
        """任务: 批量量化分析"""
        results = batch_quantify_chunks(chunks_data)
        return {"results": results, "count": len(results)}

    def quantify_chunk_workflow(self, text: str, all_chunks: list = None, keyword_list: list = None) -> dict:
        """工作流: 使用 WorkflowEngine 进行量化分析"""
        if not self.use_workflow_engine:
            return quantify_chunk(text, all_chunks, keyword_list)

        tasks = {
            "quantify": {
                "function": self._task_quantify_chunk,
                "args": {"text": text},
                "context": {"all_chunks": all_chunks, "keyword_list": keyword_list}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["quantify"]["features"]

    def batch_quantify_workflow(self, chunks_data: list) -> list:
        """工作流: 使用 WorkflowEngine 进行批量量化"""
        if not self.use_workflow_engine:
            return batch_quantify_chunks(chunks_data)

        tasks = {
            "batch_quantify": {
                "function": self._task_batch_quantify,
                "args": {"chunks_data": chunks_data}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_quantify"]["results"]
