"""依赖注入函数"""
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session


def get_vector_store(request: Request):
    """获取向量存储实例"""
    if hasattr(request.app.state, 'integration_manager'):
        manager = request.app.state.integration_manager
        if manager and manager.vector_store:
            return manager.vector_store
    raise HTTPException(status_code=503, detail="Vector store not initialized")


def get_graph_builder(request: Request):
    """获取知识图谱构建器"""
    if hasattr(request.app.state, 'integration_manager'):
        manager = request.app.state.integration_manager
        if manager and manager.graph_builder:
            return manager.graph_builder
    raise HTTPException(status_code=503, detail="Graph builder not initialized")


def get_llm_enhancer(request: Request):
    """获取LLM增强器"""
    if hasattr(request.app.state, 'integration_manager'):
        manager = request.app.state.integration_manager
        if manager and manager.llm_enhancer:
            return manager.llm_enhancer
    # 返回None而不是抛出异常，允许可选功能
    return None
