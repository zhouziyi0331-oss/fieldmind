"""
Step 2: 结构分析服务
Document Structure Analysis Service

功能：
1. 分析文档的篇章结构（章节、段落层次）
2. 识别标题、列表、表格等结构元素
3. 构建文档树形结构
4. 保存到 document_structure 表
5. 更新 document_chunks 的结构字段
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging
from typing import List, Dict, Any, Optional
import uuid

from app.models.project import DocumentChunk
from app.models.unified_models import DocumentStructure
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class StructureAnalysisService:
    """结构分析服务（Step 2）"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_document_structure(self, document_id: int) -> Dict[str, Any]:
        """
        分析文档结构

        Args:
            document_id: 文档 ID

        Returns:
            分析结果
        """
        logger.info(f"📊 Step 2: 开始结构分析 - 文档 {document_id}")

        try:
            # 获取所有 chunks（使用清洗后的文本）
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()

            if not chunks:
                logger.warning(f"文档 {document_id} 没有 chunks")
                return {
                    'success': False,
                    'message': '文档没有 chunks'
                }

            # 分析结构
            structure_nodes = self._analyze_chunks(document_id, chunks)

            # 保存到数据库
            saved_count = self._save_structure(document_id, structure_nodes)

            # 更新 chunks 的结构字段
            self._update_chunk_structure_fields(chunks, structure_nodes)

            result = {
                'success': True,
                'document_id': document_id,
                'total_chunks': len(chunks),
                'structure_nodes': saved_count,
                'max_level': max([n['node_level'] for n in structure_nodes]) if structure_nodes else 0
            }

            logger.info(
                f"✅ Step 2 完成: 识别了 {saved_count} 个结构节点, "
                f"最大层级 {result['max_level']}"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.PIPELINE_STEP_COMPLETED,
                payload={
                    'step': 2,
                    'step_name': 'structure_analysis',
                    'document_id': document_id,
                    'result': result
                },
                publisher='StructureAnalysisService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 2 失败: {e}", exc_info=True)
            raise

    def _analyze_chunks(self, document_id: int, chunks: List[DocumentChunk]) -> List[Dict]:
        """
        分析 chunks 的结构

        策略：
        1. 识别标题（基于格式、长度、位置）
        2. 识别段落
        3. 构建层次关系
        """
        structure_nodes = []
        parent_stack = []  # 父节点栈

        for i, chunk in enumerate(chunks):
            text = chunk.cleaned_text or chunk.text
            if not text:
                continue

            # 分析节点类型和层级
            node_info = self._identify_node_type(text, i, len(chunks))

            # 创建结构节点
            node = {
                'chunk_id': chunk.id,
                'node_type': node_info['type'],
                'node_level': node_info['level'],
                'title': node_info['title'],
                'sequence_order': i,
                'parent_id': None,
                'content_summary': text[:200] if len(text) > 200 else text
            }

            # 确定父节点
            if node['node_level'] > 0:
                # 找到最近的更高层级节点作为父节点
                while parent_stack and parent_stack[-1]['node_level'] >= node['node_level']:
                    parent_stack.pop()

                if parent_stack:
                    node['parent_id'] = parent_stack[-1]['id']

            # 分配临时 ID
            node['id'] = len(structure_nodes)

            # 如果是标题类节点，加入父节点栈
            if node['node_type'] in ['chapter', 'section', 'subsection']:
                parent_stack.append(node)

            structure_nodes.append(node)

        return structure_nodes

    def _identify_node_type(self, text: str, position: int, total: int) -> Dict[str, Any]:
        """
        识别节点类型和层级

        规则：
        1. 短文本 + 特殊格式 -> 标题
        2. 包含数字编号 -> 列表
        3. 普通文本 -> 段落
        """
        text_stripped = text.strip()
        text_length = len(text_stripped)

        # 规则1: 识别章节标题（一级标题）
        chapter_patterns = [
            r'^第[一二三四五六七八九十百千\d]+[章节部分]',  # 第一章
            r'^[一二三四五六七八九十]+[、\.]',  # 一、
            r'^\d+\.',  # 1.
            r'^Chapter\s+\d+',  # Chapter 1
        ]

        for pattern in chapter_patterns:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return {
                    'type': 'chapter',
                    'level': 1,
                    'title': text_stripped.split('\n')[0][:100]
                }

        # 规则2: 识别节标题（二级标题）
        section_patterns = [
            r'^\d+\.\d+',  # 1.1
            r'^[(（]\d+[)）]',  # (1)
        ]

        for pattern in section_patterns:
            if re.match(pattern, text_stripped):
                return {
                    'type': 'section',
                    'level': 2,
                    'title': text_stripped.split('\n')[0][:100]
                }

        # 规则3: 短文本可能是标题
        if text_length < 50 and position < total * 0.2:
            return {
                'type': 'subsection',
                'level': 3,
                'title': text_stripped[:100]
            }

        # 规则4: 列表项
        list_patterns = [
            r'^[•·▪▫■□●○◆◇★☆]+',  # 符号列表
            r'^\d+[.、)]',  # 数字列表
            r'^[a-zA-Z][.、)]',  # 字母列表
        ]

        for pattern in list_patterns:
            if re.match(pattern, text_stripped):
                return {
                    'type': 'list',
                    'level': 4,
                    'title': None
                }

        # 默认：段落
        return {
            'type': 'paragraph',
            'level': 5,
            'title': None
        }

    def _save_structure(self, document_id: int, structure_nodes: List[Dict]) -> int:
        """
        保存结构到数据库

        Args:
            document_id: 文档 ID
            structure_nodes: 结构节点列表

        Returns:
            保存的节点数量
        """
        # 先删除旧的结构数据
        self.db.query(DocumentStructure).filter(
            DocumentStructure.document_id == document_id
        ).delete()

        # ID 映射（临时 ID -> 数据库 ID）
        id_map = {}

        # 第一遍：创建所有节点（parent_id 先设为 None）
        for node in structure_nodes:
            db_node = DocumentStructure(
                document_id=document_id,
                chunk_id=node['chunk_id'],
                node_type=node['node_type'],
                node_level=node['node_level'],
                title=node['title'],
                sequence_order=node['sequence_order'],
                content_summary=node['content_summary'],
                parent_id=None
            )

            self.db.add(db_node)
            self.db.flush()  # 获取 ID

            id_map[node['id']] = db_node.id

        # 第二遍：更新 parent_id
        for node in structure_nodes:
            if node['parent_id'] is not None:
                db_id = id_map[node['id']]
                parent_db_id = id_map[node['parent_id']]

                self.db.execute(text("""
                    UPDATE document_structure
                    SET parent_id = :parent_id
                    WHERE id = :id
                """), {'id': db_id, 'parent_id': parent_db_id})

        self.db.commit()

        return len(structure_nodes)

    def _update_chunk_structure_fields(
        self,
        chunks: List[DocumentChunk],
        structure_nodes: List[Dict]
    ):
        """
        更新 chunks 的结构字段

        Args:
            chunks: chunk 列表
            structure_nodes: 结构节点列表
        """
        # 构建 chunk_id -> node 的映射
        chunk_node_map = {node['chunk_id']: node for node in structure_nodes}

        for chunk in chunks:
            node = chunk_node_map.get(chunk.id)
            if node:
                chunk.structure_type = node['node_type']
                chunk.structure_level = node['node_level']

                # 找到父 chunk
                if node['parent_id'] is not None:
                    parent_node = structure_nodes[node['parent_id']]
                    chunk.parent_chunk_id = parent_node['chunk_id']

        self.db.commit()

    def get_document_tree(self, document_id: int) -> Dict[str, Any]:
        """
        获取文档的树形结构

        Returns:
            树形结构 JSON
        """
        nodes = self.db.query(DocumentStructure).filter(
            DocumentStructure.document_id == document_id
        ).order_by(DocumentStructure.sequence_order).all()

        if not nodes:
            return {'nodes': [], 'tree': None}

        # 构建节点字典
        node_dict = {}
        for node in nodes:
            node_dict[node.id] = {
                'id': node.id,
                'type': node.node_type,
                'level': node.node_level,
                'title': node.title,
                'children': []
            }

        # 构建树
        root_nodes = []
        for node in nodes:
            node_data = node_dict[node.id]

            if node.parent_id is None:
                root_nodes.append(node_data)
            else:
                parent = node_dict.get(node.parent_id)
                if parent:
                    parent['children'].append(node_data)

        return {
            'nodes': [node_dict[n.id] for n in nodes],
            'tree': root_nodes
        }


# ============================================================
# 便捷函数
# ============================================================

def analyze_document_structure(db: Session, document_id: int) -> Dict[str, Any]:
    """
    分析文档结构的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        分析结果
    """
    service = StructureAnalysisService(db)
    return service.analyze_document_structure(document_id)
