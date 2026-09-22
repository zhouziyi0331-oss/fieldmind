"""
数据质量检查器
防止AI胡编，确保数据可信后才显示到前端
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """数据质量检查器 - 4重验证"""

    def check_document(self, document, db: Session) -> Dict[str, Any]:
        """
        检查文档处理质量

        返回格式：
        {
            "passed": bool,
            "issues": List[str],
            "score": float,  # 0-100
            "details": {...}
        }
        """
        issues = []
        score = 100.0
        details = {}

        # 第1重：基础完整性检查
        completeness_result = self._check_completeness(document)
        if not completeness_result['passed']:
            issues.extend(completeness_result['issues'])
            score -= 30
        details['completeness'] = completeness_result

        # 第2重：实体来源验证（实体必须来自原文）
        if document.extracted_entities:
            entity_result = self._check_entity_grounding(document, db)
            if not entity_result['passed']:
                issues.extend(entity_result['issues'])
                score -= 25
            details['entity_grounding'] = entity_result

        # 第3重：防止幻觉数字（如果有生成的分析文本）
        if document.extra_data and document.extra_data.get('analysis_text'):
            hallucination_result = self._check_hallucination(document)
            if not hallucination_result['passed']:
                issues.extend(hallucination_result['issues'])
                score -= 30
            details['hallucination'] = hallucination_result

        # 第4重：引用来源检查
        citation_result = self._check_citations(document)
        if not citation_result['passed']:
            issues.extend(citation_result['issues'])
            score -= 15
        details['citations'] = citation_result

        passed = score >= 70  # 70分以上通过

        return {
            "passed": passed,
            "issues": issues,
            "score": score,
            "details": details
        }

    def _check_completeness(self, document) -> Dict[str, Any]:
        """检查数据完整性"""
        issues = []

        # 必须有文本内容
        if not document.text_content or len(document.text_content) < 50:
            issues.append("文本内容太短或为空")

        # 必须有词数统计
        if not document.word_count or document.word_count == 0:
            issues.append("缺少词数统计")

        # 如果进行了向量化，必须有chunks
        extra_data = document.extra_data or {}
        if extra_data.get('pipeline_completed') and not extra_data.get('chunks_count'):
            issues.append("向量化完成但缺少chunks统计")

        return {
            "passed": len(issues) == 0,
            "issues": issues
        }

    def _check_entity_grounding(self, document, db: Session) -> Dict[str, Any]:
        """检查实体是否真实来自原文（防止AI编造实体）"""
        issues = []

        text_content = document.text_content or ""
        extracted_entities = document.extracted_entities or []

        if not extracted_entities:
            # 没有实体不算错误，但要记录
            return {
                "passed": True,
                "issues": [],
                "note": "未提取实体"
            }

        # 检查前20个实体是否在原文中
        ungrounded_entities = []
        for entity in extracted_entities[:20]:
            entity_name = entity.get('name') or entity.get('entity_name') or str(entity)

            # 简单检查：实体名是否在原文中
            if entity_name not in text_content:
                ungrounded_entities.append(entity_name)

        if len(ungrounded_entities) > 5:  # 超过5个实体不在原文
            issues.append(f"发现{len(ungrounded_entities)}个无根据实体（可能是AI编造）：{ungrounded_entities[:3]}")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "ungrounded_count": len(ungrounded_entities),
            "total_entities": len(extracted_entities)
        }

    def _check_hallucination(self, document) -> Dict[str, Any]:
        """检测AI幻觉 - 主要检查数字"""
        from app.services.anti_hallucination_report import HallucinationDetector

        issues = []
        extra_data = document.extra_data or {}
        analysis_text = extra_data.get('analysis_text', '')

        if not analysis_text:
            return {
                "passed": True,
                "issues": [],
                "note": "无分析文本需要检查"
            }

        # 构建facts字典（从文档元数据）
        facts = {
            "word_count": document.word_count,
            "document_id": document.id,
            "chunks_count": extra_data.get('chunks_count', 0),
            "entities_count": len(document.extracted_entities or [])
        }

        # 如果有动态发现的数据，也加入facts
        if extra_data.get('dynamic_discovery'):
            facts.update(extra_data['dynamic_discovery'])

        # 运行幻觉检测
        is_valid, errors = HallucinationDetector.validate_report(analysis_text, facts)

        if not is_valid:
            issues.extend(errors)

        return {
            "passed": is_valid,
            "issues": issues,
            "text_length": len(analysis_text)
        }

    def _check_citations(self, document) -> Dict[str, Any]:
        """检查引用来源"""
        issues = []
        extra_data = document.extra_data or {}
        analysis_text = extra_data.get('analysis_text', '')

        if not analysis_text:
            return {
                "passed": True,
                "issues": [],
                "note": "无分析文本需要检查引用"
            }

        # 检查是否有直接引语但缺少来源标注
        quotes = re.findall(r'"([^"]+)"', analysis_text)

        missing_citations = 0
        for quote in quotes:
            # 检查引号后是否有（来源：xxx）或（document_xxx）
            pattern = f'"{re.escape(quote)}"[^（]*（(?:来源|引用|document)'
            if not re.search(pattern, analysis_text):
                missing_citations += 1

        if missing_citations > 0:
            issues.append(f"发现{missing_citations}处直接引语缺少来源标注")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "total_quotes": len(quotes),
            "missing_citations": missing_citations
        }

    def check_project_data(self, project_id: int, db: Session) -> Dict[str, Any]:
        """检查整个项目的数据质量"""
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        total_docs = len(documents)
        passed_docs = 0
        failed_docs = 0
        issues_summary = []

        for doc in documents:
            result = self.check_document(doc, db)
            if result['passed']:
                passed_docs += 1
            else:
                failed_docs += 1
                issues_summary.extend(result['issues'][:2])  # 只取前2个问题

        project_score = (passed_docs / total_docs * 100) if total_docs > 0 else 0

        return {
            "project_id": project_id,
            "total_documents": total_docs,
            "passed_documents": passed_docs,
            "failed_documents": failed_docs,
            "project_score": project_score,
            "issues_summary": issues_summary[:10]  # 最多10个问题
        }


# 全局实例
data_quality_checker = DataQualityChecker()
