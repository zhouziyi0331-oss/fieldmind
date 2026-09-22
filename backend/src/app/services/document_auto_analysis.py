"""
文档自动分析引擎
整合现有的6-Agent架构和数据流编排器，实现完整的自动化分析流程

完整流程：
1. 文档上传 → 自动触发
2. 音频转文字（Whisper）
3. 内容提取和分块
4. 向量化
5. 关键词提取
6. 知识图谱构建
7. 可视化看板生成
8. 时间线/编年史构建
9. 三层分析报告生成：
   - 资料层分析
   - Skill层分析
   - 商业知识层分析
10. 文档详情页面更新
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.data_flow_orchestrator import DataFlowOrchestrator, DataPacket, DataQualityLevel
from app.agents.coordinator import AgentCoordinator, PipelineMode
from app.core.transcription import TranscriptionService
from app.models.project import ProjectDocument
from app.models.pipeline_state import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentAutoAnalysisEngine:
    """
    文档自动分析引擎

    整合所有现有组件，实现完整的自动化工作流
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.orchestrator = DataFlowOrchestrator()
        self.agent_coordinator = AgentCoordinator(
            default_mode=PipelineMode.FULL,
            enable_retry=True,
            max_retries=3
        )
        self.transcription_service = TranscriptionService()

    async def process_document_complete(
        self,
        document_id: int,
        project_id: int,
        file_path: str,
        file_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        完整的文档处理流程（自动化）

        Args:
            document_id: 文档ID
            project_id: 项目ID
            file_path: 文件路径
            file_type: 文件类型
            db: 数据库会话

        Returns:
            完整的分析结果
        """
        logger.info(f"🚀 启动文档完整分析流程: 文档ID={document_id}, 项目ID={project_id}")

        result = {
            "document_id": document_id,
            "project_id": project_id,
            "stages_completed": [],
            "analysis_results": {},
            "errors": []
        }

        try:
            # === 第1步：音频转文字（如果是音频文件）===
            if file_type in ['wav', 'mp3', 'm4a', 'flac']:
                logger.info("🎤 步骤1: 音频转文字")
                transcript_result = await self._transcribe_audio(
                    file_path, document_id, db
                )
                result["stages_completed"].append("audio_transcription")
                result["analysis_results"]["transcription"] = transcript_result

            # === 第2步：通过6-Agent Coordinator处理文档 ===
            logger.info("📄 步骤2-4: 内容提取、分块、向量化")

            # 使用现有的AgentCoordinator执行完整流程
            pipeline_result = await self.agent_coordinator.execute_pipeline(
                project_id=project_id,
                mode=PipelineMode.FULL,  # 完整模式
                db=db
            )

            result["stages_completed"].extend([
                "document_extraction",
                "intelligent_chunking",
                "vectorization"
            ])
            result["analysis_results"]["pipeline"] = pipeline_result

            # === 第3步：关键词提取 ===
            logger.info("🔑 步骤5: 关键词提取")
            keywords_result = await self._extract_keywords(document_id, db)
            result["stages_completed"].append("keyword_extraction")
            result["analysis_results"]["keywords"] = keywords_result

            # === 第4步：知识图谱构建 ===
            logger.info("🕸️ 步骤6: 知识图谱构建")
            knowledge_graph_result = await self._build_knowledge_graph(
                document_id, project_id, db
            )
            result["stages_completed"].append("knowledge_graph")
            result["analysis_results"]["knowledge_graph"] = knowledge_graph_result

            # === 第5步：可视化看板生成 ===
            logger.info("📊 步骤7: 可视化看板生成")
            dashboard_result = await self._generate_dashboard(
                document_id, project_id, keywords_result, knowledge_graph_result, db
            )
            result["stages_completed"].append("visualization_dashboard")
            result["analysis_results"]["dashboard"] = dashboard_result

            # === 第6步：时间线/编年史构建 ===
            logger.info("📅 步骤8: 时间线构建")
            timeline_result = await self._build_timeline(
                document_id, project_id, db
            )
            result["stages_completed"].append("timeline")
            result["analysis_results"]["timeline"] = timeline_result

            # === 第7步：三层分析报告生成 ===
            logger.info("📝 步骤9: 生成三层分析报告")

            # 7.1 资料层分析
            material_analysis = await self._generate_material_analysis(
                document_id, project_id, db
            )

            # 7.2 Skill层分析
            skill_analysis = await self._generate_skill_analysis(
                document_id, project_id, knowledge_graph_result, db
            )

            # 7.3 商业知识层分析
            business_analysis = await self._generate_business_analysis(
                document_id, project_id, keywords_result, knowledge_graph_result, db
            )

            result["stages_completed"].append("three_layer_analysis")
            result["analysis_results"]["reports"] = {
                "material_layer": material_analysis,
                "skill_layer": skill_analysis,
                "business_layer": business_analysis
            }

            # === 第8步：更新文档详情 ===
            logger.info("✅ 步骤10: 更新文档详情")
            await self._update_document_details(
                document_id, result["analysis_results"], db
            )

            result["success"] = True
            result["completed_at"] = datetime.utcnow().isoformat()

            logger.info(f"✅ 文档分析完成: {len(result['stages_completed'])}个阶段")

            return result

        except Exception as e:
            logger.error(f"❌ 文档分析失败: {e}", exc_info=True)
            result["success"] = False
            result["errors"].append(str(e))
            return result

    # ==================== 具体处理方法 ====================

    async def _transcribe_audio(
        self,
        file_path: str,
        document_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """音频转文字"""
        try:
            # 加载Whisper模型
            self.transcription_service.load_model()

            # 转录
            result = self.transcription_service.transcribe(
                audio_path=file_path,
                language="zh"
            )

            # 保存转录文本到数据库
            doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if doc:
                # 将转录文本作为文档内容
                doc.extracted_text = result.get('text', '')
                db.commit()

            return {
                "success": True,
                "text": result.get('text', ''),
                "segments": result.get('segments', []),
                "language": result.get('language', 'zh'),
                "duration": result.get('duration', 0)
            }

        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _extract_keywords(
        self,
        document_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """提取关键词（使用jieba或TF-IDF）"""
        try:
            import jieba.analyse

            # 获取所有chunks的文本
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            all_text = " ".join([chunk.text for chunk in chunks])

            # 提取关键词
            keywords = jieba.analyse.extract_tags(
                all_text,
                topK=50,
                withWeight=True
            )

            return {
                "success": True,
                "keywords": [
                    {"word": word, "weight": weight}
                    for word, weight in keywords
                ],
                "total_keywords": len(keywords)
            }

        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return {"success": False, "error": str(e)}

    async def _build_knowledge_graph(
        self,
        document_id: int,
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """构建知识图谱（调用现有的Knowledge Agent）"""
        try:
            from app.services.knowledge_graph_service import KnowledgeGraphService

            kg_service = KnowledgeGraphService()

            # 获取文档chunks
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            entities = []
            relations = []

            # 对每个chunk提取实体和关系
            for chunk in chunks:
                chunk_kg = kg_service.extract_knowledge(chunk.text)
                entities.extend(chunk_kg.get('entities', []))
                relations.extend(chunk_kg.get('relations', []))

            return {
                "success": True,
                "entities": entities,
                "relations": relations,
                "entity_count": len(entities),
                "relation_count": len(relations)
            }

        except Exception as e:
            logger.error(f"知识图谱构建失败: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_dashboard(
        self,
        document_id: int,
        project_id: int,
        keywords_result: Dict,
        knowledge_graph_result: Dict,
        db: Session
    ) -> Dict[str, Any]:
        """生成可视化看板数据"""
        try:
            # 构建可视化数据结构
            dashboard = {
                "keyword_cloud": keywords_result.get("keywords", [])[:30],
                "entity_distribution": self._calculate_entity_distribution(
                    knowledge_graph_result.get("entities", [])
                ),
                "relation_network": {
                    "nodes": knowledge_graph_result.get("entities", [])[:50],
                    "edges": knowledge_graph_result.get("relations", [])[:100]
                },
                "document_stats": {
                    "total_chunks": db.query(DocumentChunk).filter(
                        DocumentChunk.document_id == document_id
                    ).count(),
                    "total_entities": knowledge_graph_result.get("entity_count", 0),
                    "total_relations": knowledge_graph_result.get("relation_count", 0)
                }
            }

            return {
                "success": True,
                "dashboard": dashboard
            }

        except Exception as e:
            logger.error(f"看板生成失败: {e}")
            return {"success": False, "error": str(e)}

    async def _build_timeline(
        self,
        document_id: int,
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """构建时间线/编年史"""
        try:
            # 从文本中提取时间信息
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            timeline_events = []

            # 简单的时间提取（可以用更复杂的NER）
            import re
            date_pattern = r'\d{4}年|\d{4}-\d{2}|\d{2}/\d{2}/\d{4}'

            for chunk in chunks:
                dates = re.findall(date_pattern, chunk.text)
                for date in dates:
                    timeline_events.append({
                        "date": date,
                        "content": chunk.text[:100],
                        "chunk_id": chunk.chunk_id
                    })

            return {
                "success": True,
                "timeline": sorted(timeline_events, key=lambda x: x["date"]),
                "event_count": len(timeline_events)
            }

        except Exception as e:
            logger.error(f"时间线构建失败: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_material_analysis(
        self,
        document_id: int,
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """生成资料层分析报告"""
        try:
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            all_text = " ".join([chunk.text for chunk in chunks])

            analysis = {
                "document_structure": {
                    "total_chunks": len(chunks),
                    "avg_chunk_length": sum(len(c.text) for c in chunks) / len(chunks) if chunks else 0
                },
                "content_summary": all_text[:500] + "..." if len(all_text) > 500 else all_text,
                "word_count": len(all_text),
                "char_count": len(all_text)
            }

            return {
                "success": True,
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"资料层分析失败: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_skill_analysis(
        self,
        document_id: int,
        project_id: int,
        knowledge_graph_result: Dict,
        db: Session
    ) -> Dict[str, Any]:
        """生成Skill层分析报告"""
        try:
            # 调用现有的Skill分析
            from app.services.background_tasks import skill_analysis

            doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc or not doc.extracted_text:
                return {"success": False, "error": "文档内容为空"}

            # 运行所有Skill分析
            skill_results = {}
            skill_names = ["industry", "market", "technology", "finance"]

            for skill_name in skill_names:
                try:
                    result = skill_analysis(
                        skill_name,
                        document_id,
                        doc.extracted_text,
                        project_id,
                        db
                    )
                    skill_results[skill_name] = result
                except Exception as e:
                    logger.warning(f"Skill {skill_name} 分析失败: {e}")

            return {
                "success": True,
                "skill_results": skill_results
            }

        except Exception as e:
            logger.error(f"Skill层分析失败: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_business_analysis(
        self,
        document_id: int,
        project_id: int,
        keywords_result: Dict,
        knowledge_graph_result: Dict,
        db: Session
    ) -> Dict[str, Any]:
        """生成商业知识层分析报告"""
        try:
            # 结合关键词和知识图谱进行商业分析
            keywords = keywords_result.get("keywords", [])
            entities = knowledge_graph_result.get("entities", [])

            # 识别商业相关实体
            business_entities = [
                e for e in entities
                if e.get("type") in ["ORG", "COMPANY", "PRODUCT", "MONEY"]
            ]

            analysis = {
                "business_keywords": [k for k in keywords if k["weight"] > 0.1][:20],
                "business_entities": business_entities[:30],
                "business_insights": self._generate_business_insights(
                    keywords, business_entities
                )
            }

            return {
                "success": True,
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"商业层分析失败: {e}")
            return {"success": False, "error": str(e)}

    async def _update_document_details(
        self,
        document_id: int,
        analysis_results: Dict,
        db: Session
    ):
        """更新文档详情到数据库"""
        try:
            doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if doc:
                # 更新extra_data字段，存储所有分析结果
                if not doc.extra_data:
                    doc.extra_data = {}

                doc.extra_data.update({
                    "analysis_completed": True,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "keywords": analysis_results.get("keywords", {}),
                    "knowledge_graph": {
                        "entity_count": analysis_results.get("knowledge_graph", {}).get("entity_count", 0),
                        "relation_count": analysis_results.get("knowledge_graph", {}).get("relation_count", 0)
                    },
                    "reports_generated": True
                })

                doc.status = "completed"
                db.commit()

                logger.info(f"✅ 文档 {document_id} 详情已更新")

        except Exception as e:
            logger.error(f"更新文档详情失败: {e}")

    # ==================== 辅助方法 ====================

    def _calculate_entity_distribution(self, entities: List[Dict]) -> Dict[str, int]:
        """计算实体类型分布"""
        distribution = {}
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            distribution[entity_type] = distribution.get(entity_type, 0) + 1
        return distribution

    def _generate_business_insights(
        self,
        keywords: List[Dict],
        business_entities: List[Dict]
    ) -> List[str]:
        """生成商业洞察"""
        insights = []

        # 简单的规则生成洞察
        if len(business_entities) > 10:
            insights.append(f"文档涉及{len(business_entities)}个商业实体，商业相关性较高")

        high_weight_keywords = [k for k in keywords if k["weight"] > 0.15]
        if high_weight_keywords:
            top_words = ", ".join([k["word"] for k in high_weight_keywords[:5]])
            insights.append(f"核心主题关键词: {top_words}")

        return insights


# 创建全局实例
auto_analysis_engine = DocumentAutoAnalysisEngine()
