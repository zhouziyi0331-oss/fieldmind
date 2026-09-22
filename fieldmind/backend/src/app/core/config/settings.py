"""
分层配置管理
支持环境隔离、配置验证、敏感信息保护
"""
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Set
from functools import lru_cache
import os
from pathlib import Path

from .constants import Environment, Limits, Defaults


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='',  # 移除前缀，直接读取 DATABASE_URL
        case_sensitive=False,
        extra='ignore'
    )

    # 优先使用 DATABASE_URL（支持 SQLite 和 PostgreSQL）
    database_url: Optional[str] = Field(default=None, description="完整数据库URL")

    # PostgreSQL 配置（当 database_url 为空时使用）
    postgres_user: str = Field(default="fieldmind", description="PostgreSQL用户名")
    postgres_password: str = Field(default="password", description="PostgreSQL密码")
    postgres_host: str = Field(default="localhost", description="PostgreSQL主机")
    postgres_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL端口")
    postgres_db: str = Field(default="fieldmind", description="PostgreSQL数据库名")

    # 连接池配置
    pool_size: int = Field(default=Limits.DATABASE_POOL_SIZE, ge=1, le=100)
    max_overflow: int = Field(default=Limits.DATABASE_MAX_OVERFLOW, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, description="连接池超时（秒）")
    pool_recycle: int = Field(default=3600, ge=60, description="连接回收时间（秒）")
    pool_pre_ping: bool = Field(default=True, description="连接前ping检查")

    # 查询配置
    query_timeout: int = Field(default=Limits.DATABASE_QUERY_TIMEOUT, ge=1)
    echo_sql: bool = Field(default=False, description="是否打印SQL")

    @field_validator('postgres_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证数据库密码强度"""
        import warnings

        weak_passwords = [
            'password',
            'your_password',
            'your-password',
            '123456',
            'admin',
            'root',
            'fieldmind',
            'postgres'
        ]

        if v.lower() in weak_passwords:
            env = os.getenv('ENVIRONMENT', 'development')
            if env == 'production':
                raise ValueError(f"生产环境不能使用弱密码 '{v}'！")
            else:
                warnings.warn(
                    f"检测到弱数据库密码，生产环境必须更改！",
                    UserWarning
                )

        return v

    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        # 优先使用 database_url（支持 SQLite）
        if self.database_url:
            return self.database_url
        # 否则使用 PostgreSQL 配置
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_url(self) -> str:
        """生成异步数据库连接URL"""
        if self.database_url and self.database_url.startswith('sqlite'):
            return self.database_url.replace('sqlite://', 'sqlite+aiosqlite://')
        elif self.database_url:
            return self.database_url
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class Neo4jSettings(BaseSettings):
    """Neo4j配置"""
    model_config = SettingsConfigDict(
        env_prefix='NEO4J_',
        case_sensitive=True
    )

    uri: str = Field(default="bolt://localhost:7687")
    user: str = Field(default="neo4j")
    password: str = Field(default="password")

    # 连接池配置
    max_connection_lifetime: int = Field(default=3600, ge=60)
    max_connection_pool_size: int = Field(default=50, ge=1, le=1000)
    connection_timeout: int = Field(default=30, ge=1)

    # 查询配置
    query_timeout: int = Field(default=60, ge=1)


class RedisSettings(BaseSettings):
    """Redis配置"""
    model_config = SettingsConfigDict(
        env_prefix='REDIS_',
        case_sensitive=True
    )

    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0, le=15)
    password: Optional[str] = Field(default=None)

    # 连接池配置
    max_connections: int = Field(default=Limits.REDIS_POOL_SIZE, ge=1, le=1000)
    socket_timeout: int = Field(default=5, ge=1)
    socket_connect_timeout: int = Field(default=5, ge=1)
    socket_keepalive: bool = Field(default=True)

    # 重试配置
    retry_on_timeout: bool = Field(default=True)
    health_check_interval: int = Field(default=30, ge=1)

    @property
    def url(self) -> str:
        """生成 Redis 连接 URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ChromaDBSettings(BaseSettings):
    """ChromaDB配置"""
    model_config = SettingsConfigDict(
        env_prefix='CHROMADB_',
        case_sensitive=True
    )

    host: str = Field(default="localhost")
    port: int = Field(default=8001, ge=1, le=65535)
    timeout: int = Field(default=30, ge=1)
    persist_dir: Path = Field(default=Path("/Users/alwan/FieldMind/chroma_db"))
    collection_name: str = Field(default="fieldmind_documents")
    enable_indexing: bool = Field(default=True)
    expected_dimension: int = Field(default=512, ge=0)


class AIServiceSettings(BaseSettings):
    """AI服务配置"""
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(default=None, alias="OPENAI_API_BASE")
    openai_organization: Optional[str] = Field(default=None, alias="OPENAI_ORGANIZATION")
    openai_timeout: int = Field(default=Limits.AI_API_TIMEOUT, ge=10)
    openai_max_retries: int = Field(default=Limits.MAX_RETRY_ATTEMPTS, ge=0, le=10)

    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_timeout: int = Field(default=Limits.AI_API_TIMEOUT, ge=10)

    # Whisper
    whisper_model: str = Field(default=Defaults.WHISPER_MODEL)
    whisper_device: str = Field(default=Defaults.WHISPER_DEVICE)
    whisper_language: str = Field(default="zh")

    # Embedding
    embedding_model: str = Field(default=Defaults.EMBEDDING_MODEL)
    embedding_dimension: int = Field(default=Defaults.EMBEDDING_DIMENSION, ge=128)
    embedding_batch_size: int = Field(default=32, ge=1, le=128)

    # RAGFlow
    ragflow_api_url: str = Field(default="http://localhost:9380")
    ragflow_api_key: Optional[str] = Field(default=None)

    @field_validator('whisper_model')
    @classmethod
    def validate_whisper_model(cls, v: str) -> str:
        valid_models = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        if v not in valid_models:
            raise ValueError(f"whisper_model must be one of {valid_models}")
        return v

    @field_validator('whisper_device')
    @classmethod
    def validate_whisper_device(cls, v: str) -> str:
        valid_devices = ['cpu', 'cuda', 'mps']
        if v not in valid_devices:
            raise ValueError(f"whisper_device must be one of {valid_devices}")
        return v


class FileStorageSettings(BaseSettings):
    """文件存储配置"""
    upload_dir: Path = Field(default=Path("./uploads"))
    data_dir: Path = Field(default=Path("./data"))
    temp_dir: Path = Field(default=Path("./temp"))

    # 文件大小限制
    max_file_size: int = Field(default=Limits.MAX_FILE_SIZE, ge=1024)
    max_video_size: int = Field(default=Limits.MAX_VIDEO_SIZE, ge=1024)
    max_audio_size: int = Field(default=Limits.MAX_AUDIO_SIZE, ge=1024)
    max_document_size: int = Field(default=Limits.MAX_DOCUMENT_SIZE, ge=1024)

    # 并发控制
    max_concurrent_uploads: int = Field(default=Limits.MAX_CONCURRENT_UPLOADS, ge=1, le=20)
    max_concurrent_processing: int = Field(default=Limits.MAX_CONCURRENT_PROCESSING, ge=1, le=10)

    # 支持的文件类型
    allowed_video_types: Set[str] = Field(
        default={'video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'}
    )
    allowed_audio_types: Set[str] = Field(
        default={'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/ogg', 'audio/flac', 'audio/aac'}
    )
    allowed_document_types: Set[str] = Field(
        default={'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'}
    )
    allowed_table_types: Set[str] = Field(
        default={'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv'}
    )

    @model_validator(mode='after')
    def create_directories(self) -> 'FileStorageSettings':
        """确保目录存在"""
        for dir_path in [self.upload_dir, self.data_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        return self


class SecuritySettings(BaseSettings):
    """安全配置"""
    # JWT
    secret_key: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        min_length=32,
        description="JWT密钥（生产环境必须修改）"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    # 速率限制
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=Limits.RATE_LIMIT_PER_USER_PER_MINUTE, ge=1)
    rate_limit_per_hour: int = Field(default=1000, ge=1)

    # 安全选项
    allow_password_reset: bool = Field(default=True)
    require_email_verification: bool = Field(default=False)
    password_min_length: int = Field(default=8, ge=6)

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """验证 SECRET_KEY 强度"""
        # 检查是否使用了默认/弱密钥
        weak_patterns = [
            'your-secret',
            'change-this',
            'changeme',
            'dev-only',
            'test-key',
            'example',
            '12345'
        ]

        v_lower = v.lower()
        for pattern in weak_patterns:
            if pattern in v_lower:
                import warnings
                warnings.warn(
                    f"检测到弱密钥模式 '{pattern}'，生产环境必须使用安全随机密钥！",
                    UserWarning
                )
                break

        # 生产环境强制检查
        env = os.getenv('ENVIRONMENT', 'development')
        if env == 'production':
            if len(v) < 64:
                raise ValueError("生产环境 SECRET_KEY 长度必须至少 64 字符！")

            for pattern in weak_patterns:
                if pattern in v_lower:
                    raise ValueError(f"生产环境不能使用包含 '{pattern}' 的密钥！")

        return v

    @model_validator(mode='after')
    def validate_production_secret(self) -> 'SecuritySettings':
        """生产环境检查密钥"""
        env = os.getenv('ENVIRONMENT', 'development')
        if env == Environment.PRODUCTION.value:
            if 'change-in-production' in self.secret_key.lower():
                raise ValueError("生产环境必须修改SECRET_KEY!")
        return self


class ProcessingSettings(BaseSettings):
    """处理配置"""
    # 文本处理
    max_text_length: int = Field(default=Limits.MAX_TEXT_LENGTH, ge=1000)
    chunk_size: int = Field(default=Limits.MAX_CHUNK_SIZE, ge=100, le=2000)
    chunk_overlap: int = Field(default=Limits.CHUNK_OVERLAP, ge=0, le=500)
    chunk_strategy: str = Field(default=Defaults.CHUNK_STRATEGY)

    # 网络分析
    similarity_threshold: float = Field(
        default=Defaults.DEFAULT_SIMILARITY_THRESHOLD,
        ge=Limits.MIN_SIMILARITY_THRESHOLD,
        le=Limits.MAX_SIMILARITY_THRESHOLD
    )
    min_documents_for_network: int = Field(default=Limits.MIN_DOCUMENTS_FOR_NETWORK, ge=2)
    min_documents_for_deep_analysis: int = Field(default=Limits.MIN_DOCUMENTS_FOR_DEEP_ANALYSIS, ge=3)

    # 实体提取
    entity_extraction_enabled: bool = Field(default=True)
    entity_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # 批处理
    batch_size: int = Field(default=Limits.MAX_BATCH_SIZE, ge=1, le=1000)

    # 并发控制
    thread_pool_workers: int = Field(default=Limits.THREAD_POOL_WORKERS, ge=1, le=16)
    process_pool_workers: int = Field(default=Limits.PROCESS_POOL_WORKERS, ge=1, le=8)


class MonitoringSettings(BaseSettings):
    """监控配置"""
    # 日志
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json | text
    log_file: Optional[Path] = Field(default=Path("./logs/app.log"))
    log_rotation: str = Field(default="100 MB")
    log_retention: str = Field(default="30 days")
    log_compression: bool = Field(default=True)

    # Metrics
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)

    # 健康检查
    health_check_enabled: bool = Field(default=True)
    health_check_interval: int = Field(default=30, ge=5)

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None)
    sentry_environment: Optional[str] = Field(default=None)
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @model_validator(mode='after')
    def create_log_directory(self) -> 'MonitoringSettings':
        """确保日志目录存在"""
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        return self


class Settings(BaseSettings):
    """主配置类"""
    model_config = SettingsConfigDict(
        env_file=['.env.local', '.env', '.env.development'],  # 按优先级加载
        env_file_encoding='utf-8',
        case_sensitive=False,  # 改为不区分大小写，更容易匹配
        extra='ignore',
        env_nested_delimiter='__'  # 支持嵌套配置 DATABASE__URL
    )

    # 应用基础配置
    app_name: str = Field(default="FieldMind")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    api_prefix: str = Field(default="/api/v1")

    # 版本信息
    version: str = Field(default="1.0.0")

    # 缓存配置
    use_redis_cache: bool = Field(default=False, description="是否使用 Redis 缓存（默认使用内存缓存）")
    cache_default_ttl: int = Field(default=300, ge=10, le=86400, description="默认缓存过期时间（秒）")

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    chromadb: ChromaDBSettings = Field(default_factory=ChromaDBSettings)
    ai: AIServiceSettings = Field(default_factory=AIServiceSettings)
    storage: FileStorageSettings = Field(default_factory=FileStorageSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    enable_external_enrichment: bool = Field(default=True)
    enable_dynamic_discovery: bool = Field(default=True)
    enable_workflow_chaining: bool = Field(default=True)

    @model_validator(mode='after')
    def validate_environment_config(self) -> 'Settings':
        """环境配置验证"""
        # 生产环境检查
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("生产环境不能开启DEBUG模式!")

            # 检查必需的API密钥
            if not self.ai.openai_api_key and not self.ai.anthropic_api_key:
                raise ValueError("生产环境至少需要配置一个AI服务API密钥")

        # 开发环境警告
        if self.environment == Environment.DEVELOPMENT:
            if 'change-in-production' in self.security.secret_key:
                import warnings
                warnings.warn("开发环境使用默认SECRET_KEY，请不要在生产环境使用!", UserWarning)

        return self

    def is_production(self) -> bool:
        """是否生产环境"""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """是否开发环境"""
        return self.environment == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """是否测试环境"""
        return self.environment == Environment.TESTING


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存）"""
    return Settings()


# 导出全局配置实例
settings = get_settings()
