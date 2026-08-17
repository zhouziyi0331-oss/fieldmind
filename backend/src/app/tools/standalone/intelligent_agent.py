"""智能Agent服务 - 基于项目资料和对话历史的深度学习自进化Agent"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic SDK not installed")
    ANTHROPIC_AVAILABLE = False
    Anthropic = None


class IntelligentAgent:
    """
    智能Agent - 具备以下能力：
    1. 深度学习项目资料和对话历史
    2. 自动构建项目专属的skill/工作流
    3. 自我进化和优化
    4. 联网深度思考
    5. 长记忆管理
    """

    def __init__(self, api_key: Optional[str] = None):
        """初始化智能Agent"""
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic SDK not available")
            self.client = None
            return

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No Anthropic API key provided")
            self.client = None
            return

        self.client = Anthropic(api_key=self.api_key)
        logger.info("Intelligent Agent initialized")

    def analyze_project_context(
        self,
        project_id: int,
        documents: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析项目上下文，构建项目专属的知识框架

        返回：
        - 关键主题
        - 研究方向
        - 常用概念
        - 推荐的工作流
        """
        if not self.client:
            return {"error": "Agent not available"}

        try:
            # 构建分析提示
            analysis_prompt = self._build_analysis_prompt(documents, conversations, memories)

            # 调用Claude进行深度分析
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.3,
                system="""你是FieldMind的智能分析Agent。你的任务是深度分析用户的研究项目，理解其核心内容、研究方向和工作模式。

基于提供的文档、对话历史和记忆，你需要：
1. 识别项目的核心主题和研究方向
2. 提取关键概念、实体和关系
3. 分析用户的工作模式和偏好
4. 构建适合该项目的工作流框架
5. 生成结构化的JSON输出

输出格式：
{
  "project_summary": "项目总结",
  "key_themes": ["主题1", "主题2"],
  "research_directions": ["方向1", "方向2"],
  "key_concepts": [{"concept": "概念", "frequency": 10, "importance": "high"}],
  "entities": [{"name": "实体", "type": "person/org/concept", "context": "上下文"}],
  "user_preferences": {
    "analysis_style": "描述",
    "output_format": "偏好",
    "depth_level": "深度/浅显"
  },
  "recommended_workflows": [
    {
      "name": "工作流名称",
      "description": "描述",
      "steps": ["步骤1", "步骤2"],
      "use_cases": ["场景1", "场景2"]
    }
  ],
  "skill_framework": {
    "name": "项目专属技能名称",
    "description": "技能描述",
    "capabilities": ["能力1", "能力2"],
    "knowledge_base": ["知识点1", "知识点2"]
  }
}""",
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            # 解析响应
            content = response.content[0].text

            # 尝试提取JSON
            try:
                # 寻找JSON代码块
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                elif "{" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_str = content[json_start:json_end]
                else:
                    json_str = content

                analysis = json.loads(json_str)

                # 添加元数据
                analysis["analyzed_at"] = datetime.utcnow().isoformat()
                analysis["project_id"] = project_id
                analysis["agent_version"] = "1.0"

                logger.info(f"Project {project_id} context analyzed successfully")
                return analysis

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return {
                    "error": "Failed to parse analysis",
                    "raw_content": content
                }

        except Exception as e:
            logger.error(f"Failed to analyze project context: {e}")
            return {"error": str(e)}

    def _build_analysis_prompt(
        self,
        documents: List[Dict[str, Any]],
        conversations: List[Dict[str, Any]],
        memories: List[Dict[str, Any]]
    ) -> str:
        """构建分析提示"""

        prompt_parts = ["# 项目数据分析\n"]

        # 文档信息
        if documents:
            prompt_parts.append("## 文档内容\n")
            for i, doc in enumerate(documents[:10], 1):  # 限制前10个
                prompt_parts.append(f"### 文档 {i}: {doc.get('filename', 'Unknown')}\n")
                content = doc.get('text_content', '')[:1000]  # 限制长度
                prompt_parts.append(f"{content}\n...\n\n")

        # 对话历史
        if conversations:
            prompt_parts.append("## 对话历史\n")
            for i, conv in enumerate(conversations[:20], 1):  # 限制前20条
                role = conv.get('role', 'unknown')
                content = conv.get('content', '')[:500]
                prompt_parts.append(f"**{role.upper()}**: {content}\n\n")

        # 记忆
        if memories:
            prompt_parts.append("## 长期记忆\n")
            for i, mem in enumerate(memories[:15], 1):  # 限制前15条
                content = mem.get('content', '')[:300]
                mem_type = mem.get('memory_type', 'unknown')
                prompt_parts.append(f"- [{mem_type}] {content}\n")

        prompt_parts.append("\n请基于以上信息，进行深度分析并生成结构化的JSON输出。")

        return "".join(prompt_parts)

    def generate_response(
        self,
        project_id: int,
        user_message: str,
        context: Dict[str, Any],
        skill_framework: Optional[Dict[str, Any]] = None,
        enable_deep_thinking: bool = True,
        enable_web_search: bool = False
    ) -> Dict[str, Any]:
        """
        生成智能响应

        参数：
        - user_message: 用户消息
        - context: 项目上下文（文档、对话历史、记忆）
        - skill_framework: 项目专属技能框架
        - enable_deep_thinking: 启用深度思考
        - enable_web_search: 启用联网搜索
        """
        if not self.client:
            return {"error": "Agent not available"}

        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt(
                project_id=project_id,
                context=context,
                skill_framework=skill_framework,
                enable_deep_thinking=enable_deep_thinking
            )

            # 构建消息历史
            messages = self._build_message_history(context.get("recent_conversations", []))
            messages.append({"role": "user", "content": user_message})

            # 调用Claude
            thinking_config = {}
            if enable_deep_thinking:
                thinking_config = {
                    "type": "enabled",
                    "budget_tokens": 10000
                }

            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=16000,
                temperature=0.7,
                system=system_prompt,
                messages=messages,
                thinking=thinking_config if enable_deep_thinking else None
            )

            # 提取响应和思考过程
            assistant_message = ""
            thinking_process = ""

            for block in response.content:
                if block.type == "thinking":
                    thinking_process = block.thinking
                elif block.type == "text":
                    assistant_message = block.text

            # 如果启用了联网搜索，这里可以集成搜索结果
            sources = []
            if enable_web_search:
                # TODO: 集成网络搜索API
                pass

            result = {
                "message": assistant_message,
                "thinking_process": thinking_process if enable_deep_thinking else None,
                "sources": sources,
                "model": "claude-3-7-sonnet-20250219",
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "generated_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Generated response for project {project_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {"error": str(e)}

    def _build_system_prompt(
        self,
        project_id: int,
        context: Dict[str, Any],
        skill_framework: Optional[Dict[str, Any]],
        enable_deep_thinking: bool
    ) -> str:
        """构建系统提示"""

        prompt_parts = [
            f"你是FieldMind为项目 {project_id} 创建的专属智能助手。"
        ]

        # 添加技能框架
        if skill_framework:
            prompt_parts.append(f"\n## 你的专属技能框架\n")
            prompt_parts.append(f"**技能名称**: {skill_framework.get('name', 'Unknown')}\n")
            prompt_parts.append(f"**描述**: {skill_framework.get('description', '')}\n")
            prompt_parts.append(f"**核心能力**: {', '.join(skill_framework.get('capabilities', []))}\n")
            prompt_parts.append(f"**知识库**: {', '.join(skill_framework.get('knowledge_base', []))}\n")

        # 添加项目上下文
        if context.get("project_summary"):
            prompt_parts.append(f"\n## 项目概述\n{context['project_summary']}\n")

        if context.get("key_themes"):
            prompt_parts.append(f"\n## 关键主题\n{', '.join(context['key_themes'])}\n")

        # 添加相关记忆
        if context.get("relevant_memories"):
            prompt_parts.append("\n## 相关记忆\n")
            for mem in context["relevant_memories"][:10]:
                prompt_parts.append(f"- {mem.get('content', '')[:200]}\n")

        # 添加相关文档片段
        if context.get("relevant_documents"):
            prompt_parts.append("\n## 相关文档\n")
            for doc in context["relevant_documents"][:5]:
                prompt_parts.append(f"### {doc.get('filename', 'Unknown')}\n")
                prompt_parts.append(f"{doc.get('content', '')[:500]}...\n\n")

        # 工作指引
        prompt_parts.append("\n## 工作指引\n")
        prompt_parts.append("1. 基于项目的专属知识库和历史对话回答问题\n")
        prompt_parts.append("2. 保持与项目研究方向一致\n")
        prompt_parts.append("3. 引用相关文档和记忆作为支持\n")

        if enable_deep_thinking:
            prompt_parts.append("4. 使用扩展思考进行深度推理\n")
            prompt_parts.append("5. 分析问题的多个维度和潜在影响\n")

        return "".join(prompt_parts)

    def _build_message_history(
        self,
        recent_conversations: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """构建消息历史"""
        messages = []
        for conv in recent_conversations[-10:]:  # 最近10条对话
            messages.append({
                "role": conv.get("role", "user"),
                "content": conv.get("content", "")
            })
        return messages

    def evolve_skill_framework(
        self,
        project_id: int,
        current_framework: Dict[str, Any],
        new_interactions: List[Dict[str, Any]],
        feedback: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        技能框架自进化

        基于新的交互和反馈，更新项目的技能框架
        """
        if not self.client:
            return {"error": "Agent not available"}

        try:
            evolution_prompt = f"""# 技能框架进化任务

## 当前技能框架
{json.dumps(current_framework, ensure_ascii=False, indent=2)}

## 新的交互数据
{json.dumps(new_interactions[:20], ensure_ascii=False, indent=2)}

## 用户反馈
{json.dumps(feedback or [], ensure_ascii=False, indent=2)}

请分析新的交互和反馈，优化和进化当前的技能框架。输出更新后的完整技能框架JSON。

重点关注：
1. 新出现的概念和知识点
2. 用户的新需求和偏好变化
3. 工作流的优化机会
4. 能力的扩展方向

输出格式与原框架保持一致，但要包含改进和新增内容。"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.3,
                messages=[{"role": "user", "content": evolution_prompt}]
            )

            content = response.content[0].text

            # 解析JSON
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                elif "{" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_str = content[json_start:json_end]
                else:
                    json_str = content

                evolved_framework = json.loads(json_str)
                evolved_framework["evolved_at"] = datetime.utcnow().isoformat()
                evolved_framework["version"] = current_framework.get("version", 1.0) + 0.1

                logger.info(f"Skill framework evolved for project {project_id}")
                return evolved_framework

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse evolved framework: {e}")
                return current_framework

        except Exception as e:
            logger.error(f"Failed to evolve skill framework: {e}")
            return current_framework
