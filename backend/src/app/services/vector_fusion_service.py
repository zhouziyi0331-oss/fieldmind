"""
向量融合服务
关键：多向量协同增强，不相互打架
策略：门控融合 + 相关性对齐 + 质量验证
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from app.models.enriched_chunk import MultiVectorResult, FusedVectorResult

logger = logging.getLogger(__name__)


class VectorFusionService:
    """向量融合服务 - 协同增强而非冲突 ⭐⭐⭐"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.embedding_dim = 1024
        logger.info("向量融合服务初始化完成")

    def fuse_vectors(
        self,
        multi_vector: MultiVectorResult,
        strategy: str = "gated_concat"  # "concat" | "weighted_concat" | "gated_concat" | "attention_concat"
    ) -> FusedVectorResult:
        """融合多个向量 - 协同增强

        Args:
            multi_vector: 多向量结果
            strategy: 融合策略
                - concat: 直接拼接（4096维）
                - weighted_concat: 加权拼接（4096维）
                - gated_concat: 门控融合拼接（4096维）⭐ 推荐
                - attention_concat: 注意力融合拼接（4096维）

        Returns:
            融合向量结果
        """
        if strategy == "concat":
            return self._strategy_concat(multi_vector)
        elif strategy == "weighted_concat":
            return self._strategy_weighted_concat(multi_vector)
        elif strategy == "gated_concat":
            return self._strategy_gated_concat(multi_vector)
        elif strategy == "attention_concat":
            return self._strategy_attention_concat(multi_vector)
        else:
            raise ValueError(f"Unknown fusion strategy: {strategy}")

    def _strategy_concat(
        self,
        multi_vector: MultiVectorResult
    ) -> FusedVectorResult:
        """策略1：直接拼接 ⭐

        [text || entity || relation || domain]
        = [1024 + 1024 + 1024 + 1024] = 4096维

        优点：保留所有信息，不丢失
        缺点：没有考虑向量间的协同关系
        """
        # 转换为numpy数组
        text_emb = np.array(multi_vector.text_embedding)
        entity_emb = np.array(multi_vector.entity_embedding)
        relation_emb = np.array(multi_vector.relation_embedding)
        domain_emb = np.array(multi_vector.domain_embedding)

        # 直接拼接
        fused = np.concatenate([text_emb, entity_emb, relation_emb, domain_emb])  # [4096]

        # 质量评估
        coherence, enhancement = self._assess_fusion_quality(
            text_emb, entity_emb, relation_emb, domain_emb,
            fused, weights=None
        )

        logger.info(f"直接拼接融合完成 - 一致性: {coherence:.3f}, 增强度: {enhancement:.3f}")

        return FusedVectorResult(
            fused_embedding=fused.tolist(),
            strategy="concat",
            dimensions=4096,
            components={
                "text": (0, 1024),
                "entity": (1024, 2048),
                "relation": (2048, 3072),
                "domain": (3072, 4096)
            },
            coherence_score=coherence,
            enhancement_score=enhancement,
            quality_passed=(coherence > 0.3 and enhancement > 0.5)
        )

    def _strategy_weighted_concat(
        self,
        multi_vector: MultiVectorResult
    ) -> FusedVectorResult:
        """策略2：加权拼接 ⭐⭐

        对每个向量加权后拼接：
        [w1*text || w2*entity || w3*relation || w4*domain]

        权重根据质量动态调整 ⭐
        """
        # 转换为numpy数组
        text_emb = np.array(multi_vector.text_embedding)
        entity_emb = np.array(multi_vector.entity_embedding)
        relation_emb = np.array(multi_vector.relation_embedding)
        domain_emb = np.array(multi_vector.domain_embedding)

        # 动态计算权重（基于质量分数）⭐
        quality_scores = multi_vector.quality_scores
        weights = self._calculate_dynamic_weights(quality_scores)

        logger.info(f"动态权重: 文本={weights['text']:.2f}, 实体={weights['entity']:.2f}, "
                   f"关系={weights['relation']:.2f}, 领域={weights['domain']:.2f}")

        # 加权
        weighted_text = text_emb * weights["text"]
        weighted_entity = entity_emb * weights["entity"]
        weighted_relation = relation_emb * weights["relation"]
        weighted_domain = domain_emb * weights["domain"]

        # 拼接
        fused = np.concatenate([
            weighted_text,
            weighted_entity,
            weighted_relation,
            weighted_domain
        ])  # [4096]

        # 质量评估
        coherence, enhancement = self._assess_fusion_quality(
            text_emb, entity_emb, relation_emb, domain_emb,
            fused, weights=weights
        )

        logger.info(f"加权拼接融合完成 - 一致性: {coherence:.3f}, 增强度: {enhancement:.3f}")

        return FusedVectorResult(
            fused_embedding=fused.tolist(),
            strategy="weighted_concat",
            dimensions=4096,
            weights=weights,
            components={
                "text": (0, 1024),
                "entity": (1024, 2048),
                "relation": (2048, 3072),
                "domain": (3072, 4096)
            },
            coherence_score=coherence,
            enhancement_score=enhancement,
            quality_passed=(coherence > 0.4 and enhancement > 0.6)
        )

    def _strategy_gated_concat(
        self,
        multi_vector: MultiVectorResult
    ) -> FusedVectorResult:
        """策略3：门控融合拼接 ⭐⭐⭐ 推荐

        使用门控机制动态调整每个维度的贡献
        强的向量贡献更多，弱的向量被抑制

        门控公式：
        gate = sigmoid(quality_score)
        gated_vector = vector * gate

        这样可以：
        1. 强的向量（高质量）→ gate接近1 → 完全保留
        2. 弱的向量（低质量）→ gate接近0 → 被抑制
        3. 避免低质量向量污染高质量向量 ⭐
        """
        # 转换为numpy数组
        text_emb = np.array(multi_vector.text_embedding)
        entity_emb = np.array(multi_vector.entity_embedding)
        relation_emb = np.array(multi_vector.relation_embedding)
        domain_emb = np.array(multi_vector.domain_embedding)

        # 计算门控值（基于质量分数）⭐
        quality_scores = multi_vector.quality_scores
        gates = self._calculate_gates(quality_scores)

        logger.info(f"门控值: 文本={gates['text']:.3f}, 实体={gates['entity']:.3f}, "
                   f"关系={gates['relation']:.3f}, 领域={gates['domain']:.3f}")

        # 门控调制 ⭐
        gated_text = text_emb * gates["text"]
        gated_entity = entity_emb * gates["entity"]
        gated_relation = relation_emb * gates["relation"]
        gated_domain = domain_emb * gates["domain"]

        # 相关性对齐 ⭐⭐
        # 计算向量间的余弦相似度，增强相关的部分
        aligned_text, aligned_entity, aligned_relation, aligned_domain = self._align_vectors(
            gated_text, gated_entity, gated_relation, gated_domain
        )

        # 拼接
        fused = np.concatenate([
            aligned_text,
            aligned_entity,
            aligned_relation,
            aligned_domain
        ])  # [4096]

        # 质量评估
        coherence, enhancement = self._assess_fusion_quality(
            text_emb, entity_emb, relation_emb, domain_emb,
            fused, weights=gates
        )

        logger.info(f"门控融合拼接完成 - 一致性: {coherence:.3f}, 增强度: {enhancement:.3f}")

        return FusedVectorResult(
            fused_embedding=fused.tolist(),
            strategy="gated_concat",
            dimensions=4096,
            weights=gates,
            components={
                "text": (0, 1024),
                "entity": (1024, 2048),
                "relation": (2048, 3072),
                "domain": (3072, 4096)
            },
            coherence_score=coherence,
            enhancement_score=enhancement,
            quality_passed=(coherence > 0.5 and enhancement > 0.7)
        )

    def _strategy_attention_concat(
        self,
        multi_vector: MultiVectorResult
    ) -> FusedVectorResult:
        """策略4：注意力融合 + 拼接 ⭐⭐⭐

        步骤：
        1. 将4个向量作为序列：[text, entity, relation, domain]
        2. 使用自注意力机制计算相互关系
        3. 得到4个注意力加权的向量
        4. 拼接

        优点：向量之间相互感知，协同增强
        缺点：计算复杂度稍高
        """
        # 转换为numpy数组
        text_emb = np.array(multi_vector.text_embedding)
        entity_emb = np.array(multi_vector.entity_embedding)
        relation_emb = np.array(multi_vector.relation_embedding)
        domain_emb = np.array(multi_vector.domain_embedding)

        # 堆叠为序列
        vector_sequence = np.stack([text_emb, entity_emb, relation_emb, domain_emb])  # [4, 1024]

        # 自注意力 ⭐⭐
        # Q = K = V = vector_sequence
        # Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
        d_k = 1024
        scores = np.dot(vector_sequence, vector_sequence.T) / np.sqrt(d_k)  # [4, 4]

        # 质量加权的注意力 ⭐
        # 高质量的向量应该有更高的注意力权重
        quality_scores = multi_vector.quality_scores
        quality_weights = np.array([
            quality_scores.get("text", 0.5),
            quality_scores.get("entity", 0.5),
            quality_scores.get("relation", 0.5),
            quality_scores.get("domain", 0.5)
        ]).reshape(-1, 1)  # [4, 1]

        # 加权注意力分数
        weighted_scores = scores * quality_weights  # [4, 4]

        attention_weights = self._softmax(weighted_scores, axis=-1)  # [4, 4]

        logger.info(f"注意力权重矩阵:\n{attention_weights}")

        # 应用注意力
        attended_vectors = np.dot(attention_weights, vector_sequence)  # [4, 1024]

        # 拼接
        fused = attended_vectors.flatten()  # [4096]

        # 质量评估
        coherence, enhancement = self._assess_fusion_quality(
            text_emb, entity_emb, relation_emb, domain_emb,
            fused, weights=None
        )

        logger.info(f"注意力融合拼接完成 - 一致性: {coherence:.3f}, 增强度: {enhancement:.3f}")

        return FusedVectorResult(
            fused_embedding=fused.tolist(),
            strategy="attention_concat",
            dimensions=4096,
            attention_weights=attention_weights.tolist(),
            components={
                "text": (0, 1024),
                "entity": (1024, 2048),
                "relation": (2048, 3072),
                "domain": (3072, 4096)
            },
            coherence_score=coherence,
            enhancement_score=enhancement,
            quality_passed=(coherence > 0.5 and enhancement > 0.75)
        )

    def _calculate_dynamic_weights(
        self,
        quality_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """动态计算权重（基于质量分数）⭐

        策略：
        - 基础权重：文本=0.4, 实体=0.3, 关系=0.2, 领域=0.1
        - 质量调整：高质量的向量权重增加，低质量的权重减少
        """
        # 基础权重（田野调查场景）
        base_weights = {
            "text": 0.4,      # 文本最重要
            "entity": 0.3,    # 实体次之（关注遗产实体）
            "relation": 0.2,  # 关系也重要（组织架构、支持关系）
            "domain": 0.1     # 领域作为补充
        }

        # 质量调整
        adjusted_weights = {}
        for key, base_weight in base_weights.items():
            quality = quality_scores.get(key, 0.5)
            # 质量越高，权重增加越多
            adjusted_weights[key] = base_weight * (0.5 + quality)

        # 归一化
        total = sum(adjusted_weights.values())
        normalized_weights = {k: v / total for k, v in adjusted_weights.items()}

        return normalized_weights

    def _calculate_gates(
        self,
        quality_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """计算门控值（基于质量分数）⭐

        门控函数：gate = sigmoid(α * (quality - threshold))
        - quality > threshold → gate接近1（完全保留）
        - quality < threshold → gate接近0（被抑制）
        """
        threshold = 0.5  # 质量阈值
        alpha = 10.0     # 陡峭度

        gates = {}
        for key, quality in quality_scores.items():
            # Sigmoid门控
            x = alpha * (quality - threshold)
            gate = 1.0 / (1.0 + np.exp(-x))
            gates[key] = gate

        return gates

    def _align_vectors(
        self,
        text_emb: np.ndarray,
        entity_emb: np.ndarray,
        relation_emb: np.ndarray,
        domain_emb: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """相关性对齐 ⭐⭐

        策略：
        1. 计算向量间的余弦相似度
        2. 相似度高的向量互相增强
        3. 相似度低的向量保持独立（避免冲突）
        """
        vectors = [text_emb, entity_emb, relation_emb, domain_emb]
        aligned_vectors = []

        for i, vec in enumerate(vectors):
            # 计算与其他向量的相似度
            similarities = []
            for j, other_vec in enumerate(vectors):
                if i != j:
                    sim = self._cosine_similarity(vec, other_vec)
                    similarities.append((j, sim))

            # 如果有高相似度的向量，增强该方向
            aligned_vec = vec.copy()
            for j, sim in similarities:
                if sim > 0.5:  # 相似度阈值
                    # 增强相似方向
                    aligned_vec += sim * 0.1 * vectors[j]

            # 归一化
            aligned_vec = aligned_vec / np.linalg.norm(aligned_vec)
            aligned_vectors.append(aligned_vec)

        return tuple(aligned_vectors)

    def _assess_fusion_quality(
        self,
        text_emb: np.ndarray,
        entity_emb: np.ndarray,
        relation_emb: np.ndarray,
        domain_emb: np.ndarray,
        fused: np.ndarray,
        weights: Optional[Dict[str, float]]
    ) -> Tuple[float, float]:
        """评估融合质量 ⭐⭐⭐

        Returns:
            (coherence_score, enhancement_score)
            - coherence_score: 一致性分数（向量不冲突）
            - enhancement_score: 增强分数（向量互补）
        """
        # 1. 一致性分数：向量间的平均余弦相似度
        vectors = [text_emb, entity_emb, relation_emb, domain_emb]
        similarities = []
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                sim = self._cosine_similarity(vectors[i], vectors[j])
                similarities.append(sim)

        coherence_score = np.mean(similarities)

        # 2. 增强分数：融合向量与原始向量的相关性
        # 融合向量应该与所有原始向量都有正相关
        fused_text = fused[:1024]
        fused_entity = fused[1024:2048]
        fused_relation = fused[2048:3072]
        fused_domain = fused[3072:4096]

        correlations = [
            self._cosine_similarity(fused_text, text_emb),
            self._cosine_similarity(fused_entity, entity_emb),
            self._cosine_similarity(fused_relation, relation_emb),
            self._cosine_similarity(fused_domain, domain_emb),
        ]

        # 加权平均（如果有权重）
        if weights:
            weight_list = [
                weights.get("text", 0.25),
                weights.get("entity", 0.25),
                weights.get("relation", 0.25),
                weights.get("domain", 0.25),
            ]
            enhancement_score = np.average(correlations, weights=weight_list)
        else:
            enhancement_score = np.mean(correlations)

        return coherence_score, enhancement_score

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    @staticmethod
    def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Softmax函数"""
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
