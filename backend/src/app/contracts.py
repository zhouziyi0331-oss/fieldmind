"""
API数据契约 - 统一前后端接口定义
Python版本（后端使用）

规则：
1. 所有API响应必须遵循统一格式
2. 字段名必须与前端contracts.ts保持一致
3. 新增字段必须同步更新两个契约文件
"""

from typing import TypedDict, Optional, List, Any
from datetime import datetime


# ============= 统一响应格式 =============

class APIResponse(TypedDict):
    """所有API响应的统一格式"""
    code: int          # 0=成功, 非0=错误
    message: str       # 成功/错误信息
    data: Optional[Any]  # 实际数据


# ============= 文档相关 =============

class DocumentUploadResponse(TypedDict):
    """文档上传响应"""
    document_id: int
    filename: str
    status: str  # "uploading" | "processing" | "completed" | "failed"
    upload_time: str  # ISO格式时间


class DocumentDetail(TypedDict):
    """文档详情"""
    id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    text_content: Optional[str]
    word_count: int
    created_at: str
    extra_data: Optional[dict]


class DocumentListResponse(TypedDict):
    """文档列表响应"""
    documents: List[DocumentDetail]
    total: int


# ============= 数据分析相关 =============

class TopicStat(TypedDict):
    """主题统计"""
    topic: str
    count: int
    percentage: float


class EntityStat(TypedDict):
    """实体统计"""
    name: str
    count: int


class TopicDistributionResponse(TypedDict):
    """主题分布响应"""
    project_id: int
    topics: List[TopicStat]
    total: int


class ReportValidation(TypedDict):
    """报告验证结果"""
    passed: bool
    method: str  # "template-based" | "llm-generated"
    errors: List[str]


class ReportResponse(TypedDict):
    """报告生成响应"""
    type: str
    generated_at: str
    text: str
    facts: dict
    validation: ReportValidation


# ============= 错误码定义 =============

class ErrorCodes:
    """统一错误码"""
    SUCCESS = 0

    # 客户端错误 4xx
    INVALID_PARAMS = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404

    # 服务端错误 5xx
    INTERNAL_ERROR = 500
    DATABASE_ERROR = 501
    CHROMADB_ERROR = 502
    HALLUCINATION_DETECTED = 503  # 幻觉检测失败


# ============= 辅助函数 =============

def success_response(data: Any, message: str = "success") -> APIResponse:
    """构建成功响应"""
    return {
        "code": ErrorCodes.SUCCESS,
        "message": message,
        "data": data
    }


def error_response(code: int, message: str, data: Any = None) -> APIResponse:
    """构建错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


# ============= 示例用法 =============

"""
# 后端使用示例

from app.contracts import success_response, error_response, ErrorCodes

@router.post("/upload")
def upload_document(file: UploadFile):
    try:
        # 处理上传
        doc_id = save_file(file)

        # 返回成功响应
        return success_response({
            "document_id": doc_id,
            "filename": file.filename,
            "status": "uploading",
            "upload_time": datetime.now().isoformat()
        })

    except Exception as e:
        # 返回错误响应
        return error_response(
            code=ErrorCodes.INTERNAL_ERROR,
            message=str(e)
        )
"""
