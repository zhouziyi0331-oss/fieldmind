"""
Khoj服务 - 个人AI助手与知识管理
=======================================

功能特性：
- 跨模态语义搜索（文本、PDF、图片）
- 基于个人知识库的AI对话
- 增量索引与实时更新
- 多项目隔离的知识管理

架构说明：
- Khoj作为独立服务运行（默认端口42110）
- FieldMind通过HTTP API调用Khoj服务
- 支持本地部署和云端部署两种模式
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class KhojService:
    """Khoj服务客户端 - 个人AI助手与知识管理"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化Khoj服务客户端

        Args:
            api_url: Khoj服务地址（默认 http://localhost:42110）
            api_key: Khoj API密钥（可选，用于云端服务）
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url or os.getenv('KHOJ_API_URL', 'http://localhost:42110')
        self.api_key = api_key or os.getenv('KHOJ_API_KEY')
        self.timeout = timeout

        # HTTP客户端配置
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=headers,
            timeout=timeout
        )

        logger.info(f"✅ Khoj服务初始化完成: {self.api_url}")

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查 - 验证Khoj服务是否可用

        Returns:
            {"status": "ok|error", "version": "...", "available": bool}
        """
        try:
            response = await self.client.get('/api/health')

            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'ok',
                    'version': data.get('version', 'unknown'),
                    'available': True
                }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP {response.status_code}',
                    'available': False
                }

        except httpx.ConnectError:
            logger.warning(f"⚠️ Khoj服务未运行: {self.api_url}")
            return {
                'status': 'error',
                'message': 'Khoj服务未运行，请先启动Khoj',
                'available': False,
                'hint': 'Run: khoj --anonymous-mode'
            }

        except Exception as e:
            logger.error(f"⚠️ Khoj健康检查失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'available': False
            }

    async def index_document(
        self,
        content: str,
        title: Optional[str] = None,
        file_type: str = 'text',
        project_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        索引文档到Khoj知识库

        Args:
            content: 文档内容
            title: 文档标题
            file_type: 文件类型（text/pdf/markdown）
            project_id: 项目ID（用于隔离不同项目）
            metadata: 额外元数据

        Returns:
            {"status": "success|error", "indexed": bool, "doc_id": "..."}
        """
        try:
            # 构建索引请求
            payload = {
                'content': content,
                'title': title or 'Untitled Document',
                'file_type': file_type,
                'timestamp': datetime.now().isoformat()
            }

            # 添加项目标签用于隔离
            if project_id:
                payload['tags'] = [f'project:{project_id}']

            # 添加元数据
            if metadata:
                payload['metadata'] = metadata

            # 调用Khoj索引API
            response = await self.client.post(
                '/api/v1/index/update',
                json=payload
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Khoj索引成功: {title}")
                return {
                    'status': 'success',
                    'indexed': True,
                    'doc_id': result.get('id'),
                    'message': 'Document indexed successfully'
                }
            else:
                logger.warning(f"⚠️ Khoj索引失败: HTTP {response.status_code}")
                return {
                    'status': 'error',
                    'indexed': False,
                    'message': response.text
                }

        except Exception as e:
            logger.error(f"⚠️ Khoj索引异常: {e}", exc_info=True)
            return {
                'status': 'error',
                'indexed': False,
                'error': str(e)
            }

    async def search(
        self,
        query: str,
        n: int = 5,
        project_id: Optional[str] = None,
        search_type: str = 'all'
    ) -> Dict[str, Any]:
        """
        语义搜索知识库

        Args:
            query: 搜索查询
            n: 返回结果数量
            project_id: 项目ID（限定搜索范围）
            search_type: 搜索类型（all/text/pdf/image）

        Returns:
            {
                "status": "success|error",
                "results": [
                    {
                        "content": "...",
                        "title": "...",
                        "score": 0.95,
                        "metadata": {...}
                    }
                ],
                "total": 5
            }
        """
        try:
            # 构建搜索参数
            params = {
                'q': query,
                'n': n,
                't': search_type
            }

            # 添加项目过滤
            if project_id:
                params['filter'] = f'tag:project:{project_id}'

            # 调用Khoj搜索API
            response = await self.client.get(
                '/api/search',
                params=params
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"✅ Khoj搜索成功: {len(results)}条结果")

                return {
                    'status': 'success',
                    'results': results,
                    'total': len(results),
                    'query': query
                }
            else:
                logger.warning(f"⚠️ Khoj搜索失败: HTTP {response.status_code}")
                return {
                    'status': 'error',
                    'results': [],
                    'total': 0,
                    'message': response.text
                }

        except Exception as e:
            logger.error(f"⚠️ Khoj搜索异常: {e}", exc_info=True)
            return {
                'status': 'error',
                'results': [],
                'total': 0,
                'error': str(e)
            }

    async def chat(
        self,
        query: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        基于知识库的AI对话

        Args:
            query: 用户问题
            project_id: 项目ID（限定知识范围）
            conversation_id: 会话ID（保持上下文）

        Returns:
            {
                "status": "success|error",
                "response": "AI回答内容",
                "sources": [...],
                "conversation_id": "..."
            }
        """
        try:
            # 构建对话请求
            payload = {
                'q': query,
                'create_new': conversation_id is None
            }

            if conversation_id:
                payload['conversation_id'] = conversation_id

            # 添加项目上下文过滤
            if project_id:
                payload['context_filter'] = f'project:{project_id}'

            # 调用Khoj对话API
            response = await self.client.post(
                '/api/chat',
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Khoj对话成功")

                return {
                    'status': 'success',
                    'response': result.get('response', ''),
                    'sources': result.get('context', []),
                    'conversation_id': result.get('conversation_id'),
                    'query': query
                }
            else:
                logger.warning(f"⚠️ Khoj对话失败: HTTP {response.status_code}")
                return {
                    'status': 'error',
                    'response': '',
                    'message': response.text
                }

        except Exception as e:
            logger.error(f"⚠️ Khoj对话异常: {e}", exc_info=True)
            return {
                'status': 'error',
                'response': '',
                'error': str(e)
            }

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# ==================== 全局单例 ====================

_khoj_service = None


def get_khoj_service() -> KhojService:
    """获取Khoj服务单例"""
    global _khoj_service
    if _khoj_service is None:
        _khoj_service = KhojService()
    return _khoj_service


# ==================== 同步包装器（用于非异步环境） ====================

def sync_search(query: str, n: int = 5, project_id: Optional[str] = None) -> Dict[str, Any]:
    """同步搜索包装器"""
    service = get_khoj_service()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(service.search(query, n, project_id))
    finally:
        loop.close()


def sync_index(content: str, title: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
    """同步索引包装器"""
    service = get_khoj_service()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(service.index_document(content, title, project_id=project_id))
    finally:
        loop.close()
