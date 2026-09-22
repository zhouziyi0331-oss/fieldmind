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
