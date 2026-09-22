"""
神堂记忆：社会记忆视角下的乡村文化遗产发展指导 Skill

基于景军《神堂记忆》的社会记忆理论，将乡村文化遗产视为活的社会记忆载体
核心理念：
- 社会记忆：社群共享的关于过去的集体性认知
- 记忆建构：记忆不是被发现的，而是被建构的
- 创造性转化：对文化符号进行创造性转化以适应当代需求
- 事件团结：通过共同的重建行动凝聚社区
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass

from .llm_analysis_helper import LLMAnalysisHelper

logger = logging.getLogger(__name__)


@dataclass
class MemoryCarrier:
    """记忆载体"""
    carrier_type: str  # 物质/仪式/文本/口头
    carrier_name: str  # 载体名称
    memory_content: str  # 承载的记忆内容
    emotional_intensity: str  # 情感强度（强/中/弱）
    shareability: str  # 共享性（广泛/局部/个人）


@dataclass
class MemoryType:
    """记忆类型分析"""
    type_name: str  # 历史记忆/仪式记忆/族谱记忆/文化象征记忆等
    key_elements: List[str]  # 核心要素
    memory_subjects: List[str]  # 记忆主体（谁在记忆）
    transformation_potential: str  # 转化潜力
    commercial_direction: str  # 商业化方向


@dataclass
class MemoryOpportunity:
    """基于记忆的发展机会"""
    memory_asset: str  # 记忆资产
    transformation_path: str  # 转化路径
    experience_design: str  # 体验设计
    cultural_innovation: str  # 文化创新点


class SocialMemorySkill:
    """
    社会记忆视角的乡村文化遗产分析 Skill

    核心思路：
    1. 定义景军社会记忆理论的核心维度
    2. 从田野数据中识别记忆载体和记忆类型
    3. 调用LLM深度分析记忆的建构、传承与转化
    4. 生成有洞察力的万字报告
    """
    def __init__(self, use_workflow_engine: bool = True):

        # 景军社会记忆理论框架
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.memory_types = {
            "历史记忆": {
                "定义": "对重大历史事件的群体性记忆",
                "对应资源": "村落变迁史、重大事件遗址",
                "分析重点": "记忆如何被选择性保留、如何随时间重构"
            },
            "仪式记忆": {
                "定义": "通过仪式行为传承和再现的记忆",
                "对应资源": "传统节庆、祭祀仪式、人生礼仪",
                "分析重点": "仪式的表演性、参与主体、象征系统"
            },
            "族谱记忆": {
                "定义": "通过血缘谱系维系的家族/宗族记忆",
                "对应资源": "族谱、祠堂、家族故事",
                "分析重点": "血缘网络、家族认同、代际传承"
            },
            "文化象征记忆": {
                "定义": "附着于特定文化符号上的集体记忆",
                "对应资源": "庙宇、神像、图腾、象征物",
                "分析重点": "符号的意义系统、情感依附、神圣性"
            },
            "苦难记忆": {
                "定义": "对灾难、迫害、损失的集体创伤记忆",
                "对应资源": "移民遗址、灾难遗迹、口述史",
                "分析重点": "创伤的集体治愈、苦难的意义转化"
            },
            "日常生活记忆": {
                "定义": "平凡生活实践中沉淀的记忆",
                "对应资源": "老物件、老手艺、老味道、老规矩",
                "分析重点": "日常性、身体性、感官性记忆"
            }
        }

        # 记忆评估维度
        self.memory_assessment_dimensions = {
            "记忆连续性": "传统仪式是否持续？老故事有人讲？",
            "记忆活力": "村民是否主动讨论和重构记忆？",
            "记忆共识": "村民对核心文化符号是否有共同认同？",
            "记忆转化力": "村民能否创造性转化传统？"
        }

        # 初始化LLM辅助类
        self.llm_helper = LLMAnalysisHelper()

    def generate_report(self, report_material: Dict[str, Any]) -> str:
        """
        生成社会记忆视角的田野调查报告

        核心流程：
        1. 提取田野数据上下文
        2. 对每种记忆类型进行LLM深度分析
        3. 分析记忆的建构、传承与转化机制
        4. 组装成完整报告
        """
        logger.info("开始生成社会记忆分析报告")

        # 提取田野数据
        data_context = self._extract_data_context(report_material)

        # 生成报告
        content = "# 神堂记忆：社会记忆视角的文化遗产分析报告\n\n"

        # 第一部分：理论框架介绍
        content += self._generate_framework_intro()

        # 第二部分：识别记忆载体
        content += self._identify_memory_carriers_with_llm(data_context)

        # 第三部分：按记忆类型深度分析
        for memory_type, type_info in self.memory_types.items():
            logger.info(f"正在分析记忆类型：{memory_type}")
            content += self._analyze_memory_type_with_llm(
                memory_type,
                type_info,
                data_context
            )

        # 第四部分：记忆的建构与转化
        content += self._analyze_memory_transformation_with_llm(data_context)

        # 第五部分：发展策略建议
        content += self._generate_development_strategy_with_llm(data_context)

        logger.info(f"✅ 报告生成完成，共{len(content)}字")
        return content

    def _extract_data_context(self, report_material: Dict[str, Any]) -> str:
        """
        从report_material中提取田野数据上下文
        """
        lines = []

        # 1. 关键词
        main_keywords = report_material.get('main_keywords', [])
        if main_keywords:
            lines.append("### 主要关键词")
            for kw in main_keywords[:20]:
                kw_text = kw.get('keyword', '') if isinstance(kw, dict) else str(kw)
                lines.append(f"- {kw_text}")
            lines.append("")

        # 2. 核心实体
        core_entities = report_material.get('core_entities', {})
        if core_entities:
            lines.append("### 核心实体")
            if isinstance(core_entities, dict):
                for entity_type, entity_list in core_entities.items():
                    entities_text = []
                    for entity_obj in entity_list[:10]:
                        entity = entity_obj.get('entity', '') if isinstance(entity_obj, dict) else str(entity_obj)
                        entities_text.append(entity)
                    if entities_text:
                        lines.append(f"- **{entity_type}**: {', '.join(entities_text)}")
            lines.append("")

        # 3. 引文池（重点关注文化、仪式、记忆相关内容）
        citation_pool = report_material.get('citation_pool', [])
        if citation_pool:
            lines.append("### 田野原文摘录（前30条）")
            for i, citation in enumerate(citation_pool[:30], 1):
                text = citation.get('content', '') or citation.get('text', '')
                source = citation.get('source_document', '未知来源')
                if text:
                    lines.append(f"{i}. 【{source}】{text[:200]}")
            lines.append("")

        # 4. 时间线（历史记忆的重要来源）
        timeline = report_material.get('timeline', [])
        if timeline:
            lines.append("### 时间线")
            for event in timeline[:10]:
                event_text = event.get('event', '') if isinstance(event, dict) else str(event)
                lines.append(f"- {event_text}")
            lines.append("")

        return "\n".join(lines)

    def _generate_framework_intro(self) -> str:
        """生成理论框架介绍"""
        return """
## 一、理论框架：景军《神堂记忆》

景军教授在《神堂记忆》中提出的社会记忆理论，为我们理解乡村文化遗产提供了新的视角。核心观点包括：

1. **社会记忆是建构的**：记忆不是客观的历史再现，而是社群在当下情境中不断建构的
2. **记忆载体的多样性**：物质遗产（庙宇）、仪式实践（祭祀）、口述传统、族谱文本等都是记忆载体
3. **创造性转化**：社群会根据当代需求，创造性地重新解释和利用传统符号
4. **事件团结**：通过共同的文化实践（如重建庙宇），凝聚社区认同
5. **记忆的情感维度**：记忆不仅是认知的，更是情感的、身体的

本报告将运用这一框架，分析村落的记忆系统、记忆载体、记忆主体及其转化潜力。

---

## 二、记忆载体识别

"""

    def _identify_memory_carriers_with_llm(self, data_context: str) -> str:
        """
        使用LLM识别记忆载体
        """
        analysis_focus = """
请从田野数据中识别这个村落的主要记忆载体。

记忆载体类型：
1. **物质载体**：庙宇、祠堂、古建筑、纪念碑、老物件等
2. **仪式载体**：节庆、祭祀、人生礼仪（婚丧嫁娶）等
3. **文本载体**：族谱、碑文、地方志、老照片等
4. **口头载体**：故事、传说、民歌、谚语等
5. **身体载体**：手艺、舞蹈、武术、烹饪技艺等

分析要求：
1. 从田野原文中找出具体的记忆载体
2. 分析每种载体承载了什么记忆内容
3. 评估载体的保存状况和活力
4. 识别记忆主体（谁在维护这些记忆）
5. 输出1000-1200字

输出格式：
### 识别到的记忆载体

#### 物质记忆载体
（具体载体、承载的记忆、保存状况）

#### 仪式记忆载体
（具体仪式、参与者、传承状况）

#### 其他载体类型
...
"""

        return self.llm_helper.analyze_with_framework(
            framework_name="景军《神堂记忆》社会记忆理论",
            framework_dimensions={"记忆载体": "物质、仪式、文本、口头、身体"},
            data_context=data_context,
            analysis_focus=analysis_focus,
            max_tokens=1500
        ) + "\n\n---\n\n## 三、记忆类型深度分析\n\n"

    def _analyze_memory_type_with_llm(
        self,
        memory_type: str,
        type_info: Dict[str, str],
        data_context: str
    ) -> str:
        """
        使用LLM对单个记忆类型进行深度分析
        """
        analysis_focus = f"""
请从「{memory_type}」的视角深度分析这个村落的田野数据。

理论框架：
- 定义：{type_info['定义']}
- 对应资源：{type_info['对应资源']}
- 分析重点：{type_info['分析重点']}

分析要求：
1. 从田野数据中找出与「{memory_type}」相关的具体证据
2. 分析这类记忆是如何被建构和传承的
3. 识别记忆主体（谁在记忆？谁在传承？）
4. 分析记忆的情感强度和共享范围
5. 评估当代变迁对这类记忆的影响
6. 输出800-1000字

输出格式：
### {memory_type}

#### 1. 田野证据
（具体的记忆载体和内容）

#### 2. 记忆建构机制
（这类记忆如何被建构和传承）

#### 3. 记忆主体与情感
（谁在记忆？情感强度如何？）

#### 4. 当代状况
（这类记忆的延续或衰退）
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="景军《神堂记忆》",
            framework_dimensions={memory_type: type_info},
            data_context=data_context,
            analysis_focus=analysis_focus,
            max_tokens=1500
        )

        return llm_analysis + "\n\n---\n\n"

    def _analyze_memory_transformation_with_llm(self, data_context: str) -> str:
        """
        分析记忆的创造性转化
        """
        transformation_prompt = """
请分析这个村落的记忆系统如何进行创造性转化以适应当代需求。

景军的核心观点：
- 记忆不是静态的，而是不断被重新建构的
- 社群会根据当代情境，创造性地重新解释传统
- 文化符号可以被赋予新的意义，为当代服务

分析任务：
1. **记忆的选择性保留**：哪些记忆被强化？哪些被遗忘？为什么？
2. **记忆的重新诠释**：传统符号是否被赋予新意义？
3. **记忆的实践转化**：记忆如何转化为当代的文化实践？
4. **转化的动力机制**：谁在推动转化？动力何在（经济、政治、文化）？

要求：基于田野数据，深度分析，1200-1500字
"""

        analysis = self.llm_helper.analyze_with_framework(
            framework_name="景军《神堂记忆》",
            framework_dimensions=self.memory_types,
            data_context=data_context,
            analysis_focus=transformation_prompt,
            max_tokens=2000
        )

        return f"""
## 四、记忆的建构与创造性转化

{analysis}

---

"""

    def _generate_development_strategy_with_llm(self, data_context: str) -> str:
        """
        生成基于社会记忆的发展策略
        """
        strategy_prompt = """
基于社会记忆理论，为这个村落的文化遗产活化提出发展策略。

策略方向：
1. **记忆激活**：如何重新激活沉睡的记忆？
2. **记忆空间营造**：如何创造记忆的物理和社会空间？
3. **记忆主体培育**：如何培养记忆的传承人和讲述者？
4. **记忆产品设计**：如何将记忆转化为文化产品和体验？
5. **事件团结策略**：通过什么样的共同行动凝聚社区？

要求：
- 策略要具体可操作
- 基于村落的实际记忆资源
- 尊重记忆的神圣性和情感性
- 避免过度商业化破坏记忆的真实性
- 1500-2000字
"""

        strategy = self.llm_helper.analyze_with_framework(
            framework_name="景军《神堂记忆》",
            framework_dimensions=self.memory_types,
            data_context=data_context,
            analysis_focus=strategy_prompt,
            max_tokens=2500
        )

        return f"""
## 五、基于社会记忆的发展策略

{strategy}

---

## 报告说明

本报告基于景军《神堂记忆》的社会记忆理论，分析了村落的记忆系统、记忆载体及其转化潜力。社会记忆不仅是文化遗产的核心，更是凝聚社区认同、激活文化活力的关键资源。
"""
