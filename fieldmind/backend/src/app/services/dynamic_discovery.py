"""
动态发现引擎 - 破茧三刀核心实现
无预设词表、无固定分类、无模板框架
真正的自适应智能分析系统
"""

from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import re
import logging

# 轻量级NLP工具
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

logger = logging.getLogger(__name__)


class DynamicDiscoveryEngine:
    """
    动态发现引擎 - 三大核心能力：
    1. 无监督主题聚类（BERTopic）
    2. 通用实体识别+指称消歧
    3. 数据画像生成
    """

    def __init__(self, enable_ner: bool = False):
        """初始化轻量级模型（CPU可运行）

        Args:
            enable_ner: 是否启用HanLP实体识别（需下载468MB，默认关闭）
        """
        logger.info("🚀 初始化动态发现引擎（轻量模式）...")

        # 使用轻量级句子向量模型（本地已缓存）
        from app.services.semantic_embedding import get_embedding_model
        self.embedding_model = get_embedding_model()

        if self.embedding_model is None:
            logger.warning("⚠️ 动态发现引擎未加载到语义模型，将使用退化模式")

        # HDBSCAN聚类器（无需预设类别数）
        self.hdbscan_model = HDBSCAN(
            min_cluster_size=2,      # 最小聚类大小
            min_samples=1,           # 最小样本数
            metric='euclidean',
            cluster_selection_method='eom'
        )

        # BERTopic主题模型（c-TF-IDF轻量模式）
        self.topic_model = None  # 按需创建

        # HanLP通用NER（支持中英文）
        self.ner_model = None
        self.enable_ner = enable_ner
        self._init_ner()

        logger.info("✅ 动态发现引擎初始化完成")

    def _init_ner(self):
        """初始化HanLP通用NER（可选）"""
        # ⚠️ HanLP模型468MB，默认禁用，避免下载时间过长
        if not self.enable_ner:
            logger.info("⚠️ NER功能已禁用（避免下载大模型）")
            return

        try:
            import hanlp
            # 使用多任务模型（支持NER+词性标注+依存分析）
            self.ner_model = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)
            logger.info("✅ HanLP NER模型加载成功")
        except Exception as e:
            logger.warning(f"⚠️ HanLP加载失败，将使用备用NER: {e}")
            self.ner_model = None

    def discover_topics(
        self,
        texts: List[str],
        min_topic_size: int = 2
    ) -> Dict[str, Any]:
        """
        第一刀：无监督主题发现

        Args:
            texts: 文本列表（可以是文档切块）
            min_topic_size: 最小主题大小

        Returns:
            {
                "topics": [
                    {
                        "cluster_id": 0,
                        "auto_name": "草场纠纷",
                        "keywords": ["草场", "围栏", "越界"],
                        "doc_count": 15,
                        "representativeness": 0.85
                    }
                ],
                "outliers": [...],  # 未分类的文本
                "topic_distribution": {...}
            }
        """
        logger.info(f"🔍 开始无监督主题发现（文本数={len(texts)}）...")

        if len(texts) < 2:
            logger.warning("⚠️ 文本数量不足，跳过聚类")
            return {
                "topics": [],
                "outliers": texts,
                "topic_distribution": {}
            }

        # BERTopic 默认的 UMAP 邻居数和特征分解要求较大的样本量。
        # 单篇文档通常只有 2-4 个段落，强行聚类会触发 "k >= N" 异常；
        # 此时保留实体、关键词和画像，主题结果明确为空。
        if len(texts) < 5:
            logger.info("文本样本量过小（%s），跳过BERTopic聚类", len(texts))
            return {
                "topics": [],
                "outliers": texts,
                "topic_distribution": {},
                "model_meta": {
                    "total_docs": len(texts),
                    "clustered_docs": 0,
                    "cluster_rate": 0.0,
                    "skipped": True,
                    "reason": "insufficient_samples",
                },
            }

        try:
            # 1. 创建BERTopic模型（使用预训练embedding）
            vectorizer_model = CountVectorizer(
                ngram_range=(1, 2),
                stop_words=None,
                min_df=1
            )

            if self.embedding_model is None:
                raise RuntimeError("no embedding model available")

            self.topic_model = BERTopic(
                embedding_model=self.embedding_model,
                hdbscan_model=self.hdbscan_model,
                vectorizer_model=vectorizer_model,
                min_topic_size=min_topic_size,
                nr_topics='auto',
                calculate_probabilities=False,
                verbose=False
            )

            # 2. 拟合并预测主题
            topics, probs = self.topic_model.fit_transform(texts)

            # 3. 提取主题信息
            topic_info = self.topic_model.get_topic_info()

            discovered_topics = []
            topic_distribution = Counter(topics)

            for _, row in topic_info.iterrows():
                topic_id = row['Topic']

                # -1是离群点，跳过
                if topic_id == -1:
                    continue

                # 获取主题关键词
                topic_words = self.topic_model.get_topic(topic_id)
                if not topic_words:
                    continue

                keywords = [word for word, _ in topic_words[:10]]

                # 自动命名（取前3个关键词组合）
                auto_name = "-".join(keywords[:3])

                discovered_topics.append({
                    "cluster_id": int(topic_id),
                    "auto_name": auto_name,
                    "keywords": keywords,
                    "doc_count": int(topic_distribution.get(topic_id, 0)),
                    "representativeness": float(row.get('Count', 0)) / len(texts)
                })

            # 4. 统计离群点
            outlier_indices = [i for i, t in enumerate(topics) if t == -1]
            outliers = [texts[i] for i in outlier_indices]

            logger.info(f"✅ 发现 {len(discovered_topics)} 个主题，{len(outliers)} 个离群点")

            return {
                "topics": discovered_topics,
                "outliers": outliers,
                "topic_distribution": dict(topic_distribution),
                "model_meta": {
                    "total_docs": len(texts),
                    "clustered_docs": len(texts) - len(outliers),
                    "cluster_rate": (len(texts) - len(outliers)) / len(texts)
                }
            }

        except Exception as e:
            logger.error(f"❌ 主题发现失败: {e}", exc_info=True)
            return {
                "topics": [],
                "outliers": texts,
                "topic_distribution": {},
                "error": str(e)
            }

    def extract_and_merge_entities(
        self,
        texts: List[str],
        merge_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        第二刀：通用实体识别 + 指称消歧

        Args:
            texts: 文本列表
            merge_threshold: 向量相似度阈值（>此值则合并）

        Returns:
            [
                {
                    "canonical_name": "张建国",  # 规范名称
                    "aliases": ["张书记", "老张"],  # 别名
                    "entity_type": "PERSON",
                    "mention_count": 23,
                    "confidence": 0.92,
                    "contexts": [...]  # 上下文片段
                }
            ]
        """
        logger.info(f"🔍 开始通用实体识别+指称消歧（文本数={len(texts)}）...")

        # 1. 使用HanLP进行NER
        raw_entities = self._extract_raw_entities(texts)

        if not raw_entities:
            logger.warning("⚠️ 未提取到任何实体")
            return []

        # 2. 按类型分组
        entities_by_type = defaultdict(list)
        for entity in raw_entities:
            entities_by_type[entity['type']].append(entity)

        # 3. 对每种类型进行指称消歧
        merged_entities = []

        for entity_type, entities in entities_by_type.items():
            merged = self._merge_coreferences(entities, merge_threshold)
            merged_entities.extend(merged)

        # 4. 按mention_count排序
        merged_entities.sort(key=lambda x: x['mention_count'], reverse=True)

        logger.info(f"✅ 提取 {len(raw_entities)} 个原始实体，合并后 {len(merged_entities)} 个")

        return merged_entities

    def _extract_raw_entities(self, texts: List[str]) -> List[Dict[str, Any]]:
        """使用HanLP提取原始实体"""
        raw_entities = []

        if self.ner_model is None:
            # 备用方案：使用jieba+规则
            return self._fallback_ner(texts)

        try:
            for text_idx, text in enumerate(texts):
                if not text or len(text) < 5:
                    continue

                # HanLP多任务预测
                result = self.ner_model(text, tasks='ner')

                if 'ner' not in result:
                    continue

                ner_tags = result['ner']

                # 提取命名实体
                for entity_span in ner_tags:
                    entity_text = entity_span[0]
                    entity_label = entity_span[1]

                    # 映射HanLP标签到通用类型
                    entity_type = self._map_hanlp_label(entity_label)

                    if entity_type:
                        raw_entities.append({
                            "name": entity_text,
                            "type": entity_type,
                            "source_text_idx": text_idx,
                            "context": text[:100]  # 保留上下文
                        })

        except Exception as e:
            logger.error(f"❌ HanLP NER失败: {e}")
            return self._fallback_ner(texts)

        return raw_entities

    def _map_hanlp_label(self, label: str) -> str:
        """映射HanLP标签到通用类型"""
        label_map = {
            'PERSON': 'PERSON',
            'LOCATION': 'LOCATION',
            'GPE': 'LOCATION',
            'ORGANIZATION': 'ORGANIZATION',
            'ORG': 'ORGANIZATION',
            'FACILITY': 'LOCATION',
            'DATE': 'TEMPORAL',
            'TIME': 'TEMPORAL'
        }
        return label_map.get(label.upper(), None)

    def _fallback_ner(self, texts: List[str]) -> List[Dict[str, Any]]:
        """备用NER（使用jieba）"""
        import jieba.posseg as pseg

        raw_entities = []

        for text_idx, text in enumerate(texts):
            words = pseg.cut(text)

            for pair in words:
                word = pair.word
                flag = pair.flag
                entity_type = None

                if flag.startswith('nr'):
                    entity_type = 'PERSON'
                elif flag.startswith('ns'):
                    entity_type = 'LOCATION'
                elif flag.startswith('nt'):
                    entity_type = 'ORGANIZATION'

                if entity_type and len(word) >= 2:
                    raw_entities.append({
                        "name": word,
                        "type": entity_type,
                        "source_text_idx": text_idx,
                        "context": text[:100]
                    })

        return raw_entities

    def _merge_coreferences(
        self,
        entities: List[Dict],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """指称消歧：合并指向同一实体的不同表述"""
        if len(entities) <= 1:
            return [self._build_entity_record(entities)]

        # 1. 计算所有实体名的向量
        entity_names = [e['name'] for e in entities]
        embeddings = self.embedding_model.encode(entity_names, convert_to_numpy=True)

        # 2. 计算相似度矩阵
        from sklearn.metrics.pairwise import cosine_similarity
        sim_matrix = cosine_similarity(embeddings)

        # 3. 贪心合并
        merged_groups = []
        used = set()

        for i in range(len(entities)):
            if i in used:
                continue

            # 找到所有相似的实体
            group = [i]
            for j in range(i + 1, len(entities)):
                if j not in used and sim_matrix[i][j] >= threshold:
                    group.append(j)
                    used.add(j)

            used.add(i)

            # 构建合并记录
            group_entities = [entities[idx] for idx in group]
            merged_groups.append(self._build_entity_record(group_entities))

        return merged_groups

    def _build_entity_record(self, entities: List[Dict]) -> Dict[str, Any]:
        """构建合并后的实体记录"""
        if not entities:
            return {}

        # 选择最长的名称作为规范名
        canonical = max(entities, key=lambda e: len(e['name']))

        # 收集所有别名
        aliases = list(set([e['name'] for e in entities if e['name'] != canonical['name']]))

        # 收集上下文
        contexts = [e.get('context', '') for e in entities if e.get('context')]

        return {
            "canonical_name": canonical['name'],
            "aliases": aliases,
            "entity_type": canonical['type'],
            "mention_count": len(entities),
            "confidence": min(0.95, 0.6 + len(entities) * 0.05),  # 越多提及越可信
            "contexts": contexts[:5]  # 保留5个上下文
        }

    def generate_data_profile(
        self,
        texts: List[str],
        topics: List[Dict],
        entities: List[Dict]
    ) -> Dict[str, Any]:
        """
        第三刀：数据画像生成

        为动态报告生成提供输入

        Returns:
            {
                "content_overview": {...},
                "discovered_dimensions": [...],  # 发现的维度
                "key_entities": [...],
                "temporal_span": {...},
                "recommended_outline": [...]  # 推荐的报告大纲
            }
        """
        logger.info("🔍 生成数据画像...")

        # 1. 内容概览
        content_overview = {
            "total_texts": len(texts),
            "total_chars": sum(len(t) for t in texts),
            "avg_length": sum(len(t) for t in texts) / len(texts) if texts else 0,
            "topic_count": len(topics),
            "entity_count": len(entities)
        }

        # 2. 发现的维度（主题即维度）
        discovered_dimensions = []
        for topic in topics:
            discovered_dimensions.append({
                "dimension_name": topic['auto_name'],
                "keywords": topic['keywords'],
                "coverage": topic['doc_count'] / len(texts) if texts else 0,
                "priority": topic['representativeness']
            })

        # 按优先级排序
        discovered_dimensions.sort(key=lambda x: x['priority'], reverse=True)

        # 3. 关键实体（高频实体）
        key_entities = entities[:20]  # Top 20

        # 4. 时间跨度（简化版）
        temporal_span = self._extract_temporal_span(texts)

        # 5. 推荐大纲（基于发现的维度）
        recommended_outline = self._generate_outline(discovered_dimensions, key_entities)

        profile = {
            "content_overview": content_overview,
            "discovered_dimensions": discovered_dimensions,
            "key_entities": key_entities,
            "temporal_span": temporal_span,
            "recommended_outline": recommended_outline,
            "generated_at": datetime.now().isoformat()
        }

        logger.info(f"✅ 数据画像生成完成（维度数={len(discovered_dimensions)}）")

        return profile

    def _extract_temporal_span(self, texts: List[str]) -> Dict[str, Any]:
        """提取时间跨度"""
        # 简化实现：提取年份
        years = []
        year_pattern = r'(?:19|20)\d{2}年?'

        for text in texts:
            matches = re.findall(year_pattern, text)
            years.extend([int(re.sub(r"年$", "", m)) for m in matches])

        if not years:
            return {"has_temporal": False}

        return {
            "has_temporal": True,
            "earliest_year": min(years),
            "latest_year": max(years),
            "span_years": max(years) - min(years) + 1
        }

    def _generate_outline(
        self,
        dimensions: List[Dict],
        entities: List[Dict]
    ) -> List[Dict[str, str]]:
        """根据数据画像生成推荐大纲"""
        outline = []

        # 1. 概述章节（固定）
        outline.append({
            "chapter": "1. 概述",
            "reason": "总体情况介绍"
        })

        # 2. 按维度生成章节（数据驱动）
        for idx, dim in enumerate(dimensions[:5], start=2):  # 最多5个维度
            outline.append({
                "chapter": f"{idx}. {dim['dimension_name']}",
                "reason": f"覆盖{dim['coverage']:.1%}的内容，关键词：{', '.join(dim['keywords'][:3])}"
            })

        # 3. 关键人物章节（如果有高频人物）
        person_entities = [e for e in entities if e['entity_type'] == 'PERSON']
        if len(person_entities) >= 3:
            outline.append({
                "chapter": f"{len(outline)+1}. 关键人物",
                "reason": f"发现{len(person_entities)}个高频人物"
            })

        # 4. 总结章节（固定）
        outline.append({
            "chapter": f"{len(outline)+1}. 总结与展望",
            "reason": "归纳与建议"
        })

        return outline


# 导入datetime（上面用到了）
from datetime import datetime
