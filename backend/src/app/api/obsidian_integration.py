"""
Obsidian 集成 API
支持导入 Obsidian 笔记库、同步双链关系、构建知识图谱
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import os
import json
from pathlib import Path

from app.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, EntityRelation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/obsidian", tags=["Obsidian集成"])


class ObsidianNote(BaseModel):
    """Obsidian 笔记"""
    title: str
    content: str
    path: str
    tags: List[str] = []
    links: List[str] = []  # [[双链]] 引用
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


class ObsidianImportRequest(BaseModel):
    """Obsidian 导入请求"""
    project_id: int = Field(..., description="目标项目ID")
    vault_path: str = Field(..., description="Obsidian vault 路径")
    include_attachments: bool = Field(True, description="是否包含附件")
    parse_wikilinks: bool = Field(True, description="是否解析 [[双链]]")


class ObsidianSyncRequest(BaseModel):
    """Obsidian 同步请求"""
    project_id: int
    vault_path: str
    sync_mode: str = Field("incremental", description="同步模式: full 或 incremental")


@router.post("/import", response_model=dict)
async def import_obsidian_vault(
    request: ObsidianImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    导入 Obsidian 笔记库到项目

    Args:
        request: 导入请求
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        dict: 导入任务信息
    """
    vault_path = Path(request.vault_path)

    if not vault_path.exists():
        raise HTTPException(status_code=404, detail=f"Vault path not found: {request.vault_path}")

    if not vault_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Vault path is not a directory: {request.vault_path}")

    # 扫描 markdown 文件
    markdown_files = list(vault_path.rglob("*.md"))

    if not markdown_files:
        raise HTTPException(status_code=404, detail="No markdown files found in vault")

    # 解析笔记
    notes = []
    wikilinks = {}  # 双链关系映射

    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取标题（第一行 # 或文件名）
            lines = content.split('\n')
            title = md_file.stem
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            # 提取标签
            tags = []
            import re
            tag_pattern = r'#(\w+)'
            tags = re.findall(tag_pattern, content)

            # 提取双链 [[...]]
            links = []
            if request.parse_wikilinks:
                wikilink_pattern = r'\[\[([^\]]+)\]\]'
                links = re.findall(wikilink_pattern, content)

            note = {
                "title": title,
                "content": content,
                "path": str(md_file.relative_to(vault_path)),
                "tags": tags,
                "links": links,
                "created_at": None,
                "modified_at": None,
            }

            notes.append(note)
            wikilinks[title] = links

        except Exception as e:
            logger.error(f"Failed to parse {md_file}: {e}")
            continue

    # 导入笔记到文档表
    imported_docs = []
    for note in notes:
        try:
            # 创建文档记录
            doc = Document(
                id=f"obs_{note['title'].lower().replace(' ', '_')}",
                project_id=request.project_id,
                name=note['title'],
                file_path=str(vault_path / note['path']),
                file_type="markdown",
                content=note['content'],
                metadata=json.dumps({
                    "source": "obsidian",
                    "tags": note['tags'],
                    "links": note['links'],
                    "vault_path": request.vault_path,
                })
            )

            db.add(doc)
            imported_docs.append({
                "doc_id": doc.id,
                "title": note['title'],
                "links": note['links'],
            })

        except Exception as e:
            logger.error(f"Failed to import note {note['title']}: {e}")
            continue

    db.commit()

    # 构建双链关系图谱
    relation_count = 0
    for doc_info in imported_docs:
        for link in doc_info['links']:
            # 查找链接目标文档
            target_doc_id = f"obs_{link.lower().replace(' ', '_')}"
            target_exists = db.query(Document).filter_by(id=target_doc_id).first()

            if target_exists:
                # 创建实体关系
                try:
                    relation = EntityRelation(
                        source_entity_id=doc_info['doc_id'],
                        target_entity_id=target_doc_id,
                        relation_type="wikilink",
                        confidence=1.0,
                        metadata=json.dumps({"link_text": link})
                    )
                    db.add(relation)
                    relation_count += 1
                except Exception as e:
                    logger.error(f"Failed to create relation {doc_info['doc_id']} -> {target_doc_id}: {e}")

    db.commit()

    return {
        "status": "success",
        "project_id": request.project_id,
        "vault_path": request.vault_path,
        "total_notes": len(markdown_files),
        "imported_notes": len(imported_docs),
        "wikilinks_created": relation_count,
        "notes": imported_docs[:10],  # 返回前10个作为预览
    }


@router.post("/sync", response_model=dict)
async def sync_obsidian_vault(
    request: ObsidianSyncRequest,
    db: Session = Depends(get_db),
):
    """
    同步 Obsidian 笔记库更新

    Args:
        request: 同步请求
        db: 数据库会话

    Returns:
        dict: 同步结果
    """
    vault_path = Path(request.vault_path)

    if not vault_path.exists():
        raise HTTPException(status_code=404, detail=f"Vault path not found: {request.vault_path}")

    # 查找已导入的 Obsidian 文档
    existing_docs = (
        db.query(Document)
        .filter(
            Document.project_id == request.project_id,
            Document.metadata.contains('"source": "obsidian"')
        )
        .all()
    )

    updated = 0
    new = 0
    deleted = 0

    # 扫描当前文件
    markdown_files = {f.stem: f for f in vault_path.rglob("*.md")}

    # 更新已有文档
    for doc in existing_docs:
        title = doc.name
        if title in markdown_files:
            file_path = markdown_files[title]

            # 检查文件修改时间
            file_mtime = os.path.getmtime(file_path)
            doc_mtime = doc.updated_at.timestamp() if doc.updated_at else 0

            if file_mtime > doc_mtime:
                # 文件已更新，重新读取内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    doc.content = content
                    updated += 1
                except Exception as e:
                    logger.error(f"Failed to update {title}: {e}")
        else:
            # 文件已删除
            if request.sync_mode == "full":
                db.delete(doc)
                deleted += 1

    db.commit()

    return {
        "status": "success",
        "project_id": request.project_id,
        "sync_mode": request.sync_mode,
        "updated": updated,
        "new": new,
        "deleted": deleted,
    }


@router.get("/graph", response_model=dict)
async def get_obsidian_graph(
    project_id: int = Query(..., description="项目ID"),
    max_depth: int = Query(3, description="图谱最大深度"),
    db: Session = Depends(get_db),
):
    """
    获取 Obsidian 双链知识图谱

    Args:
        project_id: 项目ID
        max_depth: 图谱最大深度
        db: 数据库会话

    Returns:
        dict: 知识图谱数据（nodes + edges）
    """
    # 查询项目的 Obsidian 文档
    docs = (
        db.query(Document)
        .filter(
            Document.project_id == project_id,
            Document.metadata.contains('"source": "obsidian"')
        )
        .all()
    )

    if not docs:
        return {
            "nodes": [],
            "edges": [],
            "message": "No Obsidian notes found in this project",
        }

    # 构建节点
    nodes = []
    for doc in docs:
        metadata = json.loads(doc.metadata) if doc.metadata else {}
        nodes.append({
            "id": doc.id,
            "label": doc.name,
            "type": "note",
            "tags": metadata.get("tags", []),
        })

    # 查询双链关系
    doc_ids = [doc.id for doc in docs]
    relations = (
        db.query(EntityRelation)
        .filter(
            EntityRelation.source_entity_id.in_(doc_ids),
            EntityRelation.relation_type == "wikilink"
        )
        .all()
    )

    # 构建边
    edges = []
    for rel in relations:
        edges.append({
            "source": rel.source_entity_id,
            "target": rel.target_entity_id,
            "type": "wikilink",
            "confidence": rel.confidence,
        })

    return {
        "project_id": project_id,
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_notes": len(nodes),
            "total_links": len(edges),
        }
    }


@router.get("/search", response_model=dict)
async def search_obsidian_notes(
    project_id: int = Query(..., description="项目ID"),
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    搜索 Obsidian 笔记

    Args:
        project_id: 项目ID
        query: 搜索关键词
        limit: 返回数量限制
        db: 数据库会话

    Returns:
        dict: 搜索结果
    """
    # 查询匹配的文档
    docs = (
        db.query(Document)
        .filter(
            Document.project_id == project_id,
            Document.metadata.contains('"source": "obsidian"'),
            Document.content.contains(query)
        )
        .limit(limit)
        .all()
    )

    results = []
    for doc in docs:
        # 提取匹配上下文
        content = doc.content or ""
        index = content.find(query)
        if index != -1:
            start = max(0, index - 100)
            end = min(len(content), index + len(query) + 100)
            context = content[start:end]
        else:
            context = content[:200]

        results.append({
            "doc_id": doc.id,
            "title": doc.name,
            "context": context,
            "match_position": index,
        })

    return {
        "query": query,
        "total_results": len(results),
        "results": results,
    }
