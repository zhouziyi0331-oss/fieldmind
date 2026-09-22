"""
配置管理
"""

from pydantic_settings import BaseSettings, NoDecode
from pydantic import ConfigDict, Field, field_validator
from typing import Annotated, List
import json
import os
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
BACKEND_SRC_DIR = APP_DIR.parent
DATA_DIR = BACKEND_SRC_DIR / "data"


def _resolve_project_path(value: str, default_relative: str) -> str:
    path = Path(value or default_relative).expanduser()
    if not path.is_absolute():
        if path.parts and path.parts[0] == "data":
            path = BACKEND_SRC_DIR / path
        else:
            path = DATA_DIR / path
    return str(path.resolve())


def _resolve_sqlite_url(value: str) -> str:
    raw = value or f"sqlite:///{DATA_DIR / 'fieldmind.db'}"
    if not raw.startswith("sqlite:///"):
        return raw

    sqlite_path = raw.replace("sqlite:///", "", 1)
    return f"sqlite:///{_resolve_project_path(sqlite_path, 'data/fieldmind.db')}"


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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        """兼容部署环境把 DEBUG 写成 release/development 的历史配置。"""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "development", "dev", "true", "1", "yes", "on"}:
                return True
        return value

    # CORS
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(
        default=[
        "http://localhost:3000",  # React Web
        "http://localhost:3002",  # React Web (alternative port)
        "http://localhost:5173",  # Vite dev server
        "capacitor://localhost",  # iOS App
        "ionic://localhost",
        ],
        validation_alias="BACKEND_CORS_ORIGINS",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    # 数据库
    DATABASE_URL: str = Field(
        default_factory=lambda: f"sqlite:///{DATA_DIR / 'fieldmind.db'}"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        return _resolve_sqlite_url(value)
    POSTGRES_USER: str = "fieldmind"
    POSTGRES_PASSWORD: str = "fieldmind_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fieldmind"

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "fieldmind123")

    # ArangoDB
    ARANGO_HOST: str = os.getenv("ARANGO_HOST", "localhost")
    ARANGO_PORT: str = os.getenv("ARANGO_PORT", "8529")
    ARANGO_USER: str = os.getenv("ARANGO_USER", "root")
    ARANGO_PASSWORD: str = os.getenv("ARANGO_PASSWORD", "fieldmind123")
    ARANGO_DB: str = os.getenv("ARANGO_DB", "fieldmind")

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
        str(DATA_DIR / "chroma_db")
    )

    @field_validator("CHROMA_PERSIST_DIR", mode="before")
    @classmethod
    def normalize_chroma_persist_dir(cls, value):
        return _resolve_project_path(value, "chroma_db")

    CHROMA_COLLECTION_NAME: str = "fieldmind_documents"
    ENABLE_CHROMA_INDEXING: bool = True
    CHROMA_EXPECTED_DIMENSION: int = 0

    # 上传后的主链路以 SQLite 结构化数据为准。外部增强链路默认关闭，避免未配置服务拖慢上传。
    ENABLE_EXTERNAL_ENRICHMENT: bool = True
    ENABLE_DYNAMIC_DISCOVERY: bool = True
    ENABLE_WORKFLOW_CHAINING: bool = True

    # AI API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # 文件存储
    UPLOAD_DIR: str = Field(default_factory=lambda: str(DATA_DIR / "uploads"))

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def normalize_upload_dir(cls, value):
        return _resolve_project_path(value, "uploads")
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

    # 新向量存储配置
    USE_NEW_VECTOR_STORE: bool = False  # 是否使用新的高性能向量存储
    VECTOR_STORE_INDEX_TYPE: str = "hnsw"  # flat/hnsw/ivf
    VECTOR_STORE_USE_CACHE: bool = True  # 是否启用缓存
    VECTOR_STORE_DIMENSION: int = 1536  # 向量维度（OpenAI默认）

    # HuggingFace Token（如果使用私有模型）
    HUGGINGFACE_TOKEN: str = ""

    # RAGFlow配置
    RAGFLOW_API_URL: str = os.getenv("RAGFLOW_API_URL", "http://localhost:9380")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")

    # Redis 缓存配置
    REDIS_ENABLED: bool = Field(default=False)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")

    # Sentry 错误追踪
    SENTRY_ENABLED: bool = Field(default=False)
    SENTRY_DSN: str = Field(default="")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1)  # 10% 采样
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.1)  # 10% 采样

    # 应用版本和环境
    VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")  # development/staging/production

    # Prometheus 监控
    PROMETHEUS_ENABLED: bool = Field(default=False)
    PROMETHEUS_PORT: int = Field(default=9090)


settings = Settings()
