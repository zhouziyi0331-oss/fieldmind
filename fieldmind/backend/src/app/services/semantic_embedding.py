"""
语义嵌入服务

使用本地 Sentence-Transformers 模型进行真实语义向量化，
优先加载 bge-small-zh-v1.5 / bge-large-zh-v1.5 的本地缓存。
"""
import logging
from typing import List, Union, Optional, Any
import numpy as np
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 全局模型实例
_model = None


class EmbeddingUnavailable(RuntimeError):
    """本地语义模型不可用，禁止生成伪向量。"""

_LOCAL_MODEL_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "models" / "bge-small-zh-v1.5",
    Path(__file__).resolve().parents[2] / "models" / "bge-large-zh-v1.5",
]


def _load_local_sentence_transformer():
    from sentence_transformers import SentenceTransformer

    for model_path in _LOCAL_MODEL_CANDIDATES:
        if model_path.exists():
            logger.info(f"🔄 加载本地语义嵌入模型: {model_path}")
            return SentenceTransformer(str(model_path), device='cpu')
    return None


@dataclass
class SemanticEmbeddingBackend:
    """Sentence-Transformers 兼容包装器。"""

    model: Any
    model_name: str
    query_instruction: str = "为这个句子生成表示以用于检索相关文章："

    def encode(self, texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        kwargs.setdefault("convert_to_numpy", True)
        kwargs.setdefault("normalize_embeddings", True)
        return self.model.encode(texts, **kwargs)

    def embed_query(self, text: str):
        query = text.strip()
        if self.query_instruction and query:
            query = f"{self.query_instruction}{query}"
        vector = self.encode([query])[0]
        return vector.tolist()

    def embed_documents(self, texts):
        vectors = self.encode(texts)
        return [vector.tolist() for vector in vectors]

    def get_sentence_embedding_dimension(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())


def load_embedding_backend(query_instruction: str = "为这个句子生成表示以用于检索相关文章：") -> Optional[SemanticEmbeddingBackend]:
    """加载本地语义嵌入后端。"""
    model = get_embedding_model()
    if model is None:
        return None
    raw_name = getattr(model, "name_or_path", "local-sentence-transformer")
    model_name = Path(str(raw_name)).name if "/" in str(raw_name) else str(raw_name)
    return SemanticEmbeddingBackend(
        model=model,
        model_name=str(model_name),
        query_instruction=query_instruction,
    )


def get_embedding_model():
    """
    获取或初始化嵌入模型

    默认加载本机缓存的 bge-small-zh-v1.5 / bge-large-zh-v1.5：
    - 真实语义向量
    - 离线可用
    - 适合当前 FieldMind 本地运行
    """
    global _model

    if _model is None:
        try:
            import os

            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'

            _model = _load_local_sentence_transformer()
            if _model is not None:
                logger.info("✅ 语义嵌入模型加载完成（本地离线模式）")
            else:
                logger.warning("未找到本地语义嵌入模型，语义向量服务不可用")

        except Exception as e:
            logger.error(f"❌ 加载嵌入模型失败: {e}")
            logger.warning("⚠️ 语义向量服务不可用，调用方必须选择真实降级方案")
            return None

    return _model


def encode_text(text: Union[str, List[str]], show_progress: bool = False) -> Optional[np.ndarray]:
    """
    将文本编码为语义向量

    Args:
        text: 单个文本或文本列表
        show_progress: 是否显示进度条

    Returns:
        numpy数组，shape为(n_texts, 384)
    """
    model = get_embedding_model()

    if model is None:
        logger.error("语义嵌入模型不可用，拒绝写入占位向量")
        return None

    try:
        # 统一转为列表处理
        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        # 过滤空文本
        valid_texts = [t for t in texts if t and len(t.strip()) > 0]

        if not valid_texts:
            logger.warning("没有有效的文本需要编码")
            return np.array([])

        # 编码为向量
        embeddings = model.encode(
            valid_texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # 如果输入是单个文本，返回单个向量
        if is_single:
            return embeddings[0]

        return embeddings

    except Exception as e:
        logger.error(f"文本编码失败: {e}")
        return None


def encode_chunks(chunks: List[str], batch_size: int = 32) -> List[np.ndarray]:
    """
    批量编码文本块

    Args:
        chunks: 文本块列表
        batch_size: 批处理大小

    Returns:
        向量列表
    """
    model = get_embedding_model()

    if model is None:
        logger.error("语义嵌入模型不可用，批量向量化返回空结果")
        return []

    try:
        logger.info(f"开始编码 {len(chunks)} 个文本块（批大小：{batch_size}）")

        embeddings = []

        # 分批处理
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_embeddings = encode_text(batch, show_progress=False)

            if batch_embeddings is not None:
                embeddings.extend(batch_embeddings)

            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"  已编码 {len(embeddings)}/{len(chunks)} 个块")

        logger.info(f"✅ 编码完成，共 {len(embeddings)} 个向量")
        return embeddings

    except Exception as e:
        logger.error(f"批量编码失败: {e}")
        return []


def get_embedding_dimension() -> int:
    """
    获取嵌入向量的维度

    Returns:
        实际模型维度（当前本机缓存通常为 512）
    """
    model = get_embedding_model()

    if model is None:
        return 0

    return model.get_sentence_embedding_dimension()


def test_embedding():
    """
    测试嵌入功能
    """
    try:
        test_texts = [
            "这是一个测试句子",
            "布依族山歌",
            "乡村振兴战略"
        ]

        logger.info("测试语义嵌入...")

        embeddings = encode_text(test_texts)

        if embeddings is not None:
            logger.info(f"✅ 测试成功")
            logger.info(f"   输入文本数: {len(test_texts)}")
            logger.info(f"   输出向量shape: {embeddings.shape}")
            logger.info(f"   向量维度: {embeddings.shape[1]}")
            return True
        else:
            logger.error("❌ 测试失败")
            return False

    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


# 启动时预加载模型
def preload_model():
    """
    预加载模型到内存
    """
    logger.info("预加载语义嵌入模型...")
    model = get_embedding_model()

    if model:
        # 运行一次测试编码，确保模型完全加载
        _ = encode_text("预热模型")
        logger.info("✅ 模型预加载完成")
    else:
        logger.warning("⚠️ 模型加载失败")
