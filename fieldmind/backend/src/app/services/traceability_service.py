"""
溯源回溯服务 (Traceability Service)
实现报告结论到原始材料的完整追溯链路
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)


class TraceabilityService:
    """
    溯源回溯服务

    功能：
    1. 结论 → chunk → 原始文件的追溯链
    2. 音频时间码定位
    3. 文档段落高亮
    4. 溯源树构建
    """

    def __init__(self):
        pass

    def trace_conclusion(
        self,
        db: Session,
        conclusion_text: str,
        project_id: int
    ) -> Dict[str, Any]:
        """
        追溯一个结论的来源

        Args:
            db: 数据库会话
            conclusion_text: 结论文本
            project_id: 项目 ID

        Returns:
            {
                "conclusion": str,
                "sources": [
                    {
                        "chunk_id": int,
                        "chunk_content": str,
                        "document_id": int,
                        "document_name": str,
                        "file_type": str,
                        "timestamp": float,  # 音频时间码（如果有）
                        "match_score": float  # 匹配度
                    }
                ]
            }
        """
        from app.models.chunk import Chunk
        from app.models.project import ProjectDocument

        # 1. 在 chunks 中搜索相关内容（简单文本匹配）
        chunks = db.query(Chunk).filter(
            Chunk.project_id == project_id
        ).all()

        sources = []

        # 提取结论中的关键词（简单方法：取前5个实词）
        keywords = self._extract_keywords_from_text(conclusion_text)

        for chunk in chunks:
            if not chunk.content:
                continue

            # 计算匹配度
            match_score = self._calculate_match_score(
                conclusion_text,
                chunk.content,
                keywords
            )

            if match_score > 0.3:  # 阈值：30%
                # 获取文档信息
                doc = db.query(ProjectDocument).filter(
                    ProjectDocument.id == chunk.document_id
                ).first()

                if doc:
                    source = {
                        "chunk_id": chunk.id,
                        "chunk_content": chunk.content[:200],  # 前200字
                        "full_content": chunk.content,
                        "document_id": doc.id,
                        "document_name": doc.original_filename,
                        "file_type": doc.file_type,
                        "match_score": round(match_score, 2)
                    }

                    # 如果是音频，尝试获取时间码
                    if doc.file_type in ["audio", "video"]:
                        timestamp = self._extract_timestamp(chunk, doc)
                        if timestamp:
                            source["timestamp"] = timestamp
                            source["timestamp_formatted"] = self._format_timestamp(timestamp)

                    sources.append(source)

        # 按匹配度排序
        sources.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "conclusion": conclusion_text,
            "sources": sources[:10],  # 最多返回10个来源
            "total_sources": len(sources)
        }

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单实现：去除标点，取长度>1的词
        import re

        words = re.findall(r'[一-龥a-zA-Z]+', text)
        keywords = [w for w in words if len(w) > 1]

        return keywords[:10]  # 取前10个

    def _calculate_match_score(
        self,
        conclusion: str,
        chunk_content: str,
        keywords: List[str]
    ) -> float:
        """
        计算匹配分数

        方法：
        1. 关键词匹配（70%权重）
        2. 文本相似度（30%权重）
        """
        # 1. 关键词匹配
        if not keywords:
            keyword_score = 0.0
        else:
            matched_keywords = sum(1 for kw in keywords if kw in chunk_content)
            keyword_score = matched_keywords / len(keywords)

        # 2. 文本相似度（简单实现：检查结论是否在chunk中）
        similarity_score = 0.0
        if conclusion in chunk_content:
            similarity_score = 1.0
        elif len(conclusion) > 10:
            # 检查部分匹配
            conclusion_parts = conclusion.split('。')
            matched_parts = sum(1 for part in conclusion_parts if len(part) > 5 and part in chunk_content)
            if conclusion_parts:
                similarity_score = matched_parts / len(conclusion_parts)

        # 综合评分
        match_score = keyword_score * 0.7 + similarity_score * 0.3

        return match_score

    def _extract_timestamp(self, chunk, document) -> Optional[float]:
        """
        提取音频时间码

        从 chunk 或 document 的 extra_data 中提取
        """
        # 尝试从 chunk 的位置推算时间码
        if chunk.position is not None and document.extra_data:
            transcript = document.extra_data.get("transcript")
            if transcript and isinstance(transcript, dict):
                # 如果转录包含时间信息
                segments = transcript.get("segments", [])
                if segments and chunk.position < len(segments):
                    segment = segments[chunk.position]
                    return segment.get("start", 0.0)

        return None

    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间码为 MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def build_trace_tree(
        self,
        db: Session,
        conclusion_id: int
    ) -> Dict[str, Any]:
        """
        构建溯源树

        结构：
        结论
         ├─ Chunk 1
         │   └─ 原始文件 A (音频 03:25)
         ├─ Chunk 2
         │   └─ 原始文件 B (PDF 第3页)
         └─ Chunk 3
             └─ 原始文件 A (音频 15:42)
        """
        # TODO: 需要先有 conclusions 表
        # 暂时返回空树
        return {
            "conclusion_id": conclusion_id,
            "tree": []
        }

    def get_chunk_context(
        self,
        db: Session,
        chunk_id: int,
        context_size: int = 1
    ) -> Dict[str, Any]:
        """
        获取 chunk 的上下文

        Args:
            chunk_id: chunk ID
            context_size: 上下文大小（前后各取几个chunk）

        Returns:
            {
                "current": {...},
                "before": [...],
                "after": [...]
            }
        """
        from app.models.chunk import Chunk

        current_chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()

        if not current_chunk:
            return {"error": "Chunk 不存在"}

        # 获取同一文档的前后 chunks
        before_chunks = db.query(Chunk).filter(
            Chunk.document_id == current_chunk.document_id,
            Chunk.position < current_chunk.position
        ).order_by(Chunk.position.desc()).limit(context_size).all()

        after_chunks = db.query(Chunk).filter(
            Chunk.document_id == current_chunk.document_id,
            Chunk.position > current_chunk.position
        ).order_by(Chunk.position.asc()).limit(context_size).all()

        return {
            "current": {
                "id": current_chunk.id,
                "content": current_chunk.content,
                "position": current_chunk.position
            },
            "before": [
                {
                    "id": c.id,
                    "content": c.content,
                    "position": c.position
                }
                for c in reversed(before_chunks)
            ],
            "after": [
                {
                    "id": c.id,
                    "content": c.content,
                    "position": c.position
                }
                for c in after_chunks
            ]
        }

    def highlight_in_document(
        self,
        db: Session,
        document_id: int,
        chunk_id: int
    ) -> Dict[str, Any]:
        """
        在文档中高亮显示 chunk

        Returns:
            {
                "document_id": int,
                "document_name": str,
                "file_type": str,
                "chunk_position": int,
                "highlight_start": int,  # 字符位置
                "highlight_end": int,
                "full_text": str
            }
        """
        from app.models.chunk import Chunk
        from app.models.project import ProjectDocument

        chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
        if not chunk:
            return {"error": "Chunk 不存在"}

        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            return {"error": "文档不存在"}

        # 在文档全文中找到 chunk 的位置
        full_text = doc.text_content or ""
        chunk_text = chunk.content

        highlight_start = full_text.find(chunk_text)
        highlight_end = highlight_start + len(chunk_text) if highlight_start != -1 else -1

        return {
            "document_id": doc.id,
            "document_name": doc.original_filename,
            "file_type": doc.file_type,
            "chunk_id": chunk.id,
            "chunk_position": chunk.position,
            "highlight_start": highlight_start,
            "highlight_end": highlight_end,
            "full_text": full_text if len(full_text) < 10000 else full_text[:10000] + "...",
            "can_highlight": highlight_start != -1
        }


# 全局实例
traceability_service = TraceabilityService()
