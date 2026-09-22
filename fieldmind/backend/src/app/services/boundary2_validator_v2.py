"""
边界2验证器（可验证版本）：文本→可用知识
核心：知识丰富度可量化、可验证、可追溯

原则：
1. 所有知识都保留（不筛选）
2. 丰富度基于相对密度计算（不是绝对数量）
3. 计算公式透明（可验证）
4. 每个知识点可追溯来源
"""

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RichnessLevel(str, Enum):
    """知识丰富度等级"""
    HIGH = "高"       # ≥80%
    MEDIUM = "中"     # 50-80%
    LOW = "低"        # <50%


class SourceType(str, Enum):
    """知识来源类型"""
    EXTRACTED = "extracted"   # 从文本提取
    INFERRED = "inferred"     # AI推理得出


class Boundary2ValidatorV2:
    """边界2验证器 V2 - 可验证版本"""

    @staticmethod
    def validate(document: Dict[str, Any], pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证知识丰富度（可验证版本）

        Args:
            document: 文档数据
            pipeline_result: 九步流水线结果

        Returns:
            验证结果（包含详细计算过程）
        """
        word_count = document.get("word_count", 1)
        results = pipeline_result.get("results", {})

        # 获取九步流水线的输出
        step3 = results.get(3, {})  # 实体提取
        step4 = results.get(4, {})  # 事件提取
        step5 = results.get(5, {})  # 关系发现

        entities_count = step3.get("entities_count", 0)
        events_count = step4.get("events_count", 0)
        relationships_count = step5.get("relationships_count", 0)

        # KG节点和边
        kg_nodes = step3.get("kg_nodes_created", 0) + step4.get("kg_nodes_created", 0)
        kg_edges = step5.get("kg_edges_created", 0)

        # 1. 实体密度（每100字）
        entity_density = (entities_count / word_count) * 100 if word_count > 0 else 0
        # 正常范围：0.5-2个/100字，取2为满分
        entity_score = min(entity_density / 2.0, 1.0)

        # 2. 事件密度（每500字）
        event_density = (events_count / word_count) * 500 if word_count > 0 else 0
        # 正常范围：0.2-1个/500字，取1为满分
        event_score = min(event_density / 1.0, 1.0)

        # 3. 关系完整度
        # 理想情况：每个实体和事件至少有1个关系
        expected_relationships = entities_count + events_count
        relationship_ratio = relationships_count / expected_relationships if expected_relationships > 0 else 0
        relationship_score = min(relationship_ratio, 1.0)

        # 4. 知识连通性
        if kg_nodes > 0:
            # 简化连通性计算：有边的节点数 / 总节点数
            # 每条边连接2个节点，但可能有重复
            max_connected = min(kg_edges * 2, kg_nodes)
            connectivity = max_connected / kg_nodes
        else:
            max_connected = 0
            connectivity = 0

        # 加权平均
        richness = (
            entity_score * 0.3 +
            event_score * 0.3 +
            relationship_score * 0.2 +
            connectivity * 0.2
        )

        # 判断质量等级
        if richness >= 0.8:
            quality_level = RichnessLevel.HIGH
        elif richness >= 0.5:
            quality_level = RichnessLevel.MEDIUM
        else:
            quality_level = RichnessLevel.LOW

        result = {
            "document_id": document.get("id"),
            "filename": document.get("original_filename", document.get("filename")),
            "richness": richness,
            "quality_level": quality_level,
            "validated_at": datetime.utcnow().isoformat(),
            "usable": True,  # 所有数据都可用
            "details": {
                "entity_density": entity_density,
                "event_density": event_density,
                "relationship_ratio": relationship_ratio,
                "connectivity": connectivity,
                "entities": entities_count,
                "events": events_count,
                "relationships": relationships_count,
                "kg_nodes": kg_nodes,
                "kg_edges": kg_edges,
                "word_count": word_count,
                "max_connected": max_connected
            },
            "scores": {
                "entity_score": entity_score,
                "event_score": event_score,
                "relationship_score": relationship_score,
                "connectivity_score": connectivity
            },
            "verification": {
                "formula": "0.3×实体密度 + 0.3×事件密度 + 0.2×关系完整度 + 0.2×连通性",
                "calculation": f"0.3×{entity_score:.2f} + 0.3×{event_score:.2f} + 0.2×{relationship_score:.2f} + 0.2×{connectivity:.2f} = {richness:.2f}",
                "entity_density_calc": f"({entities_count}/{word_count})×100 = {entity_density:.2f}个/100字 → 归一化为 {entity_score:.2f}",
                "event_density_calc": f"({events_count}/{word_count})×500 = {event_density:.2f}个/500字 → 归一化为 {event_score:.2f}",
                "relationship_ratio_calc": f"{relationships_count}/({entities_count}+{events_count}) = {relationship_ratio:.2f}",
                "connectivity_calc": f"{max_connected}/{kg_nodes} = {connectivity:.2f}" if kg_nodes > 0 else "0/0 = 0.00",
                "verifiable": True
            },
            "usable_for": {
                "knowledge_graph": kg_nodes > 0 and kg_edges > 0,
                "dashboard": entities_count > 0 or events_count > 0,
                "search": word_count > 0,
                "visualization": connectivity >= 0.3  # 至少30%连通性才好可视化
            },
            "recommendations": Boundary2ValidatorV2._generate_recommendations(
                entity_density, event_density, relationship_ratio, connectivity
            )
        }

        logger.info(f"✅ 边界2验证完成: 文档 {result['document_id']}, 知识丰富度 {richness:.1%}, 等级 {quality_level}")

        return result

    @staticmethod
    def _generate_recommendations(
        entity_density: float,
        event_density: float,
        relationship_ratio: float,
        connectivity: float
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if entity_density < 0.5:
            recommendations.append(f"实体密度较低（{entity_density:.2f}/100字），建议检查文本是否包含足够的人物、地点、组织等信息")

        if event_density < 0.2:
            recommendations.append(f"事件密度较低（{event_density:.2f}/500字），建议检查文本是否包含明确的事件描述")

        if relationship_ratio < 0.5:
            recommendations.append(f"关系完整度不足（{relationship_ratio:.1%}），建议补充实体和事件之间的关联信息")

        if connectivity < 0.4:
            recommendations.append(f"知识连通性较低（{connectivity:.1%}），知识点较孤立，建议增加上下文信息")

        if not recommendations:
            recommendations.append("知识提取质量良好，无需改进")

        return recommendations

    @staticmethod
    def add_source_traceability(
        knowledge_item: Dict[str, Any],
        document_id: int,
        source_type: SourceType,
        text_position: Optional[Dict[str, int]] = None,
        audio_position: Optional[Dict[str, float]] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        为知识项添加来源可追溯信息

        Args:
            knowledge_item: 知识项（实体、事件、关系等）
            document_id: 文档ID
            source_type: 来源类型（提取/推理）
            text_position: 文本位置
            audio_position: 音频位置（如果是音频文件）
            evidence: 推理依据（如果是推理得出）
            confidence: 置信度

        Returns:
            带来源信息的知识项
        """
        knowledge_item["source"] = {
            "type": source_type.value,
            "document_id": document_id,
            "confidence": confidence,
            "is_ai_generated": source_type == SourceType.INFERRED
        }

        # 文本位置
        if text_position:
            knowledge_item["source"]["text_position"] = {
                "start": text_position.get("start"),
                "end": text_position.get("end"),
                "context": text_position.get("context", "")
            }

        # 音频位置
        if audio_position:
            knowledge_item["source"]["audio_position"] = {
                "start_time": audio_position.get("start_time"),
                "end_time": audio_position.get("end_time"),
                "speaker": audio_position.get("speaker")
            }

        # 推理依据
        if evidence and source_type == SourceType.INFERRED:
            knowledge_item["source"]["evidence"] = evidence
            knowledge_item["source"]["inference_note"] = "此信息由AI推理得出，非直接提取"

        return knowledge_item


# ========== 便捷函数 ==========

def validate_boundary2_v2(document: Dict[str, Any], pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证边界2（可验证版本）

    Args:
        document: 文档数据
        pipeline_result: 九步流水线结果

    Returns:
        验证结果（包含详细计算过程）
    """
    return Boundary2ValidatorV2.validate(document, pipeline_result)


def get_boundary2_report_v2(validation_result: Dict[str, Any]) -> str:
    """
    获取边界2验证报告（可验证版本）

    Args:
        validation_result: 验证结果

    Returns:
        报告文本
    """
    details = validation_result.get("details", {})
    scores = validation_result.get("scores", {})
    verification = validation_result.get("verification", {})
    usable_for = validation_result.get("usable_for", {})

    report = f"""
╔══════════════════════════════════════════════════════════════
║ 边界2验证报告：文本→可用知识（可验证版本）
╠══════════════════════════════════════════════════════════════
║ 文档ID: {validation_result.get('document_id')}
║ 文件名: {validation_result.get('filename')}
║ 知识丰富度: {validation_result['richness']:.1%}
║ 质量等级: {validation_result['quality_level']} ⭐
║ 状态: ✅ 可用（所有知识都保留）
╠══════════════════════════════════════════════════════════════
║ 📐 计算公式（可验证）:
║    {verification['formula']}
║
║ 🔢 详细计算:
║    {verification['calculation']}
╠══════════════════════════════════════════════════════════════
║ 📊 详细指标:
║
║ 1️⃣  实体密度: {details['entity_density']:.2f}个/100字
║     实体总数: {details['entities']}个
║     文档字数: {details['word_count']}字
║     计算: {verification['entity_density_calc']}
║     得分: {scores['entity_score']:.2f}
║
║ 2️⃣  事件密度: {details['event_density']:.2f}个/500字
║     事件总数: {details['events']}个
║     计算: {verification['event_density_calc']}
║     得分: {scores['event_score']:.2f}
║
║ 3️⃣  关系完整度: {details['relationship_ratio']:.1%}
║     关系总数: {details['relationships']}个
║     预期关系: {details['entities'] + details['events']}个
║     计算: {verification['relationship_ratio_calc']}
║     得分: {scores['relationship_score']:.2f}
║
║ 4️⃣  知识连通性: {details['connectivity']:.1%}
║     KG节点: {details['kg_nodes']}个
║     KG边: {details['kg_edges']}条
║     计算: {verification['connectivity_calc']}
║     得分: {scores['connectivity_score']:.2f}
╠══════════════════════════════════════════════════════════════
║ ✨ 可用性评估:
║    知识图谱: {'✅ 可用' if usable_for['knowledge_graph'] else '❌ 不可用'}
║    数据看板: {'✅ 可用' if usable_for['dashboard'] else '❌ 不可用'}
║    检索功能: {'✅ 可用' if usable_for['search'] else '❌ 不可用'}
║    图谱可视化: {'✅ 可用' if usable_for['visualization'] else '❌ 不可用'}
"""

    # 改进建议
    if validation_result.get('recommendations'):
        report += f"╠══════════════════════════════════════════════════════════════\n"
        report += f"║ 💡 改进建议:\n"
        for rec in validation_result['recommendations']:
            report += f"║    - {rec}\n"

    report += f"║\n║ ✅ 所有计算可验证\n"
    report += "╚══════════════════════════════════════════════════════════════\n"

    return report


def format_knowledge_with_source(knowledge_item: Dict[str, Any]) -> str:
    """
    格式化知识项，包含来源信息

    Args:
        knowledge_item: 带来源的知识项

    Returns:
        格式化的字符串
    """
    source = knowledge_item.get("source", {})
    source_type = source.get("type", "unknown")
    is_ai = source.get("is_ai_generated", False)

    output = f"{knowledge_item.get('name', knowledge_item.get('text', 'Unknown'))}\n"

    if source_type == "extracted":
        output += "  └─ 来源: 提取 ✅\n"
    elif source_type == "inferred":
        output += "  └─ 来源: AI推理 🤖\n"

    if "text_position" in source:
        pos = source["text_position"]
        output += f"  └─ 文本位置: 第{pos['start']}-{pos['end']}字符\n"
        if pos.get("context"):
            output += f"  └─ 上下文: \"{pos['context']}\"\n"

    if "audio_position" in source:
        pos = source["audio_position"]
        output += f"  └─ 音频位置: {pos['start_time']:.1f}-{pos['end_time']:.1f}秒\n"
        if pos.get("speaker"):
            output += f"  └─ 说话人: {pos['speaker']}\n"

    if "evidence" in source and source.get("is_ai_generated"):
        output += f"  └─ 推理依据:\n"
        for evidence in source["evidence"]:
            output += f"      - {evidence.get('text', 'N/A')}\n"

    output += f"  └─ 置信度: {source.get('confidence', 1.0):.1%}\n"

    return output
