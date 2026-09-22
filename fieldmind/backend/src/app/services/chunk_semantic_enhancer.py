"""
Chunk 语义增强器 - Chunk Semantic Enhancer

为每个 chunk 添加丰富的语义上下文
包括：章节标题、关键实体、领域标签、前后摘要等

核心理念：
- Chunk 不应该是孤立的文本片段
- 应该知道自己"在哪"、"谈什么"、"前后是什么"
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChunkSemanticEnhancer:
    """
    Chunk 语义增强器

    为 chunk 添加以下上下文：
    1. 文档结构上下文（所属章节、层级）
    2. 关键实体（人名、地名、事物）
    3. 领域标签（民俗、饮食、节日等）
    4. 前后 chunk 摘要
    5. 时空上下文（时间、地点）
    """

    def __init__(self):
        self.entity_extractor = None
        self.domain_classifier = None
        logger.info("✅ Chunk 语义增强器初始化完成")

    def enhance_chunk(
        self,
        chunk: Dict[str, Any],
        document_context: Dict[str, Any],
        prev_chunk: Optional[Dict[str, Any]] = None,
        next_chunk: Optional[Dict[str, Any]] = None,
        entities: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        为 chunk 添加语义上下文

        Args:
            chunk: 原始 chunk
            document_context: 文档上下文（从 DocumentStructureAnalyzer 获取）
            prev_chunk: 前一个 chunk
            next_chunk: 后一个 chunk
            entities: 已提取的实体列表

        Returns:
            增强后的 chunk
        """
        chunk_text = chunk.get("text", "")
        chunk_metadata = chunk.get("metadata", {})

        # 初始化语义上下文
        semantic_context = {
            # 文档结构上下文
            "chapter": None,
            "section": None,
            "subsection": None,
            "parent_chain": [],

            # 实体上下文
            "key_entities": [],
            "entity_summary": "",

            # 领域标签
            "domain_tags": [],
            "primary_domain": None,

            # 前后文摘要
            "prev_chunk_summary": None,
            "next_chunk_summary": None,

            # 时空上下文
            "temporal_context": None,
            "spatial_context": None,

            # 其他
            "chunk_role": "content",  # content, introduction, conclusion, transition
            "confidence": 0.0
        }

        # 1. 添加文档结构上下文
        if document_context:
            semantic_context["chapter"] = document_context.get("chapter")
            semantic_context["section"] = document_context.get("section")
            semantic_context["subsection"] = document_context.get("subsection")
            semantic_context["parent_chain"] = document_context.get("parent_chain", [])

        # 2. 添加实体上下文
        if entities:
            semantic_context["key_entities"] = self._extract_key_entities(entities, chunk_text)
            semantic_context["entity_summary"] = self._generate_entity_summary(
                semantic_context["key_entities"]
            )

        # 3. 推断领域标签
        semantic_context["domain_tags"] = self._infer_domain_tags(chunk_text, entities or [])
        if semantic_context["domain_tags"]:
            semantic_context["primary_domain"] = semantic_context["domain_tags"][0]

        # 4. 生成前后文摘要
        if prev_chunk:
            semantic_context["prev_chunk_summary"] = self._generate_summary(
                prev_chunk.get("text", "")
            )

        if next_chunk:
            semantic_context["next_chunk_summary"] = self._generate_summary(
                next_chunk.get("text", "")
            )

        # 5. 提取时空上下文
        semantic_context["temporal_context"] = self._extract_temporal_context(chunk_text)
        semantic_context["spatial_context"] = self._extract_spatial_context(chunk_text, entities or [])

        # 6. 推断 chunk 角色
        semantic_context["chunk_role"] = self._infer_chunk_role(
            chunk_text,
            chunk_metadata,
            prev_chunk,
            next_chunk
        )

        # 7. 计算置信度
        semantic_context["confidence"] = self._calculate_confidence(semantic_context)

        # 将语义上下文添加到 chunk
        enhanced_chunk = chunk.copy()
        enhanced_chunk["semantic_context"] = semantic_context
        enhanced_chunk["enhanced_at"] = datetime.utcnow().isoformat()

        return enhanced_chunk

    def _extract_key_entities(
        self,
        entities: List[Dict[str, Any]],
        chunk_text: str
    ) -> List[Dict[str, Any]]:
        """提取关键实体（在 chunk 中出现的）"""
        key_entities = []

        for entity in entities:
            entity_name = entity.get("name", "")
            entity_type = entity.get("entity_type", "")

            # 检查实体是否在 chunk 中
            if entity_name and entity_name in chunk_text:
                key_entities.append({
                    "name": entity_name,
                    "type": entity_type,
                    "confidence": entity.get("confidence", 0.0)
                })

        # 按置信度排序，取前5个
        key_entities.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return key_entities[:5]

    def _generate_entity_summary(self, entities: List[Dict[str, Any]]) -> str:
        """生成实体摘要"""
        if not entities:
            return ""

        # 按类型分组
        by_type = {}
        for entity in entities:
            entity_type = entity["type"]
            entity_name = entity["name"]

            if entity_type not in by_type:
                by_type[entity_type] = []

            by_type[entity_type].append(entity_name)

        # 生成摘要
        parts = []
        type_names = {
            "Person": "人物",
            "Location": "地点",
            "CulturalAsset": "文化资产",
            "Event": "事件",
            "Organization": "组织",
            "Policy": "政策"
        }

        for entity_type, names in by_type.items():
            type_label = type_names.get(entity_type, entity_type)
            parts.append(f"{type_label}：{', '.join(names)}")

        return "；".join(parts)

    def _infer_domain_tags(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[str]:
        """推断领域标签"""
        tags = []

        # 基于关键词推断
        keyword_domains = {
            "民俗": ["习俗", "传统", "风俗", "仪式", "祭祀", "节日"],
            "饮食": ["美食", "菜", "吃", "食物", "烹饪", "做法"],
            "节庆": ["节", "庆", "活动", "聚会", "庆典"],
            "建筑": ["房屋", "建筑", "吊脚楼", "祠堂", "寨门"],
            "服饰": ["衣服", "服装", "穿着", "刺绣", "织布"],
            "口述史": ["说", "讲", "回忆", "访谈", "记得"],
            "非遗": ["非遗", "传承", "技艺", "手艺", "工艺"],
            "生计": ["生活", "收入", "工作", "种植", "养殖"],
            "社会组织": ["村委", "组织", "协会", "合作社", "理事会"]
        }

        text_lower = text.lower()

        for domain, keywords in keyword_domains.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(domain)

        # 基于实体类型推断
        if entities:
            entity_types = [e.get("entity_type") for e in entities]

            if "CulturalAsset" in entity_types:
                if "非遗" not in tags:
                    tags.append("非遗")

            if "Event" in entity_types:
                if "节庆" not in tags:
                    tags.append("节庆")

        # 去重并限制数量
        tags = list(set(tags))
        return tags[:3]

    def _generate_summary(self, text: str, max_length: int = 50) -> str:
        """生成文本摘要（简单版本）"""
        if not text:
            return ""

        # 简单截取前N个字符
        text = text.strip()

        if len(text) <= max_length:
            return text

        # 尝试在句子边界截断
        truncated = text[:max_length]
        last_period = max(
            truncated.rfind("。"),
            truncated.rfind("！"),
            truncated.rfind("？"),
            truncated.rfind(".")
        )

        if last_period > max_length // 2:
            return truncated[:last_period + 1]
        else:
            return truncated + "..."

    def _extract_temporal_context(self, text: str) -> Optional[str]:
        """提取时间上下文"""
        import re

        # 时间模式
        temporal_patterns = [
            r'(\d{4})年',
            r'(春节|端午|中秋|国庆|五一)',
            r'(春天|夏天|秋天|冬天)',
            r'(早上|中午|下午|晚上|夜里)',
            r'(过去|现在|以前|当时|那时候)'
        ]

        for pattern in temporal_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_spatial_context(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> Optional[str]:
        """提取空间上下文"""
        # 优先从实体中提取地点
        locations = [
            e["name"] for e in entities
            if e.get("entity_type") == "Location"
        ]

        if locations:
            return locations[0]

        # 使用关键词
        import re
        location_patterns = [
            r'([一-龥]{2,8})(村|寨|镇|乡|县|市)',
            r'在([一-龥]{2,10})'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.lastindex >= 1 else match.group(0)

        return None

    def _infer_chunk_role(
        self,
        text: str,
        metadata: Dict[str, Any],
        prev_chunk: Optional[Dict[str, Any]],
        next_chunk: Optional[Dict[str, Any]]
    ) -> str:
        """推断 chunk 的角色"""
        text_lower = text.lower()

        # 引言/介绍
        if any(keyword in text_lower for keyword in ["引言", "介绍", "背景", "概述"]):
            return "introduction"

        # 结论/总结
        if any(keyword in text_lower for keyword in ["结论", "总结", "综上", "总之"]):
            return "conclusion"

        # 过渡段落
        if any(keyword in text_lower for keyword in ["然而", "但是", "因此", "所以", "接下来"]):
            return "transition"

        # 问答
        if metadata.get("qa_type"):
            return metadata["qa_type"]

        # 默认为内容
        return "content"

    def _calculate_confidence(self, semantic_context: Dict[str, Any]) -> float:
        """计算语义增强的置信度"""
        score = 0.0
        total_factors = 0

        # 有章节信息
        if semantic_context.get("chapter"):
            score += 0.2
        total_factors += 1

        # 有关键实体
        if semantic_context.get("key_entities"):
            score += 0.2 * min(len(semantic_context["key_entities"]) / 3, 1.0)
        total_factors += 1

        # 有领域标签
        if semantic_context.get("domain_tags"):
            score += 0.2
        total_factors += 1

        # 有时空上下文
        if semantic_context.get("temporal_context") or semantic_context.get("spatial_context"):
            score += 0.2
        total_factors += 1

        # 有前后文摘要
        if semantic_context.get("prev_chunk_summary") or semantic_context.get("next_chunk_summary"):
            score += 0.2
        total_factors += 1

        return score

    def enhance_chunks_batch(
        self,
        chunks: List[Dict[str, Any]],
        document_context: Dict[str, Any],
        entities: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量增强 chunks

        Args:
            chunks: chunk 列表
            document_context: 文档上下文
            entities: 实体列表

        Returns:
            增强后的 chunks
        """
        logger.info(f"🔍 开始批量增强 {len(chunks)} 个 chunks")

        enhanced_chunks = []

        for i, chunk in enumerate(chunks):
            prev_chunk = chunks[i - 1] if i > 0 else None
            next_chunk = chunks[i + 1] if i < len(chunks) - 1 else None

            # 获取当前 chunk 的位置上下文
            chunk_start = chunk.get("metadata", {}).get("start_pos", 0)
            chunk_end = chunk.get("metadata", {}).get("end_pos", 0)

            # 从文档结构中获取上下文
            from app.services.document_structure_analyzer import document_structure_analyzer

            # 注意：这里需要完整的 DocumentStructure 对象
            # 简化处理：直接使用传入的 document_context
            position_context = document_context

            enhanced_chunk = self.enhance_chunk(
                chunk=chunk,
                document_context=position_context,
                prev_chunk=prev_chunk,
                next_chunk=next_chunk,
                entities=entities
            )

            enhanced_chunks.append(enhanced_chunk)

        logger.info(f"✅ 批量增强完成")

        return enhanced_chunks


# 全局实例
chunk_semantic_enhancer = ChunkSemanticEnhancer()


def enhance_chunk_semantics(
    chunk: Dict[str, Any],
    document_context: Dict[str, Any],
    prev_chunk: Optional[Dict[str, Any]] = None,
    next_chunk: Optional[Dict[str, Any]] = None,
    entities: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """便捷函数：增强 chunk 语义"""
    return chunk_semantic_enhancer.enhance_chunk(
        chunk, document_context, prev_chunk, next_chunk, entities
    )


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("🧪 Chunk 语义增强器测试")
    print("=" * 80)

    test_chunk = {
        "text": "王大爷说，杀猪菜是我们村的传统美食。每年冬天杀年猪的时候，全村人都会聚在一起。",
        "metadata": {
            "start_pos": 0,
            "end_pos": 100
        }
    }

    test_context = {
        "chapter": "第一章：传统美食",
        "section": "王大爷访谈",
        "parent_chain": [
            {"level": 1, "text": "第一章：传统美食"}
        ]
    }

    test_entities = [
        {"name": "王大爷", "entity_type": "Person", "confidence": 0.9},
        {"name": "杀猪菜", "entity_type": "CulturalAsset", "confidence": 0.85}
    ]

    enhanced = enhance_chunk_semantics(
        test_chunk,
        test_context,
        entities=test_entities
    )

    print("\n✅ 增强完成:")
    print(f"   章节: {enhanced['semantic_context']['chapter']}")
    print(f"   关键实体: {enhanced['semantic_context']['entity_summary']}")
    print(f"   领域标签: {enhanced['semantic_context']['domain_tags']}")
    print(f"   置信度: {enhanced['semantic_context']['confidence']:.2f}")

    print("=" * 80)
