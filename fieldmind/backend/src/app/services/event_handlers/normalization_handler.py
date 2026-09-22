"""
规范化事件处理器
监听文档规范化完成事件，自动触发下游服务

功能：
1. 索引到所有RAG引擎
2. 更新知识图谱
3. 触发摘要生成
4. 发布后续事件
"""

import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def on_document_normalized(event_data: Dict[str, Any]):
    """
    文档规范化完成后自动执行:
    1. 索引到所有RAG引擎（Quivr, LightRAG, GraphRAG, Cognee, Mem0）
    2. 更新知识图谱（提取实体和关系）
    3. 触发后续事件

    Args:
        event_data: 事件数据
            - document_id: 文档ID
            - project_id: 项目ID
            - normalized_text: 规范化后的文本
            - word_count: 字数
            - confidence: 置信度
            - method: 规范化方法
            - metadata: 元数据
    """
    document_id = event_data.get('document_id')
    project_id = event_data.get('project_id')
    normalized_text = event_data.get('normalized_text')
    metadata = event_data.get('metadata', {})

    logger.info(f"{'='*60}")
    logger.info(f"🎯 处理文档规范化事件")
    logger.info(f"   文档ID: {document_id}")
    logger.info(f"   项目ID: {project_id}")
    logger.info(f"   文本长度: {len(normalized_text)} 字符")
    logger.info(f"   置信度: {event_data.get('confidence', 0):.2%}")
    logger.info(f"   方法: {event_data.get('method')}")
    logger.info(f"{'='*60}")

    # ========== 任务1: 索引到RAG引擎 ==========
    try:
        from app.services.rag_integration_service import get_rag_integration_service

        logger.info(f"📊 任务1: 索引到RAG引擎")

        rag_service = get_rag_integration_service()
        rag_results = await rag_service.index_normalized_document(
            document_id=document_id,
            normalized_text=normalized_text,
            project_id=str(project_id),
            metadata=metadata
        )

        success_count = rag_results.get('success_count', 0)
        total_count = rag_results.get('total_engines', 0)

        logger.info(f"✅ RAG索引完成: {success_count}/{total_count} 个引擎成功")

        # 记录详细结果
        for engine_name, result in rag_results.get('results', {}).items():
            status = result.get('status', 'unknown')
            if status == 'success':
                logger.info(f"   ✅ {engine_name}: 成功")
            elif status == 'error':
                logger.warning(f"   ❌ {engine_name}: {result.get('error')}")
            else:
                logger.info(f"   ⚠️ {engine_name}: {status}")

    except Exception as e:
        logger.error(f"❌ RAG索引失败: {e}", exc_info=True)

    # ========== 任务2: 实体提取并更新知识图谱 ==========
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service

        logger.info(f"🕸️ 任务2: 实体提取并更新知识图谱")

        kg_service = get_knowledge_graph_service()

        # 从规范化文本中提取实体和关系
        entities, relations = kg_service.extract_entities_and_relations(
            text=normalized_text,
            document_id=document_id,
            use_llm=True  # 使用LLM增强提取
        )

        logger.info(f"   提取到 {len(entities)} 个实体, {len(relations)} 个关系")

        # 添加到知识图谱
        if entities or relations:
            kg_service.add_entities_and_relations(
                entities=entities,
                relations=relations,
                document_id=document_id
            )

            logger.info(f"✅ 知识图谱更新完成")

            # 发布知识图谱更新事件
            from app.services.event_bus import publish_event, EventTypes

            if hasattr(EventTypes, 'KNOWLEDGE_GRAPH_UPDATED'):
                publish_event(EventTypes.KNOWLEDGE_GRAPH_UPDATED, {
                    'document_id': document_id,
                    'project_id': project_id,
                    'entities_count': len(entities),
                    'relations_count': len(relations)
                })
                logger.info(f"   ✅ 已发布 KNOWLEDGE_GRAPH_UPDATED 事件")

    except Exception as e:
        logger.error(f"❌ 知识图谱更新失败: {e}", exc_info=True)

    # ========== 任务3: 触发文档摘要生成（可选）==========
    try:
        # 如果文本足够长，触发摘要生成
        if len(normalized_text) > 500:
            logger.info(f"📝 任务3: 触发摘要生成")

            from app.services.event_bus import publish_event, EventTypes

            if hasattr(EventTypes, 'DOCUMENT_READY_FOR_SUMMARIZATION'):
                publish_event(EventTypes.DOCUMENT_READY_FOR_SUMMARIZATION, {
                    'document_id': document_id,
                    'project_id': project_id,
                    'text_length': len(normalized_text),
                    'confidence': event_data.get('confidence')
                })
                logger.info(f"   ✅ 已发布 DOCUMENT_READY_FOR_SUMMARIZATION 事件")

    except Exception as e:
        logger.warning(f"⚠️ 触发摘要生成失败（非致命）: {e}")

    logger.info(f"{'='*60}")
    logger.info(f"✅ 规范化事件处理完成 - 文档 {document_id}")
    logger.info(f"{'='*60}")


def register_normalization_handlers():
    """
    注册规范化相关的事件处理器

    应在应用启动时调用
    """
    try:
        from app.services.event_bus import register_event_handler, EventTypes

        # 检查是否存在 DOCUMENT_NORMALIZED 事件类型
        if not hasattr(EventTypes, 'DOCUMENT_NORMALIZED'):
            logger.warning("⚠️ EventTypes.DOCUMENT_NORMALIZED 未定义，需要添加到 event_bus.py")
            return

        # 注册事件处理器
        register_event_handler(
            event_type=EventTypes.DOCUMENT_NORMALIZED,
            handler=on_document_normalized
        )

        logger.info("✅ 规范化事件处理器已注册")

    except Exception as e:
        logger.error(f"❌ 注册规范化事件处理器失败: {e}", exc_info=True)


# ========== 同步版本（用于非异步环境）==========

def on_document_normalized_sync(event_data: Dict[str, Any]):
    """
    同步版本的规范化事件处理器

    在无法使用异步的环境中调用
    """
    try:
        asyncio.run(on_document_normalized(event_data))
    except Exception as e:
        logger.error(f"❌ 同步处理规范化事件失败: {e}", exc_info=True)
