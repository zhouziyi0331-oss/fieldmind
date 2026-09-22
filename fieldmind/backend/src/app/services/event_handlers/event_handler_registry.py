"""
事件处理器注册中心
Event Handler Registry

功能：
1. 注册所有模块的事件处理器
2. 自动连接流水线、知识图谱、缩影系统
3. 事件驱动的自动更新
4. 事件日志和监控
"""

from sqlalchemy.orm import Session
import logging
from typing import Dict, Any

from app.core.database import SessionLocal
from app.services.event_bus import event_bus, EventTypes, event_handler
from app.services.summary.enhanced_summary_generator import generate_enhanced_summary
from app.services.knowledge_graph.kg_query_service import KnowledgeGraphQueryService

logger = logging.getLogger(__name__)


class EventHandlerRegistry:
    """事件处理器注册中心"""

    def __init__(self):
        self.handlers_registered = False

    def register_all_handlers(self):
        """注册所有事件处理器"""
        if self.handlers_registered:
            logger.warning("事件处理器已注册，跳过")
            return

        logger.info("📝 开始注册事件处理器...")

        # 注册流水线事件处理器
        self._register_pipeline_handlers()

        # 注册知识图谱事件处理器
        self._register_knowledge_graph_handlers()

        # 注册缩影系统事件处理器
        self._register_summary_handlers()

        self.handlers_registered = True
        logger.info("✅ 所有事件处理器注册完成")

    # ============================================================
    # 流水线事件处理器
    # ============================================================

    def _register_pipeline_handlers(self):
        """注册流水线事件处理器"""
        logger.info("  📌 注册流水线事件处理器")

        # 流水线开始
        @event_handler(EventTypes.PIPELINE_STARTED)
        def on_pipeline_started(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            logger.info(f"🚀 流水线开始 - 文档 {document_id}")

        # 流水线步骤完成
        @event_handler(EventTypes.PIPELINE_STEP_COMPLETED)
        def on_pipeline_step_completed(payload: Dict[str, Any]):
            step = payload.get('step')
            step_name = payload.get('step_name')
            document_id = payload.get('document_id')
            logger.info(f"✅ Step {step} ({step_name}) 完成 - 文档 {document_id}")

        # 流水线完成 -> 触发知识图谱更新
        @event_handler(EventTypes.PIPELINE_COMPLETED)
        def on_pipeline_completed(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            logger.info(f"🎉 流水线完成 - 文档 {document_id}")

            # 更新知识图谱统计
            try:
                db = SessionLocal()
                kg_query = KnowledgeGraphQueryService(db)
                stats = kg_query.get_graph_statistics()
                logger.info(f"📊 知识图谱统计: {stats['total_nodes']} 节点, {stats['total_edges']} 边")
                db.close()
            except Exception as e:
                logger.error(f"更新知识图谱统计失败: {e}")

        # 流水线失败
        @event_handler(EventTypes.PIPELINE_FAILED)
        def on_pipeline_failed(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            error = payload.get('error')
            logger.error(f"❌ 流水线失败 - 文档 {document_id}: {error}")

    # ============================================================
    # 知识图谱事件处理器
    # ============================================================

    def _register_knowledge_graph_handlers(self):
        """注册知识图谱事件处理器"""
        logger.info("  📌 注册知识图谱事件处理器")

        # 实体提取完成 -> 创建知识图谱节点
        @event_handler(EventTypes.ENTITIES_EXTRACTED)
        def on_entities_extracted(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            result = payload.get('result', {})
            entity_count = result.get('entities_merged', 0)
            kg_nodes = result.get('kg_nodes_created', 0)
            logger.info(f"👤 实体提取完成 - 文档 {document_id}: {entity_count} 个实体, {kg_nodes} 个知识图谱节点")

        # 事件提取完成 -> 创建知识图谱节点
        @event_handler(EventTypes.EVENTS_EXTRACTED)
        def on_events_extracted(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            result = payload.get('result', {})
            event_count = result.get('events_extracted', 0)
            kg_nodes = result.get('kg_nodes_created', 0)
            logger.info(f"⏰ 事件提取完成 - 文档 {document_id}: {event_count} 个事件, {kg_nodes} 个知识图谱节点")

        # 关系发现完成 -> 创建知识图谱边
        @event_handler(EventTypes.RELATIONSHIPS_DISCOVERED)
        def on_relationships_discovered(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            result = payload.get('result', {})
            relationship_count = result.get('relationships_discovered', 0)
            kg_edges = result.get('kg_edges_created', 0)
            logger.info(f"🔗 关系发现完成 - 文档 {document_id}: {relationship_count} 个关系, {kg_edges} 条知识图谱边")

        # 本体构建完成
        @event_handler(EventTypes.ONTOLOGY_BUILT)
        def on_ontology_built(payload: Dict[str, Any]):
            project_id = payload.get('project_id')
            result = payload.get('result', {})
            concept_count = result.get('concepts_created', 0)
            logger.info(f"🏛️ 本体构建完成 - 项目 {project_id}: {concept_count} 个概念")

        # 推理完成
        @event_handler(EventTypes.INFERENCE_COMPLETED)
        def on_inference_completed(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            result = payload.get('result', {})
            inference_count = result.get('inferences_created', 0)
            logger.info(f"🧠 推理完成 - 文档 {document_id}: {inference_count} 个推理")

        # 知识单元化完成 -> 触发缩影生成
        @event_handler(EventTypes.KNOWLEDGE_UNITS_CREATED)
        def on_knowledge_units_created(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            result = payload.get('result', {})
            unit_count = result.get('units_created', 0)
            logger.info(f"📦 知识单元化完成 - 文档 {document_id}: {unit_count} 个知识单元")

            # 自动触发缩影生成
            try:
                logger.info(f"🔄 自动触发缩影生成 - 文档 {document_id}")
                db = SessionLocal()
                summary_result = generate_enhanced_summary(db, document_id)
                if summary_result['success']:
                    logger.info(f"✅ 缩影生成成功 - 文档 {document_id}")
                else:
                    logger.warning(f"⚠️ 缩影生成失败 - 文档 {document_id}: {summary_result.get('message')}")
                db.close()
            except Exception as e:
                logger.error(f"❌ 缩影生成异常 - 文档 {document_id}: {e}")

        # 知识图谱节点创建
        @event_handler(EventTypes.KG_NODE_CREATED)
        def on_kg_node_created(payload: Dict[str, Any]):
            node_id = payload.get('node_id')
            node_type = payload.get('node_type')
            logger.debug(f"📌 知识图谱节点创建: {node_id} ({node_type})")

        # 知识图谱边创建
        @event_handler(EventTypes.KG_EDGE_CREATED)
        def on_kg_edge_created(payload: Dict[str, Any]):
            edge_id = payload.get('edge_id')
            edge_type = payload.get('edge_type')
            logger.debug(f"🔗 知识图谱边创建: {edge_id} ({edge_type})")

        # 知识图谱更新
        @event_handler(EventTypes.KG_UPDATED)
        def on_kg_updated(payload: Dict[str, Any]):
            logger.info(f"🔄 知识图谱更新")

    # ============================================================
    # 缩影系统事件处理器
    # ============================================================

    def _register_summary_handlers(self):
        """注册缩影系统事件处理器"""
        logger.info("  📌 注册缩影系统事件处理器")

        # 缩影生成完成
        @event_handler(EventTypes.SUMMARY_GENERATED)
        def on_summary_generated(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            summary_id = payload.get('summary_id')
            logger.info(f"📝 缩影生成完成 - 文档 {document_id}, 缩影 ID: {summary_id}")

        # 缩影更新
        @event_handler(EventTypes.SUMMARY_UPDATED)
        def on_summary_updated(payload: Dict[str, Any]):
            document_id = payload.get('document_id')
            logger.info(f"🔄 缩影更新 - 文档 {document_id}")


# ============================================================
# 全局注册中心实例
# ============================================================

event_registry = EventHandlerRegistry()


# ============================================================
# 初始化函数
# ============================================================

def initialize_event_handlers():
    """
    初始化所有事件处理器

    在应用启动时调用
    """
    logger.info("🚀 初始化事件处理器...")
    event_registry.register_all_handlers()
    logger.info("✅ 事件处理器初始化完成")


def get_event_statistics() -> Dict[str, Any]:
    """
    获取事件统计

    Returns:
        事件统计信息
    """
    db = SessionLocal()

    try:
        from app.models.unified_models import SystemEvent
        from sqlalchemy import func

        # 总事件数
        total_events = db.query(func.count(SystemEvent.id)).scalar()

        # 已消费事件数
        consumed_events = db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.status == 'consumed'
        ).scalar()

        # 失败事件数
        failed_events = db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.status == 'failed'
        ).scalar()

        # 各类型事件统计
        event_type_stats = db.execute(text("""
            SELECT event_type, COUNT(*) as count
            FROM system_events
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 20
        """)).fetchall()

        # 最近事件
        recent_events = db.query(SystemEvent).order_by(
            SystemEvent.created_at.desc()
        ).limit(10).all()

        return {
            'total_events': total_events,
            'consumed_events': consumed_events,
            'failed_events': failed_events,
            'success_rate': round(consumed_events / total_events * 100, 2) if total_events > 0 else 0,
            'event_type_distribution': {row[0]: row[1] for row in event_type_stats},
            'recent_events': [
                {
                    'event_id': e.event_id,
                    'event_type': e.event_type,
                    'status': e.status,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                }
                for e in recent_events
            ]
        }

    finally:
        db.close()


def clear_old_events(days: int = 7):
    """
    清理旧事件

    Args:
        days: 保留天数
    """
    db = SessionLocal()

    try:
        from app.models.unified_models import SystemEvent
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = db.query(SystemEvent).filter(
            SystemEvent.created_at < cutoff_date,
            SystemEvent.status == 'consumed'
        ).delete()

        db.commit()

        logger.info(f"🧹 清理了 {deleted} 个旧事件 (>{days} 天)")

        return {'deleted': deleted}

    except Exception as e:
        db.rollback()
        logger.error(f"清理旧事件失败: {e}")
        raise
    finally:
        db.close()
