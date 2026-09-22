"""
知识蒸馏器

独立知识轨生产线，从规范化源文档提取结构化知识点
"""

import uuid
from typing import List, Dict, Any
from datetime import datetime

from app.distillation.types import (
    KnowledgeUnit,
    KnowledgeType,
    EvidenceAnchor,
    SourceCertainty,
    ClaimAttribution,
    NormalizedSource,
    KnowledgeFreezeManifest,
)


class KnowledgeDistiller:
    """生产者角色：知识蒸馏器"""

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLM 服务实例（用于调用 Claude）
        """
        self.llm_service = llm_service
        self.producer_id = "producer:knowledge-distiller"
        self.version = "fieldmind-knowledge-distiller-1.0.0"

    async def extract_knowledge(
        self, normalized_source: NormalizedSource
    ) -> List[KnowledgeUnit]:
        """
        提取知识点

        处理流程：
        1. 逐块扫描识别候选知识点
        2. 为每个候选绑定证据锚点
        3. 提取边界和反例
        4. 去重与合并（同一概念多处出现）
        5. 质量检查（证据可解析、边界明确）
        6. 生成知识单元

        注意：不从技能反向造知识 — 知识轨独立生产
        """
        candidates = []

        # 逐章节提取
        for chapter in normalized_source.chapters:
            # 提取不同类型的知识点
            concepts = await self._extract_concepts(chapter, normalized_source)
            principles = await self._extract_principles(chapter, normalized_source)
            mechanisms = await self._extract_mechanisms(chapter, normalized_source)
            arguments = await self._extract_arguments(chapter, normalized_source)
            boundaries = await self._extract_boundaries(chapter, normalized_source)

            candidates.extend(
                concepts + principles + mechanisms + arguments + boundaries
            )

        # 去重合并
        merged = self._merge_duplicates(candidates)

        # 证据验证
        verified = [
            ku for ku in merged if self._verify_evidence(ku, normalized_source)
        ]

        return verified

    async def _extract_concepts(
        self, chapter, normalized_source: NormalizedSource
    ) -> List[KnowledgeUnit]:
        """提取概念定义"""
        if not self.llm_service:
            return []

        prompt = f"""
从以下文本中提取关键概念定义。

章节：{chapter.label}

文本：
{chapter.content[:5000]}

要求：
1. 只提取作者明确定义的概念
2. 每个概念需要包含：标题、陈述、解释、重要性
3. 必须提供原文引用（≤150字）
4. 标注概念的适用范围和边界

输出 JSON 数组格式：
[
  {{
    "title": "概念名称",
    "statement": "概念定义",
    "explanation": "详细解释",
    "why_it_matters": "为什么重要",
    "scope": "适用范围",
    "conditions": ["成立条件1", "成立条件2"],
    "boundaries": ["边界限制1", "边界限制2"],
    "counterexamples": ["反例1"],
    "quote": "原文引用",
    "quote_context": "引用上下文，用于定位字节位置"
  }}
]
"""

        response = await self.llm_service.generate(prompt, response_format="json")
        concepts_data = response.get("concepts", [])

        knowledge_units = []
        for concept_data in concepts_data:
            # 创建证据锚点
            evidence_anchor = self._create_evidence_anchor(
                concept_data["quote"],
                concept_data.get("quote_context", ""),
                chapter,
                normalized_source,
            )

            if evidence_anchor:
                ku = KnowledgeUnit(
                    id=f"ku-{uuid.uuid4().hex[:8]}",
                    type=KnowledgeType.CONCEPT,
                    title=concept_data["title"],
                    statement=concept_data["statement"],
                    explanation=concept_data["explanation"],
                    why_it_matters=concept_data["why_it_matters"],
                    scope=concept_data["scope"],
                    conditions=concept_data.get("conditions", []),
                    boundaries=concept_data.get("boundaries", []),
                    counterexamples=concept_data.get("counterexamples", []),
                    evidence_anchors=[evidence_anchor],
                    evidence_route="single-anchor",
                    source_certainty=SourceCertainty.EXPLICIT,
                    claim_attribution=ClaimAttribution.AUTHOR_CLAIM,
                    extraction_certainty=0.9,
                    producer_id=self.producer_id,
                    generation_id=normalized_source.generation_id,
                )
                knowledge_units.append(ku)

        return knowledge_units

    async def _extract_principles(
        self, chapter, normalized_source: NormalizedSource
    ) -> List[KnowledgeUnit]:
        """提取原则"""
        if not self.llm_service:
            return []

        prompt = f"""
从以下文本中提取作者提出的原则。

章节：{chapter.label}

文本：
{chapter.content[:5000]}

要求：
1. 原则必须有明确的适用条件
2. 需要双独立证据或连续论证
3. 标注原则的边界和反例
4. 提供原文引用

输出 JSON 数组。
"""

        response = await self.llm_service.generate(prompt, response_format="json")
        principles_data = response.get("principles", [])

        knowledge_units = []
        for principle_data in principles_data:
            # 原则需要双证据
            evidence_anchors = []
            for quote_info in principle_data.get("quotes", [])[:2]:
                anchor = self._create_evidence_anchor(
                    quote_info["quote"],
                    quote_info.get("context", ""),
                    chapter,
                    normalized_source,
                )
                if anchor:
                    evidence_anchors.append(anchor)

            if len(evidence_anchors) >= 1:
                ku = KnowledgeUnit(
                    id=f"ku-{uuid.uuid4().hex[:8]}",
                    type=KnowledgeType.PRINCIPLE,
                    title=principle_data["title"],
                    statement=principle_data["statement"],
                    explanation=principle_data["explanation"],
                    why_it_matters=principle_data["why_it_matters"],
                    scope=principle_data["scope"],
                    conditions=principle_data.get("conditions", []),
                    boundaries=principle_data.get("boundaries", []),
                    counterexamples=principle_data.get("counterexamples", []),
                    evidence_anchors=evidence_anchors,
                    evidence_route=(
                        "dual-independent"
                        if len(evidence_anchors) >= 2
                        else "continuous-exposition"
                    ),
                    source_certainty=SourceCertainty.EXPLICIT,
                    claim_attribution=ClaimAttribution.AUTHOR_CLAIM,
                    extraction_certainty=0.85,
                    producer_id=self.producer_id,
                    generation_id=normalized_source.generation_id,
                )
                knowledge_units.append(ku)

        return knowledge_units

    async def _extract_mechanisms(
        self, chapter, normalized_source: NormalizedSource
    ) -> List[KnowledgeUnit]:
        """提取因果机制"""
        if not self.llm_service:
            return []

        prompt = f"""
从以下文本中提取因果机制或作用机制。

章节：{chapter.label}

文本：
{chapter.content[:5000]}

要求：
1. 机制必须包含因果关系
2. 需要解释"为什么"
3. 提供证据和边界

输出 JSON 数组。
"""

        response = await self.llm_service.generate(prompt, response_format="json")
        mechanisms_data = response.get("mechanisms", [])

        knowledge_units = []
        for mechanism_data in mechanisms_data:
            evidence_anchor = self._create_evidence_anchor(
                mechanism_data["quote"],
                mechanism_data.get("quote_context", ""),
                chapter,
                normalized_source,
            )

            if evidence_anchor:
                ku = KnowledgeUnit(
                    id=f"ku-{uuid.uuid4().hex[:8]}",
                    type=KnowledgeType.MECHANISM,
                    title=mechanism_data["title"],
                    statement=mechanism_data["statement"],
                    explanation=mechanism_data["explanation"],
                    why_it_matters=mechanism_data["why_it_matters"],
                    scope=mechanism_data["scope"],
                    conditions=mechanism_data.get("conditions", []),
                    boundaries=mechanism_data.get("boundaries", []),
                    counterexamples=mechanism_data.get("counterexamples", []),
                    evidence_anchors=[evidence_anchor],
                    evidence_route="single-anchor",
                    source_certainty=SourceCertainty.EXPLICIT,
                    claim_attribution=ClaimAttribution.AUTHOR_CLAIM,
                    extraction_certainty=0.8,
                    producer_id=self.producer_id,
                    generation_id=normalized_source.generation_id,
                )
                knowledge_units.append(ku)

        return knowledge_units

    async def _extract_arguments(
        self, chapter, normalized_source: NormalizedSource
    ) -> List[KnowledgeUnit]:
        """提取论证"""
        # TODO: 实现论证提取
        return []

    async def _extract_boundaries(
        self, chapter, normalized_source: NormalizedSource
    ) -> List[KnowledgeUnit]:
        """提取边界限制"""
        # TODO: 实现边界提取
        return []

    def _create_evidence_anchor(
        self,
        quote: str,
        context: str,
        chapter,
        normalized_source: NormalizedSource,
    ) -> EvidenceAnchor | None:
        """
        创建证据锚点

        通过在章节内容中查找 quote，定位 UTF-8 字节位置
        """
        try:
            # 在章节内容中查找引用
            quote_clean = quote.strip()
            chapter_content = chapter.content

            # 尝试直接匹配
            start_pos = chapter_content.find(quote_clean)

            if start_pos == -1:
                # 尝试模糊匹配（去除标点和空格）
                import re

                quote_normalized = re.sub(r"[^\w一-鿿]", "", quote_clean)
                content_normalized = re.sub(
                    r"[^\w一-鿿]", "", chapter_content
                )

                start_pos_normalized = content_normalized.find(quote_normalized)
                if start_pos_normalized == -1:
                    return None

                # 映射回原始位置（简化实现）
                start_pos = start_pos_normalized

            # 计算全局字节偏移
            chapter_start = chapter.byte_offset_start
            quote_bytes_before = chapter_content[:start_pos].encode("utf-8")
            quote_bytes = quote_clean.encode("utf-8")

            byte_start = chapter_start + len(quote_bytes_before)
            byte_end = byte_start + len(quote_bytes)

            return EvidenceAnchor(
                chapter_id=chapter.chapter_id,
                quote=quote_clean,
                byte_start=byte_start,
                byte_end=byte_end,
                page=chapter.source_page,
                timestamp=chapter.timestamp_start,
            )

        except Exception as e:
            print(f"Failed to create evidence anchor: {e}")
            return None

    def _merge_duplicates(
        self, candidates: List[KnowledgeUnit]
    ) -> List[KnowledgeUnit]:
        """去重与合并"""
        # 使用标题相似度合并
        merged = []
        seen_titles = set()

        for candidate in candidates:
            title_normalized = candidate.title.lower().strip()

            if title_normalized not in seen_titles:
                merged.append(candidate)
                seen_titles.add(title_normalized)
            else:
                # 合并证据锚点
                for existing in merged:
                    if existing.title.lower().strip() == title_normalized:
                        existing.evidence_anchors.extend(candidate.evidence_anchors)
                        break

        return merged

    def _verify_evidence(
        self, ku: KnowledgeUnit, source: NormalizedSource
    ) -> bool:
        """验证证据锚点"""
        for anchor in ku.evidence_anchors:
            if not anchor.verify_quote(source.full_text):
                return False

        # 检查证据路线要求
        if ku.type in [KnowledgeType.PRINCIPLE, KnowledgeType.MECHANISM]:
            if ku.evidence_route == "dual-independent":
                return len(ku.evidence_anchors) >= 2
            elif ku.evidence_route == "continuous-exposition":
                return (
                    len(ku.evidence_anchors) >= 1
                    and len(ku.evidence_anchors[0].quote) >= 200
                )

        return True

    def freeze_knowledge_track(
        self, knowledge_units: List[KnowledgeUnit], source: NormalizedSource
    ) -> KnowledgeFreezeManifest:
        """冻结知识轨"""
        import hashlib

        frozen_units = []
        for ku in knowledge_units:
            # 计算知识单元的 SHA-256
            content = f"{ku.title}|{ku.statement}|{ku.explanation}"
            sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

            frozen_units.append({"id": ku.id, "sha256": f"sha256:{sha256}"})

        return KnowledgeFreezeManifest(
            generation_id=source.generation_id,
            source_sha256=source.full_text_sha256,
            knowledge_units=frozen_units,
            frozen_at=datetime.utcnow().isoformat(),
            distiller_version=self.version,
            distiller_model="claude-opus-5",
        )
