"""
关键词提取服务
支持混合方法：LLM（准确）+ TF-IDF（快速）
以及关键词关系查询
"""

import logging
import jieba
import jieba.analyse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from collections import Counter
import re

from app.models.keyword import Keyword, DocumentKeyword, KeywordRelation
from app.config.keyword_categories import (
    KeywordCategory,
    CATEGORY_INFO,
    CATEGORY_WEIGHTS,
    get_all_categories
)

logger = logging.getLogger(__name__)


class KeywordService:
    """关键词提取和管理服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        # 初始化 jieba
        self._init_jieba()

    def _init_jieba(self):
        """初始化 jieba 分词器"""
        # 添加自定义词典（田野调查相关）
        custom_words = [
            "村委会", "村民大会", "村规民约", "乡村振兴",
            "土地流转", "集体经济", "非物质文化遗产",
            "传统技艺", "民间艺术"
        ]
        for word in custom_words:
            jieba.add_word(word, freq=1000)

    async def extract_keywords_mixed(
        self,
        text: str,
        document_id: int,
        project_id: int,
        top_n: int = 30,
        use_llm: bool = True
    ) -> List[Dict[str, Any]]:
        """
        混合方法提取关键词

        流程：
        1. TF-IDF 快速提取候选关键词
        2. LLM 精炼和分类（可选）
        3. 保存到数据库

        Args:
            text: 文本内容
            document_id: 文档ID
            project_id: 项目ID
            top_n: 提取数量
            use_llm: 是否使用 LLM 精炼
        """
        logger.info(f"开始提取关键词：document_id={document_id}, method=mixed")

        # Step 1: TF-IDF 快速提取
        tfidf_keywords = self._extract_tfidf(text, top_n * 2)  # 提取2倍数量

        if not use_llm:
            # 仅使用 TF-IDF 结果
            return await self._save_keywords(
                tfidf_keywords,
                document_id,
                project_id,
                method="tfidf"
            )

        # Step 2: LLM 精炼和分类
        try:
            llm_result = await self._refine_with_llm(text, tfidf_keywords, top_n)
            keywords = llm_result
            method = "mixed"
        except Exception as e:
            logger.warning(f"LLM 精炼失败，回退到 TF-IDF: {e}")
            keywords = tfidf_keywords[:top_n]
            method = "tfidf"

        # Step 3: 保存关键词
        return await self._save_keywords(keywords, document_id, project_id, method)

    def _extract_tfidf(self, text: str, top_n: int) -> List[Dict[str, Any]]:
        """
        使用 TF-IDF 提取关键词

        Returns:
            [{"text": "村委会", "weight": 0.85, "category": None}]
        """
        # 使用 jieba 的 TF-IDF（提取更多候选词，然后过滤）
        keywords_with_weights = jieba.analyse.extract_tags(
            text,
            topK=top_n * 2,  # 提取更多，后面过滤
            withWeight=True
        )

        # 使用词性标注过滤（只保留名词类）
        import jieba.posseg as pseg
        words_in_text = pseg.cut(text)
        valid_pos = {'n', 'nr', 'ns', 'nt', 'nz', 'vn', 'v', 'a'}  # 名词、动词、形容词
        valid_words = {pair.word for pair in words_in_text if pair.flag in valid_pos}

        # 格式化结果并过滤
        results = []
        for word, weight in keywords_with_weights:
            # 过滤：至少2个字符，且是有效词性
            if len(word) < 2 or word not in valid_words:
                continue

            # 基础分类（基于规则）
            category = self._guess_category_by_rules(word, text)

            results.append({
                "text": word,
                "weight": float(weight),
                "category": category,
                "frequency": text.count(word),
                "positions": self._find_positions(text, word)
            })

            if len(results) >= top_n:
                break

        return results

    def _guess_category_by_rules(self, keyword: str, context: str) -> Optional[str]:
        """基于规则猜测关键词类别"""

        # 遍历所有类别，查找匹配的提示词
        for category, info in CATEGORY_INFO.items():
            hints = info.get("extraction_hints", [])

            # 检查关键词是否包含提示词
            for hint in hints:
                if hint in keyword or hint in context[max(0, context.find(keyword)-50):context.find(keyword)+50]:
                    return category.value

        # 未匹配到，返回 None（让 LLM 决定）
        return None

    def _find_positions(self, text: str, keyword: str) -> List[int]:
        """找到关键词在文本中的所有位置"""
        positions = []
        start = 0
        while True:
            pos = text.find(keyword, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions[:20]  # 最多记录20个位置

    async def _refine_with_llm(
        self,
        text: str,
        tfidf_keywords: List[Dict],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """
        使用 LLM 精炼关键词和分类

        功能：
        1. 验证 TF-IDF 提取的关键词是否真正重要
        2. 补充 TF-IDF 可能遗漏的关键词
        3. 精确分类
        4. 提取别名
        """
        from app.services.multi_provider_llm_manager import get_llm_manager

        # 准备 TF-IDF 候选词
        candidate_keywords = [kw["text"] for kw in tfidf_keywords[:top_n * 2]]

        # 构建提示词
        prompt = f"""你是一个田野调查关键词提取专家。请从以下文本中提取最重要的关键词，并按照指定类别分类。

【可选类别】
{chr(10).join([f"- {cat.value}: {CATEGORY_INFO[cat]['description']}" for cat in KeywordCategory])}

【TF-IDF 候选词】（参考，可以调整）
{', '.join(candidate_keywords)}

【文本内容】（截取前1500字）
{text[:1500]}

【任务要求】
1. 从 TF-IDF 候选词中筛选真正重要的关键词
2. 补充候选词中遗漏的重要关键词
3. 为每个关键词分配最合适的类别
4. 提取关键词的别名（如果有）
5. 最多返回 {top_n} 个关键词

【输出格式】（JSON）
{{
  "keywords": [
    {{
      "text": "村委会",
      "category": "组织",
      "importance": 0.95,
      "reason": "文中多次提到，是访谈的核心对象",
      "aliases": ["村委", "村级组织"]
    }}
  ]
}}

请确保返回的是有效的 JSON 格式。"""

        try:
            # 调用 LLM
            llm_manager = get_llm_manager()
            provider, model = llm_manager.select_provider(
                task_complexity="medium",
                preferred_provider=None
            )

            if provider not in llm_manager.providers:
                raise ValueError("没有可用的 LLM 提供商")

            llm = llm_manager.providers[provider]

            from app.services.llm.base import LLMMessage, MessageRole
            response = await llm.chat(
                messages=[LLMMessage(role=MessageRole.USER, content=prompt)],
                model=model,
                temperature=0.3,  # 低温度，更确定性
                max_tokens=2000
            )

            # 解析 LLM 响应
            import json
            content = response.get("content", "")

            # 提取 JSON（可能被 markdown 包裹）
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            result = json.loads(content)
            keywords = result.get("keywords", [])

            # 合并 TF-IDF 的位置信息
            tfidf_map = {kw["text"]: kw for kw in tfidf_keywords}

            refined_keywords = []
            for kw in keywords:
                text_val = kw["text"]
                tfidf_data = tfidf_map.get(text_val, {})

                refined_keywords.append({
                    "text": text_val,
                    "category": kw.get("category"),
                    "weight": kw.get("importance", 0.8),
                    "frequency": tfidf_data.get("frequency", text[:1500].count(text_val)),
                    "positions": tfidf_data.get("positions", []),
                    "aliases": kw.get("aliases", []),
                    "description": kw.get("reason")
                })

            logger.info(f"LLM 精炼成功，提取 {len(refined_keywords)} 个关键词")
            return refined_keywords

        except Exception as e:
            logger.error(f"LLM 精炼失败: {e}")
            raise

    async def _save_keywords(
        self,
        keywords: List[Dict],
        document_id: int,
        project_id: int,
        method: str
    ) -> List[Dict[str, Any]]:
        """保存关键词到数据库"""

        saved_keywords = []

        for kw_data in keywords:
            text = kw_data["text"]
            category = kw_data.get("category")

            # 查找或创建关键词
            keyword = self.db.query(Keyword).filter(
                Keyword.text == text,
                Keyword.project_id == project_id
            ).first()

            if not keyword:
                # 创建新关键词
                keyword = Keyword(
                    text=text,
                    category=category,
                    project_id=project_id,
                    frequency=kw_data.get("frequency", 1),
                    weight=kw_data.get("weight", 0.5),
                    importance=kw_data.get("weight", 0.5),
                    aliases=kw_data.get("aliases"),
                    description=kw_data.get("description"),
                    first_seen_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow()
                )
                self.db.add(keyword)
                self.db.flush()
            else:
                # 更新统计
                keyword.frequency += kw_data.get("frequency", 1)
                keyword.last_seen_at = datetime.utcnow()

            # 创建文档-关键词关联（仅当 document_id 存在时）
            if document_id is not None:
                doc_keyword = DocumentKeyword(
                    document_id=document_id,
                    keyword_id=keyword.id,
                    positions=kw_data.get("positions", []),
                    frequency=kw_data.get("frequency", 1),
                    weight=kw_data.get("weight", 0.5),
                    extraction_method=method,
                    confidence=kw_data.get("confidence", 1.0)
                )
                self.db.add(doc_keyword)

            saved_keywords.append({
                "id": keyword.id,
                "text": keyword.text,
                "category": keyword.category,
                "frequency": kw_data.get("frequency"),
                "weight": kw_data.get("weight")
            })

        self.db.commit()
        logger.info(f"保存 {len(saved_keywords)} 个关键词")

        return saved_keywords

    async def analyze_keyword_relations(self, project_id: int, min_co_occurrence: int = 2):
        """
        分析关键词之间的关系
        用于生成知识脉络
        """
        logger.info(f"开始分析关键词关系: project_id={project_id}")

        # 获取项目的所有关键词
        keywords = self.db.query(Keyword).filter(
            Keyword.project_id == project_id
        ).all()

        # 统计共现
        from itertools import combinations

        co_occurrence_map = {}

        # 遍历每个文档，找共现关键词
        for kw in keywords:
            docs = self.db.query(DocumentKeyword).filter(
                DocumentKeyword.keyword_id == kw.id
            ).all()

            for doc in docs:
                # 找该文档的其他关键词
                other_keywords = self.db.query(DocumentKeyword).filter(
                    DocumentKeyword.document_id == doc.document_id,
                    DocumentKeyword.keyword_id != kw.id
                ).all()

                for other in other_keywords:
                    pair = tuple(sorted([kw.id, other.keyword_id]))
                    co_occurrence_map[pair] = co_occurrence_map.get(pair, 0) + 1

        # 保存关系
        for (kw1_id, kw2_id), count in co_occurrence_map.items():
            if count < min_co_occurrence:
                continue

            # 查找或创建关系
            relation = self.db.query(KeywordRelation).filter(
                KeywordRelation.keyword1_id == kw1_id,
                KeywordRelation.keyword2_id == kw2_id,
                KeywordRelation.project_id == project_id
            ).first()

            if not relation:
                relation = KeywordRelation(
                    keyword1_id=kw1_id,
                    keyword2_id=kw2_id,
                    project_id=project_id,
                    co_occurrence=count,
                    strength=min(count / 10.0, 1.0)  # 简单的强度计算
                )
                self.db.add(relation)
            else:
                relation.co_occurrence = count
                relation.strength = min(count / 10.0, 1.0)

        self.db.commit()
        logger.info(f"关键词关系分析完成")

    def get_project_keywords(
        self,
        project_id: int,
        category: Optional[str] = None,
        top_n: int = 50,
        sort_by: str = "frequency"
    ) -> List[Dict]:
        """获取项目关键词"""
        query = self.db.query(Keyword).filter(
            Keyword.project_id == project_id
        )

        if category:
            query = query.filter(Keyword.category == category)

        # 排序
        if sort_by == "frequency":
            query = query.order_by(Keyword.frequency.desc())
        elif sort_by == "importance":
            query = query.order_by(Keyword.importance.desc())
        elif sort_by == "recent":
            query = query.order_by(Keyword.last_seen_at.desc())

        keywords = query.limit(top_n).all()

        return [
            {
                "id": kw.id,
                "text": kw.text,
                "category": kw.category,
                "frequency": kw.frequency,
                "weight": kw.weight,
                "importance": kw.importance,
                "first_seen": kw.first_seen_at.isoformat() if kw.first_seen_at else None,
                "last_seen": kw.last_seen_at.isoformat() if kw.last_seen_at else None
            }
            for kw in keywords
        ]


from datetime import datetime
