"""
语义嵌入服务

使用Sentence-Transformers进行真实的语义向量化
替换原有的TF-IDF伪向量化
"""
import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

# 全局模型实例
_model = None


def get_embedding_model():
    """
    获取或初始化嵌入模型

    使用all-MiniLM-L6-v2：
    - 轻量级（80MB）
    - 384维向量
    - 支持中英文
    - 适合Mac本地运行
    """
    global _model

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            import os

            logger.info("🔄 加载语义嵌入模型: all-MiniLM-L6-v2")

            # 设置离线模式，强制使用本地缓存
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'

            # 尝试加载模型（优先使用缓存）
            try:
                _model = SentenceTransformer(
                    'sentence-transformers/all-MiniLM-L6-v2',
                    device='cpu',  # Mac本地使用CPU
                    cache_folder=os.path.expanduser('~/.cache/huggingface/hub')
                )
                logger.info("✅ 语义嵌入模型加载完成（384维）")

            except Exception as download_error:
                logger.warning(f"下载模型失败: {download_error}")
                logger.info("尝试使用备用模型: paraphrase-MiniLM-L3-v2")

                # 尝试更小的备用模型
                _model = SentenceTransformer(
                    'paraphrase-MiniLM-L3-v2',
                    device='cpu'
                )
                logger.info("✅ 使用备用模型加载成功")

        except Exception as e:
            logger.error(f"❌ 加载嵌入模型失败: {e}")
            logger.warning("⚠️ 将降级使用TF-IDF")
            return None

    return _model


def encode_text(text: Union[str, List[str]], show_progress: bool = False) -> np.ndarray:
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
        logger.error("嵌入模型未加载，无法编码")
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
            normalize_embeddings=True  # 归一化，便于余弦相似度计算
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
        384 (all-MiniLM-L6-v2)
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
