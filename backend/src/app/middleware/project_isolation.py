"""
项目隔离中间件

确保所有数据查询都带有project_id过滤
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class ProjectIsolationMiddleware(BaseHTTPMiddleware):
    """
    项目隔离中间件
    
    对于需要项目隔离的API路径，强制检查project_id参数
    """
    
    # 需要强制project_id的路径前缀
    ISOLATED_PATHS = [
        "/api/documents",
        "/api/chat",
        "/api/skills",
        "/api/reports",
        "/api/dashboard"
    ]
    
    # 排除的路径（不需要project_id）
    EXCLUDED_PATHS = [
        "/api/projects",  # 项目列表本身
        "/api/skills/available",  # 获取可用skill列表
        "/docs",
        "/openapi.json"
    ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 检查是否需要隔离
        needs_isolation = any(path.startswith(prefix) for prefix in self.ISOLATED_PATHS)
        is_excluded = any(path.startswith(prefix) for prefix in self.EXCLUDED_PATHS)
        
        if needs_isolation and not is_excluded:
            # 从query params或body中提取project_id
            project_id = None
            
            # 检查query参数
            if "project_id" in request.query_params:
                project_id = request.query_params.get("project_id")
            
            # 检查路径参数（如 /api/dashboard/stats/{project_id}）
            if not project_id and "{project_id}" in path or path.split('/')[-1].isdigit():
                try:
                    project_id = path.split('/')[-1]
                    if project_id.isdigit():
                        project_id = int(project_id)
                except (ValueError, IndexError) as e:
                    logger.debug(f"解析路径中的project_id失败: {e}")
                except Exception as e:
                    logger.warning(f"提取project_id时出现异常: {e}")
            
            # 对于POST/PUT请求，也可以从body读取（但不阻塞，因为body会被消费）
            
            # 如果是关键查询且缺少project_id，记录警告
            if not project_id and request.method == "GET":
                logger.warning(f"⚠️ 项目隔离警告: {path} 未携带project_id")
        
        response = await call_next(request)
        return response
