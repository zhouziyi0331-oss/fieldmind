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
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"  # 默认False，生产环境安全
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")  # ⚠️ 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 语音转录配置
    ASR_ENGINE: str = "funasr"  # "whisper" 或 "funasr"

    # Whisper配置
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_USE_LOCAL: bool = os.getenv("WHISPER_USE_LOCAL", "true").lower() == "true"
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")

    # FunASR配置
    FUNASR_MODEL: str = os.getenv("FUNASR_MODEL", "paraformer-zh")
    FUNASR_VAD_MODEL: str = os.getenv("FUNASR_VAD_MODEL", "fsmn-vad")
    FUNASR_PUNC_MODEL: str = os.getenv("FUNASR_PUNC_MODEL", "ct-punc")
    FUNASR_HOTWORDS: str = os.getenv("FUNASR_HOTWORDS", "")

    # 向量嵌入模型
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    # HuggingFace Token（如果使用私有模型）
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")

    # Ollama配置
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # RAGFlow配置
    RAGFLOW_API_URL: str = os.getenv("RAGFLOW_API_URL", "http://localhost:9380")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")

    # MinerU配置
    MINERU_API_URL: str = os.getenv("MINERU_API_URL", "http://localhost:8765")

    # Crawl4AI配置
    CRAWL4AI_API_URL: str = os.getenv("CRAWL4AI_API_URL", "http://localhost:8080")

    # Mem0配置
    MEM0_API_URL: str = os.getenv("MEM0_API_URL", "http://localhost:8081")

    # Cognee配置
    COGNEE_API_URL: str = os.getenv("COGNEE_API_URL", "http://localhost:8082")

    # GraphRAG配置
    GRAPHRAG_API_URL: str = os.getenv("GRAPHRAG_API_URL", "http://localhost:8083")

    # Khoj配置
    KHOJ_API_URL: str = os.getenv("KHOJ_API_URL", "http://localhost:8084")


settings = Settings()
