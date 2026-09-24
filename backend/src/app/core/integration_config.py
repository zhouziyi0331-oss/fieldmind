"""统一集成配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class IntegrationConfig(BaseSettings):
    """集成配置"""

    # LLM配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_model: str = "gpt-4"

    # 嵌入模型
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536

    # Obsidian配置
    obsidian_vault_path: Optional[str] = None
    obsidian_sync_enabled: bool = False

    # RAG配置
    rag_top_k: int = 10
    rag_similarity_threshold: float = 0.7
    rag_context_max_tokens: int = 2000

    class Config:
        env_prefix = "FIELDMIND_"
        env_file = ".env"


# 全局配置实例
integration_config = IntegrationConfig()
