"""
关键词提取服务 (Keyword Extraction Service)
🔥 WorkflowEngine集成 - 阶段1
使用 TF-IDF 算法提取文本关键词
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from collections import Counter
import math
import logging
import jieba
import jieba.analyse

logger = logging.getLogger(__name__)


class KeywordExtractionService:
    """
    关键词提取服务
    🔥 支持WorkflowEngine DAG执行

    方法：
    1. TF-IDF 算法
    2. TextRank 算法
    3. 词频统计
    """

    def __init__(self, use_workflow_engine: bool = True):
        # 停用词列表
        self.stop_words = self._load_stop_words()
        self.use_workflow_engine = use_workflow_engine  # 🔥 新增

        # 🔥 初始化WorkflowEngine
        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=3)

    def _load_stop_words(self) -> set:
        """加载停用词"""
        # 简化版停用词
        return set([
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那"
        ])

    def extract_keywords(
        self,
        text: str,
        top_k: int = 20,
        method: str = "tfidf"
    ) -> List[Dict[str, Any]]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前 K 个关键词
            method: 提取方法 (tfidf/textrank/frequency)

        Returns:
            [
                {
                    "word": str,
                    "score": float,
                    "method": str
                }
            ]
        """
        if not text or len(text.strip()) == 0:
            return []

        if method == "tfidf":
            return self._extract_tfidf(text, top_k)
        elif method == "textrank":
            return self._extract_textrank(text, top_k)
        elif method == "frequency":
            return self._extract_frequency(text, top_k)
        else:
            return self._extract_tfidf(text, top_k)

    def _extract_tfidf(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """TF-IDF 提取"""
        try:
            # 使用 jieba 的 TF-IDF
            keywords = jieba.analyse.extract_tags(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a')
            )

            return [
                {
                    "word": word,
                    "score": float(score),
                    "method": "tfidf"
                }
                for word, score in keywords
            ]

        except Exception as e:
            logger.error(f"TF-IDF 提取失败: {e}")
            return []

    def _extract_textrank(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """TextRank 提取"""
        try:
            # 使用 jieba 的 TextRank
            keywords = jieba.analyse.textrank(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a')
            )

            return [
                {
                    "word": word,
                    "score": float(score),
                    "method": "textrank"
                }
                for word, score in keywords
            ]

        except Exception as e:
            logger.error(f"TextRank 提取失败: {e}")
            return []

    def _extract_frequency(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """词频统计提取"""
        try:
            # 分词
            words = jieba.lcut(text)

            # 过滤停用词和单字
            words = [
                w for w in words
                if len(w) > 1 and w not in self.stop_words
            ]

            # 统计词频
            word_counts = Counter(words)

            # 归一化
            total = sum(word_counts.values())

            keywords = [
                {
                    "word": word,
                    "score": count / total,
                    "method": "frequency"
                }
                for word, count in word_counts.most_common(top_k)
            ]

            return keywords

        except Exception as e:
            logger.error(f"词频统计失败: {e}")
            return []

    def extract_and_save_keywords(
        self,
        db: Session,
        document_id: int,
        text: str,
        top_k: int = 20
    ) -> int:
        """
        提取关键词并保存到数据库

        Args:
            db: 数据库会话
            document_id: 文档 ID
            text: 文本内容
            top_k: 提取数量

        Returns:
            保存的关键词数量
        """
        from app.models.keyword import Keyword

        # 提取关键词
        keywords = self.extract_keywords(text, top_k=top_k, method="tfidf")

        if not keywords:
            logger.warning(f"文档 {document_id} 未提取到关键词")
            return 0

        # 保存到数据库
        saved_count = 0

        for kw in keywords:
            keyword = Keyword(
                document_id=document_id,
                word=kw["word"],
                score=kw["score"],
                extraction_method=kw["method"],
            )

            db.add(keyword)
            saved_count += 1

        db.commit()

        logger.info(f"文档 {document_id} 提取了 {saved_count} 个关键词")

        return saved_count

    def extract_from_chunks(
        self,
        db: Session,
        project_id: int,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        从项目的所有 chunks 中提取关键词

        Args:
            db: 数据库会话
            project_id: 项目 ID
            top_k: 返回前 K 个

        Returns:
            项目级别的关键词列表
        """
        from app.models.chunk import Chunk

        # 获取所有 chunks
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()

        if not chunks:
            return []

        # 合并所有文本
        all_text = "\n".join([chunk.content for chunk in chunks if chunk.content])

        # 提取关键词
        keywords = self.extract_keywords(all_text, top_k=top_k, method="tfidf")

        return keywords


    def process_text(
        self,
        text: str,
        top_k: int = 20,
        methods: List[str] = None,
        use_workflow_engine: bool = None
    ) -> Dict[str, Any]:
        """
        处理文本并提取关键词
        🔥 支持WorkflowEngine DAG执行

        Args:
            text: 输入文本
            top_k: 返回前 K 个关键词
            methods: 提取方法列表 (默认: ["tfidf", "textrank", "frequency"])
            use_workflow_engine: 是否使用WorkflowEngine（默认使用初始化配置）

        Returns:
            {
                'keywords': List[Dict],
                'by_method': Dict[str, List],
                'merged': List[Dict]
            }
        """
        if methods is None:
            methods = ["tfidf", "textrank", "frequency"]

        if use_workflow_engine is None:
            use_workflow_engine = self.use_workflow_engine

        if use_workflow_engine:
            return self._process_with_workflow_engine(text, top_k, methods)
        else:
            return self._process_traditional(text, top_k, methods)

    def _process_with_workflow_engine(
        self,
        text: str,
        top_k: int,
        methods: List[str]
    ) -> Dict[str, Any]:
        """
        🔥 使用WorkflowEngine处理文本（DAG模式）
        """
        logger.info(f"🔥 [WorkflowEngine] 开始提取关键词")

        # 创建工作流
        workflow = self.workflow_engine.create_workflow(
            name=f"keyword_extraction_{len(text)}_chars",
            description=f"关键词提取流水线"
        )

        # 🔥 Task 1: 预处理文本
        self.workflow_engine.add_task(
            workflow,
            name="preprocess",
            func=self._task_preprocess_text,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 2-4: 并行提取关键词（3种方法）
        if "tfidf" in methods:
            self.workflow_engine.add_task(
                workflow,
                name="tfidf",
                func=self._task_extract_tfidf,
                kwargs={'text': text, 'top_k': top_k},
                dependencies=["preprocess"]
            )

        if "textrank" in methods:
            self.workflow_engine.add_task(
                workflow,
                name="textrank",
                func=self._task_extract_textrank,
                kwargs={'text': text, 'top_k': top_k},
                dependencies=["preprocess"]
            )

        if "frequency" in methods:
            self.workflow_engine.add_task(
                workflow,
                name="frequency",
                func=self._task_extract_frequency,
                kwargs={'text': text, 'top_k': top_k},
                dependencies=["preprocess"]
            )

        # 🔥 Task 5: 合并结果
        self.workflow_engine.add_task(
            workflow,
            name="merge",
            func=self._task_merge_keywords,
            kwargs={
                'tfidf': '$tfidf.keywords' if "tfidf" in methods else [],
                'textrank': '$textrank.keywords' if "textrank" in methods else [],
                'frequency': '$frequency.keywords' if "frequency" in methods else [],
                'top_k': top_k
            },
            dependencies=[m for m in ["tfidf", "textrank", "frequency"] if m in methods]
        )

        # 执行工作流
        results = self.workflow_engine.execute(workflow)

        logger.info(f"✅ [WorkflowEngine] 关键词提取完成")
        return results['merge']

    def _process_traditional(
        self,
        text: str,
        top_k: int,
        methods: List[str]
    ) -> Dict[str, Any]:
        """
        传统顺序处理模式（向后兼容）
        """
        logger.info(f"📝 [传统模式] 开始提取关键词")

        by_method = {}
        all_keywords = []

        for method in methods:
            keywords = self.extract_keywords(text, top_k, method)
            by_method[method] = keywords
            all_keywords.extend(keywords)

        # 合并去重
        word_scores = {}
        for kw in all_keywords:
            word = kw['word']
            score = kw['score']
            if word not in word_scores:
                word_scores[word] = []
            word_scores[word].append(score)

        # 计算平均分数
        merged = [
            {
                'word': word,
                'score': sum(scores) / len(scores),
                'method': 'merged',
                'count': len(scores)
            }
            for word, scores in word_scores.items()
        ]

        # 排序并取top_k
        merged = sorted(merged, key=lambda x: x['score'], reverse=True)[:top_k]

        return {
            'keywords': all_keywords,
            'by_method': by_method,
            'merged': merged,
            'count': len(merged)
        }

    # ========================================
    # 🔥 WorkflowEngine Task Functions
    # ========================================

    def _task_preprocess_text(self, text: str, _context: dict) -> dict:
        """
        🔥 Task 1: 预处理文本
        """
        logger.info(f"  [Task] preprocess: 预处理文本")

        # 简单清理
        text = text.strip()
        text_length = len(text)

        logger.info(f"  ✅ preprocess: {text_length} 字符")
        return {
            'text': text,
            'length': text_length
        }

    def _task_extract_tfidf(self, text: str, top_k: int, _context: dict) -> dict:
        """
        🔥 Task 2: TF-IDF提取
        """
        logger.info(f"  [Task] tfidf: TF-IDF提取")

        keywords = self._extract_tfidf(text, top_k)

        logger.info(f"  ✅ tfidf: {len(keywords)} 个关键词")
        return {'keywords': keywords}

    def _task_extract_textrank(self, text: str, top_k: int, _context: dict) -> dict:
        """
        🔥 Task 3: TextRank提取
        """
        logger.info(f"  [Task] textrank: TextRank提取")

        keywords = self._extract_textrank(text, top_k)

        logger.info(f"  ✅ textrank: {len(keywords)} 个关键词")
        return {'keywords': keywords}

    def _task_extract_frequency(self, text: str, top_k: int, _context: dict) -> dict:
        """
        🔥 Task 4: 词频统计提取
        """
        logger.info(f"  [Task] frequency: 词频统计")

        keywords = self._extract_frequency(text, top_k)

        logger.info(f"  ✅ frequency: {len(keywords)} 个关键词")
        return {'keywords': keywords}

    def _task_merge_keywords(self, tfidf: list, textrank: list, frequency: list,
                            top_k: int, _context: dict) -> dict:
        """
        🔥 Task 5: 合并关键词
        """
        logger.info(f"  [Task] merge: 合并关键词")

        all_keywords = tfidf + textrank + frequency

        # 按方法分组
        by_method = {
            'tfidf': tfidf,
            'textrank': textrank,
            'frequency': frequency
        }

        # 合并去重，计算平均分数
        word_scores = {}
        for kw in all_keywords:
            word = kw['word']
            score = kw['score']
            if word not in word_scores:
                word_scores[word] = []
            word_scores[word].append(score)

        # 计算平均分数
        merged = [
            {
                'word': word,
                'score': sum(scores) / len(scores),
                'method': 'merged',
                'count': len(scores)
            }
            for word, scores in word_scores.items()
        ]

        # 排序并取top_k
        merged = sorted(merged, key=lambda x: x['score'], reverse=True)[:top_k]

        logger.info(f"  ✅ merge: {len(merged)} 个唯一关键词")
        return {
            'keywords': all_keywords,
            'by_method': by_method,
            'merged': merged,
            'count': len(merged)
        }


# 全局实例
keyword_extraction_service = KeywordExtractionService()
