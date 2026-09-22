"""
多向量生成器
生成4个1024维向量：文本、实体、关系、领域
关键：统一语义空间，向量归一化
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional

from app.models.enriched_chunk import EnrichedChunk, MultiVectorResult

logger = logging.getLogger(__name__)


class MultiVectorGenerator:
    """多向量生成器 - 每个向量1024维"""

    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        """初始化多向量生成器

        Args:
            model_name: FlagEmbedding模型名称
        """
        self.model_name = model_name
        self.embedding_dim = 1024

        # 初始化编码器 ⭐
        self.text_encoder = self._init_text_encoder(model_name)
        self.entity_encoder = self._init_entity_encoder(model_name)
        self.relation_encoder = self._init_relation_encoder(model_name)
        self.domain_encoder = self._init_domain_encoder(model_name)

        logger.info(f"多向量生成器初始化完成 - 模型: {model_name}, 维度: {self.embedding_dim}")

    def _init_text_encoder(self, model_name: str):
        """初始化文本编码器（FlagEmbedding）"""
        try:
            from FlagEmbedding import FlagModel
            model = FlagModel(
                model_name,
                query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
                use_fp16=True
            )
            logger.info(f"文本编码器加载成功: {model_name}")
            return model
        except Exception as e:
            logger.error(f"文本编码器加载失败: {e}")
            raise

    def _init_entity_encoder(self, model_name: str):
        """初始化实体编码器

        使用与文本编码器相同的模型 ⭐
        确保在同一语义空间中
        """
        try:
            from FlagEmbedding import FlagModel
            model = FlagModel(model_name, use_fp16=True)
            logger.info(f"实体编码器加载成功: {model_name}")
            return model
        except Exception as e:
            logger.error(f"实体编码器加载失败: {e}")
            raise

    def _init_relation_encoder(self, model_name: str):
        """初始化关系编码器

        使用与文本编码器相同的模型 ⭐
        确保在同一语义空间中
        """
        try:
            from FlagEmbedding import FlagModel
            model = FlagModel(model_name, use_fp16=True)
            logger.info(f"关系编码器加载成功: {model_name}")
            return model
        except Exception as e:
            logger.error(f"关系编码器加载失败: {e}")
            raise

    def _init_domain_encoder(self, model_name: str):
        """初始化领域编码器

        使用与文本编码器相同的模型 ⭐
        确保在同一语义空间中
        """
        try:
            from FlagEmbedding import FlagModel
            model = FlagModel(model_name, use_fp16=True)
            logger.info(f"领域编码器加载成功: {model_name}")
            return model
        except Exception as e:
            logger.error(f"领域编码器加载失败: {e}")
            raise

    def generate_multi_vectors(
        self,
        enriched_chunk: EnrichedChunk
    ) -> MultiVectorResult:
        """生成4个1024维向量

        Args:
            enriched_chunk: 增强后的chunk

        Returns:
            多向量结果
        """
        # 1. 文本向量（1024维）⭐
        text_embedding, text_quality = self._generate_text_vector(enriched_chunk)

        # 2. 实体向量（1024维）⭐
        entity_embedding, entity_quality = self._generate_entity_vector(enriched_chunk)

        # 3. 关系向量（1024维）⭐
        relation_embedding, relation_quality = self._generate_relation_vector(enriched_chunk)

        # 4. 领域向量（1024维）⭐
        domain_embedding, domain_quality = self._generate_domain_vector(enriched_chunk)

        logger.info(
            f"多向量生成完成 - "
            f"文本质量: {text_quality:.2f}, "
            f"实体质量: {entity_quality:.2f}, "
            f"关系质量: {relation_quality:.2f}, "
            f"领域质量: {domain_quality:.2f}"
        )

        return MultiVectorResult(
            text_embedding=text_embedding.tolist(),
            entity_embedding=entity_embedding.tolist(),
            relation_embedding=relation_embedding.tolist(),
            domain_embedding=domain_embedding.tolist(),
            dimensions={
                "text": self.embedding_dim,
                "entity": self.embedding_dim,
                "relation": self.embedding_dim,
                "domain": self.embedding_dim
            },
            quality_scores={
                "text": text_quality,
                "entity": entity_quality,
                "relation": relation_quality,
                "domain": domain_quality
            }
        )

    def _generate_text_vector(
        self,
        enriched_chunk: EnrichedChunk
    ) -> tuple[np.ndarray, float]:
        """生成文本向量（1024维）⭐

        策略：
        - 同时考虑原文和规范化文本（方言处理后）
        - 拼接后编码，确保方言和标准词都被理解
        """
        text = enriched_chunk.text

        # 如果有方言处理结果，拼接原文和规范化文本
        if enriched_chunk.dialect_result and enriched_chunk.dialect_result.dialect_terms:
            normalized = enriched_chunk.dialect_result.normalized_text
            # 拼接：原文 + 规范化文本
            text_to_encode = f"{text} [规范化] {normalized}"
        else:
            text_to_encode = text

        # 编码
        embedding = self.text_encoder.encode_documents([text_to_encode])[0]  # [1024]

        # 归一化 ⭐
        embedding = self._normalize_vector(embedding)

        # 质量评估（基于文本长度和内容丰富度）
        quality = self._assess_text_quality(text)

        return embedding, quality

    def _generate_entity_vector(
        self,
        enriched_chunk: EnrichedChunk
    ) -> tuple[np.ndarray, float]:
        """生成实体向量（1024维）⭐

        策略：
        1. 为每个实体生成描述文本（包含类型和文化背景）
        2. 编码所有实体
        3. 加权平均（遗产类实体权重更高）
        4. 投影到1024维
        """
        if not enriched_chunk.entities:
            # 无实体时返回零向量
            zero_vector = np.zeros(self.embedding_dim)
            return zero_vector, 0.0

        # 为每个实体生成描述文本
        entity_texts = []
        entity_weights = []

        for entity in enriched_chunk.entities:
            # 构建实体描述（包含类型和文化背景）
            desc = f"{entity.text}（{entity.type.value}"

            # 添加类别信息
            if entity.category:
                desc += f"，{entity.category}"

            # 添加文化背景
            if entity.cultural_context:
                desc += f"，{entity.cultural_context}"

            desc += "）"

            entity_texts.append(desc)

            # 权重：遗产类实体权重更高 ⭐
            weight = self._calculate_entity_weight(entity)
            entity_weights.append(weight)

        # 编码所有实体
        entity_embeddings = self.entity_encoder.encode(entity_texts)  # [N, 1024]

        # 归一化每个向量 ⭐
        entity_embeddings = np.array([
            self._normalize_vector(emb) for emb in entity_embeddings
        ])

        # 加权平均 ⭐
        weights = np.array(entity_weights) / np.sum(entity_weights)
        weighted_embedding = np.average(entity_embeddings, axis=0, weights=weights)  # [1024]

        # 最终归一化
        weighted_embedding = self._normalize_vector(weighted_embedding)

        # 质量评估（基于实体数量和置信度）
        quality = self._assess_entity_quality(enriched_chunk.entities)

        return weighted_embedding, quality

    def _calculate_entity_weight(self, entity) -> float:
        """计算实体权重 ⭐

        遗产类实体权重更高，体现田野调查的重点
        """
        from app.models.enriched_chunk import EntityType

        # 基础权重
        weight = entity.confidence

        # 遗产类实体加权 ⭐⭐
        if entity.type in [
            EntityType.INTANGIBLE_HERITAGE,
            EntityType.TANGIBLE_HERITAGE,
            EntityType.NATURAL_HERITAGE
        ]:
            weight *= 2.0  # 遗产类实体权重翻倍

        # 文化习俗类实体加权
        elif entity.type in [
            EntityType.CUSTOM,
            EntityType.RITUAL,
            EntityType.FESTIVAL,
            EntityType.CEREMONY
        ]:
            weight *= 1.5

        # 方言词加权
        elif entity.type == EntityType.DIALECT_TERM:
            weight *= 1.3

        return weight

    def _generate_relation_vector(
        self,
        enriched_chunk: EnrichedChunk
    ) -> tuple[np.ndarray, float]:
        """生成关系向量（1024维）⭐

        策略：
        1. 为每个关系生成三元组描述
        2. 编码所有关系
        3. 平均池化到1024维
        """
        if not enriched_chunk.relations:
            # 无关系时返回零向量
            zero_vector = np.zeros(self.embedding_dim)
            return zero_vector, 0.0

        # 为每个关系生成三元组描述
        relation_texts = []

        for relation in enriched_chunk.relations:
            # 三元组：主体 - 关系 - 客体
            triple = f"{relation.subject} {relation.relation.value} {relation.object}"

            # 添加上下文
            if relation.context:
                triple += f"（{relation.context}）"

            # 添加额外信息
            if relation.position:
                triple += f" [职位: {relation.position}]"
            if relation.support_type:
                triple += f" [支持类型: {relation.support_type}]"

            relation_texts.append(triple)

        # 编码所有关系
        relation_embeddings = self.relation_encoder.encode(relation_texts)  # [M, 1024]

        # 归一化每个向量 ⭐
        relation_embeddings = np.array([
            self._normalize_vector(emb) for emb in relation_embeddings
        ])

        # 平均池化
        averaged_embedding = np.mean(relation_embeddings, axis=0)  # [1024]

        # 最终归一化
        averaged_embedding = self._normalize_vector(averaged_embedding)

        # 质量评估（基于关系数量和置信度）
        quality = self._assess_relation_quality(enriched_chunk.relations)

        return averaged_embedding, quality

    def _generate_domain_vector(
        self,
        enriched_chunk: EnrichedChunk
    ) -> tuple[np.ndarray, float]:
        """生成领域向量（1024维）⭐

        策略：
        1. 为每个领域标签生成多层次描述
        2. 编码所有领域
        3. 加权平均到1024维
        """
        if not enriched_chunk.domain_tags:
            # 无领域标签时返回零向量
            zero_vector = np.zeros(self.embedding_dim)
            return zero_vector, 0.0

        # 为每个领域生成描述
        domain_texts = []
        domain_weights = []

        for tag in enriched_chunk.domain_tags:
            # 多层次描述
            desc = tag.category.value
            if tag.subcategory:
                desc += f" - {tag.subcategory}"
            if tag.sub_subcategory:
                desc += f" - {tag.sub_subcategory}"

            # 添加关键词
            if tag.keywords:
                desc += f"（{', '.join(tag.keywords)}）"

            # 添加UNESCO分类
            if tag.unesco_domain:
                desc += f" [UNESCO: {tag.unesco_domain}]"

            domain_texts.append(desc)
            domain_weights.append(tag.confidence)

        # 编码所有领域
        domain_embeddings = self.domain_encoder.encode(domain_texts)  # [K, 1024]

        # 归一化每个向量 ⭐
        domain_embeddings = np.array([
            self._normalize_vector(emb) for emb in domain_embeddings
        ])

        # 加权平均
        weights = np.array(domain_weights) / np.sum(domain_weights)
        weighted_embedding = np.average(domain_embeddings, axis=0, weights=weights)  # [1024]

        # 最终归一化
        weighted_embedding = self._normalize_vector(weighted_embedding)

        # 质量评估（基于领域数量和置信度）
        quality = self._assess_domain_quality(enriched_chunk.domain_tags)

        return weighted_embedding, quality

    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """向量归一化 ⭐⭐⭐

        关键：统一尺度，避免某个向量主导

        L2归一化：v_norm = v / ||v||
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def _assess_text_quality(self, text: str) -> float:
        """评估文本质量

        基于文本长度和内容丰富度
        """
        # 长度因子（50-500字最优）
        length = len(text)
        if length < 50:
            length_score = length / 50.0
        elif length <= 500:
            length_score = 1.0
        else:
            length_score = max(0.5, 1.0 - (length - 500) / 1000.0)

        # 内容丰富度（不同字符数 / 总字符数）
        unique_chars = len(set(text))
        richness_score = min(1.0, unique_chars / (length * 0.3))

        return (length_score + richness_score) / 2.0

    def _assess_entity_quality(self, entities: List) -> float:
        """评估实体质量

        基于实体数量和平均置信度
        """
        if not entities:
            return 0.0

        # 数量因子（2-10个实体最优）
        count = len(entities)
        if count < 2:
            count_score = count / 2.0
        elif count <= 10:
            count_score = 1.0
        else:
            count_score = max(0.7, 1.0 - (count - 10) / 20.0)

        # 平均置信度
        avg_confidence = sum(e.confidence for e in entities) / len(entities)

        return (count_score + avg_confidence) / 2.0

    def _assess_relation_quality(self, relations: List) -> float:
        """评估关系质量

        基于关系数量和平均置信度
        """
        if not relations:
            return 0.0

        # 数量因子（1-5个关系最优）
        count = len(relations)
        if count <= 5:
            count_score = min(1.0, count / 3.0)
        else:
            count_score = max(0.7, 1.0 - (count - 5) / 10.0)

        # 平均置信度
        avg_confidence = sum(r.confidence for r in relations) / len(relations)

        return (count_score + avg_confidence) / 2.0

    def _assess_domain_quality(self, domain_tags: List) -> float:
        """评估领域质量

        基于领域数量和平均置信度
        """
        if not domain_tags:
            return 0.0

        # 数量因子（1-3个领域最优）
        count = len(domain_tags)
        count_score = min(1.0, count / 2.0)

        # 平均置信度
        avg_confidence = sum(t.confidence for t in domain_tags) / len(domain_tags)

        return (count_score + avg_confidence) / 2.0
