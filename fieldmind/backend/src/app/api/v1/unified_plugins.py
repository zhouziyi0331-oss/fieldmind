"""
统一插件API接口

提供文件处理插件的HTTP接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
import os
import tempfile
from pathlib import Path

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.core.plugin_manager import get_plugin_manager, PluginManager
from app.core.logging import logger
from pydantic import BaseModel, Field


router = APIRouter()


# ==================== Pydantic 模型 ====================

class PluginInfo(BaseModel):
    """插件信息"""
    name: str
    supported_extensions: List[str]
    description: str


class ProcessResult(BaseModel):
    """处理结果"""
    success: bool
    plugin_used: str
    file_path: str
    result: Dict[str, Any]
    error: Optional[str] = None


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    file_paths: List[str] = Field(..., description="文件路径列表")
    plugin_name: Optional[str] = Field(None, description="指定插件名称")


# ==================== 插件管理 ====================

@router.get("/list", response_model=List[PluginInfo], summary="获取插件列表")
async def list_plugins(
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    获取所有已注册的插件列表
    """
    plugins = plugin_mgr.list_plugins()
    return [PluginInfo(**p) for p in plugins]


@router.get("/extensions", summary="获取支持的文件扩展名")
async def get_supported_extensions(
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    获取所有支持的文件扩展名
    """
    extensions = plugin_mgr.get_supported_extensions()
    return {
        "supported_extensions": extensions,
        "total": len(extensions)
    }


@router.get("/plugin/{plugin_name}", response_model=PluginInfo, summary="获取插件详情")
async def get_plugin_info(
    plugin_name: str,
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    获取指定插件的详细信息
    """
    plugin = plugin_mgr.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 不存在")

    return PluginInfo(**plugin.get_metadata())


# ==================== 文件处理 ====================

@router.post("/process/upload", response_model=ProcessResult, summary="上传并处理文件")
async def process_uploaded_file(
    file: UploadFile = File(...),
    plugin_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager),
    db: Session = Depends(get_db)
):
    """
    上传文件并使用插件处理

    - 自动选择合适的插件（基于文件扩展名）
    - 或手动指定插件名称
    """
    # 保存上传的文件到临时目录
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # 使用插件处理
        result = plugin_mgr.process_file(
            file_path=tmp_path,
            plugin_name=plugin_name
        )

        return ProcessResult(
            success=result.get("success", False),
            plugin_used=result.get("plugin_used", "unknown"),
            file_path=file.filename,
            result=result,
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"处理上传文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.post("/process/path", response_model=ProcessResult, summary="处理服务器文件")
async def process_file_by_path(
    file_path: str = Form(...),
    plugin_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    处理服务器上已存在的文件

    - 需要提供服务器上的完整文件路径
    - 可以指定使用的插件
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件 {file_path} 不存在")

    try:
        result = plugin_mgr.process_file(
            file_path=file_path,
            plugin_name=plugin_name
        )

        return ProcessResult(
            success=result.get("success", False),
            plugin_used=result.get("plugin_used", "unknown"),
            file_path=file_path,
            result=result,
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"处理文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/batch", summary="批量处理文件")
async def batch_process_files(
    request: BatchProcessRequest,
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    批量处理多个文件

    - 支持自动选择插件或统一使用指定插件
    - 返回每个文件的处理结果
    """
    results = []

    for file_path in request.file_paths:
        try:
            if not os.path.exists(file_path):
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": "文件不存在"
                })
                continue

            result = plugin_mgr.process_file(
                file_path=file_path,
                plugin_name=request.plugin_name
            )

            results.append({
                "file_path": file_path,
                "success": result.get("success", False),
                "plugin_used": result.get("plugin_used", "unknown"),
                "result": result,
                "error": result.get("error")
            })

        except Exception as e:
            results.append({
                "file_path": file_path,
                "success": False,
                "error": str(e)
            })

    # 统计
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)

    return {
        "total": total_count,
        "success": success_count,
        "failed": total_count - success_count,
        "results": results
    }


# ==================== 插件测试 ====================

@router.get("/test/{plugin_name}", summary="测试插件")
async def test_plugin(
    plugin_name: str,
    test_file: str = Query(..., description="测试文件路径"),
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    测试指定插件是否可以处理文件
    """
    plugin = plugin_mgr.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 不存在")

    if not os.path.exists(test_file):
        raise HTTPException(status_code=404, detail=f"测试文件 {test_file} 不存在")

    # 验证文件
    can_process = plugin.validate(test_file)

    return {
        "plugin_name": plugin_name,
        "test_file": test_file,
        "can_process": can_process,
        "supported_extensions": plugin.supported_extensions
    }


# ==================== 自动推荐 ====================

@router.post("/recommend", summary="推荐插件")
async def recommend_plugin(
    file_path: str = Form(...),
    current_user: User = Depends(get_current_user),
    plugin_mgr: PluginManager = Depends(get_plugin_manager)
):
    """
    根据文件路径推荐合适的插件
    """
    plugin = plugin_mgr.get_plugin_by_file(file_path)

    if not plugin:
        return {
            "recommended_plugin": None,
            "message": f"没有找到可以处理该文件的插件",
            "file_extension": Path(file_path).suffix
        }

    return {
        "recommended_plugin": plugin.plugin_name,
        "plugin_info": plugin.get_metadata(),
        "file_extension": Path(file_path).suffix
    }
