"""
RAG闭环系统 API

将 Agent + 知识库 + 评测体系 集成为一套完整系统
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.core.database import get_db
from app.models.project import Project
from app.core.logging_config import get_logger
from app.services.knowledge_api import get_knowledge_api, KnowledgeAPI
from app.services.evaluation_engine import get_evaluation_engine, EvaluationEngine

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rag-system", tags=["RAG闭环系统"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateTestCaseRequest(BaseModel):
    """创建测试用例请求"""
    project_id: int
    question: str = Field(..., description="问题")
    expected_answer: str = Field(..., description="标准答案")
    expected_source: Dict[str, Any] = Field(..., description="标准来源 {chunk_id, file_id}")
    expected_aspects: List[str] = Field(..., description="标准答案关键点")
    category: str = Field("fact", description="分类: fact/relation/reasoning/summary")
    difficulty: str = Field("medium", description="难度: easy/medium/hard")


class RunEvaluationRequest(BaseModel):
    """运行评测请求"""
    project_id: int
    version: str = Field(..., description="版本号，如 v1.0")


class CompareVersionsRequest(BaseModel):
    """版本对比请求"""
    project_id: int
    version_old: str
    version_new: str


class AgentQueryRequest(BaseModel):
    """Agent查询请求（使用KnowledgeAPI）"""
    project_id: int
    query: str
    top_k: int = Field(5, ge=1, le=20)
    min_credibility: float = Field(0.0, ge=0.0, le=1.0)
    trace_execution: bool = Field(True, description="是否记录执行追踪")


# ============================================================================
# 一、知识库管理（通过KnowledgeAPI访问）
# ============================================================================

@router.get("/knowledge/search", summary="知识库检索（标准接口）")
async def knowledge_search(
    project_id: int,
    query: str,
    top_k: int = 10,
    min_credibility: float = 0.0,
    db: Session = Depends(get_db)
):
    """
    通过KnowledgeAPI检索知识库

    **核心约束**:
    - Agent只能通过这个接口访问知识库
    - 所有结果都带credibility（可信度）
    - 所有结果都可溯源到原始文件
    """
    knowledge_api = get_knowledge_api(db)

    try:
        results = knowledge_api.search(
            query=query,
            project_id=project_id,
            top_k=top_k,
            min_credibility=min_credibility
        )

        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"知识库检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/knowledge/chunk/{chunk_id}", summary="获取chunk详情（可溯源）")
async def get_chunk_detail(
    chunk_id: int,
    db: Session = Depends(get_db)
):
    """获取chunk详情，包含溯源信息"""
    knowledge_api = get_knowledge_api(db)

    chunk = knowledge_api.get_by_id(chunk_id)

    if not chunk:
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} 不存在")

    return {
        "success": True,
        "chunk": chunk
    }


@router.get("/knowledge/trace/{citation_id}", summary="引用溯源")
async def trace_citation(
    citation_id: int,
    db: Session = Depends(get_db)
):
    """
    溯源：从引用ID追踪到原始文件位置

    **验收标准**:
    - 给定任一引用ID
    - 返回：哪个文件、哪个位置、可信度
    """
    knowledge_api = get_knowledge_api(db)

    trace_info = knowledge_api.trace_citation(citation_id)

    if not trace_info:
        raise HTTPException(status_code=404, detail=f"无法溯源 citation {citation_id}")

    return {
        "success": True,
        "trace": trace_info
    }


@router.get("/knowledge/credibility/{source_type}", summary="查询来源可信度")
async def get_source_credibility(
    source_type: str,
    db: Session = Depends(get_db)
):
    """
    查询来源类型的可信度

    来源分级:
    - official: 0.95 (官方文件)
    - academic: 0.90 (学术论文)
    - interview: 0.75 (正式访谈)
    - note: 0.60 (田野笔记)
    - secondhand: 0.40 (二手转述)
    - ai_generated: 0.50 (AI生成)
    """
    knowledge_api = get_knowledge_api(db)
    credibility = knowledge_api.get_source_credibility(source_type)

    return {
        "success": True,
        "source_type": source_type,
        "credibility": credibility
    }


# ============================================================================
# 二、评测体系（固定测试集 + 四项指标）
# ============================================================================

@router.post("/evaluation/test-case", summary="创建测试用例")
async def create_test_case(
    request: CreateTestCaseRequest,
    db: Session = Depends(get_db)
):
    """
    创建测试用例（固定题库）

    **验收标准**:
    - 20个测试题
    - 每题包含：问题、标准答案、标准来源、关键点
    """
    eval_engine = get_evaluation_engine(db)

    try:
        test_case_id = eval_engine.create_test_case(
            project_id=request.project_id,
            question=request.question,
            expected_answer=request.expected_answer,
            expected_source=request.expected_source,
            expected_aspects=request.expected_aspects,
            category=request.category,
            difficulty=request.difficulty
        )

        return {
            "success": True,
            "test_case_id": test_case_id,
            "message": "测试用例创建成功"
        }

    except Exception as e:
        logger.error(f"创建测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/test-cases/{project_id}", summary="查看测试集")
async def get_test_cases(
    project_id: int,
    db: Session = Depends(get_db)
):
    """查看项目的测试集"""
    eval_engine = get_evaluation_engine(db)

    test_cases = eval_engine.load_test_cases(project_id)

    return {
        "success": True,
        "project_id": project_id,
        "total_cases": len(test_cases),
        "test_cases": test_cases
    }


@router.post("/evaluation/run", summary="运行评测")
async def run_evaluation(
    request: RunEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    运行完整评测流程

    **评测流程**:
    1. 加载固定测试集
    2. 对每个测试用例调用Agent
    3. 计算四项指标：准确率、召回率、引用正确率、完整度
    4. 保存评测记录
    5. 生成评测报告

    **验收标准**:
    - 跑完所有测试用例
    - 输出四项指标得分
    - 可与历史版本对比
    """
    eval_engine = get_evaluation_engine(db)

    # 创建Agent调用函数（使用KnowledgeAPI）
    def agent_callable(question: str) -> Dict[str, Any]:
        """Agent查询函数（必须通过KnowledgeAPI）"""
        knowledge_api = get_knowledge_api(db)

        # 1. 通过KnowledgeAPI检索
        search_results = knowledge_api.search(
            query=question,
            project_id=request.project_id,
            top_k=5,
            min_credibility=0.0
        )

        # 2. 构建上下文
        context = "\n\n".join([
            f"[来源 {i+1}] (可信度: {r['credibility']:.2f})\n{r['text']}"
            for i, r in enumerate(search_results)
        ])

        # 3. 生成答案（简化版）
        answer = f"根据检索到的{len(search_results)}个来源，{question}的答案如下：" + (
            search_results[0]['text'][:200] if search_results else "未找到相关信息"
        )

        # 4. 返回响应
        return {
            'answer': answer,
            'retrieval_results': [
                {
                    'chunk_id': r['chunk_id'],
                    'score': r['score'],
                    'credibility': r['credibility']
                }
                for r in search_results
            ],
            'citations': [
                {
                    'chunk_id': r['chunk_id'],
                    'confidence': r['credibility'],
                    'file_id': r['trace']['file_id']
                }
                for r in search_results
            ]
        }

    try:
        # 运行评测
        result = eval_engine.run_evaluation(
            project_id=request.project_id,
            version=request.version,
            agent_callable=agent_callable
        )

        return {
            "success": True,
            "version": request.version,
            **result
        }

    except Exception as e:
        logger.error(f"评测运行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluation/compare", summary="版本对比")
async def compare_versions(
    request: CompareVersionsRequest,
    db: Session = Depends(get_db)
):
    """
    版本对比：检测回归

    **验收标准**:
    - 对比v1.0和v1.1的四项指标
    - 自动检测回归（任一指标下降>5%）
    - 给出合并建议
    """
    eval_engine = get_evaluation_engine(db)

    try:
        comparison = eval_engine.compare_versions(
            project_id=request.project_id,
            version_old=request.version_old,
            version_new=request.version_new
        )

        return {
            "success": True,
            "version_old": request.version_old,
            "version_new": request.version_new,
            **comparison
        }

    except Exception as e:
        logger.error(f"版本对比失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/history/{project_id}", summary="评测历史")
async def get_evaluation_history(
    project_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """查看项目的评测历史"""
    from sqlalchemy import text

    query_sql = text("""
        SELECT
            id, run_version, total_cases,
            avg_accuracy, avg_recall, avg_citation_correctness,
            avg_completeness, avg_overall_score, pass_rate,
            run_at
        FROM evaluation_batches
        WHERE project_id = :project_id
        ORDER BY run_at DESC
        LIMIT :limit
    """)

    results = db.execute(query_sql, {
        'project_id': project_id,
        'limit': limit
    }).fetchall()

    history = []
    for row in results:
        history.append({
            'id': row.id,
            'version': row.run_version,
            'total_cases': row.total_cases,
            'accuracy': row.avg_accuracy,
            'recall': row.avg_recall,
            'citation_correctness': row.avg_citation_correctness,
            'completeness': row.avg_completeness,
            'overall_score': row.avg_overall_score,
            'pass_rate': row.pass_rate,
            'run_at': row.run_at.isoformat() if row.run_at else None
        })

    return {
        "success": True,
        "project_id": project_id,
        "history": history
    }


# ============================================================================
# 三、Agent执行追踪
# ============================================================================

@router.post("/agent/query", summary="Agent查询（带追踪）")
async def agent_query_with_trace(
    request: AgentQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Agent查询（完整追踪）

    **验收标准**:
    - Agent只能通过KnowledgeAPI访问知识库
    - 记录每一步操作
    - 记录用到的chunk（含credibility）
    - 最终答案可溯源
    """
    knowledge_api = get_knowledge_api(db)

    steps = []
    knowledge_used = []

    try:
        # 步骤1: 通过KnowledgeAPI检索
        steps.append({
            'step': 1,
            'action': 'knowledge_search',
            'params': {'query': request.query, 'top_k': request.top_k}
        })

        search_results = knowledge_api.search(
            query=request.query,
            project_id=request.project_id,
            top_k=request.top_k,
            min_credibility=request.min_credibility
        )

        # 记录用到的知识
        for result in search_results:
            knowledge_used.append({
                'chunk_id': result['chunk_id'],
                'text': result['text'][:100],
                'credibility': result['credibility'],
                'source': result['trace']
            })

        # 步骤2: 生成答案
        steps.append({
            'step': 2,
            'action': 'generate_answer',
            'knowledge_count': len(search_results)
        })

        answer = f"根据{len(search_results)}个可信来源（平均可信度{sum(r['credibility'] for r in search_results) / len(search_results):.2f}），" + (
            search_results[0]['text'][:200] if search_results else "未找到相关信息"
        )

        # 步骤3: 引用溯源
        citations = []
        for result in search_results:
            trace_info = knowledge_api.trace_citation(result['chunk_id'])
            if trace_info:
                citations.append({
                    'chunk_id': result['chunk_id'],
                    'file_name': trace_info['file_name'],
                    'position': trace_info['position'],
                    'credibility': trace_info['credibility']
                })

        # 保存执行追踪（如果启用）
        if request.trace_execution:
            from sqlalchemy import text
            insert_sql = text("""
                INSERT INTO agent_traces (
                    project_id, query, steps, knowledge_used,
                    final_answer, citations, created_at
                ) VALUES (
                    :project_id, :query, :steps, :knowledge_used,
                    :final_answer, :citations, CURRENT_TIMESTAMP
                )
            """)

            db.execute(insert_sql, {
                'project_id': request.project_id,
                'query': request.query,
                'steps': json.dumps(steps, ensure_ascii=False),
                'knowledge_used': json.dumps(knowledge_used, ensure_ascii=False),
                'final_answer': answer,
                'citations': json.dumps(citations, ensure_ascii=False)
            })
            db.commit()

        return {
            "success": True,
            "query": request.query,
            "answer": answer,
            "steps": steps,
            "knowledge_used": knowledge_used,
            "citations": citations,
            "used_knowledge_api": True
        }

    except Exception as e:
        logger.error(f"Agent查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/traces/{project_id}", summary="查看Agent执行追踪")
async def get_agent_traces(
    project_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """查看Agent执行追踪历史"""
    from sqlalchemy import text

    query_sql = text("""
        SELECT
            id, query, steps, knowledge_used,
            final_answer, citations, created_at
        FROM agent_traces
        WHERE project_id = :project_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    results = db.execute(query_sql, {
        'project_id': project_id,
        'limit': limit
    }).fetchall()

    traces = []
    for row in results:
        traces.append({
            'id': row.id,
            'query': row.query,
            'steps': json.loads(row.steps) if row.steps else [],
            'knowledge_used': json.loads(row.knowledge_used) if row.knowledge_used else [],
            'answer': row.final_answer,
            'citations': json.loads(row.citations) if row.citations else [],
            'created_at': row.created_at.isoformat() if row.created_at else None
        })

    return {
        "success": True,
        "project_id": project_id,
        "traces": traces
    }


@router.get("/health", summary="系统健康检查")
async def health_check():
    """RAG闭环系统健康检查"""
    return {
        "status": "healthy",
        "system": "rag_closed_loop",
        "components": {
            "knowledge_api": "ok",
            "evaluation_engine": "ok",
            "agent_tracer": "ok"
        },
        "timestamp": datetime.now().isoformat()
    }
