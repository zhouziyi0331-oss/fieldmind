"""
ChunkingAgent - CrewAI 集成封装
将 ChunkingAgent 封装为 CrewAI Agent，支持与其他 Agent 协作
"""

import logging
from typing import List, Dict, Any, Optional
from langchain.tools import Tool

try:
    from crewai import Agent, Task, Crew
    CREWAI_AVAILABLE = True
except ImportError:
    Agent = Task = Crew = None
    CREWAI_AVAILABLE = False

from app.agents.chunking_agent import (
    get_chunking_agent,
    ChunkingStrategy,
    ChunkingResult
)

logger = logging.getLogger(__name__)


def _require_crewai() -> None:
    if not CREWAI_AVAILABLE:
        raise RuntimeError(
            "CrewAI 未安装。请使用 app.agents.chunking_agent 作为主切分入口，"
            "或安装 crewai 后再启用 CrewAI 适配层。"
        )


class ChunkingAgentTools:
    """
    将 ChunkingAgent 的功能封装为 LangChain Tools
    供 CrewAI Agent 调用
    """

    def __init__(self):
        self.agent = get_chunking_agent()

    def _chunk_text_wrapper(self, input_str: str) -> str:
        """
        切分文本的Tool包装器

        输入格式：JSON字符串
        {
            "text": "要切分的文本",
            "source_file": "文件路径",
            "file_type": "pdf",
            "language": "zh",
            "strategy": "auto"
        }
        """
        import json

        try:
            params = json.loads(input_str)
        except json.JSONDecodeError:
            return json.dumps({"error": "输入必须是有效的JSON字符串"}, ensure_ascii=False)

        text = params.get("text", "")
        source_file = params.get("source_file", "unknown")
        file_type = params.get("file_type", "text")
        language = params.get("language", "zh")
        strategy_str = params.get("strategy", "auto").lower()

        # 转换策略
        strategy_map = {
            "auto": ChunkingStrategy.AUTO,
            "semantic": ChunkingStrategy.SEMANTIC,
            "recursive": ChunkingStrategy.RECURSIVE,
            "sentence": ChunkingStrategy.SENTENCE,
            "token": ChunkingStrategy.TOKEN,
            "markdown": ChunkingStrategy.MARKDOWN,
        }
        strategy = strategy_map.get(strategy_str, ChunkingStrategy.AUTO)

        # 执行切分
        result = self.agent.chunk_text(
            text=text,
            source_file=source_file,
            file_type=file_type,
            language=language,
            strategy=strategy
        )

        # 返回摘要（不返回全部chunks，太长）
        summary = {
            "success": True,
            "source_file": result.source_file,
            "strategy_used": result.strategy_used,
            "total_chunks": result.total_chunks,
            "total_chars": result.total_chars,
            "total_words": result.total_words,
            "avg_chunk_size": result.avg_chunk_size,
            "processing_time_ms": result.processing_time_ms,
            "first_3_chunks": [
                {
                    "chunk_id": chunk.metadata.chunk_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "char_count": chunk.metadata.char_count,
                    "text_preview": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text
                }
                for chunk in result.chunks[:3]
            ]
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    def _get_chunk_by_id_wrapper(self, chunk_id: str) -> str:
        """
        根据chunk_id获取完整chunk内容
        （实际项目中需要从数据库读取，这里简化处理）
        """
        return json.dumps({
            "error": "此功能需要数据库支持，请直接访问chunks列表"
        }, ensure_ascii=False)

    def _get_stats_wrapper(self, input_str: str) -> str:
        """获取切分统计信息"""
        stats = self.agent.get_stats()
        return json.dumps(stats, ensure_ascii=False, indent=2)

    def create_tools(self) -> List[Tool]:
        """创建LangChain Tools列表"""
        return [
            Tool(
                name="chunk_text",
                func=self._chunk_text_wrapper,
                description=(
                    "将文本切分成适合向量化的块。"
                    "输入必须是JSON字符串，包含以下字段："
                    '{"text": "要切分的文本", "source_file": "文件路径", '
                    '"file_type": "pdf/docx/text", "language": "zh/en", '
                    '"strategy": "auto/semantic/recursive/sentence/token/markdown"}。'
                    "返回切分结果摘要，包含总块数、平均大小等信息。"
                )
            ),
            Tool(
                name="get_chunking_stats",
                func=self._get_stats_wrapper,
                description="获取切分统计信息，包括已处理文档数、总块数、策略使用情况。"
            )
        ]


class ChunkingCrewAgent:
    """
    ChunkingAgent 的 CrewAI 封装
    """

    def __init__(self, llm_config: Optional[Any] = None):
        """
        Args:
            llm_config: CrewAI的LLM配置（例如ChatOpenAI实例）
        """
        _require_crewai()
        self.tools = ChunkingAgentTools().create_tools()
        self.llm_config = llm_config

        self.crew_agent = Agent(
            role="文本切分专员 (ChunkingAgent)",
            goal="将原始文本切分成适合向量化的块，每块200-500字，保留位置信息",
            backstory=(
                "你是一位专业的文本切分专员，负责FieldMind系统中的文档切分任务。"
                "你精通5种切分策略：语义切分、递归切分、句子切分、Token切分、Markdown结构切分。"
                "你的工作是：\n"
                "1. 接收来自IngestionAgent的原始文本\n"
                "2. 根据文档特征自动选择最优切分策略\n"
                "3. 确保每个chunk在200-500字之间\n"
                "4. 保留chunk的位置信息（char_start, char_end）\n"
                "5. 为每个chunk生成唯一ID\n"
                "6. 输出标准化的chunks供VectorizationAgent使用\n\n"
                "你调用的5个切分服务：\n"
                "- SemanticChunker: 基于语义边界切分（适合长篇文档）\n"
                "- RecursiveChunker: 递归字符分割（最稳定）\n"
                "- SentenceChunker: 基于句子边界（适合短文档）\n"
                "- TokenChunker: 基于Token数量（适配BERT）\n"
                "- MarkdownChunker: Markdown结构化切分（保留标题层级）"
            ),
            tools=self.tools,
            llm=self.llm_config,
            verbose=True,
            allow_delegation=False
        )

    def get_agent(self) -> Agent:
        """获取CrewAI Agent实例"""
        return self.crew_agent


class ChunkingCrew:
    """
    单Agent Crew：用于独立执行切分任务
    """

    def __init__(self, llm_config: Optional[Any] = None):
        self.chunking_agent = ChunkingCrewAgent(llm_config).get_agent()

    def chunk_text(
        self,
        text: str,
        source_file: str,
        file_type: str = "text",
        language: str = "zh",
        strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        执行文本切分任务

        Args:
            text: 原始文本
            source_file: 源文件路径
            file_type: 文件类型
            language: 语言
            strategy: 切分策略

        Returns:
            切分结果字典
        """
        import json

        # 构造输入
        input_json = json.dumps({
            "text": text,
            "source_file": source_file,
            "file_type": file_type,
            "language": language,
            "strategy": strategy
        }, ensure_ascii=False)

        # 创建任务
        task = Task(
            description=(
                f"请切分以下文本：\n"
                f"- 源文件: {source_file}\n"
                f"- 文件类型: {file_type}\n"
                f"- 语言: {language}\n"
                f"- 策略: {strategy}\n"
                f"- 文本长度: {len(text)} 字符\n\n"
                f"请使用 chunk_text 工具完成切分，并返回切分结果摘要。"
            ),
            agent=self.chunking_agent,
            expected_output="切分结果摘要，包含总块数、平均大小、使用的策略等信息"
        )

        # 创建Crew并执行
        crew = Crew(
            agents=[self.chunking_agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()

        # 解析结果
        try:
            return json.loads(str(result))
        except json.JSONDecodeError:
            return {"raw_output": str(result)}


# ============================================================================
# 多Agent协作示例：IngestionAgent → ChunkingAgent → VectorizationAgent
# ============================================================================

class DocumentProcessingCrew:
    """
    文档处理Crew：协调 IngestionAgent 和 ChunkingAgent
    """

    def __init__(self, llm_config: Optional[Any] = None):
        from app.agents.ingestion_crew import IngestionCrewAgent

        self.ingestion_agent = IngestionCrewAgent(llm_config).get_agent()
        self.chunking_agent = ChunkingCrewAgent(llm_config).get_agent()

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理文件：采集 → 切分

        Args:
            file_path: 文件路径

        Returns:
            处理结果
        """
        import json

        # 任务1: 采集文件内容
        task1 = Task(
            description=(
                f"请采集文件 {file_path} 的内容。\n"
                f"使用 ingest_file 工具提取原始文本和元数据。"
            ),
            agent=self.ingestion_agent,
            expected_output="文件的原始文本内容和元数据"
        )

        # 任务2: 切分文本
        task2 = Task(
            description=(
                f"请将上一步采集的文本切分成适合向量化的块。\n"
                f"根据文档特征自动选择最优切分策略。\n"
                f"使用 chunk_text 工具完成切分。"
            ),
            agent=self.chunking_agent,
            expected_output="切分结果摘要",
            context=[task1]  # 依赖任务1的输出
        )

        # 创建Crew并执行
        crew = Crew(
            agents=[self.ingestion_agent, self.chunking_agent],
            tasks=[task1, task2],
            verbose=True
        )

        result = crew.kickoff()

        return {"result": str(result)}


# ============================================================================
# 直接使用示例（不通过CrewAI）
# ============================================================================

def chunk_text_directly(
    text: str,
    source_file: str,
    file_type: str = "text",
    language: str = "zh",
    strategy: str = "auto"
) -> ChunkingResult:
    """
    直接调用ChunkingAgent（推荐方式，不需要LLM）

    Args:
        text: 原始文本
        source_file: 源文件路径
        file_type: 文件类型
        language: 语言
        strategy: 切分策略

    Returns:
        ChunkingResult对象
    """
    agent = get_chunking_agent()

    strategy_map = {
        "auto": ChunkingStrategy.AUTO,
        "semantic": ChunkingStrategy.SEMANTIC,
        "recursive": ChunkingStrategy.RECURSIVE,
        "sentence": ChunkingStrategy.SENTENCE,
        "token": ChunkingStrategy.TOKEN,
        "markdown": ChunkingStrategy.MARKDOWN,
    }

    return agent.chunk_text(
        text=text,
        source_file=source_file,
        file_type=file_type,
        language=language,
        strategy=strategy_map.get(strategy, ChunkingStrategy.AUTO)
    )


# ============================================================================
# 与 IngestionAgent 的集成示例
# ============================================================================

def ingest_and_chunk(file_path: str) -> Dict[str, Any]:
    """
    完整流程：采集 → 切分

    Args:
        file_path: 文件路径

    Returns:
        包含采集结果和切分结果的字典
    """
    from app.agents.ingestion_agent import get_ingestion_agent

    # 步骤1: 采集
    ingestion_agent = get_ingestion_agent()
    ingestion_result = ingestion_agent.ingest_file(file_path)

    logger.info(
        f"Ingestion complete: {ingestion_result.file_type.value}, "
        f"{ingestion_result.metrics['word_count']} words"
    )

    # 步骤2: 切分
    chunking_agent = get_chunking_agent()
    chunking_result = chunking_agent.chunk_text(
        text=ingestion_result.raw_content,
        source_file=ingestion_result.file_path,
        file_type=ingestion_result.file_type.value,
        language=ingestion_result.metrics.get("language", "zh"),
        strategy=ChunkingStrategy.AUTO
    )

    logger.info(
        f"Chunking complete: {chunking_result.total_chunks} chunks, "
        f"strategy={chunking_result.strategy_used}"
    )

    return {
        "ingestion": {
            "file_path": ingestion_result.file_path,
            "file_type": ingestion_result.file_type.value,
            "metrics": ingestion_result.metrics
        },
        "chunking": {
            "total_chunks": chunking_result.total_chunks,
            "strategy_used": chunking_result.strategy_used,
            "avg_chunk_size": chunking_result.avg_chunk_size,
            "chunks": [chunk.to_dict() for chunk in chunking_result.chunks]
        }
    }


# ============================================================================
# 测试用例
# ============================================================================

if __name__ == "__main__":
    # 测试1: 直接调用（推荐）
    print("=" * 80)
    print("测试1: 直接调用 ChunkingAgent")
    print("=" * 80)

    text = """
    这是一段测试文本。FieldMind是一个农村运营分析系统。
    它可以处理各种类型的文档，包括音频、视频、图片、PDF等。
    系统采用多Agent架构，包括IngestionAgent、ChunkingAgent、VectorizationAgent等。
    """ * 20

    result = chunk_text_directly(
        text=text,
        source_file="test.txt",
        file_type="text",
        language="zh",
        strategy="auto"
    )

    print(f"\n切分结果：")
    print(f"  总块数: {result.total_chunks}")
    print(f"  策略: {result.strategy_used}")
    print(f"  平均大小: {result.avg_chunk_size:.0f} 字符")
    print(f"  处理时间: {result.processing_time_ms:.0f}ms")

    print(f"\n前3个块：")
    for i, chunk in enumerate(result.chunks[:3]):
        print(f"\n  Chunk {i}:")
        print(f"    ID: {chunk.metadata.chunk_id}")
        print(f"    位置: {chunk.metadata.char_start}-{chunk.metadata.char_end}")
        print(f"    长度: {chunk.metadata.char_count} 字符")
        print(f"    内容: {chunk.text[:80]}...")

    # 测试2: 与IngestionAgent集成
    print("\n" + "=" * 80)
    print("测试2: Ingestion + Chunking 完整流程")
    print("=" * 80)

    # 这里需要实际文件路径
    # result = ingest_and_chunk("/path/to/your/file.pdf")
    # print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n✓ ChunkingAgent 测试完成")
