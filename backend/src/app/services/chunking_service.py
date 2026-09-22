"""
文本切分服务 (Chunking Service)
负责将长文本切分为可管理的块，并写入 chunks 表
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import re
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    文本切分服务

    核心功能：
    1. 智能切分（按段落、句子、字符数）
    2. 保留上下文（前后块关联）
    3. 写入 chunks 表
    """

    def __init__(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        overlap: int = 50,
        use_workflow_engine: bool = True
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=3)

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        切分文本为 chunks

        Args:
            text: 输入文本

        Returns:
            [
                {
                    "content": str,
                    "position": int,
                    "char_count": int,
                    "word_count": int,
                    "context_before": str,
                    "context_after": str
                }
            ]
        """
        if self.use_workflow_engine:
            result = self.workflow_engine.execute({
                "split_paragraphs": {
                    "task": self._task_split_paragraphs,
                    "params": {"text": text}
                },
                "merge_and_split": {
                    "task": self._task_merge_and_split,
                    "params": {"paragraphs": "$split_paragraphs.paragraphs"},
                    "depends_on": ["split_paragraphs"]
                },
                "add_context": {
                    "task": self._task_add_context,
                    "params": {"chunks_raw": "$merge_and_split.chunks"},
                    "depends_on": ["merge_and_split"]
                }
            })
            return result.get("add_context", {}).get("chunks", [])
        else:
            return self._chunk_text_legacy(text)

    def _chunk_text_legacy(self, text: str) -> List[Dict[str, Any]]:
        """Legacy implementation without WorkflowEngine"""
        if not text or len(text.strip()) == 0:
            return []

        # 1. 按段落切分
        paragraphs = self._split_paragraphs(text)

        # 2. 合并小段落，拆分大段落
        chunks_raw = self._merge_and_split(paragraphs)

        # 3. 添加上下文信息
        chunks = self._add_context(chunks_raw)

        logger.info(f"切分完成：{len(text)} 字符 → {len(chunks)} 个 chunks")

        return chunks

    # ==================== WorkflowEngine Task Functions ====================

    def _task_split_paragraphs(self, text: str, _context: dict) -> dict:
        """Task: 按段落切分文本"""
        if not text or len(text.strip()) == 0:
            return {"paragraphs": []}

        paragraphs = self._split_paragraphs(text)
        logger.info(f"段落切分：{len(text)} 字符 → {len(paragraphs)} 个段落")
        return {"paragraphs": paragraphs}

    def _task_merge_and_split(self, paragraphs: List[str], _context: dict) -> dict:
        """Task: 合并小段落，拆分大段落"""
        chunks = self._merge_and_split(paragraphs)
        logger.info(f"合并拆分：{len(paragraphs)} 个段落 → {len(chunks)} 个 chunks")
        return {"chunks": chunks}

    def _task_add_context(self, chunks_raw: List[str], _context: dict) -> dict:
        """Task: 添加上下文信息"""
        chunks = self._add_context(chunks_raw)
        logger.info(f"添加上下文：{len(chunks_raw)} 个原始 chunks → {len(chunks)} 个完整 chunks")
        return {"chunks": chunks}

    def _split_paragraphs(self, text: str) -> List[str]:
        """按段落切分"""
        # 按双换行符切分
        paragraphs = re.split(r'\n\s*\n', text)

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _merge_and_split(self, paragraphs: List[str]) -> List[str]:
        """合并小段落，拆分大段落"""
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para_len = len(para)

            # 如果段落本身就很大，需要拆分
            if para_len > self.max_chunk_size:
                # 先保存当前累积的 chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # 拆分大段落
                sub_chunks = self._split_large_paragraph(para)
                chunks.extend(sub_chunks)

            # 如果加上这个段落不会太大，就累积
            elif len(current_chunk) + para_len < self.max_chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para

            # 如果加上会太大，先保存当前 chunk，再开始新的
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para

        # 保存最后一个 chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, text: str) -> List[str]:
        """拆分超大段落"""
        # 按句子切分
        sentences = re.split(r'([。！？\.!?])', text)

        chunks = []
        current = ""

        i = 0
        while i < len(sentences):
            sent = sentences[i]

            # 如果是标点符号，和前一个句子合并
            if i + 1 < len(sentences) and sentences[i + 1] in '。！？.!?':
                sent += sentences[i + 1]
                i += 2
            else:
                i += 1

            # 累积到合适大小
            if len(current) + len(sent) < self.max_chunk_size:
                current += sent
            else:
                if current:
                    chunks.append(current.strip())
                current = sent

        if current:
            chunks.append(current.strip())

        return chunks

    def _add_context(self, chunks_raw: List[str]) -> List[Dict[str, Any]]:
        """添加上下文信息"""
        chunks = []

        for i, content in enumerate(chunks_raw):
            chunk = {
                "content": content,
                "position": i,
                "char_count": len(content),
                "word_count": len(content.replace(" ", "").replace("\n", "")),
                "context_before": chunks_raw[i - 1][-self.overlap:] if i > 0 else "",
                "context_after": chunks_raw[i + 1][:self.overlap] if i < len(chunks_raw) - 1 else ""
            }
            chunks.append(chunk)

        return chunks

    def create_chunks_from_document(
        self,
        db: Session,
        document_id: int,
        text: str,
        project_id: int
    ) -> int:
        """
        从文档创建 chunks 并写入数据库

        Args:
            db: 数据库会话
            document_id: 文档 ID
            text: 文档文本
            project_id: 项目 ID

        Returns:
            创建的 chunk 数量
        """
        if self.use_workflow_engine:
            result = self.workflow_engine.execute({
                "chunk_text": {
                    "task": self._task_chunk_text,
                    "params": {"text": text}
                },
                "save_to_db": {
                    "task": self._task_save_chunks_to_db,
                    "params": {
                        "chunks_data": "$chunk_text.chunks",
                        "db": db,
                        "document_id": document_id,
                        "project_id": project_id
                    },
                    "depends_on": ["chunk_text"]
                }
            })
            return result.get("save_to_db", {}).get("created_count", 0)
        else:
            return self._create_chunks_from_document_legacy(db, document_id, text, project_id)

    def _create_chunks_from_document_legacy(
        self,
        db: Session,
        document_id: int,
        text: str,
        project_id: int
    ) -> int:
        """Legacy implementation without WorkflowEngine"""
        from app.models.chunk import Chunk

        # 1. 切分文本
        chunks_data = self.chunk_text(text)

        if not chunks_data:
            logger.warning(f"文档 {document_id} 切分后为空")
            return 0

        # 2. 写入数据库
        created_count = 0

        for chunk_data in chunks_data:
            chunk = Chunk(
                document_id=document_id,
                project_id=project_id,
                content=chunk_data["content"],
                position=chunk_data["position"],
                char_count=chunk_data["char_count"],
                word_count=chunk_data["word_count"],
                context_before=chunk_data["context_before"],
                context_after=chunk_data["context_after"],
                # 量化字段稍后由 text_quantification 服务填充
            )

            db.add(chunk)
            created_count += 1

        db.commit()

        logger.info(f"文档 {document_id} 创建了 {created_count} 个 chunks")

        return created_count

    def _task_chunk_text(self, text: str, _context: dict) -> dict:
        """Task: 切分文本"""
        chunks = self.chunk_text(text)
        return {"chunks": chunks}

    def _task_save_chunks_to_db(
        self,
        chunks_data: List[Dict[str, Any]],
        db: Session,
        document_id: int,
        project_id: int,
        _context: dict
    ) -> dict:
        """Task: 保存chunks到数据库"""
        from app.models.chunk import Chunk

        if not chunks_data:
            logger.warning(f"文档 {document_id} 切分后为空")
            return {"created_count": 0}

        created_count = 0

        for chunk_data in chunks_data:
            chunk = Chunk(
                document_id=document_id,
                project_id=project_id,
                content=chunk_data["content"],
                position=chunk_data["position"],
                char_count=chunk_data["char_count"],
                word_count=chunk_data["word_count"],
                context_before=chunk_data["context_before"],
                context_after=chunk_data["context_after"],
            )

            db.add(chunk)
            created_count += 1

        db.commit()

        logger.info(f"文档 {document_id} 创建了 {created_count} 个 chunks")

        return {"created_count": created_count}


# 全局实例
chunking_service = ChunkingService()
