"""
向量化文本构建器 - Vectorization Text Builder

构建用于向量化的增强文本
将原始文本与语义上下文结合，生成更丰富的向量表示

核心理念：
- 原始文本：仅包含 chunk 自己的内容
- 增强文本：包含章节标题、实体、领域标签、前后文等上下文
- 向量化增强文本，检索时更准确
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class VectorizationTextBuilder:
    """
    向量化文本构建器

    为向量化构建增强文本，包含：
    1. 文档结构上下文（章节、小节）
    2. 关键实体信息
    3. 领域标签
    4. 时空背景
    5. 前后文提示
    6. 原始正文

    增强文本示例：
    '''
    文档章节：第一章：传统美食
    段落主题：王大爷访谈
    关键人物：王大爷（村民）
    关键事物：杀猪菜（传统美食）
    领域标签：民俗、饮食文化、口述史
    时间背景：春节传统
    空间背景：贵州村寨

    正文内容：王大爷说，杀猪菜是我们村的传统美食...

    上下文：前文介绍了村庄历史背景，后文将讲述杀猪菜的具体做法
    '''
    """

    def __init__(self):
        self.max_context_length = 500  # 上下文最大长度
        logger.info("✅ 向量化文本构建器初始化完成")

    def build_enhanced_text(
        self,
        chunk: Dict[str, Any],
        include_context: bool = True,
        include_entities: bool = True,
        include_tags: bool = True
    ) -> str:
        """
        构建用于向量化的增强文本

        ⭐⭐⭐ 特殊处理：
        - 普通文本：添加章节、实体、标签等上下文
        - 表格数据：保留结构化信息，添加列语义

        Args:
            chunk: chunk 数据（应包含 semantic_context）
            include_context: 是否包含文档结构上下文
            include_entities: 是否包含实体信息
            include_tags: 是否包含领域标签

        Returns:
            增强后的文本
        """
        chunk_text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})
        semantic_context = metadata.get("source_summary") or chunk.get("semantic_context", {})

        # ⭐⭐⭐ 特殊处理：表格 chunk
        if metadata.get("is_table") or metadata.get("chunk_type") == "table_sheet":
            return self._build_enhanced_table_text(chunk, metadata)

        # 如果没有语义上下文，直接返回原文
        if not semantic_context:
            logger.debug("   Chunk 无语义上下文，使用原始文本")
            return chunk_text

        parts = []

        # 1. 文档结构上下文
        if include_context:
            context_parts = self._build_structural_context(semantic_context)
            if context_parts:
                parts.extend(context_parts)

        # 2. 实体信息
        if include_entities:
            entity_parts = self._build_entity_context(semantic_context)
            if entity_parts:
                parts.extend(entity_parts)

        # 3. 领域标签
        if include_tags:
            tag_parts = self._build_tag_context(semantic_context)
            if tag_parts:
                parts.extend(tag_parts)

        # 4. 时空背景
        temporal_spatial_parts = self._build_temporal_spatial_context(semantic_context)
        if temporal_spatial_parts:
            parts.extend(temporal_spatial_parts)

        # 5. 原始正文（核心）
        parts.append(f"正文内容：{chunk_text}")

        # 6. 前后文提示
        context_hint = self._build_context_hint(semantic_context)
        if context_hint:
            parts.append(context_hint)

        # 组合成完整的增强文本
        enhanced_text = "\n".join(parts)

        # 限制长度（避免过长）
        if len(enhanced_text) > 2000:
            # 保留结构，截断正文
            truncated_text = chunk_text[:1500] + "..."
            parts[parts.index(f"正文内容：{chunk_text}")] = f"正文内容：{truncated_text}"
            enhanced_text = "\n".join(parts)

        return enhanced_text

    def _build_enhanced_table_text(self, chunk: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """
        为表格 chunk 构建增强文本 ⭐⭐⭐

        策略：
        1. 保留表格名称和范围
        2. 添加列语义（如："姓名列"、"金额列"）
        3. 保留关键数值统计
        4. 原始表格文本（行数据）
        """
        parts = []

        # 表格元信息
        sheet_name = metadata.get("sheet_name", "表格")
        row_range = metadata.get("row_range", "未知")
        parts.append(f"表格名称：{sheet_name}")
        parts.append(f"数据范围：第{row_range}行")

        # 结构化数据
        structured_data = metadata.get("structured_data", {})

        # 列类型信息
        if structured_data:
            data_types = structured_data.get("data_types", {})
            if data_types:
                type_desc = []
                for col_idx, col_type in data_types.items():
                    type_labels = {
                        "string": "文本",
                        "number": "数值",
                        "date": "日期",
                        "boolean": "布尔"
                    }
                    type_desc.append(f"第{col_idx}列:{type_labels.get(col_type, col_type)}")

                if type_desc:
                    parts.append(f"列类型：{', '.join(type_desc)}")

            # 行数统计
            row_count = structured_data.get("row_count", 0)
            if row_count:
                parts.append(f"包含{row_count}行数据")

        # 原始表格文本
        chunk_text = chunk.get("text", "")
        parts.append(f"\n表格内容：\n{chunk_text}")

        return "\n".join(parts)

    def _build_structural_context(self, semantic_context: Dict[str, Any]) -> List[str]:
        """构建结构上下文部分"""
        parts = []

        chapter = semantic_context.get("chapter")
        section = semantic_context.get("section")
        subsection = semantic_context.get("subsection")

        if chapter:
            parts.append(f"文档章节：{chapter}")

        if section:
            parts.append(f"段落主题：{section}")

        if subsection:
            parts.append(f"小节：{subsection}")

        return parts

    def _build_entity_context(self, semantic_context: Dict[str, Any]) -> List[str]:
        """构建实体上下文部分"""
        parts = []

        key_entities = semantic_context.get("key_entities", [])

        if not key_entities:
            return parts

        # 按类型分组
        entities_by_type = {}
        for entity in key_entities:
            entity_type = entity.get("type", "")
            entity_name = entity.get("name", "")

            if not entity_type or not entity_name:
                continue

            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []

            entities_by_type[entity_type].append(entity_name)

        # 生成描述
        type_labels = {
            "Person": "关键人物",
            "Location": "关键地点",
            "CulturalAsset": "关键事物",
            "Event": "相关事件",
            "Organization": "相关组织",
            "Policy": "相关政策"
        }

        for entity_type, names in entities_by_type.items():
            label = type_labels.get(entity_type, entity_type)
            parts.append(f"{label}：{', '.join(names)}")

        return parts

    def _build_tag_context(self, semantic_context: Dict[str, Any]) -> List[str]:
        """构建标签上下文部分"""
        parts = []

        domain_tags = semantic_context.get("domain_tags", [])

        if domain_tags:
            parts.append(f"领域标签：{', '.join(domain_tags)}")

        return parts

    def _build_temporal_spatial_context(self, semantic_context: Dict[str, Any]) -> List[str]:
        """构建时空上下文部分"""
        parts = []

        temporal = semantic_context.get("temporal_context")
        spatial = semantic_context.get("spatial_context")

        if temporal:
            parts.append(f"时间背景：{temporal}")

        if spatial:
            parts.append(f"空间背景：{spatial}")

        return parts

    def _build_context_hint(self, semantic_context: Dict[str, Any]) -> Optional[str]:
        """构建前后文提示"""
        prev_summary = semantic_context.get("prev_chunk_summary")
        next_summary = semantic_context.get("next_chunk_summary")

        hints = []

        if prev_summary:
            hints.append(f"前文：{prev_summary}")

        if next_summary:
            hints.append(f"后文：{next_summary}")

        if hints:
            return "上下文：" + "；".join(hints)

        return None

    def build_enhanced_text_batch(
        self,
        chunks: List[Dict[str, Any]],
        **kwargs
    ) -> List[str]:
        """
        批量构建增强文本

        Args:
            chunks: chunk 列表
            **kwargs: 传递给 build_enhanced_text 的参数

        Returns:
            增强文本列表
        """
        logger.info(f"📝 开始批量构建增强文本: {len(chunks)} 个 chunks")

        enhanced_texts = []

        for chunk in chunks:
            enhanced_text = self.build_enhanced_text(chunk, **kwargs)
            enhanced_texts.append(enhanced_text)

        logger.info(f"✅ 批量构建完成")

        return enhanced_texts

    def get_enhanced_metadata(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取用于存储的增强元数据

        这些元数据可以用于：
        1. 向量数据库的过滤查询
        2. 重排序（Reranking）
        3. 结果展示
        """
        metadata = chunk.get("metadata", {})
        semantic_context = metadata.get("source_summary") or chunk.get("semantic_context", {})

        enhanced_metadata = {
            # 文档结构
            "chapter": semantic_context.get("chapter"),
            "section": semantic_context.get("section"),
            "subsection": semantic_context.get("subsection"),

            # 实体（取前3个）
            "entities": [
                e.get("name") for e in semantic_context.get("key_entities", [])[:3]
            ],

            # 领域标签
            "domain_tags": semantic_context.get("domain_tags", []),
            "primary_domain": semantic_context.get("primary_domain"),

            # 时空
            "temporal_context": semantic_context.get("temporal_context"),
            "spatial_context": semantic_context.get("spatial_context"),

            # Chunk 角色
            "chunk_role": semantic_context.get("chunk_role"),

            # 置信度
            "enhancement_confidence": semantic_context.get("confidence", 0.0),

            # 原始元数据
            "original_metadata": metadata
        }

        # 过滤掉 None 值
        return {k: v for k, v in enhanced_metadata.items() if v is not None}


# 全局实例
vectorization_text_builder = VectorizationTextBuilder()


def build_vectorization_text(
    chunk: Dict[str, Any],
    include_context: bool = True,
    include_entities: bool = True,
    include_tags: bool = True
) -> str:
    """便捷函数：构建向量化文本"""
    return vectorization_text_builder.build_enhanced_text(
        chunk, include_context, include_entities, include_tags
    )


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("🧪 向量化文本构建器测试")
    print("=" * 80)

    test_chunk = {
        "text": "王大爷说，杀猪菜是我们村的传统美食。每年冬天杀年猪的时候，全村人都会聚在一起。",
        "semantic_context": {
            "chapter": "第一章：传统美食",
            "section": "王大爷访谈",
            "key_entities": [
                {"name": "王大爷", "type": "Person"},
                {"name": "杀猪菜", "type": "CulturalAsset"}
            ],
            "domain_tags": ["民俗", "饮食"],
            "temporal_context": "冬天",
            "spatial_context": "村里",
            "prev_chunk_summary": "介绍村庄历史背景",
            "next_chunk_summary": "讲述杀猪菜的具体做法"
        }
    }

    enhanced_text = build_vectorization_text(test_chunk)

    print("\n✅ 增强文本:")
    print("-" * 80)
    print(enhanced_text)
    print("-" * 80)

    print(f"\n原始长度: {len(test_chunk['text'])} 字符")
    print(f"增强长度: {len(enhanced_text)} 字符")
    print(f"增强比例: {len(enhanced_text) / len(test_chunk['text']):.2f}x")

    print("=" * 80)
