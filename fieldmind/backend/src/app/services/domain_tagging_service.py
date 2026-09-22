"""
领域标注服务
包含遗产分类和UNESCO标准
"""
import logging
from typing import List, Dict, Any, Optional

from app.models.enriched_chunk import Entity, DomainTag, DomainCategory, EntityType

logger = logging.getLogger(__name__)


class DomainTaggingService:
    """领域标注服务 - 多层次分类"""

    def __init__(self):
        # 领域本体（ontology）⭐
        self.ontology = self._load_domain_ontology()

        # UNESCO 非遗分类体系 ⭐
        self.unesco_taxonomy = self._load_unesco_taxonomy()

        logger.info("领域标注服务初始化完成")

    def _load_domain_ontology(self) -> Dict[str, Dict[str, Any]]:
        """加载领域本体

        结构：
        {
            "蜡染": {
                "category": "非物质文化遗产",
                "subcategory": "传统技艺",
                "sub_subcategory": "纺染织绣",
                "keywords": ["蜡刀", "蓝靛", "植物染料"],
                "unesco_domain": "传统手工艺"
            },
            ...
        }
        """
        ontology = {
            # 非物质文化遗产
            "蜡染": {
                "category": "非物质文化遗产",
                "subcategory": "传统技艺",
                "sub_subcategory": "纺染织绣",
                "keywords": ["蜡刀", "蓝靛", "植物染料", "防染"],
                "unesco_domain": "传统手工艺"
            },
            "刺绣": {
                "category": "非物质文化遗产",
                "subcategory": "传统技艺",
                "sub_subcategory": "纺染织绣",
                "keywords": ["针线", "图案", "丝线"],
                "unesco_domain": "传统手工艺"
            },
            "银饰": {
                "category": "非物质文化遗产",
                "subcategory": "传统技艺",
                "sub_subcategory": "金属工艺",
                "keywords": ["锻打", "雕刻", "银器"],
                "unesco_domain": "传统手工艺"
            },
            "芦笙": {
                "category": "非物质文化遗产",
                "subcategory": "传统音乐",
                "sub_subcategory": "乐器演奏",
                "keywords": ["竹制", "簧管", "民族乐器"],
                "unesco_domain": "表演艺术"
            },
            "侗族大歌": {
                "category": "非物质文化遗产",
                "subcategory": "传统音乐",
                "sub_subcategory": "民歌",
                "keywords": ["多声部", "无伴奏", "合唱"],
                "unesco_domain": "表演艺术"
            },

            # 物质文化遗产
            "吊脚楼": {
                "category": "物质文化遗产",
                "subcategory": "传统建筑",
                "sub_subcategory": "民居",
                "keywords": ["木结构", "架空", "干栏式"],
                "unesco_domain": None
            },
            "风雨桥": {
                "category": "物质文化遗产",
                "subcategory": "传统建筑",
                "sub_subcategory": "桥梁",
                "keywords": ["廊桥", "亭台", "侗族建筑"],
                "unesco_domain": None
            },

            # 自然遗产
            "梯田": {
                "category": "自然遗产",
                "subcategory": "农业景观",
                "sub_subcategory": "梯田",
                "keywords": ["山地农业", "稻作", "景观"],
                "unesco_domain": None
            },

            # 习俗节日
            "苗年": {
                "category": "习俗",
                "subcategory": "传统节日",
                "sub_subcategory": None,
                "keywords": ["苗族", "新年", "庆典"],
                "unesco_domain": "社会实践、仪式、节庆活动"
            },
            "三月三": {
                "category": "习俗",
                "subcategory": "传统节日",
                "sub_subcategory": None,
                "keywords": ["歌会", "对歌", "民族节日"],
                "unesco_domain": "社会实践、仪式、节庆活动"
            },
            "祭祖": {
                "category": "祭祀",
                "subcategory": "祭祀活动",
                "sub_subcategory": None,
                "keywords": ["祖先", "仪式", "祭拜"],
                "unesco_domain": "社会实践、仪式、节庆活动"
            },

            # 衣食住行
            "服饰": {
                "category": "衣",
                "subcategory": "民族服饰",
                "sub_subcategory": None,
                "keywords": ["传统服装", "民族特色"],
                "unesco_domain": None
            },
            "酸汤鱼": {
                "category": "食",
                "subcategory": "传统饮食",
                "sub_subcategory": "菜肴",
                "keywords": ["苗族", "酸汤", "鱼类"],
                "unesco_domain": None
            },
            "糯米饭": {
                "category": "食",
                "subcategory": "传统饮食",
                "sub_subcategory": "主食",
                "keywords": ["糯米", "蒸煮", "传统"],
                "unesco_domain": None
            },

            # 在地知识
            "节气": {
                "category": "在地知识",
                "subcategory": "农业知识",
                "sub_subcategory": None,
                "keywords": ["二十四节气", "农耕", "时令"],
                "unesco_domain": "有关自然界和宇宙的知识和实践"
            },
            "草药": {
                "category": "在地知识",
                "subcategory": "医药知识",
                "sub_subcategory": None,
                "keywords": ["中草药", "传统医药", "民族医药"],
                "unesco_domain": "有关自然界和宇宙的知识和实践"
            },
        }

        logger.info(f"领域本体加载完成: {len(ontology)} 个条目")
        return ontology

    def _load_unesco_taxonomy(self) -> Dict[str, Dict[str, str]]:
        """加载UNESCO非遗分类体系

        UNESCO非遗五大领域：
        1. 口头传统和表现形式
        2. 表演艺术
        3. 社会实践、仪式、节庆活动
        4. 有关自然界和宇宙的知识和实践
        5. 传统手工艺
        """
        taxonomy = {
            "传统技艺": {
                "domain": "传统手工艺",
                "subdomain": "手工技艺"
            },
            "纺染织绣": {
                "domain": "传统手工艺",
                "subdomain": "纺织技艺"
            },
            "金属工艺": {
                "domain": "传统手工艺",
                "subdomain": "金属加工"
            },
            "传统音乐": {
                "domain": "表演艺术",
                "subdomain": "音乐"
            },
            "民歌": {
                "domain": "表演艺术",
                "subdomain": "声乐"
            },
            "乐器演奏": {
                "domain": "表演艺术",
                "subdomain": "器乐"
            },
            "传统舞蹈": {
                "domain": "表演艺术",
                "subdomain": "舞蹈"
            },
            "传统节日": {
                "domain": "社会实践、仪式、节庆活动",
                "subdomain": "节庆"
            },
            "祭祀活动": {
                "domain": "社会实践、仪式、节庆活动",
                "subdomain": "仪式"
            },
            "农业知识": {
                "domain": "有关自然界和宇宙的知识和实践",
                "subdomain": "农业"
            },
            "医药知识": {
                "domain": "有关自然界和宇宙的知识和实践",
                "subdomain": "传统医药"
            },
            "口头文学": {
                "domain": "口头传统和表现形式",
                "subdomain": "口头文学"
            },
        }

        logger.info(f"UNESCO分类体系加载完成: {len(taxonomy)} 个类别")
        return taxonomy

    def tag_domains(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[DomainTag]:
        """标注所有领域

        Args:
            text: 输入文本
            entities: 已识别的实体列表

        Returns:
            领域标签列表
        """
        tags = []

        # 1. 基础领域分类（衣食住行文化在地）
        base_tags = self._tag_base_domains(text, entities)
        tags.extend(base_tags)

        # 2. 遗产分类 ⭐
        heritage_tags = self._tag_heritage_domains(text, entities)
        tags.extend(heritage_tags)

        # 3. 文化习俗分类 ⭐
        cultural_tags = self._tag_cultural_domains(text, entities)
        tags.extend(cultural_tags)

        # 4. UNESCO 分类（对于非遗）⭐
        tags = self._add_unesco_classification(tags, entities)

        # 5. 去重
        tags = self._deduplicate_tags(tags)

        logger.info(f"领域标注完成: {len(tags)} 个标签")
        return tags

    def _tag_base_domains(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[DomainTag]:
        """标注基础领域（衣食住行文化在地）"""
        tags = []

        # 衣
        if any(kw in text for kw in ["服饰", "服装", "穿戴", "衣着", "头饰", "配饰"]):
            tag = DomainTag(
                category=DomainCategory.CLOTHING,
                confidence=0.80,
                keywords=self._extract_keywords(text, ["服饰", "服装", "穿戴", "衣着", "头饰", "配饰"])
            )
            tags.append(tag)

        # 食
        if any(kw in text for kw in ["饮食", "食物", "菜肴", "烹饪", "食材", "美食"]):
            tag = DomainTag(
                category=DomainCategory.FOOD,
                confidence=0.80,
                keywords=self._extract_keywords(text, ["饮食", "食物", "菜肴", "烹饪", "食材", "美食"])
            )
            tags.append(tag)

        # 住
        if any(kw in text for kw in ["建筑", "房屋", "居住", "住宅", "民居", "村寨"]):
            tag = DomainTag(
                category=DomainCategory.HOUSING,
                confidence=0.80,
                keywords=self._extract_keywords(text, ["建筑", "房屋", "居住", "住宅", "民居", "村寨"])
            )
            tags.append(tag)

        # 行
        if any(kw in text for kw in ["交通", "道路", "出行", "运输", "桥梁", "路径"]):
            tag = DomainTag(
                category=DomainCategory.TRANSPORTATION,
                confidence=0.80,
                keywords=self._extract_keywords(text, ["交通", "道路", "出行", "运输", "桥梁", "路径"])
            )
            tags.append(tag)

        # 文化
        if any(kw in text for kw in ["文化", "传统", "习俗", "信仰", "仪式"]):
            tag = DomainTag(
                category=DomainCategory.CULTURE,
                confidence=0.75,
                keywords=self._extract_keywords(text, ["文化", "传统", "习俗", "信仰", "仪式"])
            )
            tags.append(tag)

        # 在地知识
        if any(kw in text for kw in ["知识", "经验", "技能", "传承", "世代"]):
            tag = DomainTag(
                category=DomainCategory.LOCAL_KNOWLEDGE,
                confidence=0.70,
                keywords=self._extract_keywords(text, ["知识", "经验", "技能", "传承", "世代"])
            )
            tags.append(tag)

        return tags

    def _tag_heritage_domains(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[DomainTag]:
        """标注遗产领域 ⭐"""
        tags = []

        # 查找所有遗产实体
        heritage_entities = [
            e for e in entities
            if e.type in [
                EntityType.TANGIBLE_HERITAGE,
                EntityType.INTANGIBLE_HERITAGE,
                EntityType.NATURAL_HERITAGE
            ]
        ]

        for entity in heritage_entities:
            # 从本体中查询详细分类
            ontology_info = self.ontology.get(entity.text, {})

            # 确定领域类别
            category = self._map_heritage_category(entity.type)

            tag = DomainTag(
                category=category,
                subcategory=entity.category or ontology_info.get('subcategory'),
                sub_subcategory=entity.subcategory or ontology_info.get('sub_subcategory'),
                confidence=entity.confidence,
                keywords=ontology_info.get('keywords', [entity.text]),
                heritage_info={
                    "name": entity.text,
                    "level": entity.heritage_level,
                    "ethnic_group": entity.ethnic_group,
                    "region": entity.region,
                    "unesco_id": entity.unesco_id
                },
                cultural_context=entity.cultural_context
            )
            tags.append(tag)

        return tags

    def _map_heritage_category(self, entity_type: EntityType) -> DomainCategory:
        """映射遗产实体类型到领域类别"""
        mapping = {
            EntityType.INTANGIBLE_HERITAGE: DomainCategory.INTANGIBLE_HERITAGE,
            EntityType.TANGIBLE_HERITAGE: DomainCategory.TANGIBLE_HERITAGE,
            EntityType.NATURAL_HERITAGE: DomainCategory.NATURAL_HERITAGE,
        }
        return mapping.get(entity_type, DomainCategory.CULTURE)

    def _tag_cultural_domains(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[DomainTag]:
        """标注文化习俗领域 ⭐"""
        tags = []

        # 查找文化习俗实体
        cultural_entities = [
            e for e in entities
            if e.type in [
                EntityType.CUSTOM,
                EntityType.RITUAL,
                EntityType.FESTIVAL,
                EntityType.CEREMONY
            ]
        ]

        for entity in cultural_entities:
            # 从本体中查询详细分类
            ontology_info = self.ontology.get(entity.text, {})

            # 确定领域类别
            category = self._map_cultural_category(entity.type)

            tag = DomainTag(
                category=category,
                subcategory=entity.category or ontology_info.get('subcategory'),
                confidence=entity.confidence,
                keywords=ontology_info.get('keywords', [entity.text]),
                cultural_context=entity.cultural_context
            )
            tags.append(tag)

        return tags

    def _map_cultural_category(self, entity_type: EntityType) -> DomainCategory:
        """映射文化实体类型到领域类别"""
        mapping = {
            EntityType.CUSTOM: DomainCategory.CUSTOM,
            EntityType.RITUAL: DomainCategory.RITUAL,
            EntityType.FESTIVAL: DomainCategory.FESTIVAL,
            EntityType.CEREMONY: DomainCategory.CUSTOM,
        }
        return mapping.get(entity_type, DomainCategory.CULTURE)

    def _add_unesco_classification(
        self,
        tags: List[DomainTag],
        entities: List[Entity]
    ) -> List[DomainTag]:
        """添加 UNESCO 分类 ⭐

        UNESCO 非遗五大领域：
        1. 口头传统和表现形式
        2. 表演艺术
        3. 社会实践、仪式、节庆活动
        4. 有关自然界和宇宙的知识和实践
        5. 传统手工艺
        """
        for tag in tags:
            if tag.category == DomainCategory.INTANGIBLE_HERITAGE and tag.subcategory:
                # 根据子类别映射到 UNESCO 领域
                unesco_info = self.unesco_taxonomy.get(tag.subcategory, {})
                tag.unesco_domain = unesco_info.get('domain')
                tag.unesco_subdomain = unesco_info.get('subdomain')

        return tags

    def _extract_keywords(self, text: str, candidates: List[str]) -> List[str]:
        """从文本中提取出现的关键词"""
        return [kw for kw in candidates if kw in text]

    def _deduplicate_tags(self, tags: List[DomainTag]) -> List[DomainTag]:
        """去重领域标签"""
        if not tags:
            return []

        # 按类别+子类别去重
        unique_tags = {}
        for tag in tags:
            key = f"{tag.category.value}|{tag.subcategory or ''}"

            if key not in unique_tags:
                unique_tags[key] = tag
            else:
                # 保留置信度更高的
                if tag.confidence > unique_tags[key].confidence:
                    unique_tags[key] = tag

        return list(unique_tags.values())
