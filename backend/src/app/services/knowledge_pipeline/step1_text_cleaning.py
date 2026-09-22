"""
Step 1: 文本校刊服务
Text Cleaning Service

功能：
1. 清洗原始文本（去除乱码、特殊字符）
2. 标准化格式
3. 保存清洗后的文本到 document_chunks.cleaned_text
4. 发布事件通知下游
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging
from typing import List, Dict, Any

from app.models.project import DocumentChunk
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class TextCleaningService:
    """文本校刊服务（Step 1）"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def clean_document(self, document_id: int) -> Dict[str, Any]:
        """
        清洗文档的所有 chunks

        Args:
            document_id: 文档 ID

        Returns:
            清洗结果统计
        """
        logger.info(f"🧹 Step 1: 开始文本校刊 - 文档 {document_id}")

        try:
            # 获取所有 chunks
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            if not chunks:
                logger.warning(f"文档 {document_id} 没有 chunks")
                return {
                    'success': False,
                    'message': '文档没有 chunks',
                    'chunks_cleaned': 0
                }

            cleaned_count = 0
            total_before = 0
            total_after = 0

            # 清洗每个 chunk
            for chunk in chunks:
                if not chunk.text:
                    continue

                original_text = chunk.text
                cleaned_text = self._clean_text(original_text)

                # 更新 cleaned_text 字段
                chunk.cleaned_text = cleaned_text

                total_before += len(original_text)
                total_after += len(cleaned_text)
                cleaned_count += 1

            # 提交到数据库
            self.db.commit()

            result = {
                'success': True,
                'document_id': document_id,
                'chunks_cleaned': cleaned_count,
                'total_chunks': len(chunks),
                'chars_before': total_before,
                'chars_after': total_after,
                'reduction_rate': round((1 - total_after / total_before) * 100, 2) if total_before > 0 else 0
            }

            logger.info(
                f"✅ Step 1 完成: 清洗了 {cleaned_count} 个 chunks, "
                f"字符数 {total_before} -> {total_after} "
                f"(减少 {result['reduction_rate']}%)"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.PIPELINE_STEP_COMPLETED,
                payload={
                    'step': 1,
                    'step_name': 'text_cleaning',
                    'document_id': document_id,
                    'result': result
                },
                publisher='TextCleaningService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 1 失败: {e}", exc_info=True)
            raise

    def _clean_text(self, text: str) -> str:
        """
        清洗单个文本

        清洗规则：
        1. 去除多余空白字符
        2. 去除特殊控制字符
        3. 标准化标点符号
        4. 去除乱码
        """
        if not text:
            return ""

        # 1. 去除控制字符（保留换行、制表符）
        cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # 2. 标准化空白字符
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # 多个空格/制表符 -> 单个空格
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # 多个换行 -> 最多两个

        # 3. 去除行首行尾空白
        lines = cleaned.split('\n')
        lines = [line.strip() for line in lines]
        cleaned = '\n'.join(lines)

        # 4. 标准化标点符号
        # 中文标点转英文
        punctuation_map = {
            '，': ',',
            '。': '.',
            '！': '!',
            '？': '?',
            '；': ';',
            '：': ':',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '（': '(',
            '）': ')',
            '【': '[',
            '】': ']',
            '《': '<',
            '》': '>',
        }

        # 可选：保持中文标点（根据项目需求）
        # for cn, en in punctuation_map.items():
        #     cleaned = cleaned.replace(cn, en)

        # 5. 去除明显的乱码（连续的特殊字符）
        cleaned = re.sub(r'[^一-龥0-9A-Za-z\s\.,!?;:()\[\]{}""''<>《》，。！？；：（）【】、—…]+', '', cleaned)

        # 6. 去除首尾空白
        cleaned = cleaned.strip()

        return cleaned

    def validate_cleaning(self, document_id: int) -> Dict[str, Any]:
        """
        验证清洗质量

        Returns:
            验证结果
        """
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.cleaned_text.isnot(None)
        ).all()

        if not chunks:
            return {
                'valid': False,
                'message': '没有清洗后的文本'
            }

        total_chunks = len(chunks)
        valid_chunks = 0
        issues = []

        for chunk in chunks:
            if chunk.cleaned_text and len(chunk.cleaned_text.strip()) > 0:
                valid_chunks += 1
            else:
                issues.append(f"Chunk {chunk.id} 清洗后为空")

        return {
            'valid': valid_chunks == total_chunks,
            'total_chunks': total_chunks,
            'valid_chunks': valid_chunks,
            'issues': issues
        }


# ============================================================
# 便捷函数
# ============================================================

def clean_document_text(db: Session, document_id: int) -> Dict[str, Any]:
    """
    清洗文档文本的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        清洗结果
    """
    service = TextCleaningService(db)
    return service.clean_document(document_id)
