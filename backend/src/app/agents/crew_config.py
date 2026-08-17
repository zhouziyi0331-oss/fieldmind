"""
CrewAI 多智能体系统配置
定义各个专业 Agent 及其协作方式
"""
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, SearchTool
from typing import List, Dict, Any
import os


class FieldMindAgents:
    """
    FieldMind 多智能体团队
    """

    def __init__(self):
        self.llm_config = self._get_llm_config()

    def _get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        llm_backend = os.getenv("LLM_BACKEND", "ollama").lower()

        if llm_backend == "ollama":
            return {
                "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            }
        else:
            return {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY"),
            }

    def transcript_agent(self) -> Agent:
        """
        转录专员 - 负责音频转录
        """
        return Agent(
            role="音频转录专员",
            goal="将音频文件准确转录为文字，识别说话人和时间戳",
            backstory="""你是一位经验丰富的转录专员，擅长处理各种音频质量的录音。
            你特别擅长识别田野调查中的方言和专业术语。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config,
        )

    def entity_agent(self) -> Agent:
        """
        实体识别专员 - 负责 NER
        """
        return Agent(
            role="实体识别专员",
            goal="从文本中识别人名、地名、机构名、时间等关键实体",
            backstory="""你是一位专业的自然语言处理专家，擅长命名实体识别。
            你对社会科学研究中的专有名词和术语有深入理解。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config,
        )

    def relation_agent(self) -> Agent:
        """
        关系抽取专员 - 负责构建知识图谱
        """
        return Agent(
            role="知识图谱构建专员",
            goal="从文本中抽取实体之间的关系，构建知识图谱",
            backstory="""你是一位知识图谱专家，擅长发现实体之间的复杂关系。
            你能够识别因果关系、时序关系、从属关系等多种语义关系。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config,
        )

    def search_agent(self) -> Agent:
        """
        网络搜索专员 - 负责信息检索
        """
        return Agent(
            role="网络搜索专员",
            goal="从互联网搜索相关新闻、政府文件和学术资料",
            backstory="""你是一位专业的信息检索专家，擅长从互联网获取权威资料。
            你知道如何使用搜索引擎、如何判断信息可靠性。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config,
            tools=[SearchTool()],
        )

    def summary_agent(self) -> Agent:
        """
        总结专员 - 负责生成报告
        """
        return Agent(
            role="研究报告撰写专员",
            goal="基于检索到的信息撰写专业的研究报告",
            backstory="""你是一位资深的社会科学研究者，擅长撰写田野调查报告。
            你的报告逻辑清晰、论证严密、文笔流畅。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config,
        )

    def coordinator_agent(self) -> Agent:
        """
        协调专员 - 负责任务分配和协调
        """
        return Agent(
            role="项目协调专员",
            goal="协调各个专员的工作，确保任务按流程完成",
            backstory="""你是一位经验丰富的项目经理，擅长任务分解和团队协作。
            你能够合理安排工作流程，确保每个环节高效衔接。""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm_config,
        )


class FieldMindCrews:
    """
    FieldMind 工作流团队
    """

    def __init__(self):
        self.agents = FieldMindAgents()

    def document_processing_crew(self, file_path: str) -> Crew:
        """
        文档处理团队
        流程：转录 → 实体识别 → 关系抽取 → 知识图谱构建
        """
        # 定义任务
        transcript_task = Task(
            description=f"转录文档 {file_path}，提取文字内容",
            agent=self.agents.transcript_agent(),
            expected_output="完整的文字转录结果",
        )

        entity_task = Task(
            description="从转录文本中识别所有命名实体",
            agent=self.agents.entity_agent(),
            expected_output="实体列表（JSON 格式）",
            context=[transcript_task],
        )

        relation_task = Task(
            description="分析实体之间的关系，构建知识图谱",
            agent=self.agents.relation_agent(),
            expected_output="关系三元组列表",
            context=[entity_task],
        )

        # 创建团队（顺序执行）
        crew = Crew(
            agents=[
                self.agents.transcript_agent(),
                self.agents.entity_agent(),
                self.agents.relation_agent(),
            ],
            tasks=[transcript_task, entity_task, relation_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew

    def research_crew(self, query: str) -> Crew:
        """
        研究报告团队
        流程：搜索 → 分析 → 总结 → 报告生成
        """
        search_task = Task(
            description=f"搜索与'{query}'相关的新闻、政府文件和学术资料",
            agent=self.agents.search_agent(),
            expected_output="相关资料列表（至少10条）",
        )

        analysis_task = Task(
            description="分析搜索到的资料，提取关键信息和实体",
            agent=self.agents.entity_agent(),
            expected_output="关键信息摘要",
            context=[search_task],
        )

        summary_task = Task(
            description="基于分析结果撰写专业的研究报告",
            agent=self.agents.summary_agent(),
            expected_output="完整的研究报告（markdown 格式）",
            context=[search_task, analysis_task],
        )

        crew = Crew(
            agents=[
                self.agents.search_agent(),
                self.agents.entity_agent(),
                self.agents.summary_agent(),
            ],
            tasks=[search_task, analysis_task, summary_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew

    def rag_query_crew(self, query: str, context_docs: List[str]) -> Crew:
        """
        RAG 查询团队
        流程：实体提取 → 图谱检索 → 答案生成
        """
        entity_task = Task(
            description=f"从查询 '{query}' 中提取关键实体",
            agent=self.agents.entity_agent(),
            expected_output="实体列表",
        )

        search_task = Task(
            description="基于实体在知识图谱中检索相关信息",
            agent=self.agents.search_agent(),
            expected_output="相关文档和实体关系",
            context=[entity_task],
        )

        answer_task = Task(
            description="基于检索到的上下文生成准确的答案",
            agent=self.agents.summary_agent(),
            expected_output="最终答案",
            context=[entity_task, search_task],
        )

        crew = Crew(
            agents=[
                self.agents.entity_agent(),
                self.agents.search_agent(),
                self.agents.summary_agent(),
            ],
            tasks=[entity_task, search_task, answer_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew

    def autonomous_crew(self, goal: str) -> Crew:
        """
        自主协作团队
        使用协调专员分配任务，各专员自主协作
        """
        coordination_task = Task(
            description=f"协调团队完成目标：{goal}",
            agent=self.agents.coordinator_agent(),
            expected_output="任务完成报告",
        )

        # 使用层级流程，由协调员分配任务
        crew = Crew(
            agents=[
                self.agents.coordinator_agent(),
                self.agents.transcript_agent(),
                self.agents.entity_agent(),
                self.agents.relation_agent(),
                self.agents.search_agent(),
                self.agents.summary_agent(),
            ],
            tasks=[coordination_task],
            process=Process.hierarchical,  # 层级流程
            manager_agent=self.agents.coordinator_agent(),
            verbose=True,
        )

        return crew


# 便捷函数
def create_document_crew(file_path: str) -> Crew:
    """创建文档处理团队"""
    crews = FieldMindCrews()
    return crews.document_processing_crew(file_path)


def create_research_crew(query: str) -> Crew:
    """创建研究团队"""
    crews = FieldMindCrews()
    return crews.research_crew(query)


def create_rag_crew(query: str, context_docs: List[str]) -> Crew:
    """创建 RAG 查询团队"""
    crews = FieldMindCrews()
    return crews.rag_query_crew(query, context_docs)


def create_autonomous_crew(goal: str) -> Crew:
    """创建自主协作团队"""
    crews = FieldMindCrews()
    return crews.autonomous_crew(goal)
