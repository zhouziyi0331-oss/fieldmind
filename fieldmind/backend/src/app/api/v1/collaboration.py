"""
协作与权限 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse
from app.services.collaboration_service import ProjectRole, PermissionType

router = APIRouter()


@router.get("/projects/{project_id}/members", response_model=ApiResponse)
async def get_project_members(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    获取项目成员列表

    返回所有成员及其角色
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        members = collaboration_service.get_project_members(db, project_id)

        return success_response(
            data={
                "project_id": project_id,
                "members": members,
                "total": len(members)
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/members", response_model=ApiResponse)
async def add_project_member(
    request: Request,
    project_id: int,
    user_id: int = Body(..., description="要添加的用户ID"),
    role: str = Body(..., description="角色: owner/admin/editor/viewer"),
    db: Session = Depends(get_db),
):
    """
    添加项目成员

    需要权限：MEMBER_INVITE
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        # TODO: 获取当前用户ID（从认证中间件）
        current_user_id = getattr(request.state, "user_id", 1)

        # 检查权限
        has_permission = collaboration_service.check_permission(
            db=db,
            project_id=project_id,
            user_id=current_user_id,
            permission=PermissionType.MEMBER_INVITE
        )

        if not has_permission:
            raise HTTPException(status_code=403, detail="无权限添加成员")

        # 验证角色
        try:
            project_role = ProjectRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的角色")

        # 添加成员
        result = collaboration_service.add_member(
            db=db,
            project_id=project_id,
            user_id=user_id,
            role=project_role,
            invited_by=current_user_id
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return success_response(
            data=result,
            request_id=request_id,
            message="成员添加成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/members/{user_id}", response_model=ApiResponse)
async def remove_project_member(
    request: Request,
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    移除项目成员

    需要权限：MEMBER_REMOVE
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        # 获取当前用户
        current_user_id = getattr(request.state, "user_id", 1)

        # 检查权限
        has_permission = collaboration_service.check_permission(
            db=db,
            project_id=project_id,
            user_id=current_user_id,
            permission=PermissionType.MEMBER_REMOVE
        )

        if not has_permission:
            raise HTTPException(status_code=403, detail="无权限移除成员")

        # 移除成员
        result = collaboration_service.remove_member(
            db=db,
            project_id=project_id,
            user_id=user_id,
            removed_by=current_user_id
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return success_response(
            data=result,
            request_id=request_id,
            message="成员已移除"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_id}/members/{user_id}/role", response_model=ApiResponse)
async def change_member_role(
    request: Request,
    project_id: int,
    user_id: int,
    new_role: str = Body(..., embed=True, description="新角色"),
    db: Session = Depends(get_db),
):
    """
    修改成员角色

    需要权限：MEMBER_ROLE_CHANGE
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        # 获取当前用户
        current_user_id = getattr(request.state, "user_id", 1)

        # 检查权限
        has_permission = collaboration_service.check_permission(
            db=db,
            project_id=project_id,
            user_id=current_user_id,
            permission=PermissionType.MEMBER_ROLE_CHANGE
        )

        if not has_permission:
            raise HTTPException(status_code=403, detail="无权限修改成员角色")

        # 验证角色
        try:
            project_role = ProjectRole(new_role)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的角色")

        # 修改角色
        result = collaboration_service.change_member_role(
            db=db,
            project_id=project_id,
            user_id=user_id,
            new_role=project_role,
            changed_by=current_user_id
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return success_response(
            data=result,
            request_id=request_id,
            message="角色修改成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/invites", response_model=ApiResponse)
async def create_invite_link(
    request: Request,
    project_id: int,
    role: str = Body(..., description="邀请角色"),
    expires_in_days: int = Body(7, description="有效期（天）"),
    db: Session = Depends(get_db),
):
    """
    生成邀请链接

    需要权限：MEMBER_INVITE
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        # 获取当前用户
        current_user_id = getattr(request.state, "user_id", 1)

        # 检查权限
        has_permission = collaboration_service.check_permission(
            db=db,
            project_id=project_id,
            user_id=current_user_id,
            permission=PermissionType.MEMBER_INVITE
        )

        if not has_permission:
            raise HTTPException(status_code=403, detail="无权限创建邀请")

        # 验证角色
        try:
            project_role = ProjectRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的角色")

        # 生成邀请链接
        invite = collaboration_service.generate_invite_link(
            db=db,
            project_id=project_id,
            role=project_role,
            created_by=current_user_id,
            expires_in_days=expires_in_days
        )

        return success_response(
            data=invite,
            request_id=request_id,
            message="邀请链接已生成"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/activity-log", response_model=ApiResponse)
async def get_activity_log(
    request: Request,
    project_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    获取项目活动日志

    记录所有成员的操作历史
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        logs = collaboration_service.get_activity_log(
            db=db,
            project_id=project_id,
            limit=limit
        )

        return success_response(
            data={
                "project_id": project_id,
                "logs": logs,
                "total": len(logs)
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/permissions/check", response_model=ApiResponse)
async def check_user_permission(
    request: Request,
    project_id: int,
    permission: str,
    db: Session = Depends(get_db),
):
    """
    检查当前用户是否有特定权限

    用于前端按钮显示/隐藏的判断
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.collaboration_service import collaboration_service

        # 获取当前用户
        current_user_id = getattr(request.state, "user_id", 1)

        # 验证权限类型
        try:
            perm = PermissionType(permission)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的权限类型")

        # 检查权限
        has_permission = collaboration_service.check_permission(
            db=db,
            project_id=project_id,
            user_id=current_user_id,
            permission=perm
        )

        return success_response(
            data={
                "has_permission": has_permission,
                "permission": permission
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
