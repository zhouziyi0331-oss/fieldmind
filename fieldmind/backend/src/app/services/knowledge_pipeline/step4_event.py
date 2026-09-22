"""
Step 4: 事件提取服务
Event Extraction Service

功能：
1. 事件触发词检测（300+ 触发词）
2. 5W1H 结构化提取（Who, What, When, Where, Why, How）
3. 事件链构建（因果关系）
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""
    POLITICAL = "political"  # 政治事件
    MILITARY = "military"  # 军事事件
    ECONOMIC = "economic"  # 经济事件
    SOCIAL = "social"  # 社会事件
    CULTURAL = "cultural"  # 文化事件
    NATURAL = "natural"  # 自然事件
    ACCIDENT = "accident"  # 事故
    MEETING = "meeting"  # 会议
    TRANSACTION = "transaction"  # 交易
    OTHER = "other"  # 其他


@dataclass
class EventTrigger:
    """事件触发词"""
    word: str
    event_type: EventType
    position: int
    confidence: float = 1.0


@dataclass
class Event:
    """事件"""
    id: str
    type: EventType
    trigger: str  # 触发词

    # 5W1H
    who: List[str] = field(default_factory=list)  # 谁（参与者）
    what: str = ""  # 什么（事件描述）
    when: List[str] = field(default_factory=list)  # 何时
    where: List[str] = field(default_factory=list)  # 何地
    why: str = ""  # 为何（原因）
    how: str = ""  # 如何（方式）

    # 元数据
    position: int = 0
    sentence: str = ""  # 所在句子
    confidence: float = 1.0

    # 关联
    related_entities: List[str] = field(default_factory=list)  # 关联实体ID
    related_events: List[str] = field(default_factory=list)  # 关联事件ID


@dataclass
class EventChain:
    """事件链"""
    events: List[Event]
    relations: List[Dict[str, Any]] = field(default_factory=list)  # 事件间关系


class EventTriggerDetector:
    """事件触发词检测器"""

    def __init__(self):
        self.triggers = self._initialize_triggers()

    def _initialize_triggers(self) -> Dict[EventType, List[str]]:
        """初始化触发词库（300+ 触发词）"""
        triggers = {
            EventType.POLITICAL: [
                # 政治事件（50+ 触发词）
                '革命', '起义', '政变', '改革', '变法', '运动',
                '建国', '立国', '称帝', '登基', '退位', '禅让',
                '议会', '选举', '投票', '公投', '弹劾', '罢免',
                '签署', '废除', '颁布', '实施', '修订',
                '会谈', '谈判', '峰会', '访问', '出访',
                '联盟', '结盟', '缔约', '条约', '协定',
                '独立', '自治', '统一', '分裂', '合并',
                '抗议', '示威', '游行', '罢工', '罢课',
                '镇压', '逮捕', '释放', '赦免', '流放',
                '任命', '免职', '辞职', '就任', '卸任',
            ],
            EventType.MILITARY: [
                # 军事事件（40+ 触发词）
                '战争', '战役', '战斗', '交战', '作战',
                '进攻', '攻打', '攻击', '袭击', '突袭', '偷袭',
                '防守', '防御', '抵抗', '反击', '包围', '围攻',
                '占领', '攻克', '攻陷', '夺取', '收复',
                '撤退', '撤军', '溃败', '败退', '溃散',
                '停战', '休战', '和谈', '媾和', '投降', '受降',
                '征兵', '征召', '募兵', '扩军', '裁军',
                '阅兵', '演习', '军演', '操练', '训练',
                '轰炸', '炮击', '射击', '开火', '交火',
                '伏击', '埋伏', '截击', '拦截', '突围',
            ],
            EventType.ECONOMIC: [
                # 经济事件（35+ 触发词）
                '贸易', '交易', '买卖', '购买', '出售', '销售',
                '投资', '融资', '募资', '筹资', '集资',
                '上市', 'IPO', '发行', '增发', '配股',
                '收购', '并购', '兼并', '重组', '破产',
                '涨价', '降价', '调价', '提价', '减价',
                '增长', '下跌', '上涨', '暴跌', '大涨',
                '开业', '开张', '开工', '投产', '停产',
                '签约', '合同', '协议', '订单', '合作',
                '税收', '征税', '减税', '免税', '关税',
                '补贴', '资助', '援助', '贷款', '借款',
            ],
            EventType.SOCIAL: [
                # 社会事件（30+ 触发词）
                '出生', '诞生', '降生', '生育', '生子',
                '死亡', '去世', '逝世', '病逝', '辞世',
                '结婚', '成婚', '婚配', '联姻', '嫁娶',
                '离婚', '分居', '离异', '改嫁', '再婚',
                '迁徙', '迁移', '移居', '搬迁', '移民',
                '聚会', '聚集', '集会', '聚众', '聚拢',
                '庆祝', '庆典', '典礼', '仪式', '祭祀',
                '教育', '求学', '入学', '毕业', '肄业',
                '就业', '工作', '任职', '从业', '下岗',
                '退休', '退职', '退役', '隐退', '归隐',
            ],
            EventType.CULTURAL: [
                # 文化事件（25+ 触发词）
                '创作', '著作', '撰写', '编写', '作诗', '作词',
                '出版', '发表', '发行', '刊登', '刊行',
                '演出', '表演', '演奏', '演唱', '上演',
                '展览', '展出', '展示', '陈列', '巡展',
                '发明', '创造', '发现', '研究', '探索',
                '讲学', '讲座', '授课', '传授', '教学',
                '翻译', '译介', '编译', '转译', '口译',
                '修复', '修缮', '保护', '维护', '整修',
            ],
            EventType.NATURAL: [
                # 自然事件（25+ 触发词）
                '地震', '震动', '余震', '强震', '地动',
                '洪水', '水灾', '洪灾', '涨水', '泛滥',
                '干旱', '旱灾', '缺水', '久旱', '大旱',
                '台风', '飓风', '龙卷风', '风灾', '暴风',
                '火灾', '失火', '起火', '着火', '火烧',
                '海啸', '潮汐', '巨浪', '海浪', '波涛',
                '雪崩', '泥石流', '滑坡', '山崩', '塌方',
                '疫情', '瘟疫', '传染', '流行病', '大疫',
            ],
            EventType.ACCIDENT: [
                # 事故（20+ 触发词）
                '事故', '车祸', '撞车', '相撞', '碰撞',
                '爆炸', '炸毁', '爆破', '爆裂', '引爆',
                '坠毁', '坠落', '摔落', '掉落', '坠机',
                '沉没', '沉船', '翻船', '触礁', '搁浅',
                '泄漏', '泄露', '泄漏', '流出', '溢出',
                '中毒', '中暑', '窒息', '溺水', '触电',
            ],
            EventType.MEETING: [
                # 会议（15+ 触发词）
                '会议', '大会', '代表大会', '全会', '会晤',
                '峰会', '论坛', '研讨会', '座谈会', '讨论会',
                '听证会', '审议会', '表决', '通过', '否决',
            ],
            EventType.TRANSACTION: [
                # 交易（15+ 触发词）
                '交易', '成交', '买卖', '转让', '转手',
                '赠送', '赠予', '馈赠', '捐赠', '捐献',
                '借', '贷', '租', '赁', '租赁',
            ],
        }

        return triggers

    def detect(self, text: str) -> List[EventTrigger]:
        """检测事件触发词"""
        detected = []

        for event_type, trigger_words in self.triggers.items():
            for word in trigger_words:
                for match in re.finditer(re.escape(word), text):
                    detected.append(EventTrigger(
                        word=word,
                        event_type=event_type,
                        position=match.start(),
                        confidence=0.9
                    ))

        # 按位置排序
        detected.sort(key=lambda t: t.position)

        logger.info(f"✅ 检测到 {len(detected)} 个事件触发词")
        return detected


class FiveWOneHExtractor:
    """5W1H 提取器"""

    def extract(
        self,
        trigger: EventTrigger,
        text: str,
        entities: List[Any]
    ) -> Event:
        """提取 5W1H 信息"""
        # 获取触发词所在句子
        sentence = self._extract_sentence(text, trigger.position)

        event = Event(
            id=f"event_{trigger.position}",
            type=trigger.event_type,
            trigger=trigger.word,
            position=trigger.position,
            sentence=sentence
        )

        # 提取 Who（从实体中查找）
        event.who = self._extract_who(sentence, entities)

        # 提取 What
        event.what = self._extract_what(sentence, trigger.word)

        # 提取 When
        event.when = self._extract_when(sentence, entities)

        # 提取 Where
        event.where = self._extract_where(sentence, entities)

        # 提取 Why
        event.why = self._extract_why(sentence, text, trigger.position)

        # 提取 How
        event.how = self._extract_how(sentence)

        return event

    def _extract_sentence(self, text: str, position: int) -> str:
        """提取触发词所在句子"""
        # 向前查找句子开始
        start = position
        while start > 0:
            if text[start] in ['。', '！', '？', '\n']:
                start += 1
                break
            start -= 1

        # 向后查找句子结束
        end = position
        while end < len(text):
            if text[end] in ['。', '！', '？', '\n']:
                end += 1
                break
            end += 1

        return text[start:end].strip()

    def _extract_who(self, sentence: str, entities: List[Any]) -> List[str]:
        """提取 Who（参与者）"""
        participants = []

        # 从实体中查找人物和组织
        for entity in entities:
            if hasattr(entity, 'type') and entity.type.value in ['person', 'organization']:
                if hasattr(entity, 'name') and entity.name in sentence:
                    participants.append(entity.name)

        return participants

    def _extract_what(self, sentence: str, trigger: str) -> str:
        """提取 What（事件描述）"""
        # 简化版：返回整个句子
        return sentence

    def _extract_when(self, sentence: str, entities: List[Any]) -> List[str]:
        """提取 When（时间）"""
        time_refs = []

        # 从实体中查找时间
        for entity in entities:
            if hasattr(entity, 'type') and entity.type.value == 'time':
                if hasattr(entity, 'name') and entity.name in sentence:
                    time_refs.append(entity.name)

        return time_refs

    def _extract_where(self, sentence: str, entities: List[Any]) -> List[str]:
        """提取 Where（地点）"""
        locations = []

        # 从实体中查找地点
        for entity in entities:
            if hasattr(entity, 'type') and entity.type.value == 'location':
                if hasattr(entity, 'name') and entity.name in sentence:
                    locations.append(entity.name)

        return locations

    def _extract_why(self, sentence: str, full_text: str, position: int) -> str:
        """提取 Why（原因）"""
        # 查找因果关系词
        cause_patterns = [
            r'因为(.{5,50})',
            r'由于(.{5,50})',
            r'因(.{5,50})',
            r'缘于(.{5,50})',
        ]

        # 在句子和前文中查找
        search_start = max(0, position - 200)
        search_text = full_text[search_start:position + 100]

        for pattern in cause_patterns:
            match = re.search(pattern, search_text)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_how(self, sentence: str) -> str:
        """提取 How（方式）"""
        # 查找方式状语
        how_patterns = [
            r'通过(.{5,30})',
            r'采用(.{5,30})',
            r'使用(.{5,30})',
            r'运用(.{5,30})',
            r'以(.{5,30})方式',
        ]

        for pattern in how_patterns:
            match = re.search(pattern, sentence)
            if match:
                return match.group(1).strip()

        return ""


class EventChainBuilder:
    """事件链构建器"""

    def build(self, events: List[Event], text: str) -> EventChain:
        """构建事件链"""
        chain = EventChain(events=events)

        # 检测事件间关系
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events):
                if i >= j:
                    continue

                # 检测因果关系
                relation = self._detect_relation(event1, event2, text)
                if relation:
                    chain.relations.append(relation)

        logger.info(f"✅ 构建事件链：{len(events)} 个事件，{len(chain.relations)} 个关系")
        return chain

    def _detect_relation(
        self,
        event1: Event,
        event2: Event,
        text: str
    ) -> Optional[Dict[str, Any]]:
        """检测事件间关系"""
        # 时间顺序
        if event1.position < event2.position:
            # 检测因果关系标记
            between_text = text[event1.position:event2.position]

            causal_markers = ['因此', '所以', '导致', '引发', '造成', '结果', '从而', '于是']
            for marker in causal_markers:
                if marker in between_text:
                    return {
                        'from': event1.id,
                        'to': event2.id,
                        'type': 'cause',
                        'marker': marker,
                        'confidence': 0.8
                    }

            # 时间顺序
            if event2.position - event1.position < 500:  # 距离较近
                return {
                    'from': event1.id,
                    'to': event2.id,
                    'type': 'temporal',
                    'confidence': 0.6
                }

        return None


class EventExtractionService:
    """事件提取服务"""

    def __init__(self):
        self.trigger_detector = EventTriggerDetector()
        self.extractor = FiveWOneHExtractor()
        self.chain_builder = EventChainBuilder()

    async def extract(
        self,
        text: str,
        entities: List[Any]
    ) -> Dict[str, Any]:
        """
        事件提取

        Args:
            text: 清洗后的文本
            entities: 实体列表

        Returns:
            事件提取结果
        """
        logger.info(f"开始事件提取")

        # 1. 检测事件触发词
        triggers = await asyncio.to_thread(self.trigger_detector.detect, text)
        logger.info(f"✅ 触发词检测：{len(triggers)} 个")

        # 2. 提取 5W1H（并行）
        tasks = [
            asyncio.to_thread(self.extractor.extract, trigger, text, entities)
            for trigger in triggers[:100]  # 限制数量
        ]
        events = await asyncio.gather(*tasks)
        logger.info(f"✅ 5W1H 提取：{len(events)} 个事件")

        # 3. 构建事件链
        event_chain = await asyncio.to_thread(self.chain_builder.build, events, text)
        logger.info(f"✅ 事件链构建完成")

        # 统计
        statistics = self._calculate_statistics(events, event_chain)

        result = {
            'events': events,
            'event_chain': event_chain,
            'statistics': statistics
        }

        logger.info(f"✅ 事件提取完成：{len(events)} 个事件")
        return result

    def _calculate_statistics(
        self,
        events: List[Event],
        chain: EventChain
    ) -> Dict[str, Any]:
        """计算统计信息"""
        type_counts = defaultdict(int)
        for event in events:
            type_counts[event.type.value] += 1

        # 统计 5W1H 完整度
        complete_5w1h = sum(
            1 for e in events
            if e.who and e.what and e.when and e.where
        )

        return {
            'total_events': len(events),
            'event_by_type': dict(type_counts),
            'causal_relations': len([r for r in chain.relations if r['type'] == 'cause']),
            'temporal_relations': len([r for r in chain.relations if r['type'] == 'temporal']),
            'complete_5w1h_ratio': complete_5w1h / len(events) if events else 0,
            'avg_participants': sum(len(e.who) for e in events) / len(events) if events else 0,
        }
