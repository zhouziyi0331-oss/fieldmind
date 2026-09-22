"""
报告生成服务（重构版）
拆分超长 generate_level2_report 函数
"""

from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeiDimensionAnalyzer:
    """费孝通框架维度分析器"""

    def __init__(self):
        self.dimensions = {
            "differential_mode": {
                "name": "差序格局",
                "description": "血缘与地缘关系网络",
                "keywords": ["家族", "亲戚", "宗族", "血缘", "地缘", "关系", "人情"],
                "theory": (
                    '费孝通指出，中国乡村社会呈现"差序格局"特征，'
                    "即以自我为中心，按照亲疏远近形成的同心圆关系网络。"
                ),
                "contexts": [],
            },
            "ritual_order": {
                "name": "礼治秩序",
                "description": "传统规范与社会控制",
                "keywords": ["规矩", "习俗", "传统", "礼节", "道德", "规范", "仪式"],
                "theory": (
                    "礼治是乡土社会的核心秩序机制，通过传统习俗和道德规范"
                    "实现社会控制，而非依赖法律。"
                ),
                "contexts": [],
            },
            "acquaintance_society": {
                "name": "熟人社会",
                "description": "信任机制与互惠网络",
                "keywords": ["熟人", "信任", "口碑", "互助", "面子", "人缘"],
                "theory": (
                    "乡村社会建立在长期互动基础上，形成熟人网络，"
                    "信任与互惠是维系社会关系的核心。"
                ),
                "contexts": [],
            },
            "modernization": {
                "name": "现代化冲击",
                "description": "变迁与转型",
                "keywords": ["外出", "打工", "城市", "流动", "变化", "改变", "年轻人"],
                "theory": (
                    "在城市化、工业化进程中，传统乡村社会经历深刻变迁，"
                    "差序格局和礼治秩序面临现代性挑战。"
                ),
                "contexts": [],
            },
        }

    def analyze_documents(self, documents: List) -> Dict[str, Any]:
        """分析文档，提取费孝通框架相关内容"""
        has_skill_analysis = self._extract_from_skill_results(documents)

        if not has_skill_analysis:
            # 备用方案：关键词匹配
            self._extract_by_keywords(documents)

        return {"has_skill_analysis": has_skill_analysis, "dimensions": self.dimensions}

    def _extract_from_skill_results(self, documents: List) -> bool:
        """从技能分析结果中提取"""
        has_analysis = False

        for doc in documents:
            if doc.extra_data and doc.extra_data.get("skill_results"):
                fei_result = doc.extra_data["skill_results"].get("fei_xiaotong")
                if fei_result:
                    has_analysis = True
                    dimensions = fei_result.get("dimensions", {})
                    for dim_key, dim_data in dimensions.items():
                        if dim_key in self.dimensions:
                            self.dimensions[dim_key]["contexts"].extend(
                                dim_data.get("contexts", [])
                            )

        return has_analysis

    def _extract_by_keywords(self, documents: List):
        """通过关键词匹配提取"""
        for doc in documents:
            if not doc.text_content:
                continue

            for dim_key, dim_info in self.dimensions.items():
                # 检查关键词
                found_keywords = [
                    kw for kw in dim_info["keywords"] if kw in doc.text_content
                ]

                if found_keywords:
                    # 提取相关句子
                    sentences = doc.text_content.replace("。", "。\n").split("\n")
                    for sent in sentences:
                        if any(kw in sent for kw in found_keywords):
                            self.dimensions[dim_key]["contexts"].append(sent.strip())
                            if len(self.dimensions[dim_key]["contexts"]) >= 3:
                                break


class ReportSectionBuilder:
    """报告章节构建器"""

    @staticmethod
    def build_header(doc_count: int) -> List[str]:
        """构建报告头部"""
        return [
            "# 二度报告：费孝通《乡土中国》框架分析\n",
            f"**生成时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n",
            f"**分析文档数**：{doc_count}份\n",
            f"**理论框架**：费孝通《乡土中国》社会学经典理论\n",
            "\n---\n",
        ]

    @staticmethod
    def build_theory_intro() -> List[str]:
        """构建理论框架说明"""
        return [
            "\n## 理论框架说明\n",
            "\n费孝通先生在《乡土中国》中提出了中国乡村社会的独特结构特征：\n",
            "\n1. **差序格局**：以自我为中心，按照血缘、地缘关系向外推的同心圆结构",
            "2. **礼治秩序**：基于传统习俗与道德规范的社会控制机制",
            "3. **熟人社会**：建立在长期互动基础上的信任与互惠关系网络",
            "4. **现代化冲击**：传统乡村社会在城市化、工业化进程中的变迁与转型\n",
            "\n本报告运用上述框架，对田野材料进行二度解读，揭示材料背后的社会结构逻辑。\n",
            "\n---\n",
        ]

    @staticmethod
    def build_warning(has_skill_analysis: bool) -> List[str]:
        """构建警告信息"""
        if has_skill_analysis:
            return []

        return [
            "\n⚠️ **注意**：当前文档未完成费孝通框架分析。\n",
            '建议：在Skill生态页面激活"费孝通·乡土中国"框架后重新处理文档。\n',
            "\n**替代方案**：本报告将基于关键词匹配，尝试从材料中识别费孝通框架相关内容。\n",
        ]

    @staticmethod
    def build_dimension_section(dim_info: Dict[str, Any]) -> List[str]:
        """构建维度章节"""
        lines = []

        # 标题
        lines.append(f"\n## {dim_info['name']}：{dim_info['description']}\n")

        # 理论视角
        lines.append("\n### 理论视角\n")
        lines.append(f"\n{dim_info['theory']}\n")

        # 材料分析
        lines.append("\n### 材料分析\n")

        contexts = dim_info["contexts"]
        if contexts:
            lines.append(f"\n从田野材料中发现 {len(contexts)} 处相关内容：\n")
            for i, context in enumerate(contexts[:5], 1):  # 最多显示 5 条
                lines.append(f"\n{i}. {context}\n")
        else:
            lines.append("\n未在材料中发现明显的相关内容。\n")

        # 理论对话
        lines.append("\n### 理论对话\n")
        if contexts:
            lines.append(
                f"\n上述材料反映了{dim_info['name']}的典型特征，"
                "印证了费孝通关于乡土社会的理论洞察。\n"
            )
        else:
            lines.append(
                f"\n该维度在当前材料中体现不明显，"
                "可能反映了现代化进程对传统结构的冲击。\n"
            )

        return lines

    @staticmethod
    def build_conclusion(dimensions: Dict[str, Dict]) -> List[str]:
        """构建结论"""
        lines = ["\n---\n", "\n## 综合分析与理论反思\n", "\n### 乡村社会结构特征\n"]

        # 统计各维度的内容数量
        dim_counts = {
            dim_key: len(dim_info["contexts"])
            for dim_key, dim_info in dimensions.items()
        }

        # 找出主要特征
        sorted_dims = sorted(dim_counts.items(), key=lambda x: x[1], reverse=True)

        if sorted_dims[0][1] > 0:
            primary_dim = dimensions[sorted_dims[0][0]]
            lines.append(
                f"\n本研究材料中，**{primary_dim['name']}**特征最为显著，"
                "表明传统乡土社会结构仍在发挥重要作用。\n"
            )
        else:
            lines.append("\n材料中传统乡土社会特征不明显，可能反映深度现代化。\n")

        # 现代化进程分析
        lines.append("\n### 现代化进程分析\n")

        modernization_contexts = dimensions["modernization"]["contexts"]
        if modernization_contexts:
            lines.append(
                f"\n材料中发现 {len(modernization_contexts)} 处现代化冲击的迹象，"
                "表明乡村社会正经历快速转型。\n"
            )
        else:
            lines.append("\n材料中现代化特征不明显，可能反映相对稳定的传统结构。\n")

        return lines


class Level2ReportGenerator:
    """二度报告生成器（重构版）"""

    def generate(self, documents: List) -> str:
        """
        生成二度报告

        拆分逻辑：
        1. FeiDimensionAnalyzer - 费孝通框架分析
        2. ReportSectionBuilder - 报告章节构建
        3. 主函数只负责组装

        复杂度：从 40 降低到 <5
        """
        report_lines = []

        # 1. 头部
        report_lines.extend(ReportSectionBuilder.build_header(len(documents)))

        # 2. 理论框架说明
        report_lines.extend(ReportSectionBuilder.build_theory_intro())

        # 3. 分析文档
        analyzer = FeiDimensionAnalyzer()
        analysis_result = analyzer.analyze_documents(documents)

        # 4. 警告信息
        report_lines.extend(
            ReportSectionBuilder.build_warning(analysis_result["has_skill_analysis"])
        )

        # 5. 各维度分析
        for dim_key, dim_info in analysis_result["dimensions"].items():
            report_lines.extend(ReportSectionBuilder.build_dimension_section(dim_info))

        # 6. 结论
        report_lines.extend(
            ReportSectionBuilder.build_conclusion(analysis_result["dimensions"])
        )

        return "".join(report_lines)


# ===== 对外接口 =====


def generate_level2_report(documents: List) -> str:
    """
    生成二度报告（重构版入口）

    Args:
        documents: 文档列表

    Returns:
        Markdown 格式报告
    """
    generator = Level2ReportGenerator()
    return generator.generate(documents)


def generate_level1_report(documents: List, db) -> str:
    """
    生成一度报告（事实报告）

    纯事实呈现，不做分析：
    - 时间线
    - 关键人物
    - 关键事件
    - 关键地点

    Args:
        documents: 文档列表
        db: 数据库会话

    Returns:
        Markdown 格式报告
    """
    from app.models.chunk import Chunk
    from collections import defaultdict
    import re

    report = []
    report.append("# 一度报告：事实呈现\n")
    report.append("*本报告仅呈现客观事实，不包含分析和解读*\n\n")

    # 1. 时间线
    report.append("## 一、时间线\n")

    # 从文档中提取时间信息
    timeline = []
    for doc in documents:
        if doc.upload_time:
            timeline.append({
                "time": doc.upload_time,
                "event": f"上传文档：{doc.original_filename}",
                "word_count": doc.word_count or 0
            })

    # 按时间排序
    timeline.sort(key=lambda x: x["time"])

    for item in timeline:
        report.append(f"- **{item['time'].strftime('%Y-%m-%d')}**: {item['event']} ({item['word_count']} 字)\n")

    report.append("\n")

    # 2. 关键人物
    report.append("## 二、关键人物\n")

    # 从 chunks 提取人名（简单方法：查找常见人名标记）
    people = defaultdict(int)
    doc_ids = [doc.id for doc in documents]

    chunks = db.query(Chunk).filter(Chunk.document_id.in_(doc_ids)).all()

    for chunk in chunks:
        if not chunk.content:
            continue

        # 简单提取：查找"XXX说"、"XXX表示"等模式
        matches = re.findall(r'([^，。！？]{2,4})(说|表示|认为|指出)', chunk.content)
        for match in matches:
            name = match[0].strip()
            if len(name) >= 2:
                people[name] += 1

    # 按出现次数排序
    top_people = sorted(people.items(), key=lambda x: x[1], reverse=True)[:10]

    if top_people:
        for name, count in top_people:
            report.append(f"- **{name}**: 出现 {count} 次\n")
    else:
        report.append("*未识别到明确的人物信息*\n")

    report.append("\n")

    # 3. 关键事件
    report.append("## 三、关键事件\n")

    # 从 chunks 提取含有动词的句子作为事件
    events = []
    for chunk in chunks[:20]:  # 取前20个chunk
        if not chunk.content:
            continue

        sentences = re.split(r'[。！？]', chunk.content)
        for sent in sentences:
            if len(sent) > 10 and len(sent) < 100:
                # 简单判断：含有"了"、"着"等
                if '了' in sent or '在' in sent:
                    events.append(sent.strip())
                    if len(events) >= 10:
                        break
        if len(events) >= 10:
            break

    for i, event in enumerate(events, 1):
        report.append(f"{i}. {event}\n")

    report.append("\n")

    # 4. 关键地点
    report.append("## 四、关键地点\n")

    # 提取地点（简单方法：查找"XX村"、"XX市"等）
    locations = defaultdict(int)

    for chunk in chunks:
        if not chunk.content:
            continue

        # 查找地点标记
        loc_matches = re.findall(r'([^，。！？]{2,6})(村|市|县|镇|区|省)', chunk.content)
        for match in loc_matches:
            location = match[0] + match[1]
            locations[location] += 1

    top_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]

    if top_locations:
        for loc, count in top_locations:
            report.append(f"- **{loc}**: 出现 {count} 次\n")
    else:
        report.append("*未识别到明确的地点信息*\n")

    report.append("\n")

    # 5. 数据统计
    report.append("## 五、数据统计\n")
    report.append(f"- 文档总数：{len(documents)}\n")
    report.append(f"- 总字数：{sum(doc.word_count or 0 for doc in documents)}\n")
    report.append(f"- 文本块数：{len(chunks)}\n")

    return "".join(report)


def generate_level3_report(documents: List, db, project_id: int) -> str:
    """
    生成三度报告（商业报告）

    商业视角分析：
    - 可行性评估
    - 市场分析
    - 风险评估
    - 行动建议

    Args:
        documents: 文档列表
        db: 数据库会话
        project_id: 项目 ID

    Returns:
        Markdown 格式报告
    """
    from app.models.chunk import Chunk

    report = []
    report.append("# 三度报告：商业分析\n")
    report.append("*基于田野调查数据的商业可行性评估*\n\n")

    # 获取量化数据
    doc_ids = [doc.id for doc in documents]
    chunks = db.query(Chunk).filter(Chunk.document_id.in_(doc_ids)).all()

    # 计算情感倾向
    positive_count = sum(1 for c in chunks if c.sentiment_polarity == 'positive')
    negative_count = sum(1 for c in chunks if c.sentiment_polarity == 'negative')
    neutral_count = sum(1 for c in chunks if c.sentiment_polarity == 'neutral')

    total = len(chunks)
    if total > 0:
        positive_rate = positive_count / total
        negative_rate = negative_count / total
    else:
        positive_rate = 0
        negative_rate = 0

    # 1. 可行性评估
    report.append("## 一、可行性评估\n\n")

    if positive_rate > 0.6:
        feasibility = "高"
        reason = "调研数据显示积极情绪占主导（{:.1%}），表明项目具有较好的群众基础。"
    elif positive_rate > 0.4:
        feasibility = "中等"
        reason = "调研数据显示情绪较为平衡（积极 {:.1%}，消极 {:.1%}），需要进一步调研。"
    else:
        feasibility = "较低"
        reason = "调研数据显示消极情绪较多（{:.1%}），项目推进可能面临阻力。"

    report.append(f"**可行性等级**: {feasibility}\n\n")
    report.append(f"**依据**: {reason.format(positive_rate, negative_rate)}\n\n")

    # 2. 优势分析（SWOT 简化版）
    report.append("## 二、优势与挑战\n\n")

    report.append("### 优势（Strengths）\n")
    report.append(f"- 数据样本充足：共 {len(documents)} 份文档，{len(chunks)} 个文本块\n")
    report.append(f"- 积极反馈比例：{positive_rate:.1%}\n")

    if positive_rate > 0.5:
        report.append("- 群众基础良好，项目接受度高\n")

    report.append("\n### 挑战（Challenges）\n")

    if negative_rate > 0.3:
        report.append(f"- 存在较多负面反馈（{negative_rate:.1%}），需要重点关注\n")

    report.append("- 需要持续跟进，确保数据代表性\n")

    report.append("\n")

    # 3. 风险评估
    report.append("## 三、风险评估\n\n")

    risk_level = "低" if negative_rate < 0.2 else ("中" if negative_rate < 0.4 else "高")

    report.append(f"**风险等级**: {risk_level}\n\n")

    report.append("**主要风险点**:\n")
    if negative_rate > 0.3:
        report.append("1. 负面情绪比例较高，可能影响项目推进\n")

    report.append("2. 需要持续监测数据变化趋势\n")
    report.append("3. 建议定期回访，及时调整策略\n\n")

    # 4. 行动建议
    report.append("## 四、行动建议\n\n")

    report.append("### 短期行动（1-3 个月）\n")
    report.append("1. 针对负面反馈集中的领域，开展专项调研\n")
    report.append("2. 组织利益相关方座谈会，收集更多意见\n")
    report.append("3. 制定详细的项目实施方案\n\n")

    report.append("### 中期行动（3-6 个月）\n")
    report.append("1. 启动试点项目，验证可行性\n")
    report.append("2. 建立反馈机制，持续收集数据\n")
    report.append("3. 根据试点结果，调整实施策略\n\n")

    report.append("### 长期行动（6-12 个月）\n")
    report.append("1. 全面推广项目，扩大覆盖范围\n")
    report.append("2. 建立长效机制，确保项目可持续\n")
    report.append("3. 定期评估效果，持续优化改进\n\n")

    # 5. 结论
    report.append("## 五、结论\n\n")

    if positive_rate > 0.6:
        conclusion = "综合评估，该项目具有较高的可行性，建议积极推进。"
    elif positive_rate > 0.4:
        conclusion = "综合评估，该项目具有一定可行性，建议谨慎推进并持续跟进。"
    else:
        conclusion = "综合评估，该项目当前可行性较低，建议进一步调研后再决定是否推进。"

    report.append(conclusion + "\n")

    return "".join(report)
