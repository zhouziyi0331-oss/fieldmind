"""
Vector Store Service - 向量存储服务

功能：
1. 初始化ChromaDB客户端
2. 创建和管理集合（collection）
3. 存储文档向量
4. 执行语义相似度搜索
5. 混合检索（向量 + 关键词）
"""

import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorStoreService:
    """向量存储服务"""

    def __init__(self,
        persist_directory: str = "data/chroma",
        collection_name: str = "fieldmind_chunks",


        use_workflow_engine: bool = True):
        """
        初始化向量存储服务

        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)

        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self._get_or_create_collection()

        logger.info(f"✅ ChromaDB初始化成功: {persist_directory}")
        logger.info(f"✅ 集合: {collection_name}, 文档数: {self.collection.count()}")

    def _get_or_create_collection(self):
        """获取或创建集合"""
        try:
            # 尝试获取已存在的集合
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"集合已存在: {self.collection_name}")
            return collection
        except Exception:
            # 集合不存在，创建新集合
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "FieldMind文档chunks向量存储",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"创建新集合: {self.collection_name}")
            return collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """
        添加文档到向量存储

        Args:
            documents: 文档文本列表
            metadatas: 元数据列表
            ids: 文档ID列表

        Returns:
            是否成功
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ 添加了 {len(documents)} 个文档")
            return True
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {e}")
            return False

    def search(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        语义搜索

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            {
                'ids': [[...]],
                'documents': [[...]],
                'metadatas': [[...]],
                'distances': [[...]]
            }
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            logger.info(f"✅ 搜索完成，返回 {len(results['ids'][0])} 个结果")
            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return {
                'ids': [[]],
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

    def batch_search(
        self,
        query_texts: List[str],
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        批量语义搜索

        Args:
            query_texts: 查询文本列表
            n_results: 每个查询返回结果数量

        Returns:
            结果列表
        """
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results
            )

            # 转换为列表格式
            formatted_results = []
            for i in range(len(query_texts)):
                formatted_results.append({
                    'query': query_texts[i],
                    'ids': results['ids'][i],
                    'documents': results['documents'][i],
                    'metadatas': results['metadatas'][i],
                    'distances': results['distances'][i]
                })

            logger.info(f"✅ 批量搜索完成，处理 {len(query_texts)} 个查询")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ 批量搜索失败: {e}")
            return []

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        根据ID获取文档

        Args:
            ids: 文档ID列表

        Returns:
            文档数据
        """
        try:
            results = self.collection.get(ids=ids)
            logger.info(f"✅ 获取了 {len(results['ids'])} 个文档")
            return results
        except Exception as e:
            logger.error(f"❌ 获取文档失败: {e}")
            return {'ids': [], 'documents': [], 'metadatas': []}

    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 文档ID列表

        Returns:
            是否成功
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"✅ 删除了 {len(ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"❌ 删除文档失败: {e}")
            return False

    def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        更新文档

        Args:
            ids: 文档ID列表
            documents: 新文档文本（可选）
            metadatas: 新元数据（可选）

        Returns:
            是否成功
        """
        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"✅ 更新了 {len(ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"❌ 更新文档失败: {e}")
            return False

    def count(self) -> int:
        """获取文档总数"""
        return self.collection.count()

    def clear(self) -> bool:
        """清空集合"""
        try:
            # 删除集合
            self.client.delete_collection(name=self.collection_name)
            # 重新创建
            self.collection = self._get_or_create_collection()
            logger.info(f"✅ 集合已清空: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ 清空集合失败: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        return {
            'name': self.collection_name,
            'count': self.collection.count(),
            'metadata': self.collection.metadata
        }






        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

def create_vector_store(
    persist_directory: str = "data/chroma",
    collection_name: str = "fieldmind_chunks"
) -> VectorStoreService:
    """工厂方法：创建向量存储服务"""
    return VectorStoreService(persist_directory, collection_name)
