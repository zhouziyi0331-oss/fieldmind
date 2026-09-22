"""
边界2验证器：文本→可用知识（干净数据→富化数据）
核心：脉络清晰、逻辑完整、可追溯

验证标准：
1. 脉络清晰度 ≥ 80%（逻辑链完整）
2. 可用性 ≥ 80%（能支撑下游）
3. 无关键要素缺失
"""

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Boundary2Validator:
    """边界2验证器：文本→可用知识"""

    # 田野调研场景的标准
    FIELD_RESEARCH_STANDARDS = {
        # 核心提取标准
        "core_extraction": {
            "min_events": 3,              # 至少3个事件
            "min_entities": 5,            # 至少5个实体
            "min_relationships": 4,       # 至少4个关系
            "entity_types_diversity": 3,  # 至少3种实体类型
            "event_completeness": 0.8,    # 80%的事件有完整要素
        },

        # 逻辑结构标准
        "logic_structure": {
            "requires_timeline": True,    # 必须有时间线
            "min_timeline_events": 3,     # 时间线至少3个事件
            "requires_spatial": True,     # 必须有空间信息
            "min_locations": 1,           # 至少1个地点
        },

        # 知识图谱标准
        "knowledge_graph": {
            "min_nodes": 5,               # 至少5个节点
            "min_edges": 4,               # 至少4条边
            "min_connectivity": 0.6,      # 至少60%节点有连接
            "requires_subgraph": True,    # 必须有连通子图
            "min_subgraph_size": 3,       # 子图至少3个节点
        },

        # 可用性标准
        "usability": {
            "requires_summary": True,     # 必须有缩影
            "min_summary_length": 20,     # 缩影至少20字
            "requires_kg_data": True,     # 必须有KG数据
            "requires_dashboard_data": True, # 必须有看板数据
        }
    }

    @staticmethod
    def validate(document: Dict[str, Any], pipeline_result: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        验证文档是否为"富化数据"

        Args:
            document: 文档数据
            pipeline_result: 九步流水线的执行结果

        Returns:
            (is_enriched, validation_result)
        """
        validation_result = {
            "is_enriched": False,
            "logic_clarity_score": 0.0,
            "usability_score": 0.0,
            "missing_elements": [],
            "quality_report": {
                "core_extraction": {},
                "logic_structure": {},
                "knowledge_graph": {},
                "usability": {}
            },
            "recommendations": []
        }

        standards = Boundary2Validator.FIELD_RESEARCH_STANDARDS

        # 1. 检查核心提取
        core_check = Boundary2Validator._check_core_extraction(pipeline_result, standards["core_extraction"])
        validation_result["quality_report"]["core_extraction"] = core_check

        if not core_check["passed"]:
            validation_result["missing_elements"].extend(core_check["issues"])

        # 2. 检查逻辑结构
        logic_check = Boundary2Validator._check_logic_structure(pipeline_result, standards["logic_structure"])
        validation_result["quality_report"]["logic_structure"] = logic_check

        if not logic_check["passed"]:
            validation_result["missing_elements"].extend(logic_check["issues"])

        # 3. 检查知识图谱
        kg_check = Boundary2Validator._check_knowledge_graph(pipeline_result, standards["knowledge_graph"])
        validation_result["quality_report"]["knowledge_graph"] = kg_check

        if not kg_check["passed"]:
            validation_result["missing_elements"].extend(kg_check["issues"])

        # 4. 检查可用性
        usability_check = Boundary2Validator._check_usability(document, pipeline_result, standards["usability"])
        validation_result["quality_report"]["usability"] = usability_check

        if not usability_check["passed"]:
            validation_result["missing_elements"].extend(usability_check["issues"])

        # 5. 计算脉络清晰度
        validation_result["logic_clarity_score"] = Boundary2Validator._calculate_logic_clarity(
            core_check, logic_check, kg_check
        )

        # 6. 计算可用性分数
        validation_result["usability_score"] = Boundary2Validator._calculate_usability(
            usability_check, kg_check
        )

        # 7. 判断是否为"富化数据"
        # 标准：脉络清晰度 ≥ 80% + 可用性 ≥ 80% + 无严重缺失
        if (validation_result["logic_clarity_score"] >= 0.8 and
            validation_result["usability_score"] >= 0.8 and
            len(validation_result["missing_elements"]) == 0):
            validation_result["is_enriched"] = True
            logger.info(f"✅ 边界2验证通过: 文档 {document.get('id')} 是富化数据")
            logger.info(f"   脉络清晰度: {validation_result['logic_clarity_score']:.1%}")
            logger.info(f"   可用性: {validation_result['usability_score']:.1%}")
        else:
            validation_result["recommendations"] = Boundary2Validator._generate_recommendations(validation_result)
            logger.warning(f"❌ 边界2验证失败: 文档 {document.get('id')} 不是富化数据")
            logger.warning(f"   脉络清晰度: {validation_result['logic_clarity_score']:.1%}")
            logger.warning(f"   可用性: {validation_result['usability_score']:.1%}")
            logger.warning(f"   缺失要素: {validation_result['missing_elements']}")

        return validation_result["is_enriched"], validation_result

    @staticmethod
    def _check_core_extraction(pipeline_result: Dict[str, Any], standards: Dict[str, Any]) -> Dict[str, Any]:
        """检查核心提取质量"""
        result = {
            "passed": True,
            "issues": [],
            "stats": {}
        }

        # 获取提取结果
        results = pipeline_result.get("results", {})

        # Step 3: 实体提取
        step3 = results.get(3, {})
        entities_count = step3.get("entities_count", 0)
        result["stats"]["entities_count"] = entities_count

        if entities_count < standards["min_entities"]:
            result["issues"].append(f"实体数量不足: {entities_count} < {standards['min_entities']}")
            result["passed"] = False

        # Step 4: 事件提取
        step4 = results.get(4, {})
        events_count = step4.get("events_count", 0)
        result["stats"]["events_count"] = events_count

        if events_count < standards["min_events"]:
            result["issues"].append(f"事件数量不足: {events_count} < {standards['min_events']}")
            result["passed"] = False

        # Step 5: 关系发现
        step5 = results.get(5, {})
        relationships_count = step5.get("relationships_count", 0)
        result["stats"]["relationships_count"] = relationships_count

        if relationships_count < standards["min_relationships"]:
            result["issues"].append(f"关系数量不足: {relationships_count} < {standards['min_relationships']}")
            result["passed"] = False

        # 实体类型多样性（从数据库查询）
        # 这里简化处理，实际应查询数据库
        entity_types_count = step3.get("entity_types_count", 1)
        result["stats"]["entity_types_count"] = entity_types_count

        if entity_types_count < standards["entity_types_diversity"]:
            result["issues"].append(f"实体类型多样性不足: {entity_types_count} < {standards['entity_types_diversity']}")
            result["passed"] = False

        return result

    @staticmethod
    def _check_logic_structure(pipeline_result: Dict[str, Any], standards: Dict[str, Any]) -> Dict[str, Any]:
        """检查逻辑结构"""
        result = {
            "passed": True,
            "issues": [],
            "stats": {}
        }

        results = pipeline_result.get("results", {})

        # 检查时间线
        if standards["requires_timeline"]:
            # 从 Step 4（事件提取）或 Step 9（Reader生成）获取时间线
            step4 = results.get(4, {})
            step9 = results.get(9, {})

            timeline_events = step4.get("timeline_events_count", 0) or step9.get("timeline_events", 0)
            result["stats"]["timeline_events"] = timeline_events

            if timeline_events < standards["min_timeline_events"]:
                result["issues"].append(f"时间线事件不足: {timeline_events} < {standards['min_timeline_events']}")
                result["passed"] = False

        # 检查空间信息
        if standards["requires_spatial"]:
            step3 = results.get(3, {})
            locations_count = step3.get("locations_count", 0)
            result["stats"]["locations_count"] = locations_count

            if locations_count < standards["min_locations"]:
                result["issues"].append(f"地点数量不足: {locations_count} < {standards['min_locations']}")
                result["passed"] = False

        return result

    @staticmethod
    def _check_knowledge_graph(pipeline_result: Dict[str, Any], standards: Dict[str, Any]) -> Dict[str, Any]:
        """检查知识图谱质量"""
        result = {
            "passed": True,
            "issues": [],
            "stats": {},
            "is_usable": False
        }

        results = pipeline_result.get("results", {})

        # 从 Step 3, 4, 5 汇总KG数据
        step3 = results.get(3, {})
        step4 = results.get(4, {})
        step5 = results.get(5, {})

        # 节点数量
        kg_nodes_count = (
            step3.get("kg_nodes_created", 0) +
            step4.get("kg_nodes_created", 0)
        )
        result["stats"]["kg_nodes"] = kg_nodes_count

        if kg_nodes_count < standards["min_nodes"]:
            result["issues"].append(f"KG节点数量不足: {kg_nodes_count} < {standards['min_nodes']}")
            result["passed"] = False

        # 边数量
        kg_edges_count = step5.get("kg_edges_created", 0)
        result["stats"]["kg_edges"] = kg_edges_count

        if kg_edges_count < standards["min_edges"]:
            result["issues"].append(f"KG边数量不足: {kg_edges_count} < {standards['min_edges']}")
            result["passed"] = False

        # 连通性
        if kg_nodes_count > 0 and kg_edges_count > 0:
            # 简化计算：连通性 = 有边的节点数 / 总节点数
            # 实际应该通过图算法计算
            estimated_connected = min(kg_edges_count * 1.5, kg_nodes_count)
            connectivity = estimated_connected / kg_nodes_count
            result["stats"]["connectivity"] = connectivity

            if connectivity < standards["min_connectivity"]:
                result["issues"].append(f"KG连通性不足: {connectivity:.1%} < {standards['min_connectivity']:.1%}")
                result["passed"] = False

            # 判断是否可用
            if connectivity >= standards["min_connectivity"]:
                result["is_usable"] = True

        return result

    @staticmethod
    def _check_usability(document: Dict[str, Any], pipeline_result: Dict[str, Any], standards: Dict[str, Any]) -> Dict[str, Any]:
        """检查下游可用性"""
        result = {
            "passed": True,
            "issues": [],
            "stats": {},
            "dashboard_ready": False,
            "searchable": False
        }

        extra_data = document.get("extra_data", {})
        results = pipeline_result.get("results", {})

        # 检查缩影
        if standards["requires_summary"]:
            # 缩影可能在 extra_data 或由事件处理器生成
            summary = extra_data.get("summary") or extra_data.get("one_line_summary")

            if not summary:
                result["issues"].append("缺少缩影")
                result["passed"] = False
            elif len(str(summary)) < standards["min_summary_length"]:
                result["issues"].append(f"缩影过短: {len(str(summary))}字 < {standards['min_summary_length']}字")
                result["passed"] = False

        # 检查KG数据
        if standards["requires_kg_data"]:
            step3 = results.get(3, {})
            step5 = results.get(5, {})

            has_kg_nodes = step3.get("kg_nodes_created", 0) > 0
            has_kg_edges = step5.get("kg_edges_created", 0) > 0

            if not (has_kg_nodes and has_kg_edges):
                result["issues"].append("缺少KG数据")
                result["passed"] = False

        # 检查看板数据
        if standards["requires_dashboard_data"]:
            # 看板需要统计数据
            has_entities = results.get(3, {}).get("entities_count", 0) > 0
            has_events = results.get(4, {}).get("events_count", 0) > 0

            if has_entities and has_events:
                result["dashboard_ready"] = True
                result["stats"]["dashboard_ready"] = True
            else:
                result["issues"].append("看板数据不足")
                result["passed"] = False

        # 检查可检索性（向量化）
        has_vectors = extra_data.get("vectorized") or extra_data.get("chunks_count", 0) > 0
        result["searchable"] = has_vectors
        result["stats"]["searchable"] = has_vectors

        return result

    @staticmethod
    def _calculate_logic_clarity(
        core_check: Dict[str, Any],
        logic_check: Dict[str, Any],
        kg_check: Dict[str, Any]
    ) -> float:
        """
        计算脉络清晰度分数

        考虑因素：
        1. 核心提取质量（实体、事件、关系）
        2. 逻辑结构完整性（时间线、空间）
        3. 知识图谱连通性
        """
        scores = []

        # 1. 核心提取得分（40%权重）
        if core_check["passed"]:
            scores.append(1.0)
        else:
            # 根据缺失项数量打分
            issues_count = len(core_check["issues"])
            score = max(0, 1.0 - issues_count * 0.2)
            scores.append(score)

        # 2. 逻辑结构得分（30%权重）
        if logic_check["passed"]:
            scores.append(1.0)
        else:
            issues_count = len(logic_check["issues"])
            score = max(0, 1.0 - issues_count * 0.25)
            scores.append(score)

        # 3. 知识图谱得分（30%权重）
        if kg_check["passed"]:
            scores.append(1.0)
        else:
            # 使用实际连通性
            connectivity = kg_check["stats"].get("connectivity", 0)
            scores.append(connectivity)

        # 加权平均
        weights = [0.4, 0.3, 0.3]
        weighted_score = sum(s * w for s, w in zip(scores, weights))

        return weighted_score

    @staticmethod
    def _calculate_usability(
        usability_check: Dict[str, Any],
        kg_check: Dict[str, Any]
    ) -> float:
        """
        计算可用性分数

        考虑因素：
        1. 缩影生成
        2. 看板可用
        3. 可检索
        4. KG可视化
        """
        score = 0.0
        total_weight = 0.0

        # 1. 缩影（30%）
        if "缺少缩影" not in usability_check["issues"] and "缩影过短" not in usability_check["issues"]:
            score += 0.3
        total_weight += 0.3

        # 2. 看板（30%）
        if usability_check.get("dashboard_ready"):
            score += 0.3
        total_weight += 0.3

        # 3. 可检索（20%）
        if usability_check.get("searchable"):
            score += 0.2
        total_weight += 0.2

        # 4. KG可视化（20%）
        if kg_check.get("is_usable"):
            score += 0.2
        total_weight += 0.2

        return score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _generate_recommendations(validation_result: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 根据缺失要素生成建议
        if validation_result["missing_elements"]:
            for element in validation_result["missing_elements"]:
                if "实体" in element:
                    recommendations.append("建议：检查文本内容，确保包含足够的人物、地点、组织等实体信息")
                elif "事件" in element:
                    recommendations.append("建议：检查文本内容，确保包含明确的事件描述（谁做了什么）")
                elif "关系" in element:
                    recommendations.append("建议：关系发现可能需要更复杂的文本，建议增加上下文信息")
                elif "时间线" in element:
                    recommendations.append("建议：补充时间信息（日期、时间点、时序关系）")
                elif "地点" in element:
                    recommendations.append("建议：补充空间信息（地点、位置、空间关系）")
                elif "KG" in element:
                    recommendations.append("建议：提高实体和关系的提取质量")
                elif "缩影" in element:
                    recommendations.append("建议：等待事件处理器自动生成缩影，或手动触发")

        # 根据分数给建议
        if validation_result["logic_clarity_score"] < 0.8:
            recommendations.append(f"脉络清晰度不足（{validation_result['logic_clarity_score']:.1%}），建议补充事件和关系信息")

        if validation_result["usability_score"] < 0.8:
            recommendations.append(f"可用性不足（{validation_result['usability_score']:.1%}），建议检查下游数据生成")

        return recommendations


# ========== 便捷函数 ==========

def validate_boundary2(document: Dict[str, Any], pipeline_result: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    验证边界2：文本→可用知识

    Args:
        document: 文档数据
        pipeline_result: 九步流水线结果

    Returns:
        (is_enriched, validation_result)
    """
    return Boundary2Validator.validate(document, pipeline_result)


def get_boundary2_report(document: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
    """
    获取边界2验证报告（可读格式）

    Args:
        document: 文档数据
        validation_result: 验证结果

    Returns:
        报告文本
    """
    is_enriched = validation_result["is_enriched"]

    report = f"""
╔══════════════════════════════════════════════════════════════
║ 边界2验证报告：文本→可用知识
╠══════════════════════════════════════════════════════════════
║ 文档ID: {document.get('id')}
║ 文件名: {document.get('original_filename', document.get('filename'))}
║ 验证结果: {'✅ 通过（富化数据）' if is_enriched else '❌ 未通过'}
║ 脉络清晰度: {validation_result['logic_clarity_score']:.1%}
║ 可用性: {validation_result['usability_score']:.1%}
╠══════════════════════════════════════════════════════════════
"""

    # 核心提取
    core = validation_result["quality_report"]["core_extraction"]
    if core.get("stats"):
        report += f"║ 📊 核心提取:\n"
        report += f"║    实体: {core['stats'].get('entities_count', 0)}\n"
        report += f"║    事件: {core['stats'].get('events_count', 0)}\n"
        report += f"║    关系: {core['stats'].get('relationships_count', 0)}\n"

    # 逻辑结构
    logic = validation_result["quality_report"]["logic_structure"]
    if logic.get("stats"):
        report += f"║ 🕐 逻辑结构:\n"
        report += f"║    时间线事件: {logic['stats'].get('timeline_events', 0)}\n"
        report += f"║    地点: {logic['stats'].get('locations_count', 0)}\n"

    # 知识图谱
    kg = validation_result["quality_report"]["knowledge_graph"]
    if kg.get("stats"):
        report += f"║ 🕸️  知识图谱:\n"
        report += f"║    节点: {kg['stats'].get('kg_nodes', 0)}\n"
        report += f"║    边: {kg['stats'].get('kg_edges', 0)}\n"
        if "connectivity" in kg["stats"]:
            report += f"║    连通性: {kg['stats']['connectivity']:.1%}\n"

    # 可用性
    usability = validation_result["quality_report"]["usability"]
    report += f"║ ✨ 可用性:\n"
    report += f"║    看板: {'✅' if usability.get('dashboard_ready') else '❌'}\n"
    report += f"║    检索: {'✅' if usability.get('searchable') else '❌'}\n"
    report += f"║    可视化: {'✅' if kg.get('is_usable') else '❌'}\n"

    if validation_result['missing_elements']:
        report += f"║ ⚠️  缺失要素:\n"
        for element in validation_result['missing_elements']:
            report += f"║    - {element}\n"

    if validation_result['recommendations']:
        report += f"║ 💡 改进建议:\n"
        for rec in validation_result['recommendations']:
            report += f"║    - {rec}\n"

    report += "╚══════════════════════════════════════════════════════════════\n"

    return report
