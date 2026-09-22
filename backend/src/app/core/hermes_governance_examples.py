"""
Hermes 治理框架集成示例

展示如何使用 GovernedHermes 构建企业级智能体应用
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.hermes_governance import (
    GovernedHermes,
    get_governed_hermes,
    governed_stage
)
from app.models.permission import PermissionAction, ResourceType


# ==================== 示例1: 文档处理工作流 ====================

async def setup_document_workflow():
    """
    设置文档处理工作流

    流程:
    1. 文档上传 (需要权限检查)
    2. 文档解析 (自动审计)
    3. 实体提取 (需要人工审核)
    4. 向量化存储 (自动血缘追踪)
    """

    hermes = get_governed_hermes()

    # 阶段1: 文档上传
    @governed_stage(
        stage_name="document_upload",
        require_permission=PermissionAction.CREATE,
        resource_type=ResourceType.DOCUMENT,
        next_stages=["document_parse"]
    )
    async def upload_document(data: Dict, project_id: int, db: Session):
        """上传文档 - 需要创建权限"""
        file_path = data.get("file_path")

        # 处理文档上传
        document_id = f"doc_{project_id}_{file_path}"

        return {
            "document_id": document_id,
            "file_path": file_path,
            "status": "uploaded"
        }


    # 阶段2: 文档解析
    @governed_stage(
        stage_name="document_parse",
        next_stages=["entity_extraction"]
    )
    async def parse_document(data: Dict, project_id: int, db: Session):
        """解析文档 - 自动审计"""
        document_id = data.get("document_id")

        # 模拟文档解析
        text = "这是解析后的文档内容..."

        return {
            "document_id": document_id,
            "text": text,
            "word_count": len(text),
            "status": "parsed"
        }


    # 阶段3: 实体提取 (需要人工审核)
    @governed_stage(
        stage_name="entity_extraction",
        require_approval=True,  # 关键步骤需要审核
        next_stages=["vectorization"]
    )
    async def extract_entities(data: Dict, project_id: int, db: Session):
        """提取实体 - 需要人工审核"""
        text = data.get("text")

        # 模拟 AI 实体提取
        entities = [
            {"type": "person", "name": "张三"},
            {"type": "organization", "name": "ABC公司"}
        ]

        return {
            **data,
            "entities": entities,
            "entity_count": len(entities),
            "status": "extracted"
        }


    # 阶段4: 向量化存储
    @governed_stage(
        stage_name="vectorization",
        require_permission=PermissionAction.EDIT,
        resource_type=ResourceType.DOCUMENT
    )
    async def vectorize_document(data: Dict, project_id: int, db: Session):
        """向量化 - 自动血缘追踪"""
        document_id = data.get("document_id")
        text = data.get("text")

        # 模拟向量化
        vector_id = f"vec_{document_id}"

        return {
            **data,
            "vector_id": vector_id,
            "status": "vectorized"
        }


    print("✅ 文档处理工作流已设置")
    return hermes


# ==================== 示例2: RAG 问答工作流 ====================

async def setup_rag_workflow():
    """
    设置 RAG 问答工作流

    流程:
    1. 问题接收 (权限检查)
    2. 向量检索 (自动审计)
    3. 生成答案 (AI 审计)
    4. 反幻觉检测 (需要审核)
    """

    hermes = get_governed_hermes()

    @governed_stage(
        stage_name="question_intake",
        require_permission=PermissionAction.VIEW,
        resource_type=ResourceType.PROJECT,
        next_stages=["vector_retrieval"]
    )
    async def receive_question(data: Dict, project_id: int, db: Session):
        """接收问题"""
        question = data.get("question")

        return {
            "question": question,
            "question_id": f"q_{hash(question)}",
            "status": "received"
        }


    @governed_stage(
        stage_name="vector_retrieval",
        next_stages=["answer_generation"]
    )
    async def retrieve_context(data: Dict, project_id: int, db: Session):
        """向量检索"""
        question = data.get("question")

        # 模拟检索
        contexts = [
            {"doc_id": "doc1", "text": "相关内容1", "score": 0.95},
            {"doc_id": "doc2", "text": "相关内容2", "score": 0.87}
        ]

        return {
            **data,
            "contexts": contexts,
            "status": "retrieved"
        }


    @governed_stage(
        stage_name="answer_generation",
        next_stages=["hallucination_check"]
    )
    async def generate_answer(data: Dict, project_id: int, db: Session):
        """生成答案 - AI 操作自动审计"""
        question = data.get("question")
        contexts = data.get("contexts", [])

        # 模拟 AI 生成答案
        answer = f"根据检索到的 {len(contexts)} 条内容，回答是..."

        return {
            **data,
            "answer": answer,
            "model": "gpt-4",
            "status": "generated"
        }


    @governed_stage(
        stage_name="hallucination_check",
        require_approval=True  # AI 生成内容需要审核
    )
    async def check_hallucination(data: Dict, project_id: int, db: Session):
        """反幻觉检测"""
        answer = data.get("answer")
        contexts = data.get("contexts", [])

        # 模拟幻觉检测
        is_grounded = True
        confidence = 0.92

        return {
            **data,
            "is_grounded": is_grounded,
            "confidence": confidence,
            "status": "verified"
        }


    print("✅ RAG 问答工作流已设置")
    return hermes


# ==================== 示例3: 多 Agent 协作工作流 ====================

async def setup_multi_agent_workflow():
    """
    设置多 Agent 协作工作流

    6-Agent 管道:
    1. Ingestion Agent - 数据摄入
    2. Chunking Agent - 分块处理
    3. Vectorization Agent - 向量化
    4. Knowledge Agent - 知识图谱构建
    5. Synthesis Agent - 综合分析
    6. Report Agent - 报告生成
    """

    hermes = get_governed_hermes()

    @governed_stage(
        stage_name="agent_ingestion",
        require_permission=PermissionAction.CREATE,
        resource_type=ResourceType.DOCUMENT,
        next_stages=["agent_chunking"]
    )
    async def ingestion_agent(data: Dict, project_id: int, db: Session):
        """Ingestion Agent - 数据摄入"""
        source = data.get("source")

        # 摄入数据
        raw_data = {"content": "原始数据...", "metadata": {}}

        return {
            "source": source,
            "raw_data": raw_data,
            "agent": "ingestion",
            "status": "ingested"
        }


    @governed_stage(
        stage_name="agent_chunking",
        next_stages=["agent_vectorization"]
    )
    async def chunking_agent(data: Dict, project_id: int, db: Session):
        """Chunking Agent - 分块处理"""
        raw_data = data.get("raw_data")

        # 分块
        chunks = [
            {"id": "chunk_1", "text": "分块1..."},
            {"id": "chunk_2", "text": "分块2..."}
        ]

        return {
            **data,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "agent": "chunking",
            "status": "chunked"
        }


    @governed_stage(
        stage_name="agent_vectorization",
        next_stages=["agent_knowledge"]
    )
    async def vectorization_agent(data: Dict, project_id: int, db: Session):
        """Vectorization Agent - 向量化"""
        chunks = data.get("chunks", [])

        # 向量化
        vectors = [
            {"chunk_id": chunk["id"], "vector": [0.1, 0.2, 0.3]}
            for chunk in chunks
        ]

        return {
            **data,
            "vectors": vectors,
            "agent": "vectorization",
            "status": "vectorized"
        }


    @governed_stage(
        stage_name="agent_knowledge",
        next_stages=["agent_synthesis"]
    )
    async def knowledge_agent(data: Dict, project_id: int, db: Session):
        """Knowledge Agent - 知识图谱构建"""
        chunks = data.get("chunks", [])

        # 构建知识图谱
        knowledge_graph = {
            "entities": ["实体1", "实体2"],
            "relations": [{"from": "实体1", "to": "实体2", "type": "关联"}]
        }

        return {
            **data,
            "knowledge_graph": knowledge_graph,
            "agent": "knowledge",
            "status": "knowledge_built"
        }


    @governed_stage(
        stage_name="agent_synthesis",
        next_stages=["agent_report"]
    )
    async def synthesis_agent(data: Dict, project_id: int, db: Session):
        """Synthesis Agent - 综合分析"""
        knowledge_graph = data.get("knowledge_graph", {})
        vectors = data.get("vectors", [])

        # 综合分析
        insights = [
            "洞察1: ...",
            "洞察2: ..."
        ]

        return {
            **data,
            "insights": insights,
            "agent": "synthesis",
            "status": "synthesized"
        }


    @governed_stage(
        stage_name="agent_report",
        require_approval=True  # 最终报告需要审核
    )
    async def report_agent(data: Dict, project_id: int, db: Session):
        """Report Agent - 报告生成"""
        insights = data.get("insights", [])
        knowledge_graph = data.get("knowledge_graph", {})

        # 生成报告
        report = {
            "title": "分析报告",
            "summary": "综合分析结果...",
            "insights": insights,
            "visualizations": []
        }

        return {
            **data,
            "report": report,
            "agent": "report",
            "status": "completed"
        }


    print("✅ 多 Agent 协作工作流已设置")
    return hermes


# ==================== 示例4: 完整使用流程 ====================

async def example_usage():
    """
    完整的使用示例
    """
    from app.database import get_db

    # 1. 设置工作流
    hermes = await setup_document_workflow()

    # 2. 获取数据库会话
    async for db in get_db():

        # 3. 创建治理化数据包
        packet = await hermes.create_governed_packet(
            stage_name="document_upload",
            data={
                "file_path": "/path/to/document.pdf"
            },
            project_id=1,
            user_id=123,  # 当前用户ID
            db=db
        )

        print(f"✅ 数据包已创建: {packet.packet_id}")

        # 4. 执行阶段（自动包含审计、血缘、权限检查）
        result = await hermes.execute_governed_stage(
            packet_id=packet.packet_id,
            stage_name="document_upload",
            db=db,
            user_id=123
        )

        print(f"✅ 阶段执行完成: {result}")

        # 5. 查询血缘链路
        lineage = await hermes.get_packet_lineage(
            packet_id=packet.packet_id,
            db=db,
            depth=5
        )

        print(f"📊 血缘链路: {lineage}")

        # 6. 查询审计轨迹
        audit_trail = await hermes.get_stage_audit_trail(
            stage_name="document_upload",
            project_id=1,
            db=db,
            limit=10
        )

        print(f"📝 审计轨迹: {len(audit_trail)} 条记录")

        break


# ==================== 示例5: 治理配置 ====================

def configure_governance_example():
    """
    治理能力配置示例
    """

    hermes = get_governed_hermes()

    # 场景1: 开发环境 - 关闭权限检查
    hermes.configure_governance(
        enable_audit=True,
        enable_lineage=True,
        enable_permission_check=False  # 开发时方便调试
    )

    # 场景2: 生产环境 - 完全治理
    hermes.configure_governance(
        enable_audit=True,
        enable_lineage=True,
        enable_permission_check=True
    )

    # 场景3: 性能测试 - 最小治理
    hermes.configure_governance(
        enable_audit=False,
        enable_lineage=False,
        enable_permission_check=False
    )

    print("✅ 治理配置已更新")


if __name__ == "__main__":
    import asyncio

    # 运行示例
    asyncio.run(example_usage())
