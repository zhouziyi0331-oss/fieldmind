"""
知识轨提取服务 - SBPACK 2.0标准

遵循规范：03-知识点轨生产规范.md
知识点是可判断、可解释、可检索、可比较、可引用的认知单元
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import hashlib
import json
import logging
from datetime import datetime

from app.models.sbpack import KnowledgeItem, ProducerSnapshot

logger = logging.getLogger(__name__)


class KnowledgeTrackExtractor:
    """
    知识轨提取器

    8种知识类型：
    - concept: 概念或术语定义
    - claim: 作者主张
    - principle: 具有适用条件的原则
    - mechanism: 因果或作用机制
    - reportedFact: 来源作者报告的事实性陈述
    - argument: 由前提到结论的论证
    - boundary: 适用限制
    - counterexample: 反例或失败模式
    """

    KNOWLEDGE_TYPES = [
        "concept", "claim", "principle", "mechanism",
        "reportedFact", "argument", "boundary", "counterexample"
    ]

    def __init__(self, db: Session):
        self.db = db
        self.producer_name = "knowledge_track_extractor"
        self.producer_version = "1.0.0"

    def extract(self, package_id: int,
                normalized_text: str,
                chunks: List[Dict[str, Any]],
                entities: List[Dict[str, Any]]) -> List[KnowledgeItem]:
        """
        从规范化文本中提取知识点

        参数:
            package_id: SBPACK包ID
            normalized_text: 规范化原文
            chunks: 文本块
            entities: 实体列表

        返回:
            知识点列表
        """
        logger.info(f"开始知识轨提取，package_id={package_id}")

        # 记录输入快照
        input_snapshot = self._create_input_snapshot(normalized_text, chunks, entities)

        knowledge_items = []

        # 1. 提取概念定义
        concepts = self._extract_concepts(chunks, entities)
        knowledge_items.extend(concepts)

        # 2. 提取主张
        claims = self._extract_claims(chunks)
        knowledge_items.extend(claims)

        # 3. 提取原则
        principles = self._extract_principles(chunks)
        knowledge_items.extend(principles)

        # 4. 提取机制
        mechanisms = self._extract_mechanisms(chunks, entities)
        knowledge_items.extend(mechanisms)

        # 5. 提取事实陈述
        facts = self._extract_reported_facts(chunks)
        knowledge_items.extend(facts)

        # 记录输出快照
        output_snapshot = self._create_output_snapshot(knowledge_items)

        # 保存生产者快照
        self._save_producer_snapshot(package_id, input_snapshot, output_snapshot)

        logger.info(f"知识轨提取完成，提取了 {len(knowledge_items)} 个知识点")

        return knowledge_items

    def _extract_concepts(self, chunks: List[Dict[str, Any]],
                         entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取概念定义"""
        concepts = []

        # 概念标识词
        CONCEPT_INDICATORS = [
            "是指", "指的是", "定义为", "称为", "所谓",
            "是一种", "是一个", "意思是",
            "defined as", "refers to", "means"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            # 检查是否包含概念标识词
            has_indicator = any(indicator in text for indicator in CONCEPT_INDICATORS)

            if has_indicator and len(text) > 20:
                # 从实体中找可能的概念名称
                concept_name = self._find_concept_name(text, entities, chunk_id)

                if concept_name:
                    concept = {
                        "knowledge_id": f"concept_{chunk_id}_{self._hash_short(concept_name)}",
                        "title": f"概念：{concept_name}",
                        "knowledge_type": "concept",
                        "statement": text[:200],  # 前200字符作为陈述
                        "explanation": text,
                        "why_matters": f"理解'{concept_name}'的定义对后续内容至关重要",
                        "scope": "本文档上下文",
                        "conditions": "",
                        "boundaries": "定义的适用范围限于本文档所述领域",
                        "counterexamples": "",
                        "evidence_refs": [{"chunk_id": chunk_id, "type": "definition"}],
                        "evidence_quotes": [{"quote": text[:500], "chunk_id": chunk_id}],
                        "source_certainty": "definitive",
                        "extraction_certainty": "direct",
                        "external_verification": "unverified",
                        "attribution": "source_author",
                        "inference_type": "explicit"
                    }
                    concepts.append(concept)

        return concepts

    def _extract_claims(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取作者主张"""
        claims = []

        # 主张标识词
        CLAIM_INDICATORS = [
            "我认为", "我们认为", "可以说", "应该", "必须",
            "关键在于", "重要的是", "核心是",
            "argue that", "believe that", "assert that"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            # 检查是否包含主张标识词
            has_indicator = any(indicator in text for indicator in CLAIM_INDICATORS)

            if has_indicator and len(text) > 30:
                claim = {
                    "knowledge_id": f"claim_{chunk_id}_{self._hash_short(text[:50])}",
                    "title": f"主张：{text[:50]}...",
                    "knowledge_type": "claim",
                    "statement": text[:300],
                    "explanation": text,
                    "why_matters": "这是作者的核心观点之一",
                    "scope": "适用于作者讨论的场景",
                    "conditions": "",
                    "boundaries": "这是作者的主张，不一定是客观事实",
                    "counterexamples": "",
                    "evidence_refs": [{"chunk_id": chunk_id, "type": "claim"}],
                    "evidence_quotes": [{"quote": text[:500], "chunk_id": chunk_id}],
                    "source_certainty": "reportedFact",
                    "extraction_certainty": "direct",
                    "external_verification": "unverified",
                    "attribution": "source_author",
                    "inference_type": "explicit"
                }
                claims.append(claim)

        return claims

    def _extract_principles(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取原则"""
        principles = []

        # 原则标识词
        PRINCIPLE_INDICATORS = [
            "原则", "法则", "定律", "规律", "准则",
            "如果...那么", "当...时", "在...条件下",
            "principle", "rule", "law", "guideline"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            has_indicator = any(indicator in text for indicator in PRINCIPLE_INDICATORS)

            if has_indicator and len(text) > 30:
                # 尝试提取条件
                conditions = self._extract_conditions(text)

                principle = {
                    "knowledge_id": f"principle_{chunk_id}_{self._hash_short(text[:50])}",
                    "title": f"原则：{text[:50]}...",
                    "knowledge_type": "principle",
                    "statement": text[:300],
                    "explanation": text,
                    "why_matters": "这条原则指导相关场景下的决策",
                    "scope": "特定条件下适用",
                    "conditions": conditions,
                    "boundaries": "超出条件范围时原则可能不适用",
                    "counterexamples": "",
                    "evidence_refs": [{"chunk_id": chunk_id, "type": "principle"}],
                    "evidence_quotes": [{"quote": text[:500], "chunk_id": chunk_id}],
                    "source_certainty": "definitive",
                    "extraction_certainty": "synthesized",
                    "external_verification": "unverified",
                    "attribution": "source_author",
                    "inference_type": "explicit"
                }
                principles.append(principle)

        return principles

    def _extract_mechanisms(self, chunks: List[Dict[str, Any]],
                           entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取因果机制"""
        mechanisms = []

        # 因果标识词
        CAUSAL_INDICATORS = [
            "导致", "引起", "造成", "产生", "带来",
            "因为", "由于", "原因是", "结果是",
            "causes", "leads to", "results in", "because"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            has_indicator = any(indicator in text for indicator in CAUSAL_INDICATORS)

            if has_indicator and len(text) > 40:
                mechanism = {
                    "knowledge_id": f"mechanism_{chunk_id}_{self._hash_short(text[:50])}",
                    "title": f"机制：{text[:50]}...",
                    "knowledge_type": "mechanism",
                    "statement": text[:300],
                    "explanation": text,
                    "why_matters": "理解这一因果机制有助于预测和干预",
                    "scope": "在特定条件下的因果关系",
                    "conditions": "需要满足特定前提条件",
                    "boundaries": "因果关系可能受其他因素调节",
                    "counterexamples": "",
                    "evidence_refs": [{"chunk_id": chunk_id, "type": "mechanism"}],
                    "evidence_quotes": [{"quote": text[:500], "chunk_id": chunk_id}],
                    "source_certainty": "reportedFact",
                    "extraction_certainty": "synthesized",
                    "external_verification": "unverified",
                    "attribution": "source_author",
                    "inference_type": "explicit"
                }
                mechanisms.append(mechanism)

        return mechanisms

    def _extract_reported_facts(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取事实陈述"""
        facts = []

        # 事实陈述通常包含具体数据、时间、地点
        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            # 简单启发式：包含数字或日期的陈述
            has_numbers = any(char.isdigit() for char in text)

            if has_numbers and len(text) > 20 and len(text) < 200:
                fact = {
                    "knowledge_id": f"fact_{chunk_id}_{self._hash_short(text[:50])}",
                    "title": f"事实：{text[:50]}...",
                    "knowledge_type": "reportedFact",
                    "statement": text,
                    "explanation": f"来源报告的事实性陈述：{text}",
                    "why_matters": "提供了具体的事实信息",
                    "scope": "来源作者报告的事实",
                    "conditions": "",
                    "boundaries": "这是来源报告的事实，需要外部核验",
                    "counterexamples": "",
                    "evidence_refs": [{"chunk_id": chunk_id, "type": "fact"}],
                    "evidence_quotes": [{"quote": text, "chunk_id": chunk_id}],
                    "source_certainty": "reportedFact",
                    "extraction_certainty": "direct",
                    "external_verification": "unverified",
                    "attribution": "source_author",
                    "inference_type": "explicit"
                }
                facts.append(fact)

        return facts

    def _find_concept_name(self, text: str, entities: List[Dict[str, Any]],
                          chunk_id: int) -> Optional[str]:
        """从文本和实体中查找概念名称"""
        # 在相同chunk中查找实体
        for entity in entities:
            if entity.get("chunk_id") == chunk_id:
                entity_name = entity.get("entity_name", "")
                if entity_name and entity_name in text:
                    return entity_name

        # 如果没找到实体，尝试从文本中提取（简单启发式）
        # 查找引号内的内容
        import re
        quotes = re.findall(r'[""](.*?)[""]', text)
        if quotes:
            return quotes[0]

        return None

    def _extract_conditions(self, text: str) -> str:
        """从文本中提取条件"""
        # 简单启发式：查找"如果"、"当"等词后的内容
        condition_keywords = ["如果", "当", "在...条件下", "假设", "前提是"]

        for keyword in condition_keywords:
            if keyword in text:
                # 找到关键词位置，提取后续内容
                idx = text.find(keyword)
                condition_text = text[idx:idx+100]
                return condition_text

        return "需要进一步明确前置条件"

    def _hash_short(self, text: str) -> str:
        """生成短哈希"""
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def _create_input_snapshot(self, normalized_text: str,
                              chunks: List[Dict[str, Any]],
                              entities: List[Dict[str, Any]]) -> str:
        """创建输入快照"""
        snapshot = {
            "normalized_text_length": len(normalized_text),
            "normalized_text_hash": hashlib.sha256(normalized_text.encode()).hexdigest(),
            "chunk_count": len(chunks),
            "entity_count": len(entities),
            "timestamp": datetime.utcnow().isoformat()
        }
        return json.dumps(snapshot, ensure_ascii=False)

    def _create_output_snapshot(self, knowledge_items: List[Dict[str, Any]]) -> str:
        """创建输出快照"""
        snapshot = {
            "knowledge_count": len(knowledge_items),
            "knowledge_types": {},
            "knowledge_ids": [k["knowledge_id"] for k in knowledge_items],
            "timestamp": datetime.utcnow().isoformat()
        }

        # 统计各类型数量
        for item in knowledge_items:
            k_type = item["knowledge_type"]
            snapshot["knowledge_types"][k_type] = snapshot["knowledge_types"].get(k_type, 0) + 1

        return json.dumps(snapshot, ensure_ascii=False)

    def _save_producer_snapshot(self, package_id: int,
                                input_snapshot: str,
                                output_snapshot: str):
        """保存生产者快照"""
        combined = input_snapshot + output_snapshot
        snapshot_hash = hashlib.sha256(combined.encode()).hexdigest()

        snapshot = ProducerSnapshot(
            package_id=package_id,
            role="knowledge_track",
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
            model_name=self.producer_name,
            model_version=self.producer_version,
            snapshot_hash=snapshot_hash
        )

        self.db.add(snapshot)
        self.db.commit()

        logger.info(f"生产者快照已保存，hash={snapshot_hash[:16]}...")
