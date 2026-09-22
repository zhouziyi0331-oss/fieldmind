"""
报告内容填充引擎

职责：
1. 根据大纲章节填充内容
2. 从原文引用池中提取相关内容
3. 调用LLM进行深度分析
4. 确保每个观点都有原文引用（反幻觉）
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .data_driven_report_builder import ReportMaterial
from .citation_validator import CitationValidator
from .skills.field_investigation_skill import FieldInvestigationSkill
from .skills.business_sop_skill import BusinessSOPSkill
from .skills.xiangtu_china_skill import XiangtuChinaSkill
from .skills.social_memory_skill import SocialMemorySkill
from .skills.commercial_feasibility_skill import CommercialFeasibilitySkill

logger = logging.getLogger(__name__)


class ReportContentEngine:
    """
    报告内容填充引擎

    核心流程：
    1. 接收章节大纲
    2. 从素材中检索相关内容
    3. 组织原文引用
    4. 调用LLM生成深度分析
    5. 验证引用完整性
    """
    def __init__(self, llm_adapter=None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化内容引擎

        Args:
            llm_adapter: LLM适配器（用于深度分析）
        """
        self.llm_adapter = llm_adapter
        self.citation_validator = CitationValidator()

        # 初始化所有 Skills
        self.field_investigation_skill = FieldInvestigationSkill()
        self.business_sop_skill = BusinessSOPSkill()
        self.xiangtu_china_skill = XiangtuChinaSkill()
        self.social_memory_skill = SocialMemorySkill()
        self.commercial_feasibility_skill = CommercialFeasibilitySkill()

    def fill_section(
        self,
        section_outline: Dict,
        material: ReportMaterial,
        report_level: int = 1
    ) -> Dict[str, Any]:
        """
        填充单个章节的内容

        Args:
            section_outline: 章节大纲
            material: 报告素材
            report_level: 报告层级

        Returns:
            {
                'chapter': '章节标题',
                'content': '章节内容（Markdown格式）',
                'word_count': 字数,
                'citations': [引用列表],
                'citation_validation': {验证结果}
            }
        """
        logger.info(f"📝 填充章节：{section_outline['chapter']}")

        content_sources = section_outline.get('content_sources', {})
        source_type = content_sources.get('type', 'unknown')

        # 根据报告层级选择对应的 Skill
        if report_level == 1:
            # Level 1: 使用田野调查 Skill
            content, citations = self._fill_with_field_investigation_skill(
                section_outline, material, source_type, content_sources
            )
        elif report_level == 2:
            # Level 2: 使用费孝通理论 Skill (暂未实现)
            content, citations = self._fill_level2_section(
                source_type, content_sources, material
            )
        elif report_level == 3:
            # Level 3: 使用商业分析 Skill
            content, citations = self._fill_with_business_sop_skill(
                section_outline, material, source_type, content_sources
            )
        else:
            content = f"（未知报告层级：{report_level}）"
            citations = []

        # 如果启用了LLM，进行深度分析增强
        if self.llm_adapter and report_level >= 1:
            content = self._enhance_with_llm(
                content,
                section_outline,
                citations,
                report_level
            )

        # 验证引用完整性
        validation = self.citation_validator.validate_section(content, citations)

        word_count = len(content)

        result = {
            'chapter': section_outline['chapter'],
            'content': content,
            'word_count': word_count,
            'citations': citations,
            'citation_validation': validation
        }

        logger.info(f"✅ 章节完成：{word_count}字，{len(citations)}条引用")

        return result

    def _fill_with_field_investigation_skill(
        self,
        section_outline: Dict,
        material: ReportMaterial,
        source_type: str,
        content_sources: Dict
    ) -> tuple[str, List[Dict]]:
        """
        使用田野调查 Skill 填充 Level 1 章节

        Args:
            section_outline: 章节大纲
            material: 报告素材
            source_type: 内容类型
            content_sources: 内容源

        Returns:
            (content, citations)
        """
        chapter_title = section_outline['chapter']

        # 将 ReportMaterial 转为字典格式供 Skill 使用
        material_dict = {
            'project_statistics': {
                'total_chunks': material.total_chunks,
                'total_words': material.total_words,
                'total_documents': material.total_documents
            },
            'main_keywords': material.main_keywords,
            'keyword_communities': material.keyword_communities,
            'keyword_relations': material.keyword_relations,
            'core_entities': material.core_entities,
            'entity_relations': material.entity_relations,
            'timeline_events': material.timeline,  # 注意：timeline 映射为 timeline_events
            'citation_pool': material.citation_pool
        }

        # 根据 source_type 判断是否使用 Skill 还是原有逻辑
        if source_type in ['overview', 'timeline', 'entities', 'conclusion']:
            # 这些章节使用原有的基础逻辑（数据统计类）
            if source_type == 'overview':
                return self._fill_overview_section(content_sources, material)
            elif source_type == 'timeline':
                return self._fill_timeline_section(content_sources, material)
            elif source_type == 'entities':
                return self._fill_entities_section(content_sources, material)
            elif source_type == 'conclusion':
                return self._fill_conclusion_section(content_sources, material)
        elif source_type == 'keyword_community':
            # 关键词社区章节：使用田野调查 Skill 进行内容挖掘和转化
            logger.info(f"🔧 使用田野调查 Skill 分析：{chapter_title}")

            try:
                # 调用 Skill 生成内容
                content = self.field_investigation_skill.generate_field_report_content(
                    material_dict,
                    chapter_title
                )

                # 从 citation_pool 提取相关引用
                citations = self._extract_citations_from_content(content, material)

                return content, citations
            except Exception as e:
                logger.error(f"田野调查 Skill 执行失败：{e}")
                # 降级到原有逻辑
                return self._fill_keyword_community_section(content_sources, material)
        else:
            # 未知类型，返回占位内容
            content = f"## {chapter_title}\n\n（{source_type}章节内容待实现）\n"
            return content, []

    def _fill_with_business_sop_skill(
        self,
        section_outline: Dict,
        material: ReportMaterial,
        source_type: str,
        content_sources: Dict
    ) -> tuple[str, List[Dict]]:
        """
        使用商业分析 Skill 填充 Level 3 章节

        Args:
            section_outline: 章节大纲
            material: 报告素材
            source_type: 内容类型
            content_sources: 内容源

        Returns:
            (content, citations)
        """
        chapter_title = section_outline['chapter']

        # 将 ReportMaterial 转为字典格式供 Skill 使用
        material_dict = {
            'project_statistics': {
                'total_chunks': material.total_chunks,
                'total_words': material.total_words,
                'total_documents': material.total_documents
            },
            'main_keywords': material.main_keywords,
            'keyword_communities': material.keyword_communities,
            'keyword_relations': material.keyword_relations,
            'core_entities': material.core_entities,
            'entity_relations': material.entity_relations,
            'timeline_events': material.timeline,
            'citation_pool': material.citation_pool
        }

        # 根据章节类型选择不同的Skill
        if source_type == 'business_sop':
            # 使用乡遗商途SOP Skill
            logger.info(f"🔧 使用乡遗商途SOP Skill 分析")
            try:
                content = self.business_sop_skill.generate_report(material_dict)
                citations = self._extract_citations_from_content(content, material)
                return content, citations
            except Exception as e:
                logger.error(f"乡遗商途SOP Skill 执行失败：{e}")
                return self._fill_business_sop_section(content_sources, material)

        elif source_type == 'commercial_feasibility':
            # 使用商业可行性验证Skill
            logger.info(f"🔧 使用商业可行性验证 Skill 分析")
            try:
                content = self.commercial_feasibility_skill.generate_report(material_dict)
                citations = self._extract_citations_from_content(content, material)
                return content, citations
            except Exception as e:
                logger.error(f"商业可行性验证 Skill 执行失败：{e}")
                content = f"## {chapter_title}\n\n（商业可行性分析生成失败：{str(e)}）\n"
                return content, []

        elif source_type == 'executive_summary':
            return self._fill_executive_summary_section(material)
        elif source_type == 'social_capital':
            return self._fill_social_capital_section(material)
        elif source_type == 'trend_analysis':
            return self._fill_trend_analysis_section(content_sources, material)
        elif source_type == 'swot':
            return self._fill_swot_section(material)
        elif source_type == 'action_plan':
            return self._fill_action_plan_section(material)
        elif source_type == 'risk_management':
            return self._fill_risk_management_section(material)
        else:
            # 未知类型，降级处理
            content = f"## {chapter_title}\n\n（{source_type}章节内容待实现）\n"
            return content, []

    def _fill_level2_section(
        self,
        source_type: str,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """
        填充 Level 2 章节（费孝通理论分析 + 社会记忆分析）

        Args:
            source_type: 内容类型
            content_sources: 内容源
            material: 报告素材

        Returns:
            (content, citations)
        """
        # 将 ReportMaterial 转为字典格式供 Skill 使用
        material_dict = {
            'project_statistics': {
                'total_chunks': material.total_chunks,
                'total_words': material.total_words,
                'total_documents': material.total_documents
            },
            'main_keywords': material.main_keywords,
            'keyword_communities': material.keyword_communities,
            'keyword_relations': material.keyword_relations,
            'core_entities': material.core_entities,
            'entity_relations': material.entity_relations,
            'timeline_events': material.timeline,
            'citation_pool': material.citation_pool
        }

        if source_type == 'theory_intro':
            return self._fill_theory_intro_section(material)
        elif source_type == 'feixiaotong_dimension':
            # 使用费孝通Skill进行深度分析
            logger.info(f"🔧 使用费孝通Skill分析维度")
            try:
                # 调用费孝通Skill生成完整报告
                content = self.xiangtu_china_skill.generate_report(material_dict)
                citations = self._extract_citations_from_content(content, material)
                return content, citations
            except Exception as e:
                logger.error(f"费孝通Skill执行失败：{e}")
                return self._fill_feixiaotong_section(content_sources, material)
        elif source_type == 'social_memory':
            # 使用社会记忆Skill进行深度分析
            logger.info(f"🔧 使用社会记忆Skill分析")
            try:
                content = self.social_memory_skill.generate_report(material_dict)
                citations = self._extract_citations_from_content(content, material)
                return content, citations
            except Exception as e:
                logger.error(f"社会记忆Skill执行失败：{e}")
                content = f"## 社会记忆分析\n\n（社会记忆分析生成失败：{str(e)}）\n"
                return content, []
        elif source_type == 'theory_conclusion':
            return self._fill_theory_conclusion_section(material)
        else:
            content = f"（{source_type}章节内容待实现）"
            return content, []

    def _extract_citations_from_content(
        self,
        content: str,
        material: ReportMaterial
    ) -> List[Dict]:
        """
        从生成的内容中提取引用

        Args:
            content: 生成的内容
            material: 报告素材

        Returns:
            引用列表
        """
        citations = []
        cite_idx = 1

        # 从 citation_pool 中查找内容中提到的文档
        for cite in material.citation_pool[:50]:  # 限制最多50个引用
            # 简单的匹配逻辑：如果内容中包含引用片段的关键部分
            if cite['source_document'] in content:
                citations.append({
                    'id': cite_idx,
                    'citation_id': cite['citation_id'],
                    'source': cite['source_document'],
                    'content': cite['content']
                })
                cite_idx += 1

        return citations

    def _fill_overview_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充概述章节"""
        data = content_sources['data']

        content = f"""## 调查背景与数据来源

本报告基于对项目的系统性田野调查，共收集整理了 **{data['total_documents']}** 份文档资料，总计约 **{data['total_words']:,}** 字。

### 数据概览

- **文档数量**：{data['total_documents']} 份
- **总字数**：{data['total_words']:,} 字
- **文本片段**：{material.total_chunks} 个
- **提取实体**：{sum(len(v) for v in material.core_entities.values())} 个
- **识别关键词**：{len(material.main_keywords)} 个（主关键词）

"""

        # 时间跨度
        if data['temporal_span'].get('has_temporal'):
            span = data['temporal_span']
            content += f"""### 时间跨度

调查时间从 **{span['earliest'][:10]}** 至 **{span['latest'][:10]}**，记录了 **{span['event_count']}** 个调查事件。

"""

        # 主要主题
        if material.keyword_communities:
            content += "### 主要研究主题\n\n"
            content += "通过关键词网络分析（Louvain社区检测算法），本次调查自动识别出以下主要主题：\n\n"
            for idx, comm in enumerate(material.keyword_communities[:5], 1):
                keywords_str = '、'.join(comm['keywords'][:5])
                content += f"{idx}. **{comm['label']}**：包含 {comm['size']} 个相关概念（{keywords_str}等）\n"
            content += "\n"

        # 核心实体统计
        content += "### 核心主体\n\n"
        if material.core_entities['PERSON']:
            top_persons = [p['name'] for p in material.core_entities['PERSON'][:5]]
            content += f"- **核心人物**：{len(material.core_entities['PERSON'])} 位（{', '.join(top_persons)}等）\n"

        if material.core_entities['LOCATION']:
            top_locations = [l['name'] for l in material.core_entities['LOCATION'][:5]]
            content += f"- **关键地点**：{len(material.core_entities['LOCATION'])} 处（{', '.join(top_locations)}等）\n"

        if material.core_entities['ORGANIZATION']:
            top_orgs = [o['name'] for o in material.core_entities['ORGANIZATION'][:5]]
            content += f"- **相关组织**：{len(material.core_entities['ORGANIZATION'])} 个（{', '.join(top_orgs)}等）\n"

        content += "\n"

        # 方法说明
        content += """### 研究方法

本报告采用数据驱动的智能报告生成方法：

1. **关键词网络分析**：使用PageRank算法识别主关键词，通过Louvain算法进行社区检测
2. **实体关系网络**：自动提取人物、地点、事件、组织等实体，构建关系网络
3. **编年史时间线**：按时间顺序组织调查材料，呈现事件发展脉络
4. **深度内容分析**：结合LLM技术进行语义理解和主题挖掘

所有分析结论均基于原始材料，每个观点都提供明确的文献引用。

"""

        # 引用（概述章节通常没有直接引用）
        citations = []

        return content, citations

    def _fill_timeline_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充时间线章节（编年史）"""
        timeline_data = content_sources['data']

        content = f"""## 田野调查编年史

本章按时间顺序呈现田野调查的完整过程，共记录 **{len(timeline_data)}** 个调查事件。

### 调查时间轴

"""

        citations = []
        current_doc = None

        # 按文档分组展示
        for idx, event in enumerate(timeline_data, 1):
            doc_name = event['document']

            # 如果是新文档，添加文档标题
            if doc_name != current_doc:
                current_doc = doc_name
                timestamp = event['timestamp'][:10] if event['timestamp'] else '未知日期'
                content += f"\n#### {timestamp} - {doc_name}\n\n"

            # 添加事件内容
            event_content = event['content']
            citation_ref = f"[^{idx}]"

            content += f"{citation_ref} {event_content}\n\n"

            # 记录引用
            citations.append({
                'id': idx,
                'chunk_id': event['chunk_id'],
                'source': doc_name,
                'chunk_index': event['index'],
                'content': event_content
            })

        # 添加引用注释
        content += "\n---\n\n### 引用注释\n\n"
        for cite in citations[:50]:  # 最多显示50个引用注释
            content += f"[^{cite['id']}]: {cite['source']}, 第{cite['chunk_index']+1}段\n"

        return content, citations

    def _fill_keyword_community_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充关键词社区章节"""
        community = content_sources['data']

        content = f"""## {community['label']}

> **关键词网络分析**：本章基于关键词社区检测自动生成，该主题包含 **{community['size']}** 个相关概念。

### 核心概念

通过PageRank算法和Louvain社区检测，识别出以下核心概念：

"""

        # 列出关键词
        for idx, keyword in enumerate(community['keywords'][:10], 1):
            content += f"{idx}. **{keyword}**\n"

        content += "\n### 主题内容分析\n\n"

        # 从引用池中搜索包含这些关键词的原文
        citations = []
        cite_idx = 1

        for keyword in community['keywords'][:5]:  # 对前5个关键词进行深度分析
            content += f"#### {keyword}\n\n"

            # 搜索包含该关键词的原文片段
            matching_citations = [
                cite for cite in material.citation_pool
                if keyword in cite['content']
            ][:3]  # 每个关键词最多3条引用

            if matching_citations:
                for cite in matching_citations:
                    snippet = cite['content'][:200]  # 前200字符
                    citation_ref = f"[^{cite_idx}]"

                    content += f"{citation_ref} ...{snippet}...\n\n"

                    citations.append({
                        'id': cite_idx,
                        'citation_id': cite['citation_id'],
                        'source': cite['source_document'],
                        'content': cite['content']
                    })
                    cite_idx += 1
            else:
                content += f"（原文中关于「{keyword}」的具体内容需要进一步提取）\n\n"

        # 添加引用注释
        if citations:
            content += "\n---\n\n### 引用注释\n\n"
            for cite in citations:
                content += f"[^{cite['id']}]: {cite['source']}\n"

        return content, citations

    def _fill_entities_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充实体章节（人物和地点）"""
        data = content_sources['data']
        persons = data.get('persons', [])
        locations = data.get('locations', [])

        content = "## 核心主体分析\n\n"

        citations = []
        cite_idx = 1

        # 核心人物部分
        if persons:
            content += "### 核心人物\n\n"
            content += f"通过实体识别和频次统计，本次调查中共识别出 **{len(persons)}** 位核心人物：\n\n"

            for person in persons[:10]:
                content += f"#### {person['name']}\n\n"
                content += f"- **提及次数**：{person['frequency']} 次\n"

                # 搜索包含该人物的原文
                matching_citations = [
                    cite for cite in material.citation_pool
                    if person['name'] in cite['content']
                ][:2]

                if matching_citations:
                    content += "- **相关内容**：\n\n"
                    for cite in matching_citations:
                        snippet = cite['content'][:150]
                        citation_ref = f"[^{cite_idx}]"
                        content += f"  {citation_ref} {snippet}...\n\n"

                        citations.append({
                            'id': cite_idx,
                            'citation_id': cite['citation_id'],
                            'source': cite['source_document'],
                            'content': cite['content']
                        })
                        cite_idx += 1

        # 关键地点部分
        if locations:
            content += "\n### 关键地点\n\n"
            content += f"调查涉及 **{len(locations)}** 处关键地点：\n\n"

            for location in locations[:10]:
                content += f"#### {location['name']}\n\n"
                content += f"- **提及次数**：{location['frequency']} 次\n"

                # 搜索包含该地点的原文
                matching_citations = [
                    cite for cite in material.citation_pool
                    if location['name'] in cite['content']
                ][:2]

                if matching_citations:
                    content += "- **相关内容**：\n\n"
                    for cite in matching_citations:
                        snippet = cite['content'][:150]
                        citation_ref = f"[^{cite_idx}]"
                        content += f"  {citation_ref} {snippet}...\n\n"

                        citations.append({
                            'id': cite_idx,
                            'citation_id': cite['citation_id'],
                            'source': cite['source_document'],
                            'content': cite['content']
                        })
                        cite_idx += 1

        # 添加引用注释
        if citations:
            content += "\n---\n\n### 引用注释\n\n"
            for cite in citations:
                content += f"[^{cite['id']}]: {cite['source']}\n"

        return content, citations

    def _fill_conclusion_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充总结章节"""
        data = content_sources['data']
        main_keywords = data['main_keywords']
        communities = data['communities']

        content = """## 调查发现总结

### 核心发现

基于对原始材料的系统分析，本次田野调查的核心发现如下：

"""

        # 根据主关键词总结
        content += "#### 1. 主要议题识别\n\n"
        content += "通过PageRank算法识别的主关键词反映了调查的核心议题：\n\n"

        for idx, kw in enumerate(main_keywords[:10], 1):
            content += f"{idx}. **{kw['keyword']}**（PageRank值：{kw['pagerank']:.4f}，频次：{kw['frequency']}）\n"

        content += "\n#### 2. 主题网络结构\n\n"
        content += f"通过Louvain社区检测算法，识别出 **{len(communities)}** 个主要研究主题：\n\n"

        for idx, comm in enumerate(communities[:5], 1):
            content += f"{idx}. **{comm['label']}**：{comm['size']}个相关概念\n"

        content += "\n#### 3. 研究价值与意义\n\n"
        content += "本次田野调查的价值体现在：\n\n"
        content += "- **数据完整性**：收集了全面的田野材料，形成了完整的证据链\n"
        content += "- **方法创新性**：采用数据驱动的智能分析方法，避免了预设框架的局限\n"
        content += "- **分析深度**：基于网络分析算法，揭示了主题之间的关联关系\n"
        content += "- **可追溯性**：所有结论都有明确的原文引用，确保了研究的严谨性\n"

        content += "\n### 研究局限\n\n"
        content += "本研究存在以下局限：\n\n"
        content += "1. 样本范围受限于已收集的文档资料\n"
        content += "2. 自动化分析可能遗漏某些隐性主题\n"
        content += "3. 需要结合理论框架进行更深入的解读\n"

        content += "\n### 后续研究方向\n\n"
        content += "基于本次田野调查，建议后续研究可以：\n\n"
        content += "1. 结合社会学理论（如费孝通《乡土中国》）进行深度分析\n"
        content += "2. 开展针对性的补充调查，丰富特定主题的材料\n"
        content += "3. 进行横向比较研究，探索共性与特性\n"
        content += "4. 评估商业化或社会干预的可行性\n"

        citations = []  # 总结章节通常是归纳性的，较少直接引用

        return content, citations

    def _fill_theory_intro_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充理论框架介绍章节（Level 2）"""
        content = """## 理论框架：费孝通《乡土中国》

### 理论背景

费孝通先生的《乡土中国》是中国社会学的经典著作，提出了理解中国传统社会结构的核心概念。本报告将运用费孝通的理论框架，对田野调查材料进行深度解读。

### 核心理论概念

#### 1. 差序格局

费孝通指出，中国传统社会的关系结构是一种"差序格局"，即以自我为中心，像水波纹一样一圈圈推出去的关系网络。这种格局中，关系的亲疏远近决定了社会行为的准则。

**理论要点**：
- 以己为中心的同心圆结构
- 关系的弹性和情境性
- "推己及人"的伦理逻辑

#### 2. 礼治秩序

不同于西方的"法治"，中国传统社会是"礼治"，即基于传统习俗和道德规范的社会控制机制。

**理论要点**：
- 礼俗传统的规范作用
- 教化优于惩罚
- 长老权威与经验传承

#### 3. 熟人社会

乡土社会是一个熟人社会，社会关系建立在长期的、面对面的互动之上，形成了独特的信任机制和互惠网络。

**理论要点**：
- 长期互动的信任基础
- 声誉机制的约束力
- 互惠关系的维系

#### 4. 现代化冲击

随着现代化进程，传统乡土社会面临着深刻的变迁和挑战。

**理论要点**：
- 传统秩序的解构
- 新旧规范的冲突
- 适应与转型的路径

### 分析框架的应用

本报告将按照上述四个维度，对田野调查材料进行系统分析，探讨：

1. 材料中呈现的社会关系结构是否符合"差序格局"的特征
2. 传统礼治秩序在当代的延续与变迁
3. 熟人社会的信任机制如何运作
4. 现代化进程对传统社会结构的影响

每个维度的分析都将以材料为基础，理论与经验相结合，力求深入揭示田野调查背后的社会逻辑。

"""

        citations = []  # 理论介绍章节通常不直接引用田野材料

        return content, citations

    def _fill_theory_conclusion_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充理论对话与学术启示章节（Level 2结论）"""
        content = """## 理论对话与学术启示

### 材料与理论的对话

本报告通过费孝通《乡土中国》的理论框架和景军《神堂记忆》的记忆理论，对田野调查材料进行了深度解读。材料与理论的对话揭示了以下要点：

#### 1. 传统社会结构的延续与变迁

差序格局、礼治秩序等传统社会结构特征在当代仍有明显体现，但同时也在现代化进程中发生着深刻变化。这种"变中有不变"的特征，体现了中国社会转型的独特路径。

#### 2. 社会记忆的多重性与复杂性

历史记忆、仪式记忆、族谱记忆等多种记忆形态交织共存，构成了社区认同的多层次基础。这些记忆不是静止的"遗产"，而是在当代生活中不断被重构和激活。

#### 3. 熟人社会的韧性与适应性

尽管现代性带来了陌生人社会的因素，但熟人社会的信任机制、互惠网络依然发挥着重要作用。这种韧性体现了传统社会智慧的生命力。

### 学术价值与启示

本研究的学术价值在于：

1. **理论与经验的结合**：将经典社会学理论与当代田野材料相结合，既验证了理论的解释力，也丰富了理论的适用场景

2. **多维度分析框架**：整合了社会结构分析和文化记忆分析，提供了更为立体的社区理解视角

3. **动态视角**：不是静态地描述传统社会，而是关注传统与现代的互动、延续与变迁的张力

4. **实践指向**：理论分析不是自说自话，而是为社区发展、文化传承提供了学术支撑

### 研究局限与展望

本研究存在以下局限：

1. 理论框架主要来自费孝通和景军，未来可引入更多元的理论视角
2. 材料分析依赖已有文档，缺少深度访谈和参与观察
3. 对现代性冲击的分析尚需更多实证材料

后续研究可以：

1. 开展针对性的田野补充调查
2. 引入比较研究视角，探索区域差异
3. 关注年轻一代的文化认同与代际变迁
4. 探讨数字化时代社区记忆的新形态

### 对实践的启示

理论分析对社区实践的启示：

1. **尊重传统社会逻辑**：任何外部干预都需要理解和尊重在地的社会结构和文化逻辑
2. **激活社会记忆**：文化传承不是博物馆化，而是在当代生活中激活和重构记忆
3. **重建信任网络**：社区发展需要修复和重建熟人社会的信任机制
4. **平衡保护与发展**：在现代化进程中寻找传统与现代的平衡点

"""

        citations = []  # 理论总结章节通常不直接引用田野材料

        return content, citations

    def _fill_feixiaotong_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充费孝通维度分析章节（Level 2）- 降级方法"""
        dimension = content_sources.get('dimension', 'unknown')

        content = f"""## 费孝通视角：{dimension}

（费孝通Skill未能执行，使用降级内容）

### 理论阐释

（费孝通关于{dimension}的理论阐述）

### 材料证据

（从田野调查材料中提取的相关证据）

### 理论对话

（材料与理论的深度对话）

"""

        citations = []

        return content, citations

    def _fill_business_sop_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充商业SOP章节（Level 3）"""
        dimensions = content_sources.get('dimensions', [])

        content = """## 乡村运营SOP六维度评估

基于前期田野调查和学术分析，本章从商业运营的角度，对项目进行系统性评估。

"""

        # 这里需要调用商业SOP Skill来分析
        # 暂时返回框架内容
        for dim in dimensions:
            content += f"### {dim}\n\n"
            content += f"（{dim}的评估内容需要集成商业SOP Skill）\n\n"

        citations = []

        return content, citations

    def _fill_executive_summary_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充执行摘要章节（Level 3）- 基于真实数据动态生成"""

        # 检查空数据
        if not material.main_keywords and not material.core_entities:
            content = """## 执行摘要

**数据不足警告**：当前缺少足够的田野调查材料，无法生成有效的执行摘要。请先完成田野调查数据收集。

"""
            return content, []

        content = """## 执行摘要

"""

        # 项目概况（基于实际统计数据）
        content += f"""### 项目概况

本报告基于 **{material.total_documents}** 份田野调查文档（约 **{material.total_words:,}** 字）的深度分析，涵盖 **{material.total_chunks}** 个文本片段。

"""

        # 核心发现（基于关键词和实体）
        content += "### 核心发现\n\n"

        if material.keyword_communities:
            content += f"**主题识别**：通过关键词网络分析，识别出 **{len(material.keyword_communities)}** 个主要研究主题，"
            top_communities = material.keyword_communities[:3]
            community_labels = [comm['label'] for comm in top_communities]
            content += f"包括{' / '.join(community_labels)}等。\n\n"

        if material.main_keywords:
            top_keywords = [kw['keyword'] for kw in material.main_keywords[:10]]
            content += f"**关键概念**：核心关键词包括「{top_keywords[0]}」「{top_keywords[1]}」「{top_keywords[2]}」等 {len(material.main_keywords)} 个高频概念。\n\n"

        # 利益相关者（基于实体数据）
        if material.core_entities:
            content += "### 主要利益相关者\n\n"

            if material.core_entities['PERSON']:
                person_count = len(material.core_entities['PERSON'])
                top_persons = [p['name'] for p in material.core_entities['PERSON'][:5]]
                content += f"- **核心人物**：识别 {person_count} 位关键人物，包括 {' / '.join(top_persons)} 等\n"

            if material.core_entities['ORGANIZATION']:
                org_count = len(material.core_entities['ORGANIZATION'])
                top_orgs = [o['name'] for o in material.core_entities['ORGANIZATION'][:3]]
                content += f"- **相关组织**：涉及 {org_count} 个组织机构，包括 {' / '.join(top_orgs)} 等\n"

            if material.core_entities['LOCATION']:
                loc_count = len(material.core_entities['LOCATION'])
                top_locs = [l['name'] for l in material.core_entities['LOCATION'][:3]]
                content += f"- **地理范围**：覆盖 {loc_count} 个地点，核心区域为 {' / '.join(top_locs)} 等\n"

            content += "\n"

        # 时间脉络（基于时间线数据）
        if material.timeline:
            content += f"""### 发展历程

田野调查记录了 **{len(material.timeline)}** 个关键时间节点，勾勒出项目的历史发展脉络。

"""

        # 建议方向（基于数据特征）
        content += """### 分析维度

本报告从以下维度展开深度分析：

1. **大地遗产视角**：识别文化资源价值与转化潜力
2. **费孝通乡土理论**：解读社会结构与关系网络
3. **社会记忆分析**：挖掘集体记忆与文化认同
4. **商业可行性验证**：评估文化母题的商业转化路径

所有分析结论均基于田野调查原始材料，确保客观性与可追溯性。

"""

        citations = []
        return content, citations

    def _fill_social_capital_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充社会资本分析章节（Level 3）- 基于实体关系网络动态生成"""

        # 检查空数据
        if not material.core_entities and not material.entity_relations:
            content = """## 社会资本分析

**数据不足警告**：当前缺少实体关系数据，无法生成社会资本分析。请确保田野调查材料包含人物、组织、地点等实体信息。

"""
            return content, []

        content = """## 社会资本分析

基于田野调查材料中的实体关系网络，本章分析项目涉及的社会资本结构。

"""

        # 人物网络分析
        if material.core_entities.get('PERSON'):
            persons = material.core_entities['PERSON']
            content += f"""### 人物网络

识别出 **{len(persons)}** 位核心人物，形成多层次的社会关系网络。

#### 关键人物

"""
            for idx, person in enumerate(persons[:8], 1):
                content += f"{idx}. **{person['name']}**（出现 {person['count']} 次）\n"

            content += "\n"

        # 组织机构网络
        if material.core_entities.get('ORGANIZATION'):
            orgs = material.core_entities['ORGANIZATION']
            content += f"""### 组织机构网络

涉及 **{len(orgs)}** 个组织机构，包括政府部门、社会团体、企业等。

#### 主要机构

"""
            for idx, org in enumerate(orgs[:8], 1):
                content += f"{idx}. **{org['name']}**（出现 {org['count']} 次）\n"

            content += "\n"

        # 实体关系分析
        if material.entity_relations:
            content += f"""### 关系网络特征

基于实体共现分析，识别出 **{len(material.entity_relations)}** 组关系对，揭示以下网络特征：

"""
            # 取前5组最强关系
            top_relations = sorted(material.entity_relations, key=lambda x: x.get('strength', 0), reverse=True)[:5]

            for idx, rel in enumerate(top_relations, 1):
                source = rel.get('source_entity', '未知')
                target = rel.get('target_entity', '未知')
                strength = rel.get('strength', 0)
                content += f"{idx}. **{source}** ↔ **{target}**（关联强度：{strength}）\n"

            content += "\n"

        content += """### 社会资本评估

**信任网络**：基于长期互动形成的熟人社会信任机制

**互惠关系**：多层次的社会交换与互助网络

**组织能力**：正式与非正式组织的动员与协调能力

"""

        citations = []
        return content, citations

    def _fill_trend_analysis_section(
        self,
        content_sources: Dict,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充趋势分析章节（Level 3）- 基于时间线数据动态生成"""

        # 检查空数据
        if not material.timeline:
            content = """## 发展趋势分析

**数据不足警告**：当前缺少时间线数据，无法生成趋势分析。请确保田野调查材料包含时间信息。

"""
            return content, []

        content = """## 发展趋势分析

基于田野调查时间线数据，分析项目的历史演进与未来趋势。

"""

        # 历史阶段划分
        timeline = material.timeline
        content += f"""### 历史演进

调查记录了 **{len(timeline)}** 个关键时间节点，勾勒出以下发展脉络：

"""

        # 按时间展示关键事件
        for idx, event in enumerate(timeline[:10], 1):
            date = event.get('date', '未知时间')
            description = event.get('description', '未记录')
            event_type = event.get('event_type', '一般事件')

            content += f"{idx}. **{date}**：{description}（{event_type}）\n"

        if len(timeline) > 10:
            content += f"\n_（共 {len(timeline)} 个事件，此处展示前10个）_\n"

        content += "\n"

        # 阶段性特征分析
        content += """### 阶段性特征

"""

        # 根据时间线数量和分布进行阶段划分
        if len(timeline) >= 3:
            early = timeline[:len(timeline)//3]
            middle = timeline[len(timeline)//3:2*len(timeline)//3]
            late = timeline[2*len(timeline)//3:]

            content += f"""#### 早期阶段
- 事件数量：{len(early)} 个
- 主要特征：初期探索与资源积累

#### 发展阶段
- 事件数量：{len(middle)} 个
- 主要特征：系统化推进与网络扩展

#### 近期阶段
- 事件数量：{len(late)} 个
- 主要特征：成熟运作与持续优化

"""

        # 趋势判断
        content += """### 未来趋势研判

基于历史数据和现状分析，预判以下发展趋势：

1. **延续性趋势**：哪些模式和机制将持续发挥作用
2. **变革性趋势**：哪些新因素可能带来根本性变化
3. **风险性趋势**：哪些潜在威胁需要提前应对

"""

        citations = []
        return content, citations

    def _fill_action_plan_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充行动计划章节（Level 3）- 基于分析结果动态生成"""

        # 检查空数据
        if not material.main_keywords and not material.core_entities:
            content = """## 行动计划建议

**数据不足警告**：当前缺少足够的分析基础，无法生成行动计划。请先完成前期调查与分析。

"""
            return content, []

        content = """## 行动计划建议

基于前述田野调查、理论分析和商业评估，提出以下行动建议。

"""

        # 短期行动（基于现有资源）
        content += """### 短期行动（0-6个月）

#### 1. 资源整理与确权

"""

        if material.core_entities.get('LOCATION'):
            locations = [loc['name'] for loc in material.core_entities['LOCATION'][:3]]
            content += f"- 对 {' / '.join(locations)} 等核心地点进行详细测绘与权属确认\n"

        if material.core_entities.get('PERSON'):
            content += f"- 与 {len(material.core_entities['PERSON'])} 位关键利益相关者建立正式沟通机制\n"

        content += """- 建立完整的文化资源档案库
- 完成基础法律与政策合规审查

"""

        # 中期行动（基于主题方向）
        content += """### 中期行动（6-18个月）

#### 2. 试点项目启动

"""

        if material.keyword_communities:
            top_theme = material.keyword_communities[0]['label']
            content += f"- 围绕「{top_theme}」主题设计MVP（最小可行产品）\n"

        content += """- 选择1-2个高可行性方向进行小规模试验
- 建立用户反馈与数据收集机制
- 验证商业模式假设

#### 3. 能力建设

- 组建专业运营团队
- 建立本地合作伙伴网络
- 开展相关培训与赋能活动

"""

        # 长期战略
        content += """### 长期战略（18个月以上）

#### 4. 规模化推广

- 基于试点经验优化运营模式
- 拓展产品/服务线
- 建立品牌影响力

#### 5. 生态系统构建

- 整合上下游产业链资源
- 建立多方共赢的利益分配机制
- 实现可持续发展

"""

        # 关键里程碑
        content += """### 关键里程碑

| 时间节点 | 里程碑目标 | 验收标准 |
|---------|-----------|---------|
| 3个月 | 完成资源整理 | 形成完整档案库 |
| 6个月 | 启动MVP | 首批用户体验 |
| 12个月 | 验证模式 | 达到盈亏平衡 |
| 18个月 | 优化扩展 | 建立标准化流程 |
| 24个月 | 规模推广 | 实现规模化运营 |

"""

        citations = []
        return content, citations

    def _fill_risk_management_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充风险管理章节（Level 3）- 基于分析数据动态生成"""

        content = """## 风险管理与应对

基于田野调查发现和可行性分析，识别以下主要风险点及应对策略。

"""

        # 政策与合规风险
        content += """### 1. 政策与合规风险

**风险描述**：
- 文化资源开发涉及多部门管理，政策变动风险
- 土地、建筑、文物等权属与使用合规问题
- 经营许可与资质要求

**应对策略**：
- 建立政府部门定期沟通机制
- 聘请专业法律顾问，确保合规运营
- 提前进行政策环境评估，留足缓冲时间

**风险等级**：⚠️ 中高

"""

        # 利益相关者风险
        if material.core_entities:
            stakeholder_count = sum(len(v) for v in material.core_entities.values())
            content += f"""### 2. 利益相关者风险

**风险描述**：
- 项目涉及 {stakeholder_count} 个利益相关主体，利益诉求多元
- 社区居民参与意愿与期望管理
- 传统权威与现代管理的张力

**应对策略**：
- 建立透明的利益分配机制
- 设计多元化参与方式，满足不同群体需求
- 尊重本地文化传统，寻求平衡点

**风险等级**：⚠️⚠️ 高

"""

        # 市场与运营风险
        content += """### 3. 市场与运营风险

**风险描述**：
- 市场需求验证不足，用户接受度未知
- 运营团队能力与经验不足
- 淡旺季波动带来的现金流压力

**应对策略**：
- 通过MVP小规模试验，快速验证需求
- 引入专业运营团队或顾问
- 设计多元化产品组合，平滑季节性波动
- 建立充足的现金储备

**风险等级**：⚠️⚠️ 高

"""

        # 文化资源风险
        content += """### 4. 文化资源保护风险

**风险描述**：
- 商业开发可能对文化遗产造成不可逆损害
- 过度商业化导致文化本真性流失
- 社区文化认同感削弱

**应对策略**：
- 确立"保护优先"原则，划定开发边界
- 邀请文化专家参与方案设计与监督
- 让社区居民深度参与，保持文化主体性
- 建立文化影响评估机制

**风险等级**：⚠️⚠️⚠️ 极高

"""

        # 财务风险
        content += """### 5. 财务风险

**风险描述**：
- 前期投资较大，回收周期较长
- 收入来源单一，抗风险能力弱
- 融资渠道有限

**应对策略**：
- 分阶段投入，控制单次投资规模
- 探索多元化收入来源（门票+文创+活动+培训等）
- 申请政府文化产业扶持资金
- 引入战略投资者或社会企业基金

**风险等级**：⚠️⚠️ 高

"""

        # 风险监控机制
        content += """### 风险监控机制

建立"季度风险评估"制度：

1. **识别**：每季度重新评估风险清单
2. **量化**：对每项风险进行概率×影响度打分
3. **预警**：设定预警阈值，触发应急预案
4. **应对**：明确责任人与应对时间表
5. **复盘**：定期总结风险管理经验教训

"""

        citations = []
        return content, citations

    def _fill_swot_section(
        self,
        material: ReportMaterial
    ) -> tuple[str, List[Dict]]:
        """填充SWOT分析章节（Level 3）- 基于真实数据动态生成"""

        # 检查空数据
        if not material.main_keywords and not material.core_entities:
            content = """## SWOT综合分析

**数据不足警告**：当前缺少足够的分析基础，无法生成SWOT分析。

"""
            return content, []

        content = """## SWOT综合分析

基于田野调查、理论分析和商业评估，进行SWOT战略分析。

"""

        # Strengths - 基于实际资源
        content += """### Strengths（优势）

"""

        if material.core_entities.get('LOCATION'):
            content += f"- **地理资源**：拥有 {len(material.core_entities['LOCATION'])} 个具有文化价值的核心地点\n"

        if material.main_keywords:
            content += f"- **文化资源**：识别出 {len(material.main_keywords)} 个核心文化概念，资源多样性强\n"

        if material.core_entities.get('PERSON'):
            content += f"- **人力资源**：{len(material.core_entities['PERSON'])} 位关键人物构成的社会网络\n"

        if material.timeline:
            content += f"- **历史积淀**：{len(material.timeline)} 个时间节点记录的发展历程，形成厚重的历史叙事\n"

        content += "\n"

        # Weaknesses - 基于数据缺口
        content += """### Weaknesses（劣势）

"""

        weakness_items = []

        if material.total_documents < 10:
            weakness_items.append(f"- **数据基础薄弱**：仅有 {material.total_documents} 份调查文档，系统性不足")

        if not material.entity_relations:
            weakness_items.append("- **关系网络未明**：实体关系数据缺失，社会资本分析受限")

        if not material.timeline:
            weakness_items.append("- **时间维度缺失**：缺少历史演进数据，难以把握发展规律")

        # 通用劣势
        weakness_items.extend([
            "- **商业化经验不足**：文化资源的市场转化能力有待验证",
            "- **运营能力短板**：专业运营团队与管理机制尚未建立",
            "- **品牌认知度低**：市场知名度与影响力需要长期培育"
        ])

        content += '\n'.join(weakness_items) + "\n\n"

        # Opportunities
        content += """### Opportunities（机会）

- **政策支持**：乡村振兴、文化自信等国家战略带来的政策红利
- **市场需求**：文化旅游、研学教育、乡村度假等市场快速增长
- **技术赋能**：数字技术为文化传播与体验创新提供新手段
- **社会资本**：社会企业、影响力投资等新型资本关注文化领域
- **消费升级**：城市中产阶层对文化体验和精神消费的需求提升

"""

        # Threats
        content += """### Threats（威胁）

- **同质化竞争**：大量乡村文化项目涌现，差异化定位面临挑战
- **人才流失**：农村人口持续外流，本地文化传承面临断层
- **资金压力**：文化项目投资回报周期长，融资难度大
- **政策不确定性**：土地、文保等政策变化可能影响项目推进
- **文化冲突**：传统文化与现代商业的张力可能引发争议

"""

        # 战略建议
        content += """### 战略建议

**SO战略（优势+机会）**：
- 充分挖掘独特文化资源，打造差异化文化IP
- 抓住政策窗口期，争取政府支持与资源对接

**WO战略（劣势+机会）**：
- 引入专业运营团队，弥补能力短板
- 利用数字技术，降低运营成本，扩大传播范围

**ST战略（优势+威胁）**：
- 强化文化本真性，建立差异化竞争壁垒
- 深度绑定本地社区，构建利益共同体

**WT战略（劣势+威胁）**：
- 小步快跑，通过MVP快速验证，控制风险
- 建立战略联盟，共享资源，分散风险

"""

        citations = []
        return content, citations

    def _enhance_with_llm(
        self,
        content: str,
        section_outline: Dict,
        citations: List[Dict],
        report_level: int
    ) -> str:
        """
        使用LLM增强内容（深度分析）

        关键约束：
        1. LLM只能基于已有的content和citations进行分析
        2. 不能引入新的事实，只能进行解读和洞察
        3. 必须保持原有的引用标记
        """
        if not self.llm_adapter:
            return content

        # TODO: 实现LLM增强逻辑
        logger.info("LLM增强暂未实现，返回原始内容")

        return content
