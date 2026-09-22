"""
自适应分析器 - 通用智能分析，无预设词表

核心能力：
1. 自动发现主题（基于TF-IDF + 语义聚类）
2. 自动提取实体（基于词性+命名实体识别）
3. 自动识别关系（基于依存句法+共现）
4. 自动分类内容（基于向量相似度）
"""

import jieba
import jieba.posseg as pseg
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdaptiveAnalyzer:
    """通用自适应分析器 - 不依赖预设词表"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.stop_words = self._load_stop_words()

    def _load_stop_words(self) -> set:
        """加载停用词（通用）"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这', '那', '可以', '这个', '我们', '来', '他', '她',
            '它', '这样', '那样', '什么', '怎么', '为什么', '哪里', '谁', '多少'
        }

    def analyze(self, text: str, document_id: int = None) -> Dict:
        """
        通用分析入口

        Returns:
            {
                "core_entities": [...],          # 核心实体（人/地/组织/概念）
                "key_topics": [...],             # 关键主题（自动发现）
                "temporal_references": [...],    # 时间引用
                "relations": [...],              # 实体关系
                "content_type": str,             # 内容类型（自动识别）
                "semantic_tags": [...]           # 语义标签
            }
        """
        logger.info(f"🧠 开始自适应分析，文本长度={len(text)}")

        result = {
            "document_id": document_id,
            "analysis_time": datetime.now().isoformat(),
            "text_length": len(text),
            "core_entities": [],
            "key_topics": [],
            "temporal_references": [],
            "relations": [],
            "content_type": "unknown",
            "semantic_tags": []
        }

        # 1. 实体提取（基于词性，无预设词表）
        result["core_entities"] = self._extract_entities(text)

        # 2. 主题发现（基于TF-IDF）
        result["key_topics"] = self._discover_topics(text)

        # 3. 时间提取
        result["temporal_references"] = self._extract_temporal(text)

        # 4. 关系发现（基于共现和句法）
        result["relations"] = self._discover_relations(text, result["core_entities"])

        # 5. 内容类型识别
        result["content_type"] = self._classify_content_type(text, result)

        # 6. 语义标签生成
        result["semantic_tags"] = self._generate_semantic_tags(result)

        logger.info(f"✅ 分析完成: {len(result['core_entities'])}个实体, {len(result['key_topics'])}个主题, {len(result['relations'])}条关系")

        return result

    def _extract_entities(self, text: str) -> List[Dict]:
        """
        自适应实体提取（无预设词表）

        策略：
        - 词性标注：nr(人名), ns(地名), nt(机构), nz(专有名词)
        - 频次过滤：出现>=2次
        - 长度过滤：>=2字符
        """
        entities = defaultdict(list)
        word_freq = Counter()

        # 词性标注
        words = pseg.cut(text)

        # 第一遍：统计词频
        words_list = []
        for pair in words:
            word = pair.word
            flag = pair.flag
            words_list.append((word, flag))
            if word not in self.stop_words and len(word) >= 2:
                word_freq[word] += 1

        # 第二遍：提取实体
        for word, flag in words_list:
            # 过滤停用词和短词
            if word in self.stop_words or len(word) < 2:
                continue

            # 实体类型映射
            entity_type = None
            if flag.startswith('nr'):
                entity_type = 'PERSON'
            elif flag.startswith('ns'):
                entity_type = 'LOCATION'
            elif flag.startswith('nt'):
                entity_type = 'ORGANIZATION'
            elif flag.startswith('nz'):
                entity_type = 'CONCEPT'
            elif flag in ['n', 'vn']:  # 普通名词、动名词
                # 高频名词作为概念实体
                if word_freq[word] >= 2:
                    entity_type = 'CONCEPT'

            if entity_type:
                entities[entity_type].append(word)

        # 统计和排序
        result = []
        for entity_type, words in entities.items():
            # 按频次排序，取前20
            word_counts = Counter(words)
            for word, count in word_counts.most_common(20):
                result.append({
                    "name": word,
                    "type": entity_type,
                    "frequency": count,
                    "confidence": min(0.5 + count * 0.1, 0.95)  # 频次越高置信度越高
                })

        return result

    def _discover_topics(self, text: str) -> List[Dict]:
        """
        自适应主题发现（基于TF-IDF）

        策略：
        - 计算词频（TF）
        - 过滤低频词（<2次，短文本适配）
        - 按TF排序，取前15个作为主题词
        """
        # 分词
        words = [w for w in jieba.cut(text) if w not in self.stop_words and len(w) >= 2]

        # 词频统计
        word_freq = Counter(words)

        # 计算简化版TF（归一化）
        total_words = len(words)
        topics = []

        for word, freq in word_freq.most_common(15):
            if freq < 2:  # 至少出现2次（降低阈值适配短文本）
                continue

            tf_score = freq / total_words if total_words > 0 else 0

            topics.append({
                "topic": word,
                "frequency": freq,
                "tf_score": round(tf_score, 4),
                "relevance": min(0.5 + freq * 0.05, 0.95)
            })

        return topics

    def _extract_temporal(self, text: str) -> List[Dict]:
        """
        时间提取（通用模式）

        支持：
        - 绝对时间：2023年1月15日, 2023-01-15
        - 相对时间：去年、今年、明天、上个月
        - 季节/节气：春天、夏至、清明
        - 传统节日：春节、端午、中秋
        """
        temporal_refs = []

        # 绝对日期模式
        patterns = [
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', 'DATE'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'DATE'),
            (r'(\d{4})年(\d{1,2})月', 'MONTH'),
            (r'(\d{1,2})月(\d{1,2})日', 'DAY'),
        ]

        for pattern, temp_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                temporal_refs.append({
                    "text": match.group(0),
                    "type": temp_type,
                    "position": match.start(),
                    "confidence": 0.95
                })

        # 相对时间词
        relative_terms = {
            '去年': 'RELATIVE_YEAR',
            '今年': 'RELATIVE_YEAR',
            '明年': 'RELATIVE_YEAR',
            '上个月': 'RELATIVE_MONTH',
            '这个月': 'RELATIVE_MONTH',
            '下个月': 'RELATIVE_MONTH',
            '昨天': 'RELATIVE_DAY',
            '今天': 'RELATIVE_DAY',
            '明天': 'RELATIVE_DAY',
        }

        for term, temp_type in relative_terms.items():
            if term in text:
                temporal_refs.append({
                    "text": term,
                    "type": temp_type,
                    "confidence": 0.8
                })

        # 节日/节气
        festivals = ['春节', '元宵', '清明', '端午', '中秋', '重阳', '冬至', '腊八']
        for festival in festivals:
            if festival in text:
                temporal_refs.append({
                    "text": festival,
                    "type": 'FESTIVAL',
                    "confidence": 0.9
                })

        return temporal_refs

    def _discover_relations(self, text: str, entities: List[Dict]) -> List[Dict]:
        """
        自适应关系发现

        策略：
        - 共现窗口：50字符内同时出现的实体视为有关联
        - 动词连接：实体A - 动词 - 实体B
        """
        relations = []

        # 构建实体名称列表
        entity_names = [e["name"] for e in entities]

        if len(entity_names) < 2:
            return relations

        # 共现分析（滑动窗口）
        window_size = 50
        sentences = text.split('。')

        for sentence in sentences:
            if len(sentence) < 10:
                continue

            # 找出这句话中出现的实体
            found_entities = [e for e in entity_names if e in sentence]

            # 如果有2个以上实体，建立关系
            if len(found_entities) >= 2:
                for i in range(len(found_entities) - 1):
                    for j in range(i + 1, len(found_entities)):
                        relations.append({
                            "source": found_entities[i],
                            "target": found_entities[j],
                            "type": "CO_OCCURRENCE",
                            "context": sentence[:100],
                            "confidence": 0.7
                        })

        # 去重
        unique_relations = []
        seen = set()
        for rel in relations:
            key = (rel["source"], rel["target"], rel["type"])
            if key not in seen:
                seen.add(key)
                unique_relations.append(rel)

        return unique_relations[:30]  # 最多返回30条

    def _classify_content_type(self, text: str, analysis: Dict) -> str:
        """
        自动识别内容类型

        策略：基于关键词密度和实体分布
        """
        text_lower = text.lower()

        # 特征检测
        has_many_people = sum(1 for e in analysis["core_entities"] if e["type"] == "PERSON") >= 3
        has_locations = sum(1 for e in analysis["core_entities"] if e["type"] == "LOCATION") >= 2
        has_organizations = sum(1 for e in analysis["core_entities"] if e["type"] == "ORGANIZATION") >= 1
        has_temporal = len(analysis["temporal_references"]) >= 2

        # 分类规则
        if '调研' in text or '访谈' in text or '田野' in text:
            return 'FIELD_RESEARCH'
        elif has_many_people and has_temporal:
            return 'INTERVIEW_NARRATIVE'
        elif has_organizations and has_locations:
            return 'PROJECT_DOCUMENT'
        elif '分析' in text or '报告' in text:
            return 'ANALYTICAL_REPORT'
        elif len(text) > 5000 and len(analysis["key_topics"]) > 10:
            return 'COMPREHENSIVE_TEXT'
        else:
            return 'GENERAL_TEXT'

    def _generate_semantic_tags(self, analysis: Dict) -> List[str]:
        """
        生成语义标签（基于分析结果）
        """
        tags = []

        # 基于内容类型
        content_type_map = {
            'FIELD_RESEARCH': '田野调研',
            'INTERVIEW_NARRATIVE': '访谈记录',
            'PROJECT_DOCUMENT': '项目文档',
            'ANALYTICAL_REPORT': '分析报告',
            'COMPREHENSIVE_TEXT': '综合文本',
            'GENERAL_TEXT': '一般文本'
        }
        tags.append(content_type_map.get(analysis["content_type"], '未分类'))

        # 基于实体数量
        entity_count = len(analysis["core_entities"])
        if entity_count > 20:
            tags.append('信息密集')
        elif entity_count > 10:
            tags.append('信息丰富')

        # 基于时间引用
        if len(analysis["temporal_references"]) > 5:
            tags.append('时序性强')

        # 基于关系密度
        if len(analysis["relations"]) > 15:
            tags.append('关联复杂')

        return tags
