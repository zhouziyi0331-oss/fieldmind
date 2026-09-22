"""
Step 3: 实体构建服务
Entity Construction Service

功能：
1. 命名实体识别（NER）- 人物、地点、组织、时间、事件
2. 实体消歧（Disambiguation）
3. 共指解析（Coreference Resolution）
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """实体类型"""
    PERSON = "person"  # 人物
    LOCATION = "location"  # 地点
    ORGANIZATION = "organization"  # 组织
    TIME = "time"  # 时间
    EVENT = "event"  # 事件
    OBJECT = "object"  # 物品
    CONCEPT = "concept"  # 概念
    NUMBER = "number"  # 数值
    OTHER = "other"  # 其他


@dataclass
class EntityMention:
    """实体提及"""
    text: str  # 提及文本
    type: EntityType
    position: int  # 文本位置
    confidence: float = 1.0
    context: str = ""  # 上下文
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """实体"""
    id: str
    name: str  # 标准名称
    type: EntityType
    mentions: List[EntityMention] = field(default_factory=list)
    aliases: Set[str] = field(default_factory=set)  # 别名
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class CoreferenceChain:
    """共指链"""
    entity_id: str
    mentions: List[EntityMention]
    pronouns: List[str] = field(default_factory=list)


class PatternMatcher:
    """模式匹配器"""

    def __init__(self):
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[EntityType, List[Tuple[str, float]]]:
        """初始化匹配模式"""
        patterns = {
            EntityType.PERSON: [
                # 中文人名
                (r'[一-鿿]{2,4}(?:先生|女士|老师|教授|博士|院士|主席|总统|市长|县长|局长|经理|董事长)', 0.95),
                (r'(?:老|小|大)[一-鿿]{1,2}', 0.7),
                (r'[一-鿿]{2,3}(?=说|讲|问|答|认为|表示|指出)', 0.8),
                # 英文人名
                (r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 0.85),
                (r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.\s*[A-Z][a-z]+', 0.9),
            ],
            EntityType.LOCATION: [
                # 地点
                (r'[一-鿿]{2,10}(?:省|市|县|区|镇|乡|村|街道|路|巷|弄|号)', 0.95),
                (r'[一-鿿]{2,10}(?:山|河|湖|海|江|溪|港|湾)', 0.9),
                (r'[一-鿿]{2,10}(?:国|洲|州)', 0.85),
                (r'(?:北京|上海|广州|深圳|杭州|成都|重庆|天津|南京|武汉)', 0.95),
            ],
            EntityType.ORGANIZATION: [
                # 组织机构
                (r'[一-鿿]{2,20}(?:公司|集团|企业|公司|工厂|店|馆|院|所|中心|局|部|委|会)', 0.9),
                (r'[一-鿿]{2,15}(?:大学|学院|学校|中学|小学|幼儿园)', 0.95),
                (r'[一-鿿]{2,15}(?:医院|诊所|药店)', 0.9),
                (r'\b[A-Z][a-zA-Z]*\s+(?:Inc|Corp|Ltd|LLC|University|College)\b', 0.9),
            ],
            EntityType.TIME: [
                # 时间
                (r'\d{4}年\d{1,2}月\d{1,2}日', 0.99),
                (r'\d{4}年\d{1,2}月', 0.95),
                (r'\d{4}年', 0.9),
                (r'(?:春秋|战国|秦|汉|唐|宋|元|明|清)(?:朝|代)', 0.95),
                (r'(?:公元前?)\d+年', 0.95),
                (r'(?:今天|昨天|明天|前天|后天)', 0.9),
                (r'(?:上午|下午|晚上|凌晨)\d{1,2}[点时]', 0.9),
            ],
            EntityType.EVENT: [
                # 事件
                (r'[一-鿿]{2,10}(?:战争|战役|革命|运动|会议|条约|协定)', 0.9),
                (r'[一-鿿]{2,10}(?:事件|事故|灾难|危机)', 0.85),
            ],
            EntityType.NUMBER: [
                # 数值
                (r'\d+(?:\.\d+)?(?:万|亿|千|百)?(?:元|美元|块|角|分)', 0.95),
                (r'\d+(?:\.\d+)?%', 0.95),
                (r'\d+(?:\.\d+)?(?:米|厘米|公里|克|千克|吨|升)', 0.95),
            ],
        }

        return patterns

    def match(self, text: str) -> List[EntityMention]:
        """模式匹配"""
        mentions = []

        for entity_type, patterns in self.patterns.items():
            for pattern, confidence in patterns:
                for match in re.finditer(pattern, text):
                    mention = EntityMention(
                        text=match.group(),
                        type=entity_type,
                        position=match.start(),
                        confidence=confidence,
                        context=self._extract_context(text, match.start(), match.end())
                    )
                    mentions.append(mention)

        return mentions

    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """提取上下文"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]


class NERService:
    """命名实体识别服务"""

    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        # 可以集成 spaCy 或其他 NER 模型

    async def extract(self, text: str) -> List[EntityMention]:
        """提取实体提及"""
        # 方法1：模式匹配
        pattern_mentions = await asyncio.to_thread(self.pattern_matcher.match, text)

        # 方法2：基于模型（如果有）
        # model_mentions = await self._model_extract(text)

        # 合并去重
        all_mentions = pattern_mentions
        all_mentions = self._deduplicate_mentions(all_mentions)

        logger.info(f"✅ NER 提取完成：{len(all_mentions)} 个实体提及")
        return all_mentions

    def _deduplicate_mentions(self, mentions: List[EntityMention]) -> List[EntityMention]:
        """去重实体提及"""
        # 按位置去重
        seen = {}
        result = []

        for mention in mentions:
            key = (mention.position, mention.text)
            if key not in seen:
                seen[key] = mention
                result.append(mention)
            else:
                # 保留置信度更高的
                if mention.confidence > seen[key].confidence:
                    seen[key] = mention

        return list(seen.values())


class EntityDisambiguator:
    """实体消歧器"""

    def disambiguate(self, mentions: List[EntityMention]) -> List[Entity]:
        """实体消歧 - 将多个提及合并为唯一实体"""
        # 按文本分组
        text_groups = defaultdict(list)
        for mention in mentions:
            # 规范化文本
            normalized = self._normalize_text(mention.text)
            text_groups[normalized].append(mention)

        entities = []
        entity_id = 0

        for normalized_text, group_mentions in text_groups.items():
            # 确定主类型（投票）
            type_votes = defaultdict(int)
            for m in group_mentions:
                type_votes[m.type] += 1
            main_type = max(type_votes.items(), key=lambda x: x[1])[0]

            # 创建实体
            entity = Entity(
                id=f"entity_{entity_id}",
                name=self._select_canonical_name(group_mentions),
                type=main_type,
                mentions=group_mentions,
                confidence=sum(m.confidence for m in group_mentions) / len(group_mentions)
            )

            # 提取别名
            entity.aliases = {m.text for m in group_mentions}

            entities.append(entity)
            entity_id += 1

        logger.info(f"✅ 实体消歧完成：{len(mentions)} 个提及 → {len(entities)} 个实体")
        return entities

    def _normalize_text(self, text: str) -> str:
        """规范化文本"""
        # 移除称谓
        honorifics = ['先生', '女士', '老师', '教授', '博士', '院士', '主席']
        for h in honorifics:
            text = text.replace(h, '')

        # 移除空白
        text = text.strip()

        return text

    def _select_canonical_name(self, mentions: List[EntityMention]) -> str:
        """选择标准名称（最长、最完整的）"""
        return max(mentions, key=lambda m: len(m.text)).text


class AliasExtractor:
    """别名提取器"""

    def extract(self, entities: List[Entity], text: str) -> List[Entity]:
        """提取实体别名"""
        for entity in entities:
            # 查找同位语
            appositives = self._find_appositives(entity.name, text)
            entity.aliases.update(appositives)

            # 查找缩写
            abbreviations = self._find_abbreviations(entity.name, text)
            entity.aliases.update(abbreviations)

        return entities

    def _find_appositives(self, name: str, text: str) -> Set[str]:
        """查找同位语"""
        appositives = set()

        # 模式："A，即B" 或 "A（B）"
        patterns = [
            rf'{re.escape(name)}[，,](?:即|也就是|又称)([一-鿿a-zA-Z]+)',
            rf'{re.escape(name)}[（(]([^)）]+)[)）]',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                appositives.add(match.group(1))

        return appositives

    def _find_abbreviations(self, name: str, text: str) -> Set[str]:
        """查找缩写"""
        abbreviations = set()

        # 提取首字母
        if len(name) >= 2:
            # 中文：取每个词的第一个字
            chinese_words = re.findall(r'[一-鿿]+', name)
            if len(chinese_words) >= 2:
                abbr = ''.join(w[0] for w in chinese_words)
                if abbr in text:
                    abbreviations.add(abbr)

            # 英文：首字母缩写
            english_words = re.findall(r'\b[A-Z][a-z]+', name)
            if len(english_words) >= 2:
                abbr = ''.join(w[0] for w in english_words)
                if abbr in text:
                    abbreviations.add(abbr)

        return abbreviations


class CoreferenceResolver:
    """共指解析器"""

    def __init__(self):
        self.pronouns = {
            'zh': ['他', '她', '它', '他们', '她们', '它们', '其', '此人', '该人', '这位', '那位'],
            'en': ['he', 'she', 'it', 'they', 'him', 'her', 'them', 'his', 'hers', 'their']
        }

    def resolve(self, entities: List[Entity], text: str) -> List[CoreferenceChain]:
        """共指解析"""
        chains = []

        # 为每个实体建立共指链
        for entity in entities:
            if entity.type == EntityType.PERSON:
                chain = self._build_coref_chain(entity, text)
                if chain.pronouns:
                    chains.append(chain)

        logger.info(f"✅ 共指解析完成：{len(chains)} 个共指链")
        return chains

    def _build_coref_chain(self, entity: Entity, text: str) -> CoreferenceChain:
        """构建共指链"""
        chain = CoreferenceChain(
            entity_id=entity.id,
            mentions=entity.mentions.copy()
        )

        # 查找代词指代
        # 简单规则：实体提及后的代词
        for mention in entity.mentions:
            # 在提及后的一定范围内查找代词
            search_start = mention.position + len(mention.text)
            search_end = min(search_start + 200, len(text))
            search_text = text[search_start:search_end]

            for pronoun in self.pronouns['zh']:
                if pronoun in search_text:
                    # 检查是否是最近的实体
                    if self._is_nearest_entity(mention.position, pronoun, text, entity):
                        chain.pronouns.append(pronoun)

        return chain

    def _is_nearest_entity(
        self,
        entity_position: int,
        pronoun: str,
        text: str,
        entity: Entity
    ) -> bool:
        """检查是否是最近的实体（简化版）"""
        # 实际应该实现更复杂的距离和语法判断
        return True


class EntityConstructionService:
    """实体构建服务"""

    def __init__(self):
        self.ner_service = NERService()
        self.disambiguator = EntityDisambiguator()
        self.alias_extractor = AliasExtractor()
        self.coref_resolver = CoreferenceResolver()

    async def construct(self, text: str, structure_tree=None) -> Dict[str, Any]:
        """
        实体构建

        Args:
            text: 清洗后的文本
            structure_tree: 结构树（可选）

        Returns:
            实体构建结果
        """
        logger.info(f"开始实体构建")

        # 1. 命名实体识别
        mentions = await self.ner_service.extract(text)
        logger.info(f"✅ NER 完成：{len(mentions)} 个提及")

        # 2. 实体消歧
        entities = await asyncio.to_thread(self.disambiguator.disambiguate, mentions)
        logger.info(f"✅ 消歧完成：{len(entities)} 个实体")

        # 3. 别名提取
        entities = await asyncio.to_thread(self.alias_extractor.extract, entities, text)
        logger.info(f"✅ 别名提取完成")

        # 4. 共指解析
        coref_chains = await asyncio.to_thread(self.coref_resolver.resolve, entities, text)
        logger.info(f"✅ 共指解析完成：{len(coref_chains)} 个共指链")

        # 统计
        entity_stats = self._calculate_statistics(entities, mentions, coref_chains)

        result = {
            'entities': entities,
            'mentions': mentions,
            'coref_chains': coref_chains,
            'statistics': entity_stats
        }

        logger.info(f"✅ 实体构建完成：{len(entities)} 个实体")
        return result

    def _calculate_statistics(
        self,
        entities: List[Entity],
        mentions: List[EntityMention],
        coref_chains: List[CoreferenceChain]
    ) -> Dict[str, Any]:
        """计算统计信息"""
        type_counts = defaultdict(int)
        for entity in entities:
            type_counts[entity.type.value] += 1

        return {
            'total_entities': len(entities),
            'total_mentions': len(mentions),
            'total_coref_chains': len(coref_chains),
            'entity_by_type': dict(type_counts),
            'avg_mentions_per_entity': len(mentions) / len(entities) if entities else 0,
            'entities_with_aliases': sum(1 for e in entities if len(e.aliases) > 1),
        }
