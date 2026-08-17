"""
统一实体提取引擎 - 整合jieba和HanLP两种方法

整合目标：
- entity_extraction.py (jieba版本) + entity_extractor.py (HanLP版本) → 1个统一引擎
- 实现1+1>2的功能增强，而非简单合并

核心特性：
1. 双引擎支持：jieba快速提取 + HanLP深度学习（自动降级）
2. 混合策略：结合两种方法提高准确率和召回率
3. 自定义词典：支持领域专业术语（田野调查）
4. 位置追踪：记录实体在文本中的所有出现位置
5. 关系提取：基于关键词和共现的关系识别
6. 批量处理：多文本并行提取和实体合并
7. 时间解析：将时间表达式解析为标准datetime对象
8. 置信度评分：基于多维度的实体可信度计算
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict
import re
import logging

logger = logging.getLogger(__name__)


class ExtractionEngine(str, Enum):
    """提取引擎类型"""
    JIEBA = "jieba"           # 快速，支持自定义词典
    HANLP = "hanlp"           # 深度学习，准确率高
    HYBRID = "hybrid"         # 混合模式（推荐）
    RULES = "rules"           # 纯规则（备用）


class EntityType(str, Enum):
    """实体类型"""
    PERSON = "person"              # 人名
    LOCATION = "location"          # 地点
    ORGANIZATION = "organization"  # 组织机构
    TIME = "time"                  # 时间
    CUSTOM = "custom"              # 自定义/其他


@dataclass
class EntityPosition:
    """实体位置信息"""
    start: int
    end: int
    context: Optional[str] = None  # 上下文片段


@dataclass
class ExtractedEntity:
    """提取的实体（统一格式）"""
    name: str
    type: EntityType
    confidence: float
    mention_count: int = 1
    positions: List[EntityPosition] = field(default_factory=list)
    engine: str = "unknown"
    original_type: Optional[str] = None  # 原始类型标签
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（向后兼容）"""
        result = {
            "name": self.name,
            "type": self.type.value if isinstance(self.type, EntityType) else self.type,
            "confidence": round(self.confidence, 2),
            "mention_count": self.mention_count,
            "positions": [
                (pos.start, pos.end) for pos in self.positions
            ] if self.positions else [],
            "engine": self.engine,
        }
        if self.original_type:
            result["original_type"] = self.original_type
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class ParsedTime:
    """解析后的时间"""
    raw: str                           # 原始表达式
    parsed: Optional[datetime]         # 解析后的日期
    confidence: float                  # 置信度
    position: Tuple[int, int]         # 位置


@dataclass
class EntityRelation:
    """实体关系"""
    from_entity: str
    from_type: EntityType
    to_entity: str
    to_type: EntityType
    relation_type: str
    confidence: float
    context: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "from": self.from_entity,
            "from_type": self.from_type.value if isinstance(self.from_type, EntityType) else self.from_type,
            "to": self.to_entity,
            "to_type": self.to_type.value if isinstance(self.to_type, EntityType) else self.to_type,
            "type": self.relation_type,
            "confidence": round(self.confidence, 2),
            "context": self.context[:100] if len(self.context) > 100 else self.context
        }


class UnifiedEntityExtractor:
    """统一实体提取引擎"""

    # jieba词性到实体类型的映射
    JIEBA_TYPE_MAP = {
        'nr': EntityType.PERSON,
        'ns': EntityType.LOCATION,
        'nt': EntityType.ORGANIZATION,
        'nz': EntityType.CUSTOM,
        't': EntityType.TIME,
    }

    # HanLP类型到实体类型的映射
    HANLP_TYPE_MAP = {
        'PERSON': EntityType.PERSON,
        'LOCATION': EntityType.LOCATION,
        'ORGANIZATION': EntityType.ORGANIZATION,
        'TIME': EntityType.TIME,
        'DATE': EntityType.TIME,
    }

    # 时间关键词黑名单
    TIME_KEYWORDS_BLACKLIST = {
        '年', '月', '日', '时', '分', '秒', '世纪', '年代',
        '现在', '过去', '将来', '时候', '时间', '年轻',
        '下来', '同时', '现代', '当时'
    }

    # 关系关键词
    RELATION_KEYWORDS = {
        '住在': 'lives_in',
        '来自': 'from',
        '属于': 'belongs_to',
        '前往': 'visited',
        '去了': 'visited',
        '到达': 'arrived_at',
        '调查': 'investigated',
        '研究': 'studied',
        '发现': 'discovered',
        '建立': 'established',
        '创建': 'created',
        '访问': 'visited',
        '采访': 'interviewed',
    }

    def __init__(
        self,
        engine: ExtractionEngine = ExtractionEngine.HYBRID,
        enable_custom_dict: bool = True,
        enable_position_tracking: bool = True,
        enable_context: bool = False,
        context_window: int = 50,
        min_confidence: float = 0.5
    ):
        """
        Args:
            engine: 提取引擎类型
            enable_custom_dict: 是否启用自定义词典
            enable_position_tracking: 是否追踪位置信息
            enable_context: 是否提取上下文
            context_window: 上下文窗口大小
            min_confidence: 最低置信度阈值
        """
        self.engine = engine
        self.enable_custom_dict = enable_custom_dict
        self.enable_position_tracking = enable_position_tracking
        self.enable_context = enable_context
        self.context_window = context_window
        self.min_confidence = min_confidence

        # 初始化jieba
        self.jieba_ready = self._init_jieba()

        # 延迟加载HanLP
        self.hanlp_model = None
        self.hanlp_ready = False

    def _init_jieba(self) -> bool:
        """初始化jieba分词器"""
        try:
            import jieba
            import jieba.posseg as pseg

            if self.enable_custom_dict:
                self._add_custom_words()

            logger.info("✅ jieba初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ jieba初始化失败: {e}")
            return False

    def _add_custom_words(self):
        """添加自定义词典（田野调查领域）"""
        import jieba

        custom_words = [
            # 学者人名
            ('费孝通', 10, 'nr'),
            ('林耀华', 10, 'nr'),
            ('李亦园', 10, 'nr'),

            # 地名
            ('十八洞村', 10, 'ns'),
            ('湘西', 8, 'ns'),
            ('凤凰古城', 10, 'ns'),
            ('黔东南', 8, 'ns'),

            # 民族
            ('苗族', 8, 'nz'),
            ('侗族', 8, 'nz'),
            ('布依族', 8, 'nz'),
            ('瑶族', 8, 'nz'),
            ('壮族', 8, 'nz'),

            # 文化概念
            ('非物质文化遗产', 10, 'nz'),
            ('精准扶贫', 10, 'nz'),
            ('乡村振兴', 10, 'nz'),
            ('传统村落', 10, 'nz'),

            # 食物
            ('杀猪菜', 10, 'nz'),
            ('腊肉', 8, 'nz'),
            ('酸汤鱼', 8, 'nz'),
            ('糯米饭', 8, 'nz'),
            ('油茶', 8, 'nz'),
            ('米酒', 8, 'nz'),

            # 建筑
            ('祠堂', 10, 'nz'),
            ('吊脚楼', 10, 'nz'),
            ('鼓楼', 8, 'nz'),
            ('风雨桥', 8, 'nz'),
            ('戏台', 8, 'nz'),

            # 文化活动
            ('芦笙', 8, 'nz'),
            ('侗歌', 8, 'nz'),
            ('苗歌', 8, 'nz'),
            ('踩歌堂', 8, 'nz'),
            ('芦笙节', 10, 'nz'),
            ('姊妹节', 10, 'nz'),
        ]

        for word, freq, tag in custom_words:
            jieba.add_word(word, freq, tag)

        logger.info(f"✅ 加载了 {len(custom_words)} 个自定义词汇")

    def _init_hanlp(self) -> bool:
        """延迟加载HanLP模型"""
        if self.hanlp_ready:
            return True

        try:
            import hanlp
            self.hanlp_model = hanlp.load(
                hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH
            )
            self.hanlp_ready = True
            logger.info("✅ HanLP模型加载成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ HanLP加载失败: {e}")
            return False

    def extract_entities(
        self,
        text: str,
        output_mode: str = "dataclass"
    ) -> List[Any]:
        """
        提取实体

        Args:
            text: 输入文本
            output_mode: 输出模式 ("dataclass" | "dict")

        Returns:
            实体列表
        """
        if not text or not text.strip():
            return []

        # 根据引擎选择提取方法
        if self.engine == ExtractionEngine.JIEBA:
            entities = self._extract_with_jieba(text)
        elif self.engine == ExtractionEngine.HANLP:
            entities = self._extract_with_hanlp(text)
        elif self.engine == ExtractionEngine.HYBRID:
            entities = self._extract_hybrid(text)
        else:  # RULES
            entities = self._extract_with_rules(text)

        # 过滤低置信度实体
        entities = [e for e in entities if e.confidence >= self.min_confidence]

        # 排序：置信度降序
        entities.sort(key=lambda x: x.confidence, reverse=True)

        # 输出格式转换
        if output_mode == "dict":
            return [e.to_dict() for e in entities]
        return entities

    def _extract_with_jieba(self, text: str) -> List[ExtractedEntity]:
        """使用jieba提取实体"""
        if not self.jieba_ready:
            logger.warning("jieba未初始化，使用规则方法")
            return self._extract_with_rules(text)

        import jieba.posseg as pseg

        # 词性标注
        words = list(pseg.cut(text))

        # 收集实体
        entities_dict = defaultdict(lambda: {
            "positions": [],
            "count": 0,
            "contexts": []
        })

        position = 0
        for item in words:
            word = item.word
            flag = item.flag
            word_len = len(word)

            # 根据词性映射实体类型
            if flag in self.JIEBA_TYPE_MAP:
                entity_type = self.JIEBA_TYPE_MAP[flag]

                # 跳过时间关键词黑名单
                if entity_type == EntityType.TIME and word in self.TIME_KEYWORDS_BLACKLIST:
                    position += word_len
                    continue

                key = (word, entity_type)

                # 记录位置
                start_pos = position
                end_pos = position + word_len
                entities_dict[key]["positions"].append((start_pos, end_pos))
                entities_dict[key]["count"] += 1

                # 提取上下文
                if self.enable_context:
                    ctx_start = max(0, start_pos - self.context_window)
                    ctx_end = min(len(text), end_pos + self.context_window)
                    context = text[ctx_start:ctx_end]
                    entities_dict[key]["contexts"].append(context)

            # 特殊处理：时间表达式
            elif self._is_time_expression(word):
                key = (word, EntityType.TIME)
                start_pos = position
                end_pos = position + word_len
                entities_dict[key]["positions"].append((start_pos, end_pos))
                entities_dict[key]["count"] += 1

            position += word_len

        # 转换为ExtractedEntity对象
        entities = []
        for (name, entity_type), data in entities_dict.items():
            # 计算置信度
            confidence = self._calculate_confidence(
                name=name,
                mention_count=data["count"],
                entity_type=entity_type,
                method="jieba"
            )

            # 构建位置列表
            positions = []
            if self.enable_position_tracking:
                for i, (start, end) in enumerate(data["positions"][:5]):  # 最多5个位置
                    pos = EntityPosition(
                        start=start,
                        end=end,
                        context=data["contexts"][i] if self.enable_context and i < len(data["contexts"]) else None
                    )
                    positions.append(pos)

            entity = ExtractedEntity(
                name=name,
                type=entity_type,
                confidence=confidence,
                mention_count=data["count"],
                positions=positions,
                engine="jieba"
            )
            entities.append(entity)

        return entities

    def _extract_with_hanlp(self, text: str) -> List[ExtractedEntity]:
        """使用HanLP提取实体"""
        # 尝试加载HanLP
        if not self._init_hanlp():
            logger.warning("HanLP不可用，降级到jieba")
            return self._extract_with_jieba(text)

        try:
            # HanLP NER
            result = self.hanlp_model(text, tasks='ner')
            ner_result = result.get('ner/msra', []) or result.get('ner', [])

            entities = []
            seen_names = set()

            for entity_list in ner_result:
                for entity_name, entity_type in entity_list:
                    # 去重
                    if entity_name in seen_names:
                        continue
                    seen_names.add(entity_name)

                    # 映射类型
                    mapped_type = self.HANLP_TYPE_MAP.get(entity_type, EntityType.CUSTOM)

                    # 查找位置
                    positions = []
                    if self.enable_position_tracking:
                        positions = self._find_positions(text, entity_name)

                    entity = ExtractedEntity(
                        name=entity_name,
                        type=mapped_type,
                        confidence=0.85,  # HanLP默认置信度
                        mention_count=len(positions) if positions else 1,
                        positions=positions,
                        engine="hanlp",
                        original_type=entity_type
                    )
                    entities.append(entity)

            logger.info(f"HanLP提取了 {len(entities)} 个实体")
            return entities

        except Exception as e:
            logger.error(f"HanLP提取失败: {e}")
            return self._extract_with_jieba(text)

    def _extract_hybrid(self, text: str) -> List[ExtractedEntity]:
        """混合模式：结合jieba和HanLP"""
        # 先用jieba快速提取
        jieba_entities = self._extract_with_jieba(text)

        # 再用HanLP提取
        hanlp_entities = self._extract_with_hanlp(text)

        # 合并去重
        merged = self._merge_entities(jieba_entities + hanlp_entities)

        logger.info(f"混合模式: jieba={len(jieba_entities)}, hanlp={len(hanlp_entities)}, 合并后={len(merged)}")
        return merged

    def _extract_with_rules(self, text: str) -> List[ExtractedEntity]:
        """纯规则方法（备用）"""
        entities = []

        # 1. 时间表达式
        time_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}年\d{1,2}月',
            r'\d{4}年',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}月\d{1,2}日',
        ]

        for pattern in time_patterns:
            for match in re.finditer(pattern, text):
                entity = ExtractedEntity(
                    name=match.group(),
                    type=EntityType.TIME,
                    confidence=0.9,
                    positions=[EntityPosition(match.start(), match.end())],
                    engine="rules"
                )
                entities.append(entity)

        # 2. 地名（包含特定后缀）
        location_pattern = r'[一-龥]{2,10}[村|镇|乡|县|市|省|区|州|路|街|道]'
        for match in re.finditer(location_pattern, text):
            entity = ExtractedEntity(
                name=match.group(),
                type=EntityType.LOCATION,
                confidence=0.7,
                positions=[EntityPosition(match.start(), match.end())],
                engine="rules"
            )
            entities.append(entity)

        # 3. 组织机构
        org_pattern = r'[一-龥]{2,20}[公司|合作社|协会|中心|局|委员会|学校|医院|银行]'
        for match in re.finditer(org_pattern, text):
            entity = ExtractedEntity(
                name=match.group(),
                type=EntityType.ORGANIZATION,
                confidence=0.7,
                positions=[EntityPosition(match.start(), match.end())],
                engine="rules"
            )
            entities.append(entity)

        # 去重
        merged = self._merge_entities(entities)
        logger.info(f"规则方法提取了 {len(merged)} 个实体")
        return merged

    def _merge_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """合并相同名称的实体"""
        merged_dict = {}

        for entity in entities:
            key = (entity.name, entity.type)

            if key in merged_dict:
                existing = merged_dict[key]
                # 更新出现次数
                existing.mention_count += entity.mention_count
                # 合并位置
                existing.positions.extend(entity.positions)
                # 取最高置信度
                existing.confidence = max(existing.confidence, entity.confidence)
                # 记录引擎
                if entity.engine not in existing.engine:
                    existing.engine = f"{existing.engine}+{entity.engine}"
            else:
                merged_dict[key] = entity

        return list(merged_dict.values())

    def _find_positions(
        self,
        text: str,
        entity_name: str,
        max_positions: int = 5
    ) -> List[EntityPosition]:
        """在文本中查找实体的所有位置"""
        positions = []
        start = 0

        while len(positions) < max_positions:
            idx = text.find(entity_name, start)
            if idx == -1:
                break

            pos = EntityPosition(
                start=idx,
                end=idx + len(entity_name),
                context=None
            )

            if self.enable_context:
                ctx_start = max(0, idx - self.context_window)
                ctx_end = min(len(text), idx + len(entity_name) + self.context_window)
                pos.context = text[ctx_start:ctx_end]

            positions.append(pos)
            start = idx + 1

        return positions

    def _is_time_expression(self, word: str) -> bool:
        """判断是否为时间表达式"""
        if word in self.TIME_KEYWORDS_BLACKLIST:
            return False

        time_indicators = ['年', '月', '日', '号']
        return any(ind in word for ind in time_indicators)

    def _calculate_confidence(
        self,
        name: str,
        mention_count: int,
        entity_type: EntityType,
        method: str
    ) -> float:
        """计算实体置信度"""
        base_score = 0.6

        # 基于出现次数
        count_bonus = min(mention_count * 0.1, 0.2)

        # 基于名称长度
        length_bonus = min(len(name) * 0.05, 0.15)

        # 基于类型
        type_bonus = 0.05 if entity_type != EntityType.CUSTOM else 0.0

        confidence = base_score + count_bonus + length_bonus + type_bonus
        return min(confidence, 1.0)

    def extract_time_expressions(
        self,
        text: str,
        parse_to_datetime: bool = True
    ) -> List[ParsedTime]:
        """
        提取并解析时间表达式

        Args:
            text: 输入文本
            parse_to_datetime: 是否解析为datetime对象

        Returns:
            时间表达式列表
        """
        if not text or not text.strip():
            return []

        time_patterns = [
            # YYYY年MM月DD日
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日',
             lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # YYYY年MM月
            (r'(\d{4})年(\d{1,2})月',
             lambda m: datetime(int(m.group(1)), int(m.group(2)), 1)),
            # YYYY年
            (r'(\d{4})年',
             lambda m: datetime(int(m.group(1)), 1, 1)),
            # YYYY-MM-DD
            (r'(\d{4})-(\d{1,2})-(\d{1,2})',
             lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            # YYYY/MM/DD
            (r'(\d{4})/(\d{1,2})/(\d{1,2})',
             lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        ]

        results = []
        seen_positions = set()

        for pattern, parser in time_patterns:
            for match in re.finditer(pattern, text):
                position = (match.start(), match.end())

                # 避免重复（同一位置可能匹配多个模式）
                if position in seen_positions:
                    continue
                seen_positions.add(position)

                parsed_date = None
                if parse_to_datetime:
                    try:
                        parsed_date = parser(match)
                    except (ValueError, IndexError) as e:
                        logger.debug(f"时间解析失败: {match.group()} - {e}")

                parsed_time = ParsedTime(
                    raw=match.group(),
                    parsed=parsed_date,
                    confidence=0.95 if parsed_date else 0.7,
                    position=position
                )
                results.append(parsed_time)

        return results

    def extract_relationships(
        self,
        text: str,
        entities: Optional[List[ExtractedEntity]] = None,
        output_mode: str = "dataclass"
    ) -> List[Any]:
        """
        提取实体间的关系

        Args:
            text: 输入文本
            entities: 已提取的实体（如为None则自动提取）
            output_mode: 输出模式 ("dataclass" | "dict")

        Returns:
            关系列表
        """
        # 如果没有提供实体，先提取
        if entities is None:
            entities = self.extract_entities(text, output_mode="dataclass")

        if not entities:
            return []

        relationships = []

        # 分句
        sentences = re.split(r'[。！？\n]+', text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 找出句子中的实体
            sentence_entities = [
                e for e in entities
                if e.name in sentence
            ]

            if len(sentence_entities) < 2:
                continue

            # 检查关系关键词
            for keyword, rel_type in self.RELATION_KEYWORDS.items():
                if keyword not in sentence:
                    continue

                # 关键词位置
                kw_pos = sentence.index(keyword)

                # 主体：关键词之前的实体
                before_entities = [
                    e for e in sentence_entities
                    if sentence.index(e.name) < kw_pos
                ]

                # 客体：关键词之后的实体
                after_entities = [
                    e for e in sentence_entities
                    if sentence.index(e.name) > kw_pos
                ]

                if before_entities and after_entities:
                    relation = EntityRelation(
                        from_entity=before_entities[-1].name,
                        from_type=before_entities[-1].type,
                        to_entity=after_entities[0].name,
                        to_type=after_entities[0].type,
                        relation_type=rel_type,
                        confidence=0.6,
                        context=sentence.strip()
                    )
                    relationships.append(relation)

        # 输出格式转换
        if output_mode == "dict":
            return [r.to_dict() for r in relationships]
        return relationships

    def batch_extract(
        self,
        texts: List[str],
        merge_entities: bool = True,
        output_mode: str = "dataclass"
    ) -> Dict[str, Any]:
        """
        批量提取实体

        Args:
            texts: 文本列表
            merge_entities: 是否合并相同实体
            output_mode: 输出模式

        Returns:
            {"entities": [...], "stats": {...}}
        """
        all_entities = []

        for i, text in enumerate(texts):
            entities = self.extract_entities(text, output_mode="dataclass")

            # 添加文本索引
            for entity in entities:
                entity.metadata["text_index"] = i

            all_entities.extend(entities)

        # 合并
        if merge_entities:
            all_entities = self._merge_entities(all_entities)

        # 统计
        stats = {
            "total_texts": len(texts),
            "total_entities": len(all_entities),
            "by_type": {},
            "by_engine": {}
        }

        for entity in all_entities:
            # 按类型统计
            type_key = entity.type.value if isinstance(entity.type, EntityType) else entity.type
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1

            # 按引擎统计
            stats["by_engine"][entity.engine] = stats["by_engine"].get(entity.engine, 0) + 1

        # 格式转换
        if output_mode == "dict":
            all_entities = [e.to_dict() for e in all_entities]

        return {
            "entities": all_entities,
            "stats": stats
        }

    def get_extraction_stats(self, entities: List[ExtractedEntity]) -> Dict[str, Any]:
        """获取提取统计信息"""
        if not entities:
            return {
                "total": 0,
                "by_type": {},
                "by_engine": {},
                "avg_confidence": 0.0,
                "high_confidence_count": 0
            }

        stats = {
            "total": len(entities),
            "by_type": defaultdict(int),
            "by_engine": defaultdict(int),
            "avg_confidence": sum(e.confidence for e in entities) / len(entities),
            "high_confidence_count": sum(1 for e in entities if e.confidence >= 0.8)
        }

        for entity in entities:
            type_key = entity.type.value if isinstance(entity.type, EntityType) else entity.type
            stats["by_type"][type_key] += 1
            stats["by_engine"][entity.engine] += 1

        # 转换defaultdict为普通dict
        stats["by_type"] = dict(stats["by_type"])
        stats["by_engine"] = dict(stats["by_engine"])

        return stats


# ============ 便捷函数 ============

def create_extractor(
    engine: str = "hybrid",
    **kwargs
) -> UnifiedEntityExtractor:
    """
    创建实体提取器的便捷函数

    Args:
        engine: 引擎类型 ("jieba" | "hanlp" | "hybrid" | "rules")
        **kwargs: 其他参数传递给UnifiedEntityExtractor

    Returns:
        UnifiedEntityExtractor实例
    """
    engine_enum = ExtractionEngine(engine)
    return UnifiedEntityExtractor(engine=engine_enum, **kwargs)


def extract_entities(
    text: str,
    engine: str = "hybrid",
    min_confidence: float = 0.5,
    output_mode: str = "dict"
) -> List[Dict[str, Any]]:
    """
    快速提取实体的便捷函数

    Args:
        text: 输入文本
        engine: 引擎类型
        min_confidence: 最低置信度
        output_mode: 输出模式

    Returns:
        实体列表
    """
    extractor = create_extractor(engine=engine, min_confidence=min_confidence)
    return extractor.extract_entities(text, output_mode=output_mode)


def extract_entities_and_relations(
    text: str,
    engine: str = "hybrid",
    min_confidence: float = 0.5
) -> Dict[str, Any]:
    """
    同时提取实体和关系的便捷函数

    Args:
        text: 输入文本
        engine: 引擎类型
        min_confidence: 最低置信度

    Returns:
        {"entities": [...], "relations": [...]}
    """
    extractor = create_extractor(engine=engine, min_confidence=min_confidence)
    entities = extractor.extract_entities(text, output_mode="dataclass")
    relations = extractor.extract_relationships(text, entities, output_mode="dict")

    return {
        "entities": [e.to_dict() for e in entities],
        "relations": relations
    }


def batch_extract_entities(
    texts: List[str],
    engine: str = "hybrid",
    merge_entities: bool = True
) -> Dict[str, Any]:
    """
    批量提取实体的便捷函数

    Args:
        texts: 文本列表
        engine: 引擎类型
        merge_entities: 是否合并

    Returns:
        {"entities": [...], "stats": {...}}
    """
    extractor = create_extractor(engine=engine)
    return extractor.batch_extract(texts, merge_entities, output_mode="dict")
