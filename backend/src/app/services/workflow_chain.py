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



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    @staticmethod
    def _project_settings(project) -> dict:
        """读取项目 settings，兼容空值。"""
        return dict(getattr(project, "settings", None) or {})

    @staticmethod
    def _save_project_settings(project, db: Session, settings: dict):
        """写回项目 settings，并同步更新时间。"""
        project.settings = settings
        project.updated_at = datetime.now()
        project.last_activity_at = datetime.now()
        db.commit()

    @staticmethod
    def _parse_iso_datetime(value: str | None):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

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

        # JSON 数组在 SQLite/MySQL 上的函数行为并不一致，统一在 Python 中
        # 计算并去重，避免统计接口因为方言差异直接失败。
        completed_documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed",
        ).all()
        entity_keys = set()
        for document in completed_documents:
            for item in (document.extracted_entities or document.entities or []):
                if isinstance(item, dict):
                    name = (
                        item.get("name")
                        or item.get("text")
                        or item.get("entity_name")
                        or item.get("canonical_name")
                    )
                    entity_type = (
                        item.get("type")
                        or item.get("entity_type")
                        or "UNKNOWN"
                    )
                    if name:
                        entity_keys.add((str(name).strip(), str(entity_type).upper()))
        total_entities = len(entity_keys)

        # 更新项目
        project.document_count = total_docs
        project.entity_count = total_entities
        project.updated_at = datetime.now()
        project.last_activity_at = datetime.now()

        # Project 模型没有 extra_data 字段，统计摘要统一放入 settings，
        # 避免工作流运行到最后才因字段不存在而报错。
        project_settings = self._project_settings(project)
        project_settings['stats'] = {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "total_words": total_words,
            "total_entities": total_entities,
            "last_updated": datetime.now().isoformat()
        }
        self._save_project_settings(project, db, project_settings)

        logger.info(f"📊 项目统计已更新: 文档={total_docs}, 实体={total_entities}, 词数={total_words}")

    def _sync_entities(self, document, db: Session):
        """同步实体到entities表（用于知识图谱）"""
        if not document.extracted_entities:
            return

        from app.models.entity import Entity
        from app.models.federation import FieldMindObject, ObjectRelation
        from app.services.data_federation_service import DataFederationService

        synced_count = 0
        federation = DataFederationService(db)

        def find_federated_object(object_type: str, record_id: str):
            candidates = db.query(FieldMindObject).filter(
                FieldMindObject.project_id == document.project_id,
                FieldMindObject.object_type == object_type,
            ).all()
            for candidate in candidates:
                storage = candidate.storage_info or {}
                if str(storage.get("record_id")) == str(record_id):
                    return candidate
            return None

        document_object = find_federated_object("document", document.id)
        if not document_object:
            document_fid = federation.register_document(
                doc_id=document.id,
                project_id=document.project_id,
                metadata={
                    "title": document.original_filename,
                    "file_type": document.file_type,
                    "status": document.status,
                },
            )
            document_object = db.query(FieldMindObject).filter(
                FieldMindObject.fid == document_fid
            ).first()

        for entity_data in document.extracted_entities:
            # 提取实体信息
            entity_name = (
                entity_data.get('name')
                or entity_data.get('text')
                or entity_data.get('entity_name')
                or entity_data.get('canonical_name')
            )
            entity_type = (
                entity_data.get('type')
                or entity_data.get('entity_type')
                or 'unknown'
            )

            if not entity_name:
                continue

            # 检查实体是否已存在
            entity_type = str(entity_type).upper()
            existing = db.query(Entity).filter(
                Entity.text == entity_name,
                Entity.type == entity_type,
            ).first()

            if existing:
                existing.mention_count = (existing.mention_count or 0) + 1
                document_ids = list(existing.document_ids or [])
                if document.id not in document_ids:
                    document_ids.append(document.id)
                existing.document_ids = document_ids
                metadata = dict(existing.metadata_json or {})
                project_ids = list(metadata.get("project_ids") or [])
                if document.project_id not in project_ids:
                    project_ids.append(document.project_id)
                metadata["project_ids"] = project_ids
                existing.metadata_json = metadata
                existing.updated_at = datetime.now()
            else:
                new_entity = Entity(
                    text=entity_name,
                    type=entity_type,
                    canonical_form=entity_name,
                    legacy_name=entity_name,
                    legacy_entity_type=entity_type,
                    mention_count=1,
                    confidence=float(entity_data.get("confidence") or 0.5),
                    document_ids=[document.id],
                    metadata_json={"project_ids": [document.project_id], "source": "workflow_chain"},
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_entity)
                db.flush()
                synced_count += 1

            # 统一联邦对象：实体对象只创建一次，文档到实体的提及关系保持幂等。
            entity_object = find_federated_object("entity", existing.id if existing else new_entity.id)
            if not entity_object:
                entity_object_fid = federation.register_object(
                    object_type="entity",
                    project_id=document.project_id,
                    storage_info={
                        "storage_type": "sqlite",
                        "table_name": "entities",
                        "record_id": existing.id if existing else new_entity.id,
                    },
                    metadata={
                        "entity_name": entity_name,
                        "canonical_name": entity_name,
                        "entity_type": entity_type,
                        "confidence": entity_data.get("confidence"),
                    },
                    source_fid=document_object.fid if document_object else None,
                )
                entity_object = db.query(FieldMindObject).filter(
                    FieldMindObject.fid == entity_object_fid
                ).first()

            if document_object and entity_object:
                relation_exists = db.query(ObjectRelation).filter(
                    ObjectRelation.from_fid == document_object.fid,
                    ObjectRelation.to_fid == entity_object.fid,
                    ObjectRelation.relation_type == "mentions",
                    ObjectRelation.project_id == document.project_id,
                ).first()
                if not relation_exists:
                    federation.add_relation(
                        from_fid=document_object.fid,
                        to_fid=entity_object.fid,
                        relation_type="mentions",
                        confidence=float(entity_data.get("confidence") or 0.5),
                        project_id=document.project_id,
                        relation_data={"source": "dynamic_discovery"},
                    )

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
        project_settings = self._project_settings(project)
        last_kg_build = project_settings.get('last_kg_build_time')

        if last_kg_build:
            last_build_dt = self._parse_iso_datetime(last_kg_build)
            if not last_build_dt:
                logger.warning("项目 settings 中的 last_kg_build_time 无法解析，忽略该值")
                return True
            if datetime.now() - last_build_dt < timedelta(hours=1):
                logger.debug(f"最近已构建知识图谱，跳过")
                return False

        logger.info(f"✅ 满足知识图谱构建条件: 文档={completed_docs}, 实体={entity_count}")
        return True

    def _trigger_knowledge_graph_build(self, project_id: int, db: Session):
        """触发知识图谱构建"""
        try:
            from app.services.knowledge_graph_service import get_knowledge_graph_service

            kg_service = get_knowledge_graph_service()

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
                project_settings = self._project_settings(project)
                project_settings['last_kg_build_time'] = datetime.now().isoformat()
                project_settings['kg_stats'] = {
                    "entities_count": len(entities),
                    "relations_count": len(relations)
                }
                self._save_project_settings(project, db, project_settings)

            logger.info(f"🕸️ 知识图谱构建完成: {len(entities)}个实体, {len(relations)}个关系")

        except Exception as e:
            logger.error(f"知识图谱构建失败: {e}", exc_info=True)

    def _should_generate_industry_analysis(self, project_id: int, db: Session) -> bool:
        """判断是否应该生成产业分析"""
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        project_settings = self._project_settings(project)

        # 条件1: 知识图谱已构建
        if not project_settings.get('last_kg_build_time'):
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
        last_analysis = project_settings.get('last_industry_analysis_time')
        if last_analysis:
            last_dt = self._parse_iso_datetime(last_analysis)
            if not last_dt:
                logger.warning("项目 settings 中的 last_industry_analysis_time 无法解析，忽略该值")
                return True
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
            from app.services.business_analysis_service import BusinessAnalysisService

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return

            # 调用真实分析服务；外部模型不可用时保存 unavailable，绝不伪造完成。
            analysis = asyncio.run(
                BusinessAnalysisService(db).analyze_business_formats(project_id)
            )
            project_settings = self._project_settings(project)
            project_settings["industry_analysis"] = analysis
            project_settings["industry_analysis_status"] = analysis.get("status", "completed")
            project_settings["last_industry_analysis_time"] = datetime.now().isoformat()
            self._save_project_settings(project, db, project_settings)

            logger.info(
                "📊 产业分析已执行: project_id=%s status=%s",
                project_id,
                analysis.get("status", "completed"),
            )

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
                project_settings = self._project_settings(project)
                project_settings['dashboard_last_refresh'] = datetime.now().isoformat()
                self._save_project_settings(project, db, project_settings)

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

            from app.services.cross_document_entity_resolver import cross_document_resolver
            from app.services.document_relation_discovery import document_relation_discovery

            # 1. 实体消歧
            logger.info(f"开始跨文档实体消歧...")
            entity_result = cross_document_resolver.resolve_entities(project_id, db)
            canonical_count = len(entity_result.get('canonical_entities', []))

            # 2. 文档关系发现
            logger.info(f"开始文档关系发现...")
            relations = document_relation_discovery.discover_relations(project_id, db)

            # 3. 保存结果到项目的 settings
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                project_settings = self._project_settings(project)
                project_settings['cross_document_analysis'] = {
                    'last_analysis_time': datetime.now().isoformat(),
                    'canonical_entities': canonical_count,
                    'document_relations': len(relations),
                    'statistics': entity_result.get('statistics', {})
                }
                self._save_project_settings(project, db, project_settings)

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

            # 缓存网络数据（供后续网络分析和前端查询）
            try:
                from app.core.cache import get_cache_backend
                get_cache_backend().set(f"document_network:{project_id}", network, ttl=3600)
            except Exception as e:
                logger.warning(f"文档网络缓存失败: {e}")

            # 保存统计信息到项目
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == project_id).first()

            if project:
                project_settings = self._project_settings(project)
                project_settings['document_network'] = {
                    'last_build_time': datetime.now().isoformat(),
                    'statistics': network.get('statistics', {})
                }
                self._save_project_settings(project, db, project_settings)

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

            # 获取已构建的网络；当前缓存后端可能是内存或 Redis。
            from app.core.cache import get_cache_backend

            network = get_cache_backend().get(f"document_network:{project_id}")
            if not isinstance(network, dict):
                logger.info("未找到文档网络数据，跳过网络分析")
                return

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
                project_settings = self._project_settings(project)
                project_settings['network_insights'] = {
                    'last_analysis_time': datetime.now().isoformat(),
                    'insights': insights
                }
                self._save_project_settings(project, db, project_settings)

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
