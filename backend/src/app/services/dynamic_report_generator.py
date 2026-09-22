"""
动态报告生成器 - 第三刀实现
废除预设模板，根据数据画像动态生成报告大纲和内容
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DynamicReportGenerator:
    """
    动态报告生成器

    核心原则：
    1. 先跑数据画像（Data Profiling）
    2. 根据画像动态生成大纲
    3. 按大纲检索内容填充
    4. 绝不生成预设维度（食/衣/住/行等）
    """
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def generate_report(
        self,
        project_id: int,
        report_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        生成动态报告

        Args:
            project_id: 项目ID
            report_type: 报告类型（auto=自动检测）

        Returns:
            {
                "title": "...",
                "outline": [...],
                "sections": [...],
                "metadata": {...}
            }
        """
        logger.info(f"🚀 开始生成动态报告（项目={project_id}）...")

        # 1. 加载项目所有文档的数据画像
        data_profiles = self._load_data_profiles(project_id)

        if not data_profiles:
            logger.warning("⚠️ 未找到数据画像，无法生成报告")
            return self._generate_empty_report(project_id)

        # 2. 聚合画像（跨文档）
        aggregated_profile = self._aggregate_profiles(data_profiles)

        # 3. 动态生成大纲
        outline = self._generate_dynamic_outline(aggregated_profile)

        # 4. 生成报告标题
        title = self._generate_title(aggregated_profile, project_id)

        # 5. 按大纲填充内容
        sections = self._fill_sections(outline, aggregated_profile, project_id)

        # 6. 构建完整报告
        report = {
            "title": title,
            "generated_at": datetime.now().isoformat(),
            "outline": outline,
            "sections": sections,
            "metadata": {
                "project_id": project_id,
                "document_count": len(data_profiles),
                "total_dimensions": len(aggregated_profile.get('discovered_dimensions', [])),
                "total_entities": len(aggregated_profile.get('key_entities', [])),
                "generation_mode": "dynamic"
            }
        }

        logger.info(f"✅ 动态报告生成完成（章节数={len(sections)}）")

        return report

    def _load_data_profiles(self, project_id: int) -> List[Dict[str, Any]]:
        """加载项目所有文档的数据画像"""
        from app.models.project import ProjectDocument

        docs = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        profiles = []

        for doc in docs:
            if doc.data_profile:
                profiles.append({
                    "document_id": doc.id,
                    "profile": doc.data_profile
                })
            elif doc.extra_data and 'dynamic_discovery' in doc.extra_data:
                # 兼容旧字段
                discovery = doc.extra_data['dynamic_discovery']
                if 'profile' in discovery:
                    profiles.append({
                        "document_id": doc.id,
                        "profile": discovery['profile']
                    })

        logger.info(f"📚 加载了 {len(profiles)} 个文档的数据画像")

        return profiles

    def _aggregate_profiles(self, profiles: List[Dict]) -> Dict[str, Any]:
        """聚合多个数据画像"""
        from collections import Counter

        # 聚合维度
        all_dimensions = []
        for p in profiles:
            dims = p['profile'].get('discovered_dimensions', [])
            all_dimensions.extend(dims)

        # 合并同名维度
        dimension_counter = Counter()
        dimension_keywords = {}

        for dim in all_dimensions:
            name = dim['dimension_name']
            dimension_counter[name] += dim.get('doc_count', 1)

            if name not in dimension_keywords:
                dimension_keywords[name] = set()
            dimension_keywords[name].update(dim.get('keywords', []))

        # 构建聚合维度
        aggregated_dimensions = []
        for name, count in dimension_counter.most_common(10):
            aggregated_dimensions.append({
                "dimension_name": name,
                "total_mentions": count,
                "keywords": list(dimension_keywords[name])[:10],
                "priority": count / len(profiles)  # 归一化优先级
            })

        # 聚合实体
        all_entities = []
        for p in profiles:
            entities = p['profile'].get('key_entities', [])
            all_entities.extend(entities)

        # 按canonical_name去重并计数
        entity_counter = Counter()
        entity_details = {}

        for entity in all_entities:
            name = entity.get('canonical_name', '')
            if not name:
                continue

            entity_counter[name] += entity.get('mention_count', 1)

            if name not in entity_details:
                entity_details[name] = entity

        # 构建聚合实体
        aggregated_entities = []
        for name, count in entity_counter.most_common(30):
            entity = entity_details[name].copy()
            entity['total_mentions'] = count
            aggregated_entities.append(entity)

        # 聚合时间跨度
        temporal_spans = [p['profile'].get('temporal_span', {}) for p in profiles]
        years = []
        for span in temporal_spans:
            if span.get('has_temporal'):
                years.append(span.get('earliest_year'))
                years.append(span.get('latest_year'))

        aggregated_temporal = {}
        if years:
            aggregated_temporal = {
                "has_temporal": True,
                "earliest_year": min(years),
                "latest_year": max(years),
                "span_years": max(years) - min(years) + 1
            }

        return {
            "discovered_dimensions": aggregated_dimensions,
            "key_entities": aggregated_entities,
            "temporal_span": aggregated_temporal,
            "document_count": len(profiles)
        }

    def _generate_dynamic_outline(self, profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """根据聚合画像动态生成大纲"""
        outline = []

        # 1. 概述章节（固定）
        outline.append({
            "chapter": "1. 概述",
            "reason": "总体情况介绍",
            "type": "overview"
        })

        # 2. 按发现的维度生成章节（数据驱动）
        dimensions = profile.get('discovered_dimensions', [])

        for idx, dim in enumerate(dimensions[:5], start=2):  # 最多5个维度
            outline.append({
                "chapter": f"{idx}. {dim['dimension_name']}",
                "reason": f"出现{dim['total_mentions']}次，关键词：{', '.join(dim['keywords'][:3])}",
                "type": "dimension",
                "dimension_data": dim
            })

        # 3. 关键主体章节（如果有高频实体）
        entities = profile.get('key_entities', [])
        person_entities = [e for e in entities if e.get('entity_type') == 'PERSON']
        org_entities = [e for e in entities if e.get('entity_type') == 'ORGANIZATION']

        if len(person_entities) >= 3:
            outline.append({
                "chapter": f"{len(outline)+1}. 关键人物",
                "reason": f"发现{len(person_entities)}个高频人物",
                "type": "entities",
                "entity_type": "PERSON"
            })

        if len(org_entities) >= 2:
            outline.append({
                "chapter": f"{len(outline)+1}. 相关组织",
                "reason": f"发现{len(org_entities)}个相关组织",
                "type": "entities",
                "entity_type": "ORGANIZATION"
            })

        # 4. 时间线章节（如果有时间跨度）
        temporal = profile.get('temporal_span', {})
        if temporal.get('has_temporal') and temporal.get('span_years', 0) > 1:
            outline.append({
                "chapter": f"{len(outline)+1}. 时间脉络",
                "reason": f"时间跨度：{temporal['earliest_year']}-{temporal['latest_year']}",
                "type": "temporal"
            })

        # 5. 总结章节（固定）
        outline.append({
            "chapter": f"{len(outline)+1}. 总结",
            "reason": "归纳与展望",
            "type": "conclusion"
        })

        logger.info(f"📝 动态生成大纲：{len(outline)}个章节")

        return outline

    def _generate_title(self, profile: Dict[str, Any], project_id: int) -> str:
        """根据数据画像生成报告标题"""
        dimensions = profile.get('discovered_dimensions', [])

        if not dimensions:
            return f"项目 {project_id} 分析报告"

        # 取最高优先级的维度作为标题关键词
        top_dimension = dimensions[0]['dimension_name']

        temporal = profile.get('temporal_span', {})
        if temporal.get('has_temporal'):
            year_range = f"{temporal['earliest_year']}-{temporal['latest_year']}"
            return f"{year_range}年{top_dimension}分析报告"
        else:
            return f"{top_dimension}专题分析报告"

    def _fill_sections(
        self,
        outline: List[Dict],
        profile: Dict[str, Any],
        project_id: int
    ) -> List[Dict[str, Any]]:
        """按大纲填充内容"""
        sections = []

        for item in outline:
            section_type = item.get('type', 'overview')

            if section_type == 'overview':
                content = self._generate_overview_section(profile, project_id)
            elif section_type == 'dimension':
                content = self._generate_dimension_section(item, profile, project_id)
            elif section_type == 'entities':
                content = self._generate_entities_section(item, profile, project_id)
            elif section_type == 'temporal':
                content = self._generate_temporal_section(profile, project_id)
            elif section_type == 'conclusion':
                content = self._generate_conclusion_section(profile, project_id)
            else:
                content = {"text": "（内容待补充）"}

            sections.append({
                "chapter": item['chapter'],
                "reason": item.get('reason', ''),
                "content": content
            })

        return sections

    def _generate_overview_section(self, profile: Dict, project_id: int) -> Dict:
        """生成概述章节"""
        dimensions = profile.get('discovered_dimensions', [])
        entities = profile.get('key_entities', [])
        doc_count = profile.get('document_count', 0)

        text = f"本报告基于 {doc_count} 份文档的智能分析，"
        text += f"自动发现 {len(dimensions)} 个主要维度、{len(entities)} 个关键实体。\n\n"

        if dimensions:
            text += "**发现的主要维度：**\n"
            for dim in dimensions[:3]:
                text += f"- {dim['dimension_name']}（提及{dim['total_mentions']}次）\n"

        return {
            "text": text,
            "stats": {
                "document_count": doc_count,
                "dimension_count": len(dimensions),
                "entity_count": len(entities)
            }
        }

    def _generate_dimension_section(self, item: Dict, profile: Dict, project_id: int) -> Dict:
        """生成维度章节"""
        dim_data = item.get('dimension_data', {})

        text = f"**{dim_data['dimension_name']}** 在本项目中共出现 {dim_data['total_mentions']} 次。\n\n"
        text += f"**关键词：** {', '.join(dim_data['keywords'][:8])}\n\n"
        text += "（详细内容基于原始文档检索生成）"

        return {
            "text": text,
            "keywords": dim_data['keywords']
        }

    def _generate_entities_section(self, item: Dict, profile: Dict, project_id: int) -> Dict:
        """生成实体章节"""
        entity_type = item.get('entity_type', 'PERSON')
        entities = profile.get('key_entities', [])

        filtered = [e for e in entities if e.get('entity_type') == entity_type]

        text = f"共发现 {len(filtered)} 个相关{'人物' if entity_type == 'PERSON' else '组织'}：\n\n"

        for entity in filtered[:10]:
            name = entity.get('canonical_name', '')
            mentions = entity.get('total_mentions', 0)
            aliases = entity.get('aliases', [])

            text += f"- **{name}**（提及{mentions}次）"
            if aliases:
                text += f"，别名：{', '.join(aliases[:3])}"
            text += "\n"

        return {
            "text": text,
            "entities": filtered[:10]
        }

    def _generate_temporal_section(self, profile: Dict, project_id: int) -> Dict:
        """生成时间线章节"""
        temporal = profile.get('temporal_span', {})

        text = f"时间跨度：{temporal['earliest_year']} - {temporal['latest_year']} "
        text += f"（共{temporal['span_years']}年）\n\n"
        text += "（详细时间线基于文档中的时间标记生成）"

        return {
            "text": text,
            "temporal": temporal
        }

    def _generate_conclusion_section(self, profile: Dict, project_id: int) -> Dict:
        """生成总结章节"""
        dimensions = profile.get('discovered_dimensions', [])

        text = "通过对项目文档的智能分析，本报告自动发现了以下主要维度：\n\n"

        for idx, dim in enumerate(dimensions, 1):
            text += f"{idx}. {dim['dimension_name']}\n"

        text += "\n建议后续工作可针对上述维度进行深入研究。"

        return {
            "text": text
        }

    def _generate_empty_report(self, project_id: int) -> Dict[str, Any]:
        """生成空报告（无数据时）"""
        return {
            "title": f"项目 {project_id} 分析报告",
            "generated_at": datetime.now().isoformat(),
            "outline": [],
            "sections": [],
            "metadata": {
                "project_id": project_id,
                "document_count": 0,
                "generation_mode": "empty"
            },
            "error": "无可用数据画像"
        }


def generate_dynamic_report(project_id: int, db: Session) -> Dict[str, Any]:
    """
    便捷函数：生成动态报告

    Args:
        project_id: 项目ID
        db: 数据库会话

    Returns:
        动态生成的报告字典
    """
    generator = DynamicReportGenerator(db)
    return generator.generate_report(project_id)
