"""
Quivr Service - 第二大脑RAG系统集成
作为八层AI记忆架构的第9层，提供企业级RAG能力

技术特性：
- RAG Pipeline: 完整的检索增强生成流程
- Multi-LLM支持: OpenAI/Anthropic/Mistral/Groq等
- 向量存储: Faiss本地向量库
- 文档处理: 支持多种文件格式
- 流式响应: 支持实时流式输出
- 对话历史: 内置会话管理

集成位置：
- 文档上传管道: 自动索引文档到Quivr Brain
- AI对话服务: 通过Quivr RAG检索和问答
- 项目隔离: 每个项目独立的Brain实例
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import asyncio
from typing import Any

try:
    from quivr_core import Brain
    from quivr_core.llm import LLMEndpoint
    from quivr_core.rag.entities.config import LLMEndpointConfig, DefaultModelSuppliers
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    QUIVR_AVAILABLE = True
    QUIVR_IMPORT_ERROR = None
except Exception as exc:  # Quivr 是可选增强，不得阻塞主处理链路。
    Brain = Any
    LLMEndpoint = Any
    LLMEndpointConfig = Any
    DefaultModelSuppliers = None
    FAISS = Any
    HuggingFaceEmbeddings = Any
    QUIVR_AVAILABLE = False
    QUIVR_IMPORT_ERROR = str(exc)

logger = logging.getLogger(__name__)


class QuivrService:
    """Quivr第二大脑RAG系统服务"""

    def __init__(
        self,
        brain_storage_dir: Optional[str] = None,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-3-5-sonnet-20241022",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        初始化Quivr服务

        Args:
            brain_storage_dir: Brain存储目录（用于持久化）
            llm_provider: LLM提供商（openai/anthropic/groq等）
            llm_model: 模型名称
            embedding_model: 嵌入模型（多语言支持）
        """
        self.brain_storage_dir = brain_storage_dir or os.getenv(
            'QUIVR_STORAGE_DIR',
            '/tmp/quivr_brains'
        )
        Path(self.brain_storage_dir).mkdir(parents=True, exist_ok=True)

        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.embedding_model = embedding_model

        # Brain实例缓存（project_id -> Brain）
        self._brain_cache: Dict[str, Brain] = {}

        # 初始化嵌入模型
        self.embeddings = None

        logger.info(f"✅ QuivrService初始化完成: {llm_provider}/{llm_model}")

    def _load_embeddings_model(self, model_name: str) -> Optional[HuggingFaceEmbeddings]:
        """尝试加载指定嵌入模型；没有本地缓存时直接返回 None，避免触发下载。"""
        if not self._embedding_model_cached(model_name):
            return None
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info(f"✅ 嵌入模型加载成功: {model_name}")
            return embeddings
        except Exception as e:
            logger.error(f"❌ 嵌入模型加载失败: {model_name}: {e}")
            return None

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        """延迟加载嵌入模型；只接受本地缓存命中的模型。"""
        if self.embeddings is None:
            for candidate in (self.embedding_model, "sentence-transformers/all-MiniLM-L6-v2"):
                embeddings = self._load_embeddings_model(candidate)
                if embeddings is not None:
                    self.embeddings = embeddings
                    break
            if self.embeddings is None:
                raise RuntimeError(f"本地嵌入模型未缓存: {self.embedding_model}")

        return self.embeddings

    def _embedding_model_cached(self, model_name: Optional[str] = None) -> bool:
        """快速检查嵌入模型是否已在本地缓存，避免离线环境触发长时间下载重试。"""
        model_slug = (model_name or self.embedding_model).replace("/", "--")
        cache_roots = []

        for env_name in ("SENTENCE_TRANSFORMERS_HOME", "HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE"):
            value = os.getenv(env_name)
            if value:
                cache_roots.append(Path(value).expanduser())

        cache_roots.extend([
            Path.home() / ".cache" / "huggingface" / "hub",
            Path.home() / ".cache" / "sentence_transformers",
        ])

        for root in cache_roots:
            if not root.exists():
                continue
            candidate = root / f"models--{model_slug}"
            if candidate.exists():
                return True
            if any(p.name.startswith(f"models--{model_slug}") for p in root.iterdir() if p.is_dir()):
                return True

        return False

    def _create_llm_endpoint(self) -> LLMEndpoint:
        """创建LLM端点配置"""
        # 映射供应商名称
        supplier_map = {
            'openai': DefaultModelSuppliers.OPENAI,
            'anthropic': DefaultModelSuppliers.ANTHROPIC,
            'groq': DefaultModelSuppliers.GROQ,
            'mistral': DefaultModelSuppliers.MISTRAL,
        }

        supplier = supplier_map.get(
            self.llm_provider.lower(),
            DefaultModelSuppliers.ANTHROPIC
        )

        # 获取API密钥
        api_key = None
        if supplier == DefaultModelSuppliers.ANTHROPIC:
            api_key = os.getenv('ANTHROPIC_API_KEY')
        elif supplier == DefaultModelSuppliers.OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
        elif supplier == DefaultModelSuppliers.GROQ:
            api_key = os.getenv('GROQ_API_KEY')

        config = LLMEndpointConfig(
            supplier=supplier,
            model=self.llm_model,
            llm_api_key=api_key,
            max_context_tokens=4000,
            max_output_tokens=2000,
            temperature=0.7,
            streaming=True
        )

        return LLMEndpoint.from_config(config)

    def _get_brain_path(self, project_id: str) -> Path:
        """获取Brain存储路径"""
        return Path(self.brain_storage_dir) / f"brain_{project_id}"

    async def get_or_create_brain(
        self,
        project_id: str,
        brain_name: Optional[str] = None
    ) -> Brain:
        """
        获取或创建项目的Brain实例

        Args:
            project_id: 项目ID
            brain_name: Brain名称（可选）

        Returns:
            Brain实例
        """
        if not QUIVR_AVAILABLE:
            raise RuntimeError(f"Quivr依赖不可用: {QUIVR_IMPORT_ERROR}")

        # 检查缓存
        if project_id in self._brain_cache:
            return self._brain_cache[project_id]

        brain_path = self._get_brain_path(project_id)
        brain_name = brain_name or f"FieldMind_{project_id}"

        try:
            # 尝试加载已存在的Brain
            if brain_path.exists():
                brain = await Brain.load(brain_path)
                logger.info(f"✅ 加载已存在的Brain: {project_id}")
            else:
                # 创建新Brain
                llm = self._create_llm_endpoint()
                embeddings = self._get_embeddings()

                # 创建FAISS向量存储
                vector_store = FAISS.from_texts(
                    ["初始化文档"],  # 占位文本
                    embeddings
                )

                brain = Brain(
                    name=brain_name,
                    llm=llm,
                    vector_db=vector_store,
                    embedder=embeddings
                )

                # 保存Brain
                brain_path.mkdir(parents=True, exist_ok=True)
                await brain.save(brain_path)

                logger.info(f"✅ 创建新Brain: {project_id}")

            # 缓存
            self._brain_cache[project_id] = brain
            return brain

        except Exception as e:
            logger.error(f"❌ Brain创建/加载失败: {e}", exc_info=True)
            raise

    async def index_document(
        self,
        project_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        索引文档到Quivr Brain

        Args:
            project_id: 项目ID
            content: 文档内容
            metadata: 元数据

        Returns:
            索引结果
        """
        try:
            brain = await self.get_or_create_brain(project_id)

            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # 使用from_files方法添加文档
                brain = await asyncio.to_thread(
                    Brain.from_files,
                    name=brain.name,
                    file_paths=[tmp_path],
                    vector_db=brain.vector_db,
                    llm=brain.llm,
                    embedder=brain.embedder,
                    skip_file_error=True
                )

                # 更新缓存
                self._brain_cache[project_id] = brain

                # 保存Brain
                brain_path = self._get_brain_path(project_id)
                await brain.save(brain_path)

                return {
                    'status': 'success',
                    'indexed': True,
                    'project_id': project_id,
                    'message': 'Document indexed successfully'
                }

            finally:
                # 清理临时文件
                Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"❌ Quivr索引失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'indexed': False,
                'message': str(e)
            }

    async def search(
        self,
        project_id: str,
        query: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        在Brain中搜索相关文档

        Args:
            project_id: 项目ID
            query: 查询文本
            n_results: 返回结果数

        Returns:
            搜索结果
        """
        try:
            brain = await self.get_or_create_brain(project_id)

            # 执行搜索
            results = await brain.asearch(
                query=query,
                n_results=n_results
            )

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'content': result.chunk.content,
                    'metadata': result.chunk.metadata,
                    'distance': result.distance
                })

            return {
                'status': 'success',
                'results': formatted_results,
                'total': len(formatted_results)
            }

        except Exception as e:
            logger.error(f"❌ Quivr搜索失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'results': [],
                'total': 0,
                'message': str(e)
            }

    async def ask(
        self,
        project_id: str,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        向Brain提问（RAG问答）

        Args:
            project_id: 项目ID
            question: 问题
            chat_history: 对话历史

        Returns:
            回答结果
        """
        try:
            brain = await self.get_or_create_brain(project_id)

            # 转换对话历史格式
            quivr_history = None
            if chat_history:
                from quivr_core.rag.entities.chat import ChatHistory
                quivr_history = ChatHistory()
                for msg in chat_history:
                    if msg.get('role') == 'user':
                        quivr_history.append_user_message(msg['content'])
                    elif msg.get('role') == 'assistant':
                        quivr_history.append_assistant_message(msg['content'])

            # 执行RAG问答
            response = await asyncio.to_thread(
                brain.ask,
                question=question,
                chat_history=quivr_history
            )

            return {
                'status': 'success',
                'answer': response.assistant,
                'sources': [
                    {
                        'content': source.chunk.content,
                        'metadata': source.chunk.metadata
                    }
                    for source in response.metadata.sources
                ],
                'metadata': {
                    'model': response.metadata.model,
                    'thumbs_up': response.metadata.thumbs
                }
            }

        except Exception as e:
            logger.error(f"❌ Quivr问答失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'answer': '',
                'message': str(e)
            }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not QUIVR_AVAILABLE:
                return {
                    'status': 'unavailable',
                    'available': False,
                    'message': f"Quivr依赖不可用: {QUIVR_IMPORT_ERROR}",
                    'components': {
                        'quivr_core': False,
                        'storage': False,
                        'embeddings': False,
                        'llm': False,
                    },
                    'brain_count': len(self._brain_cache),
                    'storage_dir': self.brain_storage_dir,
                }

            # 检查存储目录
            storage_ok = Path(self.brain_storage_dir).exists()

            # 检查嵌入模型
            embeddings_ok = bool(self.embeddings) or self._embedding_model_cached()
            if not embeddings_ok:
                logger.warning(f"嵌入模型未缓存: {self.embedding_model}")

            # 检查LLM配置，只看密钥是否存在，不实例化端点，避免触发网络初始化
            llm_ok = bool(
                (self.llm_provider.lower() == "anthropic" and os.getenv("ANTHROPIC_API_KEY"))
                or (self.llm_provider.lower() == "openai" and os.getenv("OPENAI_API_KEY"))
                or (self.llm_provider.lower() == "groq" and os.getenv("GROQ_API_KEY"))
                or (self.llm_provider.lower() == "mistral")
            )

            all_ok = storage_ok and embeddings_ok and llm_ok

            return {
                'status': 'ok' if all_ok else 'degraded',
                'available': all_ok,
                'components': {
                    'storage': storage_ok,
                    'embeddings': embeddings_ok,
                    'llm': llm_ok
                },
                'brain_count': len(self._brain_cache),
                'storage_dir': self.brain_storage_dir
            }

        except Exception as e:
            return {
                'status': 'error',
                'available': False,
                'message': str(e)
            }


# ===== 全局单例 =====
_quivr_service: Optional[QuivrService] = None


def get_quivr_service() -> QuivrService:
    """获取Quivr服务单例"""
    global _quivr_service
    if _quivr_service is None:
        _quivr_service = QuivrService()
    return _quivr_service
