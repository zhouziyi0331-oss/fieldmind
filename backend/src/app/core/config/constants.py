"""
系统常量定义
集中管理所有魔术数字和字符串常量
"""
from enum import Enum


class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ErrorCode(str, Enum):
    """统一错误码"""
    # 通用错误 (1xxx)
    UNKNOWN_ERROR = "1000"
    VALIDATION_ERROR = "1001"
    CONFIGURATION_ERROR = "1002"
    RESOURCE_NOT_FOUND = "1003"
    PERMISSION_DENIED = "1004"
    RATE_LIMIT_EXCEEDED = "1005"

    # 数据库错误 (2xxx)
    DATABASE_CONNECTION_ERROR = "2000"
    DATABASE_QUERY_ERROR = "2001"
    DATABASE_TRANSACTION_ERROR = "2002"
    DATABASE_CONSTRAINT_VIOLATION = "2003"
    DATABASE_DEADLOCK = "2004"

    # 文件处理错误 (3xxx)
    FILE_NOT_FOUND = "3000"
    FILE_TOO_LARGE = "3001"
    FILE_TYPE_NOT_SUPPORTED = "3002"
    FILE_CORRUPTED = "3003"
    FILE_UPLOAD_FAILED = "3004"
    FILE_PROCESSING_FAILED = "3005"

    # AI服务错误 (4xxx)
    AI_SERVICE_UNAVAILABLE = "4000"
    AI_API_KEY_INVALID = "4001"
    AI_RATE_LIMIT = "4002"
    AI_TIMEOUT = "4003"
    AI_RESPONSE_INVALID = "4004"
    EMBEDDING_GENERATION_FAILED = "4005"
    TRANSCRIPTION_FAILED = "4006"

    # 向量数据库错误 (5xxx)
    VECTOR_DB_CONNECTION_ERROR = "5000"
    VECTOR_DB_QUERY_ERROR = "5001"
    VECTOR_DB_INSERT_ERROR = "5002"

    # 图数据库错误 (6xxx)
    GRAPH_DB_CONNECTION_ERROR = "6000"
    GRAPH_DB_QUERY_ERROR = "6001"
    GRAPH_DB_WRITE_ERROR = "6002"

    # 缓存错误 (7xxx)
    CACHE_CONNECTION_ERROR = "7000"
    CACHE_OPERATION_FAILED = "7001"

    # 网络分析错误 (8xxx)
    NETWORK_BUILD_FAILED = "8000"
    ENTITY_RESOLUTION_FAILED = "8001"
    RELATION_DISCOVERY_FAILED = "8002"
    NETWORK_ANALYSIS_FAILED = "8003"


class ProcessingStage(str, Enum):
    """文档处理阶段"""
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    CHUNKING = "chunking"
    CHUNKED = "chunked"
    EMBEDDING = "embedding"
    EMBEDDED = "embedded"
    ENTITY_EXTRACTION = "entity_extraction"
    ENTITY_EXTRACTED = "entity_extracted"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    KNOWLEDGE_GRAPH_BUILT = "knowledge_graph_built"
    CROSS_DOCUMENT_ANALYSIS = "cross_document_analysis"
    CROSS_DOCUMENT_ANALYZED = "cross_document_analyzed"
    NETWORK_BUILDING = "network_building"
    NETWORK_BUILT = "network_built"
    DEEP_ANALYSIS = "deep_analysis"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentRelationType(str, Enum):
    """文档关系类型"""
    REFERENCES = "REFERENCES"  # A引用B
    SUPPLEMENTS = "SUPPLEMENTS"  # A补充B
    CONTRADICTS = "CONTRADICTS"  # A与B矛盾
    SIMILAR_TOPIC = "SIMILAR_TOPIC"  # 相似主题
    TEMPORAL_SEQUENCE = "TEMPORAL_SEQUENCE"  # 时间序列
    SAME_ENTITY = "SAME_ENTITY"  # 包含相同实体


class NetworkLayerType(str, Enum):
    """网络层类型"""
    ENTITY_NETWORK = "entity_network"
    DOCUMENT_SIMILARITY = "document_similarity"
    TEMPORAL_NETWORK = "temporal_network"


class FileType(str, Enum):
    """支持的文件类型"""
    # 文档
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOC = "application/msword"
    TXT = "text/plain"
    MD = "text/markdown"

    # 表格
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    XLS = "application/vnd.ms-excel"
    CSV = "text/csv"

    # 音频
    MP3 = "audio/mpeg"
    WAV = "audio/wav"
    M4A = "audio/mp4"
    OGG = "audio/ogg"
    FLAC = "audio/flac"
    AAC = "audio/aac"

    # 视频
    MP4 = "video/mp4"
    AVI = "video/x-msvideo"
    MOV = "video/quicktime"
    MKV = "video/x-matroska"
    WEBM = "video/webm"

    # 图片
    PNG = "image/png"
    JPEG = "image/jpeg"
    JPG = "image/jpeg"
    GIF = "image/gif"
    WEBP = "image/webp"


class CacheKey:
    """缓存键模板"""
    DOCUMENT_NETWORK = "doc_network:{project_id}"
    ENTITY_ALIGNMENT = "entity_align:{project_id}"
    DOCUMENT_EMBEDDING = "doc_embed:{document_id}"
    PROCESSING_LOCK = "lock:process:{document_id}"
    USER_RATE_LIMIT = "rate_limit:user:{user_id}"
    HEALTH_CHECK = "health:service:{service_name}"


class QueueName(str, Enum):
    """任务队列名称"""
    DOCUMENT_PROCESSING = "document_processing"
    EMBEDDING_GENERATION = "embedding_generation"
    ENTITY_EXTRACTION = "entity_extraction"
    NETWORK_ANALYSIS = "network_analysis"
    NOTIFICATION = "notification"


class MetricName(str, Enum):
    """监控指标名称"""
    # 处理时长
    DOCUMENT_PROCESSING_DURATION = "document_processing_duration_seconds"
    EMBEDDING_GENERATION_DURATION = "embedding_generation_duration_seconds"
    ENTITY_EXTRACTION_DURATION = "entity_extraction_duration_seconds"
    NETWORK_BUILD_DURATION = "network_build_duration_seconds"

    # 计数器
    DOCUMENT_PROCESSED_TOTAL = "document_processed_total"
    DOCUMENT_FAILED_TOTAL = "document_failed_total"
    API_REQUEST_TOTAL = "api_request_total"
    API_ERROR_TOTAL = "api_error_total"

    # 资源使用
    DATABASE_CONNECTION_POOL_SIZE = "database_connection_pool_size"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUEUE_SIZE = "queue_size"

    # AI服务
    AI_API_CALL_TOTAL = "ai_api_call_total"
    AI_API_ERROR_TOTAL = "ai_api_error_total"
    AI_TOKEN_USAGE_TOTAL = "ai_token_usage_total"


# 限制常量
class Limits:
    """系统限制"""
    # 文件大小限制（字节）
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_AUDIO_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100MB

    # 文本限制
    MAX_TEXT_LENGTH = 1_000_000  # 100万字符
    MAX_CHUNK_SIZE = 1000  # 分块大小
    CHUNK_OVERLAP = 200  # 分块重叠

    # 批处理限制
    MAX_BATCH_SIZE = 100
    MAX_CONCURRENT_UPLOADS = 5
    MAX_CONCURRENT_PROCESSING = 3

    # 网络分析限制
    MIN_SIMILARITY_THRESHOLD = 0.70
    DEFAULT_SIMILARITY_THRESHOLD = 0.85
    MAX_SIMILARITY_THRESHOLD = 0.95
    MIN_DOCUMENTS_FOR_NETWORK = 2
    MIN_DOCUMENTS_FOR_DEEP_ANALYSIS = 3

    # 超时设置（秒）
    DATABASE_QUERY_TIMEOUT = 30
    AI_API_TIMEOUT = 120
    FILE_PROCESSING_TIMEOUT = 600
    NETWORK_BUILD_TIMEOUT = 300

    # 重试设置
    MAX_RETRY_ATTEMPTS = 3
    RETRY_BASE_DELAY = 1.0  # 秒
    RETRY_MAX_DELAY = 60.0  # 秒
    RETRY_EXPONENTIAL_BASE = 2

    # 速率限制
    RATE_LIMIT_PER_USER_PER_MINUTE = 60
    RATE_LIMIT_PER_IP_PER_MINUTE = 100

    # 缓存TTL（秒）
    CACHE_TTL_SHORT = 300  # 5分钟
    CACHE_TTL_MEDIUM = 3600  # 1小时
    CACHE_TTL_LONG = 86400  # 24小时

    # 连接池大小
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 40
    REDIS_POOL_SIZE = 50

    # 线程池大小
    THREAD_POOL_WORKERS = 4
    PROCESS_POOL_WORKERS = 2


# 默认值
class Defaults:
    """默认配置值"""
    WHISPER_MODEL = "base"  # base | small | medium | large | large-v3
    WHISPER_DEVICE = "cpu"
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION = 768
    LANGUAGE = "zh"
    CHUNK_STRATEGY = "semantic"  # fixed | semantic | sliding
    SIMILARITY_METRIC = "cosine"  # cosine | euclidean | dot
    DEFAULT_SIMILARITY_THRESHOLD = 0.85
