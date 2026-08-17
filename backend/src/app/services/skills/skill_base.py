"""
Skill 基类 - 所有专业分析技能的抽象基类

设计原则:
1. 每个skill代表一个学术理论框架或专业分析维度
2. 使用向量语义检索，不是简单关键词匹配
3. 独立可测试，标准化输入输出
4. 可选LLM深度分析
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend
from app.tools.ingestion.text_processor import split_sentences, extract_keywords

logger = logging.getLogger(__name__)


@dataclass
class DimensionDefinition:
    """
    维度定义

    每个维度代表理论框架中的一个分析角度
    """
    dimension_id: str              # 维度ID（如 power_structure）
    dimension_name: str            # 维度名称（如 权力结构）
    description: str               # 维度描述（理论定义）
    keywords: List[str]            # 关键概念列表
    example_sentences: List[str]   # 示例句子（用于构建语义向量）
    vector: Optional[np.ndarray] = None  # 维度的语义向量（从example_sentences编码）


@dataclass
class AnalysisMatch:
    """
    单个匹配结果
    """
    dimension_id: str        # 匹配的维度ID
    dimension_name: str      # 维度名称
    sentence: str            # 匹配的句子
    similarity: float        # 相似度分数 (0-1)
    context: str             # 上下文（前后句）
    keywords_found: List[str]  # 发现的关键词


@dataclass
class SkillResult:
    """
    Skill分析结果标准输出
    """
    skill_id: str                          # Skill ID
    skill_name: str                        # Skill名称
    success: bool                          # 是否成功
    dimensions: Dict[str, List[AnalysisMatch]]  # 各维度的匹配结果
    total_matches: int                     # 总匹配数
    avg_confidence: float                  # 平均置信度
    keywords: List[str]                    # 提取的关键词
    execution_time: float                  # 执行时间（秒）
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class SkillBase(ABC):
    """
    Skill基类 - 所有分析技能继承此类

    核心方法:
    1. semantic_retrieve: 向量语义检索
    2. analyze: 主分析入口
    3. get_definition: 返回skill定义
    """

    def __init__(self):
        """初始化"""
        # 使用BGE-small引擎进行向量化（512维，平衡性能和精度）
        self.vectorization_engine = UnifiedVectorizationEngine(
            engine=VectorEngine.BGE_SMALL,
            storage=StorageBackend.MEMORY  # Skills不需要持久化向量
        )
        self.dimensions: Dict[str, DimensionDefinition] = {}
        self._initialize_dimensions()
        self._compute_dimension_vectors()

    @abstractmethod
    def _initialize_dimensions(self):
        """
        子类必须实现：初始化维度定义

        例如:
        self.dimensions = {
            'power_structure': DimensionDefinition(
                dimension_id='power_structure',
                dimension_name='权力结构',
                description='村庄权力分配、决策机制、权威来源',
                keywords=['村委会', '党支部', '族长', '权力', '决策'],
                example_sentences=[
                    '村委会主任掌握着村里的主要决策权',
                    '党支部书记在村庄治理中发挥核心作用',
                    '族长在宗族事务中具有很高的威望'
                ]
            ),
            ...
        }
        """
        pass

    @property
    @abstractmethod
    def skill_id(self) -> str:
        """返回skill ID"""
        pass

    @property
    @abstractmethod
    def skill_name(self) -> str:
        """返回skill名称"""
        pass

    @property
    @abstractmethod
    def skill_description(self) -> str:
        """返回skill描述"""
        pass

    def _compute_dimension_vectors(self):
        """
        为每个维度计算语义向量

        使用维度的example_sentences，通过BGE模型编码
        然后取平均作为该维度的语义表示
        """
        for dim_id, dimension in self.dimensions.items():
            if dimension.example_sentences:
                try:
                    # 编码所有示例句子
                    sentence_vectors = self.vectorization_engine.encode_documents(
                        texts=dimension.example_sentences,
                        normalize=True
                    )
                    # 取平均作为维度向量
                    dimension.vector = np.mean(sentence_vectors, axis=0)
                    logger.debug(f"维度 {dimension.dimension_name} 向量计算完成")
                except Exception as e:
                    logger.error(f"维度 {dimension.dimension_name} 向量计算失败: {str(e)}")
                    dimension.vector = None

    def semantic_retrieve(
        self,
        text: str,
        dimension: DimensionDefinition,
        threshold: float = 0.65,
        top_k: int = 10
    ) -> List[Tuple[str, float, str]]:
        """
        向量语义检索 - 核心功能

        从文本中检索与指定维度语义相关的句子

        参数:
            text: 待分析文本
            dimension: 维度定义
            threshold: 相似度阈值（0-1，默认0.65）
            top_k: 最多返回多少个匹配

        返回:
            [(句子, 相似度, 上下文), ...]
        """
        if dimension.vector is None:
            logger.warning(f"维度 {dimension.dimension_name} 没有向量表示")
            return []

        # 分句
        sentences = split_sentences(text)
        if not sentences:
            return []

        # 编码所有句子
        try:
            sentence_vectors = self.vectorization_engine.encode_documents(
                texts=sentences,
                normalize=True
            )
        except Exception as e:
            logger.error(f"句子向量化失败: {str(e)}")
            return []

        # 计算余弦相似度
        # dimension.vector shape: (1024,)
        # sentence_vectors shape: (n, 1024)
        dim_vector_2d = dimension.vector.reshape(1, -1)
        similarities = cosine_similarity(sentence_vectors, dim_vector_2d).flatten()

        # 筛选超过阈值的句子
        results = []
        for i, (sentence, similarity) in enumerate(zip(sentences, similarities)):
            if similarity >= threshold:
                # 构建上下文（前后各一句）
                context_parts = []
                if i > 0:
                    context_parts.append(sentences[i-1])
                context_parts.append(sentence)
                if i < len(sentences) - 1:
                    context_parts.append(sentences[i+1])
                context = ' '.join(context_parts)

                results.append((sentence, float(similarity), context))

        # 按相似度排序，取top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def find_keywords_in_text(
        self,
        text: str,
        keywords: List[str]
    ) -> List[str]:
        """
        在文本中查找关键词

        参数:
            text: 文本
            keywords: 关键词列表

        返回:
            找到的关键词列表
        """
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        return found

    def analyze(
        self,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """
        主分析入口 - 对文本进行完整的维度分析

        参数:
            text_content: 待分析的文本内容
            metadata: 额外的元数据（如实体关系等）

        返回:
            SkillResult: 标准化的分析结果
        """
        start_time = datetime.now()
        metadata = metadata or {}

        try:
            # 提取文本关键词（用于整体理解）
            text_keywords = extract_keywords(text_content, top_k=15)

            # 对每个维度进行语义检索
            dimension_results: Dict[str, List[AnalysisMatch]] = {}
            total_matches = 0

            for dim_id, dimension in self.dimensions.items():
                # 语义检索
                matches = self.semantic_retrieve(
                    text=text_content,
                    dimension=dimension,
                    threshold=0.65,  # 可以根据需要调整
                    top_k=5          # 每个维度最多5个匹配
                )

                # 构建AnalysisMatch对象
                analysis_matches = []
                for sentence, similarity, context in matches:
                    # 查找句子中的关键词
                    keywords_found = self.find_keywords_in_text(
                        sentence,
                        dimension.keywords
                    )

                    match = AnalysisMatch(
                        dimension_id=dim_id,
                        dimension_name=dimension.dimension_name,
                        sentence=sentence,
                        similarity=similarity,
                        context=context,
                        keywords_found=keywords_found
                    )
                    analysis_matches.append(match)

                if analysis_matches:
                    dimension_results[dim_id] = analysis_matches
                    total_matches += len(analysis_matches)

            # 计算平均置信度
            all_similarities = []
            for matches in dimension_results.values():
                all_similarities.extend([m.similarity for m in matches])

            avg_confidence = (
                sum(all_similarities) / len(all_similarities)
                if all_similarities else 0.0
            )

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillResult(
                skill_id=self.skill_id,
                skill_name=self.skill_name,
                success=True,
                dimensions=dimension_results,
                total_matches=total_matches,
                avg_confidence=avg_confidence,
                keywords=text_keywords,
                execution_time=execution_time,
                metadata={
                    'dimensions_analyzed': len(self.dimensions),
                    'dimensions_matched': len(dimension_results),
                    **metadata
                }
            )

        except Exception as e:
            logger.error(f"Skill {self.skill_id} 分析失败: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillResult(
                skill_id=self.skill_id,
                skill_name=self.skill_name,
                success=False,
                dimensions={},
                total_matches=0,
                avg_confidence=0.0,
                keywords=[],
                execution_time=execution_time,
                errors=[str(e)]
            )

    def get_definition(self) -> Dict[str, Any]:
        """
        返回skill定义（用于配置和展示）

        返回:
            {
                'skill_id': str,
                'skill_name': str,
                'description': str,
                'dimensions': [
                    {
                        'dimension_id': str,
                        'dimension_name': str,
                        'description': str,
                        'keywords': List[str]
                    },
                    ...
                ]
            }
        """
        return {
            'skill_id': self.skill_id,
            'skill_name': self.skill_name,
            'description': self.skill_description,
            'dimensions': [
                {
                    'dimension_id': dim.dimension_id,
                    'dimension_name': dim.dimension_name,
                    'description': dim.description,
                    'keywords': dim.keywords
                }
                for dim in self.dimensions.values()
            ]
        }
