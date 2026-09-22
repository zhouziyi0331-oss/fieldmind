"""
IngestionAgent 的 CrewAI 集成
将独立的 IngestionAgent 封装为 CrewAI Agent，实现多Agent协作
"""

import logging
from typing import Dict, Any, List, Optional
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    Agent = Task = Crew = Process = None
    CREWAI_AVAILABLE = False

from app.agents.ingestion_agent import (
    get_ingestion_agent,
    IngestionAgent,
)

logger = logging.getLogger(__name__)


def _require_crewai() -> None:
    if not CREWAI_AVAILABLE:
        raise RuntimeError(
            "CrewAI 未安装。主上传链使用 IngestionAgent，不依赖 CrewAI；"
            "如需启用多智能体增强，请安装 crewai。"
        )


class IngestionAgentTools:
    """将 IngestionAgent 的功能封装为 LangChain Tools，供 CrewAI 调用"""

    def __init__(self):
        self.agent = get_ingestion_agent()

    def create_tools(self) -> List[Tool]:
        """创建工具列表"""
        return [
            Tool(
                name="ingest_file",
                func=self._ingest_file_wrapper,
                description="""
                提取文件内容的工具。支持多种文件格式：
                - 文档：PDF, DOCX, TXT, Markdown, HTML, EPUB
                - 音频：MP3, WAV, M4A, FLAC (使用 Whisper 转录)
                - 视频：MP4, AVI, MOV (提取音轨 + Whisper)
                - 图片：PNG, JPG (使用 PaddleOCR 识别文字)

                输入：文件路径 (string)
                输出：JSON 格式的采集结果，包含：
                  - raw_content: 原始文本内容
                  - metrics: 量化指标（字数、时长、语言等）
                  - metadata: 文件元数据
                """
            ),
            Tool(
                name="get_ingestion_stats",
                func=self._get_stats_wrapper,
                description="""
                获取数据采集统计信息。

                输入：无 (传入空字符串 "")
                输出：JSON 格式的统计数据，包含：
                  - total_processed: 总处理文件数
                  - success_count: 成功数
                  - by_file_type: 按文件类型的统计
                """
            )
        ]

    def _ingest_file_wrapper(self, file_path: str) -> str:
        """文件采集工具的包装器"""
        try:
            result = self.agent.ingest_file(file_path)

            # 返回精简的 JSON 结果（避免内容过长）
            return self._format_result(result)

        except Exception as e:
            logger.error(f"采集失败: {e}")
            return f"ERROR: 文件采集失败 - {str(e)}"

    def _get_stats_wrapper(self, _: str) -> str:
        """统计信息工具的包装器"""
        stats = self.agent.get_statistics()
        return str(stats)

    def _format_result(self, result: Dict[str, Any]) -> str:
        """格式化采集结果为字符串（供 LLM 理解）"""
        metrics = result.get("structured_metadata", {})
        extraction = result.get("extraction_info", {})
        raw_content = result.get("raw_text", "")
        return f"""
✅ 文件采集成功

📄 文件信息：
- 文件名: {result.get('filename', '')}
- 类型: {result.get('file_type', 'unknown')}

📊 量化指标：
- 字符数: {len(raw_content)}
- 词数: {metrics.get('total_words', 0)}
- 语言: {metrics.get('language', 'unknown')}
- 提取方法: {extraction.get('method', 'unknown')}
- 提取状态: {extraction.get('status', 'unknown')}

📝 内容预览（前200字符）:
{raw_content[:200]}...

🔗 完整内容已存储，可用于后续处理阶段。
"""


class IngestionCrewAgent:
    """CrewAI 风格的 IngestionAgent 封装"""

    def __init__(self, llm_config: Optional[ChatOpenAI] = None):
        """
        初始化 CrewAI Agent

        Args:
            llm_config: LLM 配置（默认使用 GPT-4）
        """
        _require_crewai()
        self.llm_config = llm_config or ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )

        self.tools_provider = IngestionAgentTools()
        self.tools = self.tools_provider.create_tools()

        # 创建 CrewAI Agent
        self.crew_agent = Agent(
            role="数据采集专员 (IngestionAgent)",
            goal="从各类文件中提取原始内容，输出统一格式的文本数据",
            backstory="""
你是一位专业的数据采集专员，精通多种文件格式的内容提取。

你的核心职责：
1. 识别文件类型（文档、音频、视频、图片）
2. 调用对应的服务插件提取内容
3. 输出统一的原始文本，不做任何分析或解读
4. 提供准确的量化指标（字数、时长、语言等）

你整合了18个后端服务插件：
- 文档转换：PDF、DOCX、TXT、Markdown、HTML、EPUB、Pandoc
- 音频处理：Whisper转录、音频元数据提取
- 视频处理：视频转录（音轨提取 + Whisper）
- OCR识别：PaddleOCR（中文优先）、Tesseract
- 数据质量：文本清洗、编码检测
- 元数据：EXIF、文件属性、MIME检测、语言识别

你的工作原则：
- 只提取内容，不做分析
- 保证输出格式统一
- 提供准确的量化指标
- 处理失败时给出清晰的错误信息
            """,
            verbose=True,
            allow_delegation=False,  # 采集阶段不需要委托
            tools=self.tools,
            llm=self.llm_config
        )

    def create_ingestion_task(
        self,
        file_path: str,
        description: Optional[str] = None
    ) -> Task:
        """
        创建数据采集任务

        Args:
            file_path: 要处理的文件路径
            description: 任务描述（可选）

        Returns:
            CrewAI Task
        """
        task_description = description or f"""
从文件 {file_path} 中提取内容。

要求：
1. 使用 ingest_file 工具提取文件内容
2. 记录量化指标（字数、时长、文件类型、语言等）
3. 输出原始文本，不做任何分析
4. 如果提取失败，说明失败原因

输出格式：
- 文件信息
- 量化指标
- 原始文本（完整或预览）
        """

        return Task(
            description=task_description,
            agent=self.crew_agent,
            expected_output="文件内容提取报告，包含量化指标和原始文本"
        )


class IngestionCrew:
    """完整的数据采集 Crew（单Agent模式）"""

    def __init__(self, llm_config: Optional[ChatOpenAI] = None):
        self.ingestion_crew_agent = IngestionCrewAgent(llm_config)

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理单个文件

        Args:
            file_path: 文件路径

        Returns:
            处理结果字典
        """
        logger.info(f"🚀 启动 IngestionCrew 处理文件: {file_path}")

        # 创建任务
        task = self.ingestion_crew_agent.create_ingestion_task(file_path)

        # 创建 Crew（单Agent）
        crew = Crew(
            agents=[self.ingestion_crew_agent.crew_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        # 执行
        result = crew.kickoff()

        logger.info(f"✅ IngestionCrew 处理完成")

        return {
            "file_path": file_path,
            "result": result,
            "status": "success"
        }

    def process_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        批量处理文件

        Args:
            file_paths: 文件路径列表

        Returns:
            处理结果列表
        """
        logger.info(f"🚀 启动 IngestionCrew 批量处理 {len(file_paths)} 个文件")

        results = []
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"处理失败 {file_path}: {e}")
                results.append({
                    "file_path": file_path,
                    "result": None,
                    "status": "failed",
                    "error": str(e)
                })

        success_count = len([r for r in results if r['status'] == 'success'])
        logger.info(f"✅ 批量处理完成: {success_count}/{len(file_paths)} 成功")

        return results


# ==================== 与其他 Agent 的协作示例 ====================

class MultiAgentPipeline:
    """
    完整的8-Agent流水线（示例）

    Agent 1: IngestionAgent (数据采集)
    Agent 2: ChunkingAgent (文本切分)
    Agent 3: VectorizationAgent (向量化)
    Agent 4: EntityExtractionAgent (实体识别)
    Agent 5: RelationExtractionAgent (关系抽取)
    Agent 6: MemoryIntegrationAgent (记忆整合)
    Agent 7: RetrievalAgent (检索)
    Agent 8: AnalysisAgent (分析)
    """

    def __init__(self, llm_config: Optional[ChatOpenAI] = None):
        self.llm_config = llm_config or ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )

        # 初始化 Agent 1: IngestionAgent
        self.ingestion_agent = IngestionCrewAgent(self.llm_config)

        # TODO: 初始化其他7个 Agent
        # self.chunking_agent = ChunkingCrewAgent(self.llm_config)
        # self.vectorization_agent = VectorizationCrewAgent(self.llm_config)
        # ...

    def run_full_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        运行完整的8-Agent流水线

        流程：
        1. IngestionAgent: 提取原始内容
        2. ChunkingAgent: 切分文本
        3. VectorizationAgent: 向量化
        4. EntityExtractionAgent: 实体识别
        5. RelationExtractionAgent: 关系抽取
        6. MemoryIntegrationAgent: 整合到7个记忆平台
        7. RetrievalAgent: 测试检索
        8. AnalysisAgent: 生成分析报告
        """
        logger.info(f"🚀 启动完整8-Agent流水线: {file_path}")

        pipeline_result = {
            "file_path": file_path,
            "stages": {}
        }

        # Stage 1: 数据采集
        logger.info("📥 Stage 1: IngestionAgent 数据采集")
        ingestion_task = self.ingestion_agent.create_ingestion_task(file_path)

        # 直接使用底层 IngestionAgent（更高效）
        ingestion_agent = get_ingestion_agent()
        ingestion_result = ingestion_agent.ingest_file(file_path)

        pipeline_result["stages"]["ingestion"] = {
            "status": "completed",
            "metrics": ingestion_result.metrics,
            "raw_content": ingestion_result.raw_content
        }

        # Stage 2-8: TODO
        # logger.info("✂️  Stage 2: ChunkingAgent 文本切分")
        # ...

        logger.info(f"✅ 完整流水线执行完成")

        return pipeline_result


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""

    # 方式1: 直接使用底层 IngestionAgent（推荐，性能更好）
    print("=== 方式1: 直接使用 IngestionAgent ===")
    agent = get_ingestion_agent()
    result = agent.ingest_file("/path/to/document.pdf")
    print(f"采集结果: {result.metrics}")

    # 方式2: 使用 CrewAI 封装（适合多Agent协作场景）
    print("\n=== 方式2: 使用 CrewAI 封装 ===")
    crew = IngestionCrew()
    crew_result = crew.process_file("/path/to/document.pdf")
    print(f"Crew结果: {crew_result['status']}")

    # 方式3: 批量处理
    print("\n=== 方式3: 批量处理 ===")
    files = [
        "/path/to/doc1.pdf",
        "/path/to/audio1.mp3",
        "/path/to/image1.png"
    ]
    batch_results = crew.process_batch(files)
    print(f"批量处理: {len(batch_results)} 个文件")

    # 方式4: 完整8-Agent流水线
    print("\n=== 方式4: 完整流水线 ===")
    pipeline = MultiAgentPipeline()
    full_result = pipeline.run_full_pipeline("/path/to/document.pdf")
    print(f"流水线阶段: {list(full_result['stages'].keys())}")


if __name__ == "__main__":
    example_usage()
