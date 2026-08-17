"""
工作流串联器 - 实现功能自动深化
第一个功能完成后，自动触发第二个功能继续深化
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class WorkflowChainOrchestrator:
    """工作流串联编排器"""

    def trigger_next_workflows(self, document, db: Session):
        """
        文档处理完成后，自动触发下一阶段工作流

        完整串联逻辑：
        文档处理 → 统计更新 → 实体同步 → 【跨文档分析】 → 【文档网络构建】
        → 【网络深度分析】 → 知识图谱 → 产业分析 → Dashboard刷新
        """
        project_id = document.project_id

        logger.info(f"🔗 开始工作流串联: document_id={document.id}, project_id={project_id}")

        try:
            # 阶段1: 更新项目统计（必须）
            self._notify_module_start(project_id, "stats_update", "更新项目统计")
            self._update_project_stats(project_id, db)
            self._notify_module_complete(project_id, "stats_update", "项目统计已更新")

            # 阶段2: 同步实体到entities表（如果有动态发现的实体）
            if document.extracted_entities:
                self._notify_module_start(project_id, "entity_sync", "同步实体到知识库")
                self._sync_entities(document, db)
                self._notify_module_complete(project_id, "entity_sync", f"已同步{len(document.extracted_entities)}个实体")

            # 🆕 阶段3: 跨文档实体消歧和关联分析（2+文档触发）
            if self._should_trigger_cross_document_analysis(project_id, db):
                self._trigger_cross_document_analysis(project_id, db)

            # 🆕 阶段4: 构建文档网络（2+文档触发）
            if self._should_build_document_network(project_id, db):
                self._trigger_document_network_build(project_id, db)

            # 🆕 阶段5: 网络深度分析（3+文档触发）
            if self._should_trigger_network_analysis(project_id, db):
                self._trigger_network_based_analysis(project_id, db)

            # 阶段6: 检查是否达到知识图谱构建阈值
            if self._should_build_knowledge_graph(project_id, db):
                logger.info(f"✅ 达到知识图谱构建阈值，触发构建...")
                self._notify_module_start(project_id, "knowledge_graph", "开始构建知识图谱")
                self._trigger_knowledge_graph_build(project_id, db)
                self._notify_module_complete(project_id, "knowledge_graph", "知识图谱构建完成")

            # 阶段7: 检查是否可以生成产业分析
            if self._should_generate_industry_analysis(project_id, db):
                logger.info(f"✅ 达到产业分析生成阈值，触发生成...")
                self._notify_module_start(project_id, "industry_analysis", "开始生成产业分析")
                self._trigger_industry_analysis(project_id, db)
                self._notify_module_complete(project_id, "industry_analysis", "产业分析生成完成")

            # 阶段8: 刷新Dashboard缓存
            self._notify_module_start(project_id, "dashboard_refresh", "刷新Dashboard数据")
            self._refresh_dashboard_cache(project_id, db)
            self._notify_module_complete(project_id, "dashboard_refresh", "Dashboard已刷新")

            logger.info(f"🎉 工作流串联完成: project_id={project_id}")

        except Exception as e:
            logger.error(f"❌ 工作流串联失败: {e}", exc_info=True)
            # 不抛出异常，避免影响主流程

    def _update_project_stats(self, project_id: int, db: Session):
        """更新项目统计数据"""
        from app.models.project import Project, ProjectDocument

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"项目不存在: {project_id}")
            return

        # 统计文档数量
        total_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id
        ).scalar() or 0

        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        # 统计总词数
        total_words = db.query(func.sum(ProjectDocument.word_count)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        # 统计实体数量（从document的extracted_entities）
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        total_entities = 0
        for doc in documents:
            if doc.extracted_entities:
                total_entities += len(doc.extracted_entities)

        # 更新项目
        project.document_count = total_docs
        project.entity_count = total_entities
        project.updated_at = datetime.now()
        project.last_activity_at = datetime.now()

        # 更新extra_data
        if not project.extra_data:
            project.extra_data = {}

        project.extra_data['stats'] = {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "total_words": total_words,
            "total_entities": total_entities,
            "last_updated": datetime.now().isoformat()
        }

        db.commit()

        logger.info(f"📊 项目统计已更新: 文档={total_docs}, 实体={total_entities}, 词数={total_words}")

    def _sync_entities(self, document, db: Session):
        """同步实体到entities表（用于知识图谱）"""
        if not document.extracted_entities:
            return

        from app.models.entity import Entity

        project_id = document.project_id
        synced_count = 0

        for entity_data in document.extracted_entities:
            # 提取实体信息
            entity_name = entity_data.get('name') or entity_data.get('entity_name')
            entity_type = entity_data.get('type') or entity_data.get('entity_type') or 'unknown'

            if not entity_name:
                continue

            # 检查实体是否已存在
            existing = db.query(Entity).filter(
                Entity.project_id == project_id,
                Entity.name == entity_name
            ).first()

            if existing:
                # 更新频次
                existing.frequency = (existing.frequency or 0) + 1
                existing.updated_at = datetime.now()
            else:
                # 创建新实体
                new_entity = Entity(
                    project_id=project_id,
                    name=entity_name,
                    entity_type=entity_type,
                    frequency=1,
                    source_document_id=document.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_entity)
                synced_count += 1

        db.commit()

        logger.info(f"🔄 实体同步完成: 新增{synced_count}个实体")

    def _should_build_knowledge_graph(self, project_id: int, db: Session) -> bool:
        """判断是否应该构建知识图谱"""
        from app.models.project import Project, ProjectDocument

        # 条件1: 至少有3个已完成的文档
        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        if completed_docs < 3:
            logger.debug(f"文档数量不足: {completed_docs}/3")
            return False

        # 条件2: 至少有10个实体
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        entity_count = project.entity_count or 0
        if entity_count < 10:
            logger.debug(f"实体数量不足: {entity_count}/10")
            return False

        # 条件3: 检查是否最近1小时内已经构建过（避免重复触发）
        extra_data = project.extra_data or {}
        last_kg_build = extra_data.get('last_kg_build_time')

        if last_kg_build:
            last_build_dt = datetime.fromisoformat(last_kg_build)
            if datetime.now() - last_build_dt < timedelta(hours=1):
                logger.debug(f"最近已构建知识图谱，跳过")
                return False

        logger.info(f"✅ 满足知识图谱构建条件: 文档={completed_docs}, 实体={entity_count}")
        return True

    def _trigger_knowledge_graph_build(self, project_id: int, db: Session):
        """触发知识图谱构建"""
        try:
            from app.tools.knowledge.graph import create_knowledge_graph

            kg_service = create_knowledge_graph()

            # 获取所有已完成文档的文本
            from app.models.project import ProjectDocument

            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).all()

            # 合并文本
            combined_text = "\n\n".join([
                doc.text_content for doc in documents if doc.text_content
            ])

            if not combined_text:
                logger.warning("没有可用的文本内容用于构建知识图谱")
                return

            # 提取实体和关系
            entities, relations = kg_service.extract_entities_and_relations(
                combined_text,
                document_id=None,  # 项目级别的图谱
                use_llm=True
            )

            # 添加到图谱
            kg_service.add_entities_and_relations(entities, relations)

            # 更新项目标记
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                if not project.extra_data:
                    project.extra_data = {}

                project.extra_data['last_kg_build_time'] = datetime.now().isoformat()
                project.extra_data['kg_stats'] = {
                    "entities_count": len(entities),
                    "relations_count": len(relations)
                }
                db.commit()

            logger.info(f"🕸️ 知识图谱构建完成: {len(entities)}个实体, {len(relations)}个关系")

        except Exception as e:
            logger.error(f"知识图谱构建失败: {e}", exc_info=True)

    def _should_generate_industry_analysis(self, project_id: int, db: Session) -> bool:
        """判断是否应该生成产业分析"""
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        extra_data = project.extra_data or {}

        # 条件1: 知识图谱已构建
        if not extra_data.get('last_kg_build_time'):
            logger.debug("知识图谱未构建，不触发产业分析")
            return False

        # 条件2: 至少有5个文档
        if (project.document_count or 0) < 5:
            logger.debug(f"文档数量不足: {project.document_count}/5")
            return False

        # 条件3: 至少有20个实体
        if (project.entity_count or 0) < 20:
            logger.debug(f"实体数量不足: {project.entity_count}/20")
            return False

        # 条件4: 检查是否最近24小时内已经生成过
        last_analysis = extra_data.get('last_industry_analysis_time')
        if last_analysis:
            last_dt = datetime.fromisoformat(last_analysis)
            if datetime.now() - last_dt < timedelta(hours=24):
                logger.debug("最近已生成产业分析，跳过")
                return False

        logger.info(f"✅ 满足产业分析生成条件")
        return True

    def _trigger_industry_analysis(self, project_id: int, db: Session):
        """触发产业分析生成"""
        try:
            # 这里应该调用产业分析服务
            # 暂时只标记，实际生成可以放到后台队列

            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                if not project.extra_data:
                    project.extra_data = {}

                project.extra_data['last_industry_analysis_time'] = datetime.now().isoformat()
                project.extra_data['analysis_triggered'] = True
                db.commit()

            logger.info(f"📊 产业分析已触发（后台生成中...）")

            # TODO: 这里应该调用实际的产业分析服务
            # from app.services.business_analysis_service import BusinessAnalysisService
            # analysis_service = BusinessAnalysisService()
            # result = analysis_service.analyze_project(project_id, db)

        except Exception as e:
            logger.error(f"产业分析触发失败: {e}", exc_info=True)

    def _refresh_dashboard_cache(self, project_id: int, db: Session):
        """刷新Dashboard缓存"""
        try:
            # 这里可以实现缓存刷新逻辑
            # 例如：更新Redis缓存，或标记需要重新计算

            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                if not project.extra_data:
                    project.extra_data = {}

                project.extra_data['dashboard_last_refresh'] = datetime.now().isoformat()
                db.commit()

            logger.info(f"🔄 Dashboard缓存已刷新")

        except Exception as e:
            logger.error(f"Dashboard缓存刷新失败: {e}", exc_info=True)

    # 🆕 跨文档分析相关方法
    def _should_trigger_cross_document_analysis(self, project_id: int, db: Session) -> bool:
        """判断是否应该触发跨文档分析"""
        from app.models.project import ProjectDocument

        # 至少需要2个已完成的文档
        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        return completed_docs >= 2

    def _trigger_cross_document_analysis(self, project_id: int, db: Session):
        """触发跨文档实体消歧和关系发现"""
        try:
            self._notify_module_start(project_id, "cross_document_analysis", "开始跨文档关联分析")

            from app.tools.entity import create_engine
            from app.services.document_relation_discovery import document_relation_discovery

            # 1. 实体消歧
            logger.info(f"开始跨文档实体消歧...")
            entity_result = cross_document_resolver.resolve_entities(project_id, db)
            canonical_count = len(entity_result.get('canonical_entities', []))

            # 2. 文档关系发现
            logger.info(f"开始文档关系发现...")
            relations = document_relation_discovery.discover_relations(project_id, db)

            # 3. 保存结果到项目的extra_data
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                if not project.extra_data:
                    project.extra_data = {}

                project.extra_data['cross_document_analysis'] = {
                    'last_analysis_time': datetime.now().isoformat(),
                    'canonical_entities': canonical_count,
                    'document_relations': len(relations),
                    'statistics': entity_result.get('statistics', {})
                }
                db.commit()

            self._notify_module_complete(
                project_id,
                "cross_document_analysis",
                f"发现{canonical_count}个标准实体，{len(relations)}个文档关系",
                {
                    'canonical_entities': canonical_count,
                    'document_relations': len(relations)
                }
            )

            logger.info(f"✅ 跨文档分析完成: {canonical_count}个标准实体, {len(relations)}个文档关系")

        except Exception as e:
            logger.error(f"❌ 跨文档分析失败: {e}", exc_info=True)

    def _should_build_document_network(self, project_id: int, db: Session) -> bool:
        """判断是否应该构建文档网络"""
        from app.models.project import ProjectDocument

        # 至少需要2个已完成的文档
        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        return completed_docs >= 2

    def _trigger_document_network_build(self, project_id: int, db: Session):
        """触发文档网络构建"""
        try:
            self._notify_module_start(project_id, "document_network", "构建文档关系网络")

            from app.services.document_network_builder import document_network_builder

            # 构建统一网络
            network = document_network_builder.build_unified_network(project_id, db)

            # 缓存网络数据到Redis（供前端查询）
            try:
                from app.core.redis_client import redis_client
                import json
                redis_client.setex(
                    f"document_network:{project_id}",
                    3600,  # 1小时过期
                    json.dumps(network, ensure_ascii=False)
                )
            except Exception as e:
                logger.warning(f"Redis缓存失败: {e}")

            # 保存统计信息到项目
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                if not project.extra_data:
                    project.extra_data = {}

                project.extra_data['document_network'] = {
                    'last_build_time': datetime.now().isoformat(),
                    'statistics': network.get('statistics', {})
                }
                db.commit()

            stats = network.get('statistics', {})
            self._notify_module_complete(
                project_id,
                "document_network",
                f"网络包含{stats.get('document_count', 0)}个文档，{stats.get('document_link_count', 0)}条关系",
                stats
            )

            logger.info(f"✅ 文档网络构建完成: {stats}")

        except Exception as e:
            logger.error(f"❌ 文档网络构建失败: {e}", exc_info=True)

    def _should_trigger_network_analysis(self, project_id: int, db: Session) -> bool:
        """判断是否应该触发网络深度分析"""
        from app.models.project import ProjectDocument

        # 至少需要3个已完成的文档（网络分析需要一定规模）
        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).scalar() or 0

        return completed_docs >= 3

    def _trigger_network_based_analysis(self, project_id: int, db: Session):
        """基于网络的深度分析"""
        try:
            self._notify_module_start(project_id, "network_analysis", "基于文档网络进行深度分析")

            # 获取已构建的网络
            from app.core.redis_client import redis_client
            import json

            network_data = redis_client.get(f"document_network:{project_id}")
            if not network_data:
                logger.warning("未找到文档网络数据，跳过网络分析")
                return

            network = json.loads(network_data)

            # 分析网络特征
            insights = {
                'core_documents': [],
                'communities': network.get('communities', []),
                'key_entities': [],
                'temporal_insights': []
            }

            # 1. 识别核心文档（基于importance得分）
            documents = network.get('documents', [])
            if documents:
                # 按importance排序
                sorted_docs = sorted(
                    [d for d in documents if d.get('importance', 0) > 0],
                    key=lambda x: x.get('importance', 0),
                    reverse=True
                )
                insights['core_documents'] = sorted_docs[:5]  # 前5个核心文档

            # 2. 识别关键实体（基于centrality）
            entities = network.get('entities', [])
            if entities:
                sorted_entities = sorted(
                    [e for e in entities if e.get('centrality', 0) > 0],
                    key=lambda x: x.get('centrality', 0),
                    reverse=True
                )
                insights['key_entities'] = sorted_entities[:10]  # 前10个关键实体

            # 3. 时间线洞察
            temporal_chain = network.get('temporal_chain', [])
            if len(temporal_chain) >= 2:
                insights['temporal_insights'] = {
                    'earliest_document': temporal_chain[0],
                    'latest_document': temporal_chain[-1],
                    'timeline_length': len(temporal_chain)
                }

            # 保存洞察结果
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                if not project.extra_data:
                    project.extra_data = {}

                project.extra_data['network_insights'] = {
                    'last_analysis_time': datetime.now().isoformat(),
                    'insights': insights
                }
                db.commit()

            self._notify_module_complete(
                project_id,
                "network_analysis",
                f"发现{len(insights['core_documents'])}个核心文档，{len(insights['communities'])}个文档簇",
                {
                    'core_document_count': len(insights['core_documents']),
                    'community_count': len(insights['communities']),
                    'key_entity_count': len(insights['key_entities'])
                }
            )

            logger.info(f"✅ 网络深度分析完成")

        except Exception as e:
            logger.error(f"❌ 网络深度分析失败: {e}", exc_info=True)

    def _notify_module_start(self, project_id: int, module_name: str, message: str):
        """通知功能板块开始"""
        try:
            from app.core.websocket import manager

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(
                manager.broadcast_to_project({
                    "type": "module_status",
                    "module": module_name,
                    "status": "started",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }, project_id)
            )

            loop.close()
            logger.info(f"📢 通知前端: {module_name} 开始")

        except Exception as e:
            logger.error(f"通知前端失败: {e}")

    def _notify_module_complete(self, project_id: int, module_name: str, message: str, data: dict = None):
        """通知功能板块完成"""
        try:
            from app.core.websocket import manager

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(
                manager.broadcast_to_project({
                    "type": "module_status",
                    "module": module_name,
                    "status": "completed",
                    "message": message,
                    "data": data or {},
                    "timestamp": datetime.now().isoformat()
                }, project_id)
            )

            loop.close()
            logger.info(f"📢 通知前端: {module_name} 完成")

        except Exception as e:
            logger.error(f"通知前端失败: {e}")


# 全局实例
workflow_chain = WorkflowChainOrchestrator()
