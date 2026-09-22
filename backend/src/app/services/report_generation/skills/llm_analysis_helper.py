"""
LLM分析辅助类

为Skills提供统一的LLM调用接口，用于深度分析田野数据
"""

import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)


class LLMAnalysisHelper:
    """
    LLM分析辅助类

    职责：
    1. 提供统一的LLM调用接口
    2. 构建分析提示词
    3. 处理LLM响应
    4. 控制输出长度
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")

            if not api_key:
                logger.warning("OPENAI_API_KEY未设置，LLM分析功能将不可用")
                return

            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url

            self.client = OpenAI(**kwargs)
            logger.info("✅ LLM客户端初始化成功")
        except ImportError:
            logger.warning("openai库未安装，LLM分析功能将不可用")
        except Exception as e:
            logger.error(f"LLM客户端初始化失败：{e}")

    def analyze_with_framework(
        self,
        framework_name: str,
        framework_dimensions: Dict[str, Any],
        data_context: str,
        analysis_focus: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 4000
    ) -> str:
        """
        使用理论框架分析数据

        Args:
            framework_name: 框架名称（如"费孝通《乡土中国》"）
            framework_dimensions: 框架的核心维度
            data_context: 数据上下文（引文、实体、关键词等）
            analysis_focus: 分析焦点（要回答什么问题）
            model: 使用的模型
            max_tokens: 最大生成token数

        Returns:
            分析结果文本
        """
        if not self.client:
            logger.warning("LLM客户端未初始化，返回基础分析")
            return self._fallback_analysis(framework_name, analysis_focus)

        # 构建系统提示词
        system_prompt = f"""你是一位专业的社会学研究者，擅长使用{framework_name}的理论框架分析田野调查数据。

你的任务是：
1. 深度阅读提供的田野数据（关键词、实体、原文引用等）
2. 运用{framework_name}的理论框架进行分析
3. 生成深度洞察，而不是简单的描述
4. 每个观点都要基于具体的数据证据
5. 输出应该详实、有深度、有洞察力

分析风格：
- 学术性但不晦涩
- 有理论深度但接地气
- 有具体例证支撑
- 字数充足，深入展开（目标3000-5000字）
"""

        # 构建用户提示词
        user_prompt = f"""## 理论框架维度

{self._format_framework_dimensions(framework_dimensions)}

## 田野数据

{data_context}

## 分析任务

{analysis_focus}

请基于以上田野数据，运用理论框架进行深度分析。要求：
1. 详细展开每个维度的分析
2. 引用具体的数据例证
3. 揭示深层的社会逻辑
4. 输出3000-5000字的深度分析
"""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            logger.info(f"✅ LLM分析完成，生成{len(content)}字")
            return content

        except Exception as e:
            logger.error(f"LLM调用失败：{e}")
            return self._fallback_analysis(framework_name, analysis_focus)

    def _format_framework_dimensions(self, dimensions: Dict[str, Any]) -> str:
        """格式化框架维度"""
        lines = []
        for dim_name, dim_info in dimensions.items():
            lines.append(f"### {dim_name}")
            if isinstance(dim_info, dict):
                for key, value in dim_info.items():
                    if isinstance(value, list):
                        lines.append(f"- **{key}**: {', '.join(value)}")
                    else:
                        lines.append(f"- **{key}**: {value}")
            else:
                lines.append(f"- {dim_info}")
            lines.append("")
        return "\n".join(lines)

    def _fallback_analysis(self, framework_name: str, analysis_focus: str) -> str:
        """降级分析（当LLM不可用时）"""
        return f"""## {framework_name}分析

{analysis_focus}

（LLM分析服务暂不可用，这是基础分析结果。建议配置OPENAI_API_KEY以启用深度分析功能。）
"""

    def extract_and_summarize(
        self,
        raw_data: List[str],
        extraction_goal: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000
    ) -> str:
        """
        从原始数据中提取和总结信息

        Args:
            raw_data: 原始数据列表（如引文列表）
            extraction_goal: 提取目标
            model: 使用的模型
            max_tokens: 最大生成token数

        Returns:
            提取和总结的结果
        """
        if not self.client:
            return f"（{extraction_goal}：LLM服务不可用）"

        # 限制数据量
        data_sample = raw_data[:50]  # 最多50条

        prompt = f"""请从以下田野数据中提取信息：

{extraction_goal}

数据：
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(data_sample))}

要求：
1. 提取关键信息
2. 进行分类和总结
3. 输出清晰有条理
4. 字数500-1000字
"""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM提取失败：{e}")
            return f"（{extraction_goal}：数据提取失败）"
