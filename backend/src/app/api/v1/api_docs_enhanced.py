"""
API文档补全
为所有端点添加详细的Swagger文档
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from app.middleware.auth import get_current_user

# ============= 示例：增强的API文档 =============

# 请求模型（带详细描述）
class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(
        ...,
        description="项目名称",
        example="田野调查-王村",
        min_length=1,
        max_length=200
    )
    description: Optional[str] = Field(
        None,
        description="项目描述",
        example="2024年王村传统文化田野调查"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "田野调查-王村",
                "description": "2024年王村传统文化田野调查"
            }
        }


class ProjectResponse(BaseModel):
    """项目响应"""
    id: int = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    created_at: str = Field(..., description="创建时间")
    document_count: int = Field(0, description="文档数量")
    owner_id: int = Field(..., description="所有者ID")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "田野调查-王村",
                "description": "2024年王村传统文化田野调查",
                "created_at": "2024-08-05T20:00:00",
                "document_count": 15,
                "owner_id": 1
            }
        }


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool = Field(..., description="是否成功")
    document_id: int = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    status: str = Field(..., description="处理状态")
    message: str = Field("", description="提示信息")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "document_id": 123,
                "filename": "interview_001.mp3",
                "file_type": "audio",
                "status": "processing",
                "message": "文件上传成功，正在处理..."
            }
        }


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(False, description="始终为false")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误码")
    error: Optional[str] = Field(None, description="详细错误信息")
    timestamp: str = Field(..., description="时间戳")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "文件格式不支持",
                "error_code": "UNSUPPORTED_FILE_TYPE",
                "error": "Only PDF, DOCX, TXT, MP3, WAV are supported",
                "timestamp": "2024-08-05T20:00:00"
            }
        }


# ============= API端点文档示例 =============

router = APIRouter()

@router.post(
    "/projects/",
    response_model=ProjectResponse,
    status_code=201,
    summary="创建新项目",
    description="""
    创建一个新的田野调查项目。

    项目是组织文档和数据的基本单位，每个项目可以包含：
    - 文档（文本、PDF、音频、图片）
    - 分析报告
    - 知识图谱
    - 时间线

    **权限要求**: 需要登录

    **创建后**:
    - 自动设置当前用户为项目所有者
    - 生成唯一的项目ID
    - 初始化项目统计数据
    """,
    responses={
        201: {
            "description": "项目创建成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "田野调查-王村",
                        "description": "2024年王村传统文化田野调查",
                        "created_at": "2024-08-05T20:00:00",
                        "document_count": 0,
                        "owner_id": 1
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse
        },
        401: {
            "description": "未授权，需要登录",
            "model": ErrorResponse
        }
    },
    tags=["项目管理"]
)
async def create_project(
    project: ProjectCreate,
    current_user = Depends(get_current_user)
):
    """
    创建新项目

    Args:
        project: 项目信息
        current_user: 当前登录用户

    Returns:
        创建的项目信息

    Raises:
        HTTPException:
            - 400: 参数验证失败
            - 401: 未登录
    """
    raise HTTPException(
        status_code=501,
        detail="该文档示例路由未挂载，请使用 /api/v1/projects 和 /api/v1/projects/{project_id}/documents/upload。",
    )


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="上传文档",
    description="""
    上传文档到指定项目。

    **支持的文件类型**:
    - 📄 文本: TXT, MD
    - 📑 文档: PDF, DOCX, DOC
    - 🎤 音频: MP3, WAV, M4A
    - 🖼️ 图片: PNG, JPG, JPEG

    **处理流程**:
    1. 文件上传到服务器
    2. 文件类型检测和验证
    3. 后台异步处理：
       - 文本提取（PDF、DOCX）
       - 语音转文字（音频）
       - OCR识别（图片）
    4. 向量化和索引
    5. 事实陈述提取

    **文件大小限制**: 500MB

    **权限要求**: 需要登录且对项目有写权限
    """,
    responses={
        201: {
            "description": "文件上传成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "document_id": 123,
                        "filename": "interview_001.mp3",
                        "file_type": "audio",
                        "status": "processing",
                        "message": "文件上传成功，正在处理..."
                    }
                }
            }
        },
        400: {
            "description": "文件格式不支持或文件太大",
            "model": ErrorResponse
        },
        401: {
            "description": "未授权",
            "model": ErrorResponse
        },
        413: {
            "description": "文件太大",
            "model": ErrorResponse
        }
    },
    tags=["文档管理"]
)
async def upload_document(
    file: UploadFile = File(..., description="要上传的文件"),
    project_id: int = Query(..., description="项目ID"),
    current_user = Depends(get_current_user)
):
    """
    上传文档

    Args:
        file: 上传的文件
        project_id: 目标项目ID
        current_user: 当前用户

    Returns:
        上传结果和文档信息
    """
    raise HTTPException(
        status_code=501,
        detail="该文档示例路由未挂载，请使用 /api/v1/projects/{project_id}/documents/upload。",
    )


# ============= 错误码文档 =============

ERROR_CODES = {
    # 认证错误
    "UNAUTHORIZED": "未授权，需要登录",
    "TOKEN_EXPIRED": "登录已过期",
    "INVALID_CREDENTIALS": "用户名或密码错误",
    "FORBIDDEN": "无权限访问",

    # 资源错误
    "NOT_FOUND": "资源不存在",
    "RESOURCE_NOT_FOUND": "找不到指定的内容",
    "DUPLICATE_ENTRY": "该记录已存在",

    # 文件错误
    "FILE_TOO_LARGE": "文件太大",
    "UNSUPPORTED_FILE_TYPE": "不支持的文件格式",
    "FILE_UPLOAD_FAILED": "文件上传失败",

    # 验证错误
    "VALIDATION_ERROR": "数据验证失败",
    "INVALID_PARAMETER": "参数无效",

    # 处理错误
    "PROCESSING_FAILED": "处理失败",
    "EXTRACTION_FAILED": "内容提取失败",
    "VECTORIZATION_FAILED": "向量化失败",

    # 系统错误
    "INTERNAL_SERVER_ERROR": "服务器内部错误",
    "SERVICE_UNAVAILABLE": "服务暂时不可用",
    "DATABASE_ERROR": "数据库错误",
}
