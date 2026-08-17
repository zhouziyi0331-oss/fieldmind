"""
File Manager API - 文件管理（基于路径的虚拟文件夹）
通过文件路径前缀模拟文件夹结构，无需数据库重构
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging
import os

from app.core.database import get_db
from app.models.project import ProjectDocument

router = APIRouter(tags=["file-manager"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class FileNodeResponse(BaseModel):
    """文件节点响应（树状结构）"""
    id: str
    name: str
    is_folder: bool
    type: str
    size: int
    modified_at: datetime
    path: str  # 完整路径，如 "documents/reports/2024"
    children: List['FileNodeResponse'] = []

    class Config:
        from_attributes = True


FileNodeResponse.model_rebuild()  # 解决前向引用


class FileTreeResponse(BaseModel):
    """文件树响应"""
    root: FileNodeResponse
    total_files: int
    total_folders: int
    total_size: int


class CreateFolderRequest(BaseModel):
    """创建文件夹请求"""
    project_id: int
    folder_path: str  # 如 "documents/reports/2024"


class MoveFileRequest(BaseModel):
    """移动文件请求"""
    file_id: int
    target_path: str  # 目标文件夹路径


# ==================== Helper Functions ====================

def parse_path(file_path: str, base_dir: str) -> str:
    """
    从文件系统路径提取虚拟路径
    例如: /uploads/project_1/documents/reports/file.pdf -> documents/reports
    """
    try:
        # 移除base_dir前缀
        if file_path.startswith(base_dir):
            relative = file_path[len(base_dir):].lstrip('/')
        else:
            relative = file_path

        # 获取目录部分
        dir_path = os.path.dirname(relative)
        return dir_path if dir_path else ""
    except:
        return ""


def build_tree_structure(documents: List[ProjectDocument], base_dir: str) -> FileNodeResponse:
    """
    从扁平文档列表构建树状结构
    使用路径前缀模拟文件夹
    """
    # 构建路径 -> 文档映射
    path_map = {}
    folders = set()

    for doc in documents:
        virtual_path = parse_path(doc.file_path, base_dir)

        # 记录所有父文件夹
        parts = virtual_path.split('/') if virtual_path else []
        for i in range(len(parts)):
            folder_path = '/'.join(parts[:i+1])
            folders.add(folder_path)

        # 记录文件
        if virtual_path not in path_map:
            path_map[virtual_path] = []
        path_map[virtual_path].append(doc)

    # 构建树 - 使用迭代而非递归避免无限递归
    def build_node(path: str, name: str, is_folder: bool, doc: Optional[ProjectDocument] = None) -> FileNodeResponse:
        if is_folder:
            # 文件夹节点
            children = []

            # 添加直接子文件夹（避免递归调用自己）
            for folder in sorted(folders):
                parent_path = '/'.join(folder.split('/')[:-1]) if '/' in folder else ""
                if parent_path == path:
                    folder_name = folder.split('/')[-1]
                    # 创建子文件夹节点，但不递归构建其children
                    child_node = FileNodeResponse(
                        id=f"folder_{folder}",
                        name=folder_name,
                        is_folder=True,
                        type="folder",
                        size=0,
                        modified_at=datetime.utcnow(),
                        path=folder,
                        children=[]  # 先设为空，后续填充
                    )
                    children.append(child_node)

            # 添加文件
            if path in path_map:
                for doc in path_map[path]:
                    file_name = doc.filename
                    file_node = FileNodeResponse(
                        id=str(doc.id),
                        name=file_name,
                        is_folder=False,
                        type=doc.file_type or "unknown",
                        size=doc.file_size or 0,
                        modified_at=doc.updated_at or doc.created_at,
                        path=path,
                        children=[]
                    )
                    children.append(file_node)

            return FileNodeResponse(
                id=f"folder_{path}" if path else "root",
                name=name,
                is_folder=True,
                type="folder",
                size=0,
                modified_at=datetime.utcnow(),
                path=path,
                children=children
            )
        else:
            # 文件节点
            return FileNodeResponse(
                id=str(doc.id),
                name=doc.filename,
                is_folder=False,
                type=doc.file_type or "unknown",
                size=doc.file_size or 0,
                modified_at=doc.updated_at or doc.created_at,
                path=path,
                children=[]
            )

    # 从根开始构建（只构建一层）
    root = build_node("", "我的文件", True)

    # 递归填充子文件夹的children（使用栈避免深度递归）
    stack = [root]
    visited = set()

    while stack:
        node = stack.pop()
        if node.path in visited or not node.is_folder:
            continue
        visited.add(node.path)

        # 为每个子文件夹填充其children
        for child in node.children:
            if child.is_folder and child.path not in visited:
                # 填充这个子文件夹的内容
                child_children = []

                # 添加子文件夹
                for folder in sorted(folders):
                    parent_path = '/'.join(folder.split('/')[:-1]) if '/' in folder else ""
                    if parent_path == child.path:
                        folder_name = folder.split('/')[-1]
                        child_children.append(FileNodeResponse(
                            id=f"folder_{folder}",
                            name=folder_name,
                            is_folder=True,
                            type="folder",
                            size=0,
                            modified_at=datetime.utcnow(),
                            path=folder,
                            children=[]
                        ))

                # 添加文件
                if child.path in path_map:
                    for doc in path_map[child.path]:
                        child_children.append(FileNodeResponse(
                            id=str(doc.id),
                            name=doc.filename,
                            is_folder=False,
                            type=doc.file_type or "unknown",
                            size=doc.file_size or 0,
                            modified_at=doc.updated_at or doc.created_at,
                            path=child.path,
                            children=[]
                        ))

                child.children = child_children
                stack.append(child)

    return root


# ==================== API接口 ====================

@router.get("/file-tree/{project_id}", response_model=FileTreeResponse)
async def get_file_tree(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目文件树（虚拟文件夹结构）
    基于文件路径自动构建文件夹层级
    """
    try:
        # 获取所有文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        # 构建base_dir
        from app.config import settings
        base_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")

        # 构建树结构
        root = build_tree_structure(documents, base_dir)

        # 统计
        total_files = len(documents)
        total_folders = len(set(parse_path(doc.file_path, base_dir) for doc in documents))
        total_size = sum(doc.file_size or 0 for doc in documents)

        return FileTreeResponse(
            root=root,
            total_files=total_files,
            total_folders=total_folders,
            total_size=total_size
        )

    except Exception as e:
        logger.error(f"❌ 获取文件树失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/folders")
async def create_folder(
    request: CreateFolderRequest,
    db: Session = Depends(get_db)
):
    """
    创建虚拟文件夹
    实际上是在文件系统创建目录
    """
    try:
        from app.config import settings

        # 构建文件夹路径
        folder_path = os.path.join(
            settings.UPLOAD_DIR,
            f"project_{request.project_id}",
            request.folder_path
        )

        # 创建目录
        os.makedirs(folder_path, exist_ok=True)

        logger.info(f"✅ 创建文件夹: {request.folder_path}")
        return {
            "status": "success",
            "folder_path": request.folder_path,
            "message": "文件夹已创建"
        }

    except Exception as e:
        logger.error(f"❌ 创建文件夹失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/files/{file_id}/move")
async def move_file(
    file_id: int,
    request: MoveFileRequest,
    db: Session = Depends(get_db)
):
    """
    移动文件到其他文件夹
    通过修改file_path实现
    """
    try:
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="文件不存在")

        from app.config import settings

        # 构建新路径
        old_path = doc.file_path
        filename = os.path.basename(old_path)

        new_path = os.path.join(
            settings.UPLOAD_DIR,
            f"project_{doc.project_id}",
            request.target_path,
            filename
        )

        # 确保目标目录存在
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        # 移动文件
        if os.path.exists(old_path):
            os.rename(old_path, new_path)

        # 更新数据库
        doc.file_path = new_path
        doc.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"✅ 移动文件: {filename} -> {request.target_path}")
        return {
            "status": "success",
            "old_path": old_path,
            "new_path": new_path,
            "message": "文件已移动"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 移动文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/folders")
async def delete_folder(
    project_id: int = Query(...),
    folder_path: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    删除虚拟文件夹
    会删除该文件夹下的所有文件
    """
    try:
        from app.config import settings

        # 构建文件夹路径
        full_path = os.path.join(
            settings.UPLOAD_DIR,
            f"project_{project_id}",
            folder_path
        )

        # 查找该路径下的所有文档
        base_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        deleted_count = 0
        for doc in documents:
            doc_path = parse_path(doc.file_path, base_dir)
            if doc_path.startswith(folder_path):
                # 删除文件
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
                # 删除数据库记录
                db.delete(doc)
                deleted_count += 1

        # 删除文件夹
        if os.path.exists(full_path):
            import shutil
            shutil.rmtree(full_path)

        db.commit()

        logger.info(f"✅ 删除文件夹: {folder_path}, 删除文件数: {deleted_count}")
        return {
            "status": "success",
            "folder_path": folder_path,
            "deleted_files": deleted_count,
            "message": f"已删除文件夹及其中的 {deleted_count} 个文件"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 删除文件夹失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folder-contents")
async def get_folder_contents(
    project_id: int = Query(...),
    folder_path: str = Query("", description="文件夹路径，空字符串表示根目录"),
    db: Session = Depends(get_db)
):
    """
    获取指定文件夹的内容（不递归）
    用于按需加载大型文件树
    """
    try:
        from app.config import settings

        # 获取所有文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        base_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")

        # 查找该路径下的直接子项
        folders = set()
        files = []

        for doc in documents:
            doc_path = parse_path(doc.file_path, base_dir)

            if folder_path:
                # 非根目录
                if doc_path.startswith(folder_path + '/'):
                    remaining = doc_path[len(folder_path)+1:]
                    if '/' in remaining:
                        # 是子文件夹中的文件
                        subfolder = remaining.split('/')[0]
                        folders.add(folder_path + '/' + subfolder)
                    else:
                        # 是直接子文件
                        pass
                elif doc_path == folder_path:
                    # 直接在该文件夹下
                    files.append(doc)
            else:
                # 根目录
                if '/' in doc_path:
                    # 在子文件夹中
                    subfolder = doc_path.split('/')[0]
                    folders.add(subfolder)
                else:
                    # 在根目录
                    if not doc_path:
                        files.append(doc)

        # 构建响应
        items = []

        # 添加文件夹
        for folder in sorted(folders):
            folder_name = folder.split('/')[-1]
            items.append({
                "id": f"folder_{folder}",
                "name": folder_name,
                "is_folder": True,
                "type": "folder",
                "size": 0,
                "modified_at": datetime.utcnow(),
                "path": folder
            })

        # 添加文件
        for doc in files:
            items.append({
                "id": str(doc.id),
                "name": doc.filename,
                "is_folder": False,
                "type": doc.file_type or "unknown",
                "size": doc.file_size or 0,
                "modified_at": doc.updated_at or doc.created_at,
                "path": folder_path
            })

        return {
            "folder_path": folder_path,
            "items": items,
            "total": len(items)
        }

    except Exception as e:
        logger.error(f"❌ 获取文件夹内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
