"""
配置管理
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""
    model_config = ConfigDict(
        env_file=".env",  # 从.env加载
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    # 应用设置
    APP_NAME: str = "FieldMind"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,capacitor://localhost,ionic://localhost"
    ).split(",") if isinstance(os.getenv("CORS_ORIGINS"), str) else [
        "http://localhost:3000",  # React Web
        "http://localhost:5173",  # Vite dev server
        "capacitor://localhost",  # iOS App
        "ionic://localhost",
    ]

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fieldmind.db')}"
    )
    POSTGRES_USER: str = "fieldmind"
    POSTGRES_PASSWORD: str = "fieldmind_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fieldmind"

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "fieldmind123")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ChromaDB
    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT: int = int(os.getenv("CHROMADB_PORT", "8001"))
    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
    )
    CHROMA_COLLECTION_NAME: str = "fieldmind_documents"

    # AI API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 语音转录配置
    ASR_ENGINE: str = "funasr"  # "whisper" 或 "funasr"

    # Whisper配置
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"  # 或 "cuda"

    # FunASR配置
    FUNASR_MODEL: str = "paraformer-zh"  # 中文识别模型
    FUNASR_VAD_MODEL: str = "fsmn-vad"  # 语音活动检测
    FUNASR_PUNC_MODEL: str = "ct-punc"  # 标点恢复
    FUNASR_HOTWORDS: str = ""  # 热词，用空格分隔，如 "口述历史 田野调查"

    # 向量嵌入模型
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # HuggingFace Token（如果使用私有模型）
    HUGGINGFACE_TOKEN: str = ""

    # RAGFlow配置
    RAGFLOW_API_URL: str = os.getenv("RAGFLOW_API_URL", "http://localhost:9380")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")


settings = Settings()
