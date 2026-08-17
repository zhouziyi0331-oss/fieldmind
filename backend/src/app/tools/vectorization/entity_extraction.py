"""实体提取服务 - 使用jieba.posseg进行中文NER"""
import jieba.posseg as pseg
import re
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict

# 实体类型映射
ENTITY_TYPE_MAP = {
    'nr': 'person',      # 人名
    'ns': 'location',    # 地名
    'nt': 'organization',  # 机构名
    'nz': 'custom',      # 其他专名
    't': 'time',         # 时间词
}

# 时间关键词（这些词不作为独立实体）
TIME_KEYWORDS = ['年', '月', '日', '时', '分', '秒', '世纪', '年代', '现在', '过去', '将来',
                 '时候', '时间', '年轻', '下来', '同时', '现代', '当时']


class EntityExtractionService:
    """实体提取服务"""

    def __init__(self):
        """初始化jieba分词器"""
        import jieba
        # 添加田野调查领域词典
        self._add_custom_words()

    def _add_custom_words(self):
        """添加自定义词典（田野调查常见实体）"""
        import jieba
        custom_words = [
            ('费孝通', 10, 'nr'),
            ('十八洞村', 10, 'ns'),
            ('湘西', 8, 'ns'),
            ('苗族', 8, 'nz'),
            ('侗族', 8, 'nz'),
            ('布依族', 8, 'nz'),
            ('非物质文化遗产', 10, 'nz'),
            ('精准扶贫', 10, 'nz'),
            # 食物相关（使用nz标记为专有名词）
            ('杀猪菜', 10, 'nz'),
            ('腊肉', 8, 'nz'),
            ('酸汤鱼', 8, 'nz'),
            ('糯米饭', 8, 'nz'),
            # 建筑相关
            ('祠堂', 10, 'nz'),
            ('吊脚楼', 10, 'nz'),
            ('鼓楼', 8, 'nz'),
            ('风雨桥', 8, 'nz'),
            # 文化相关
            ('芦笙', 8, 'nz'),
            ('侗歌', 8, 'nz'),
            ('苗歌', 8, 'nz'),
        ]
        for word, freq, tag in custom_words:
            jieba.add_word(word, freq, tag)

    def extract_entities(self, text: str, min_confidence: float = 0.5) -> List[Dict]:
        """
        从文本中提取实体

        Args:
            text: 输入文本
            min_confidence: 最低置信度阈值

        Returns:
            实体列表 [{"type": "person", "name": "张三", "confidence": 0.95, "positions": [(10, 12)]}]
        """
        if not text or not text.strip():
            return []

        # 使用jieba进行词性标注
        words = list(pseg.cut(text))  # 转换为列表

        # 收集实体
        entities_dict = defaultdict(lambda: {"positions": [], "count": 0})

        position = 0
        for item in words:
            word = item.word
            flag = item.flag
            word_len = len(word)

            # 根据词性判断实体类型
            if flag in ENTITY_TYPE_MAP:
                entity_type = ENTITY_TYPE_MAP[flag]

                # 跳过通用时间词（如"现在"、"时候"等）
                if entity_type == 'time' and word in TIME_KEYWORDS:
                    position += word_len
                    continue

                key = (word, entity_type)
                entities_dict[key]["positions"].append((position, position + word_len))
                entities_dict[key]["count"] += 1

            # 特殊处理：具体时间表达式（但排除通用时间词）
            elif any(kw in word for kw in ['年', '月', '日']) and word not in TIME_KEYWORDS:
                key = (word, 'time')
                entities_dict[key]["positions"].append((position, position + word_len))
                entities_dict[key]["count"] += 1

            position += word_len

        # 转换为标准格式
        result = []
        for (name, entity_type), data in entities_dict.items():
            # 计算置信度（基于出现次数和名称长度）
            confidence = min(0.6 + data["count"] * 0.1 + len(name) * 0.05, 1.0)

            if confidence >= min_confidence:
                result.append({
                    "type": entity_type,
                    "name": name,
                    "confidence": round(confidence, 2),
                    "mention_count": data["count"],
                    "positions": data["positions"][:5]  # 只保留前5个位置
                })

        # 按置信度排序
        result.sort(key=lambda x: x["confidence"], reverse=True)
        return result

    def extract_time_expressions(self, text: str) -> List[Dict]:
        """
        提取时间表达式并尝试解析为标准日期

        Returns:
            时间表达式列表 [{"raw": "2020年3月", "parsed": datetime(...), "confidence": 0.9}]
        """
        if not text or not text.strip():
            return []

        time_patterns = [
            # YYYY年MM月DD日
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # YYYY年MM月
            (r'(\d{4})年(\d{1,2})月', lambda m: datetime(int(m.group(1)), int(m.group(2)), 1)),
            # YYYY年
            (r'(\d{4})年', lambda m: datetime(int(m.group(1)), 1, 1)),
            # YYYY-MM-DD
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        ]

        results = []
        for pattern, parser in time_patterns:
            for match in re.finditer(pattern, text):
                try:
                    parsed_date = parser(match)
                    results.append({
                        "raw": match.group(0),
                        "parsed": parsed_date,
                        "confidence": 0.95,
                        "position": (match.start(), match.end())
                    })
                except (ValueError, IndexError):
                    # 解析失败，跳过
                    continue

        return results

    def extract_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """
        提取实体间的关系（简单规则）

        Args:
            entities: 已提取的实体列表
            text: 原文本

        Returns:
            关系列表 [{"from": "张三", "to": "十八洞村", "type": "visited", "confidence": 0.7}]
        """
        # 关系关键词
        relation_keywords = {
            '住在': 'lives_in',
            '来自': 'from',
            '属于': 'belongs_to',
            '前往': 'visited',
            '调查': 'investigated',
            '研究': 'studied',
            '发现': 'discovered',
            '建立': 'established',
        }

        relationships = []

        # 简单规则：在同一句话中出现的实体可能有关系
        sentences = re.split(r'[。！？\n]', text)

        for sentence in sentences:
            # 找出句子中的实体
            sentence_entities = []
            for entity in entities:
                if entity['name'] in sentence:
                    sentence_entities.append(entity)

            # 如果有2个或更多实体，检查是否有关系关键词
            if len(sentence_entities) >= 2:
                for keyword, rel_type in relation_keywords.items():
                    if keyword in sentence:
                        # 简单假设：关键词前的实体是主体，后的是客体
                        kw_pos = sentence.index(keyword)
                        before_entities = [e for e in sentence_entities if sentence.index(e['name']) < kw_pos]
                        after_entities = [e for e in sentence_entities if sentence.index(e['name']) > kw_pos]

                        if before_entities and after_entities:
                            relationships.append({
                                "from": before_entities[-1]['name'],
                                "from_type": before_entities[-1]['type'],
                                "to": after_entities[0]['name'],
                                "to_type": after_entities[0]['type'],
                                "type": rel_type,
                                "confidence": 0.6,
                                "context": sentence[:100]
                            })

        return relationships


# 全局单例
_entity_extraction_service = None

def get_entity_extraction_service() -> EntityExtractionService:
    """获取实体提取服务单例"""
    global _entity_extraction_service
    if _entity_extraction_service is None:
        _entity_extraction_service = EntityExtractionService()
    return _entity_extraction_service
