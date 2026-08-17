"""
结构化数据抽取服务
从非结构化文本中自动提取时间、事件、关系等结构化信息
"""
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import jieba
import jieba.posseg as pseg


class TemporalExtractor:
    """时间抽取器"""

    # 完整日期格式
    DATE_PATTERNS = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2023年1月15日
        r'(\d{4})-(\d{1,2})-(\d{1,2})',      # 2023-01-15
        r'(\d{4})/(\d{1,2})/(\d{1,2})',      # 2023/01/15
        r'(\d{1,2})月(\d{1,2})日',            # 1月15日
    ]

    # 模糊时间词
    FUZZY_TEMPORAL = {
        '去年': -365,
        '前年': -730,
        '今年': 0,
        '明年': 365,
        '上个月': -30,
        '这个月': 0,
        '下个月': 30,
        '昨天': -1,
        '今天': 0,
        '明天': 1,
        '前天': -2,
        '后天': 2,
    }

    # 中国传统节日/节气
    TRADITIONAL_DATES = {
        '春节': (1, 1),
        '元宵': (1, 15),
        '清明': (4, 5),
        '端午': (5, 5),
        '中秋': (8, 15),
        '重阳': (9, 9),
        '冬至': (12, 22),
        '腊八': (12, 8),
        '除夕': (12, 30),
        '正月': (1, 1),
    }

    @classmethod
    def extract(cls, text: str, reference_date: Optional[datetime] = None) -> List[Dict]:
        """
        从文本中提取时间信息

        返回格式:
        [
            {
                'raw_text': '2023年1月15日',
                'normalized_date': '2023-01-15',
                'type': 'absolute',  # absolute/relative/fuzzy/traditional
                'confidence': 0.95
            }
        ]
        """
        if not reference_date:
            reference_date = datetime.now()

        results = []

        # 1. 提取完整日期
        for pattern in cls.DATE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # 有年份
                            year, month, day = map(int, groups)
                            normalized = f"{year:04d}-{month:02d}-{day:02d}"
                        else:  # 没有年份，补充当前年
                            month, day = map(int, groups[:2])
                            normalized = f"{reference_date.year:04d}-{month:02d}-{day:02d}"

                        results.append({
                            'raw_text': match.group(0),
                            'normalized_date': normalized,
                            'type': 'absolute',
                            'confidence': 0.95,
                            'position': match.start()
                        })
                except (ValueError, IndexError):
                    continue

        # 2. 提取模糊时间
        for fuzzy_word, days_offset in cls.FUZZY_TEMPORAL.items():
            if fuzzy_word in text:
                target_date = reference_date + datetime.timedelta(days=days_offset)
                results.append({
                    'raw_text': fuzzy_word,
                    'normalized_date': target_date.strftime('%Y-%m-%d'),
                    'type': 'relative',
                    'confidence': 0.75,
                    'position': text.index(fuzzy_word)
                })

        # 3. 提取传统节日
        for festival, (month, day) in cls.TRADITIONAL_DATES.items():
            if festival in text:
                # 农历转公历需要专门库，这里简化为标记
                results.append({
                    'raw_text': festival,
                    'normalized_date': f"{reference_date.year:04d}-{month:02d}-{day:02d}",
                    'type': 'traditional',
                    'confidence': 0.60,  # 农历转换不精确
                    'position': text.index(festival),
                    'note': '农历日期，需人工核对'
                })

        # 按出现位置排序
        results.sort(key=lambda x: x['position'])

        return results


class EventExtractor:
    """事件抽取器"""

    # 常见动作词库（田野调查场景）
    ACTION_VERBS = {
        '召开', '举行', '举办', '组织', '参加', '出席',
        '调解', '处理', '解决', '商议', '讨论', '协商',
        '选举', '任命', '罢免', '推选', '投票',
        '修建', '建设', '拆除', '改造', '维修',
        '祭祀', '祭拜', '祈福', '供奉', '纪念',
        '迁移', '搬迁', '回归', '离开', '前往',
        '签订', '订立', '废除', '修改', '执行',
        '分配', '分发', '收取', '缴纳', '发放',
        '培训', '学习', '教育', '指导', '传授',
        '调查', '访谈', '记录', '统计', '测量',
    }

    @classmethod
    def extract(cls, text: str) -> List[Dict]:
        """
        从文本中提取事件三元组 (主语, 动词, 宾语)

        返回格式:
        [
            {
                'subject': '老王',
                'predicate': '调解',
                'object': '纠纷',
                'event_summary': '老王调解纠纷',
                'confidence': 0.85,
                'context': '原文片段...'
            }
        ]
        """
        results = []
        words = pseg.cut(text)
        words_list = list(words)

        for i, (word, flag) in enumerate(words_list):
            # 如果当前词是动作动词
            if word in cls.ACTION_VERBS:
                subject = None
                obj = None

                # 向前找主语（人名、机构名）
                for j in range(max(0, i - 5), i):
                    prev_word, prev_flag = words_list[j]
                    if prev_flag in ['nr', 'nt', 'ns']:  # 人名、机构、地名
                        subject = prev_word
                        break

                # 向后找宾语（名词）
                for j in range(i + 1, min(len(words_list), i + 6)):
                    next_word, next_flag = words_list[j]
                    if next_flag in ['n', 'nr', 'nt', 'ns', 'nz']:  # 各类名词
                        obj = next_word
                        break

                # 如果找到完整的三元组
                if subject or obj:
                    event_summary = f"{subject or '(未知)'}{word}{obj or '(未知)'}"
                    results.append({
                        'subject': subject,
                        'predicate': word,
                        'object': obj,
                        'event_summary': event_summary,
                        'confidence': 0.85 if (subject and obj) else 0.60,
                        'context': text[max(0, i*2-20):min(len(text), i*2+50)]  # 上下文
                    })

        return results


class RelationExtractor:
    """关系抽取器"""

    @classmethod
    def extract_co_occurrence(cls, text: str, window_size: int = 50) -> List[Dict]:
        """
        提取共现关系：在同一段落中同时出现的实体对

        返回格式:
        [
            {
                'entity1': '老王',
                'entity1_type': 'person',
                'entity2': '村委会',
                'entity2_type': 'organization',
                'relation_type': 'MENTIONED_TOGETHER',
                'confidence': 0.70,
                'context': '原文片段...'
            }
        ]
        """
        results = []
        words = pseg.cut(text)
        words_list = list(words)

        entities = []
        for i, (word, flag) in enumerate(words_list):
            if flag in ['nr', 'nt', 'ns', 'nz']:  # 人名、机构、地名、专有名词
                entity_type = {
                    'nr': 'person',
                    'nt': 'organization',
                    'ns': 'location',
                    'nz': 'concept'
                }.get(flag, 'unknown')

                entities.append({
                    'text': word,
                    'type': entity_type,
                    'position': i
                })

        # 寻找距离在window_size内的实体对
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                if abs(e2['position'] - e1['position']) <= window_size:
                    # 计算上下文范围
                    start_pos = max(0, e1['position'] * 2 - 20)
                    end_pos = min(len(text), e2['position'] * 2 + 20)

                    results.append({
                        'entity1': e1['text'],
                        'entity1_type': e1['type'],
                        'entity2': e2['text'],
                        'entity2_type': e2['type'],
                        'relation_type': 'MENTIONED_TOGETHER',
                        'confidence': 0.70,
                        'context': text[start_pos:end_pos],
                        'distance': e2['position'] - e1['position']
                    })

        return results


class StructuredExtractor:
    """统一的结构化抽取接口"""

    def __init__(self):
        self.temporal = TemporalExtractor()
        self.event = EventExtractor()
        self.relation = RelationExtractor()

    def extract_all(self, text: str, reference_date: Optional[datetime] = None) -> Dict:
        """
        一次性提取所有结构化信息

        返回:
        {
            'dates': [...],
            'events': [...],
            'relations': [...]
        }
        """
        return {
            'dates': self.temporal.extract(text, reference_date),
            'events': self.event.extract(text),
            'relations': self.relation.extract_co_occurrence(text)
        }


# 单例
structured_extractor = StructuredExtractor()
