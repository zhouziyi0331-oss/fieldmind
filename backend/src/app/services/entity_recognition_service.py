"""
实体识别服务
专为田野调查设计 - 识别遗产、文化、方言实体
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.models.enriched_chunk import Entity, EntityType

logger = logging.getLogger(__name__)


class EntityRecognitionService:
    """实体识别服务 - 多模型融合"""
    def __init__(self, use_workflow_engine: bool = True):

        # 基础 NER（通用）
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.base_ner = self._init_base_ner()

        # 文化遗产 NER（自定义）⭐
        self.heritage_ner = self._init_heritage_ner()

        # 方言词典（预加载）⭐
        self.dialect_dict = self._load_dialect_dictionary()

        # 遗产知识库（预加载）⭐
        self.heritage_kb = self._load_heritage_knowledge_base()

        logger.info("实体识别服务初始化完成")

    def _init_base_ner(self):
        """初始化基础NER模型"""
        try:
            from transformers import pipeline
            model = pipeline(
                "ner",
                model="hfl/chinese-roberta-wwm-ext",
                aggregation_strategy="simple"
            )
            logger.info("基础NER模型加载成功: hfl/chinese-roberta-wwm-ext")
            return model
        except Exception as e:
            logger.warning(f"基础NER模型加载失败: {e}，使用规则匹配")
            return None

    def _init_heritage_ner(self):
        """初始化文化遗产NER模型 ⭐

        TODO: 使用自定义训练的模型
        当前：使用规则匹配 + 知识库
        """
        # 暂时使用规则匹配，未来可训练专用模型
        logger.info("文化遗产NER：使用规则匹配 + 知识库")
        return None

    def _load_dialect_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """加载方言词典 ⭐

        结构：
        {
            "赶场": {
                "standard": "集市",
                "region": "贵州方言",
                "cultural_meaning": "农村地区定期举行的集市贸易活动",
                "usage_context": "多用于描述乡镇集市"
            },
            ...
        }
        """
        dialect_dict = {
            # 贵州方言
            "赶场": {
                "standard": "集市",
                "region": "贵州方言",
                "cultural_meaning": "农村地区定期举行的集市贸易活动",
                "usage_context": "多用于描述乡镇集市"
            },
            "洋芋": {
                "standard": "土豆",
                "region": "贵州方言",
                "cultural_meaning": "马铃薯的方言说法",
                "usage_context": "日常饮食中常用"
            },
            "背篼": {
                "standard": "背篓",
                "region": "西南方言",
                "cultural_meaning": "用竹篾编制的背负用具",
                "usage_context": "山区农耕劳作"
            },
            "坝坝": {
                "standard": "广场",
                "region": "西南方言",
                "cultural_meaning": "平整的空地或广场",
                "usage_context": "用于晒谷、集会等"
            },
            "摆摊": {
                "standard": "摆摊",
                "region": "通用",
                "cultural_meaning": "在集市上摆设摊位售卖商品",
                "usage_context": "集市贸易"
            },
            # TODO: 从外部文件加载更多方言词
        }

        logger.info(f"方言词典加载完成: {len(dialect_dict)} 个词条")
        return dialect_dict

    def _load_heritage_knowledge_base(self) -> Dict[str, Dict[str, Any]]:
        """加载遗产知识库 ⭐

        结构：
        {
            "布依族蜡染": {
                "type": "intangible_heritage",
                "category": "传统技艺",
                "subcategory": "纺染织绣",
                "level": "国家级",
                "region": "贵州",
                "ethnic_group": "布依族",
                "description": "布依族传统的蜡染技艺..."
            },
            ...
        }
        """
        heritage_kb = {
            # 非物质文化遗产
            "布依族蜡染": {
                "type": "intangible_heritage",
                "category": "传统技艺",
                "subcategory": "纺染织绣",
                "level": "国家级",
                "region": "贵州安顺",
                "ethnic_group": "布依族",
                "description": "布依族传统的蜡染技艺，使用蜡刀点蜡，以蓝靛染色"
            },
            "苗族银饰锻制": {
                "type": "intangible_heritage",
                "category": "传统技艺",
                "subcategory": "金属工艺",
                "level": "国家级",
                "region": "贵州黔东南",
                "ethnic_group": "苗族",
                "description": "苗族传统的银饰制作技艺，包括铸造、锻打、雕刻等工艺"
            },
            "侗族大歌": {
                "type": "intangible_heritage",
                "category": "传统音乐",
                "subcategory": "民歌",
                "level": "世界级",
                "region": "贵州黔东南",
                "ethnic_group": "侗族",
                "unesco_id": "UNESCO-ICH-00202",
                "description": "侗族多声部无伴奏合唱，被誉为'天籁之音'"
            },
            "芦笙": {
                "type": "intangible_heritage",
                "category": "传统音乐",
                "subcategory": "乐器演奏",
                "level": "国家级",
                "region": "西南地区",
                "ethnic_group": "苗族、侗族等",
                "description": "苗族、侗族等民族的传统竹制簧管乐器"
            },

            # 物质文化遗产
            "吊脚楼": {
                "type": "tangible_heritage",
                "category": "传统建筑",
                "subcategory": "民居",
                "level": "省级",
                "region": "西南山区",
                "description": "依山而建的木结构建筑，底层架空"
            },
            "风雨桥": {
                "type": "tangible_heritage",
                "category": "传统建筑",
                "subcategory": "桥梁",
                "level": "国家级",
                "region": "贵州黔东南",
                "ethnic_group": "侗族",
                "description": "侗族特有的廊桥建筑，集桥、廊、亭于一体"
            },

            # 自然遗产
            "梯田": {
                "type": "natural_heritage",
                "category": "农业景观",
                "subcategory": "梯田",
                "level": "国家级",
                "region": "西南山区",
                "description": "山地农业的典型景观，层层叠叠如诗如画"
            },

            # 习俗
            "苗年": {
                "type": "festival",
                "category": "传统节日",
                "level": "国家级",
                "region": "贵州黔东南",
                "ethnic_group": "苗族",
                "description": "苗族最隆重的传统节日，相当于汉族的春节"
            },
            "三月三": {
                "type": "festival",
                "category": "传统节日",
                "level": "国家级",
                "region": "南方地区",
                "description": "多个民族的传统节日，举行歌会、祭祀等活动"
            },

            # TODO: 从外部文件加载更多遗产信息
        }

        logger.info(f"遗产知识库加载完成: {len(heritage_kb)} 个条目")
        return heritage_kb

    def recognize_entities(self, text: str, region: Optional[str] = None) -> List[Entity]:
        """识别所有类型的实体

        Args:
            text: 输入文本
            region: 地域（用于方言识别）

        Returns:
            实体列表
        """
        entities = []

        # 1. 基础实体识别（人名、地名、组织）
        base_entities = self._recognize_base_entities(text)
        entities.extend(base_entities)

        # 2. 文化遗产实体识别 ⭐
        heritage_entities = self._recognize_heritage_entities(text)
        entities.extend(heritage_entities)

        # 3. 方言词识别 ⭐
        dialect_entities = self._recognize_dialect_terms(text, region)
        entities.extend(dialect_entities)

        # 4. 实体去重和合并
        entities = self._merge_overlapping_entities(entities)

        # 5. 实体扩展（添加文化背景）⭐
        entities = self._enrich_entities_with_context(entities)

        logger.info(f"识别实体完成: {len(entities)} 个实体")
        return entities

    def _recognize_base_entities(self, text: str) -> List[Entity]:
        """识别基础实体（人名、地名、组织）"""
        entities = []

        if self.base_ner:
            # 使用模型识别
            try:
                results = self.base_ner(text)
                for result in results:
                    entity_type = self._map_base_entity_type(result.get('entity_group', 'MISC'))
                    entity = Entity(
                        text=result['word'],
                        type=entity_type,
                        start=result['start'],
                        end=result['end'],
                        confidence=result['score']
                    )
                    entities.append(entity)
            except Exception as e:
                logger.error(f"基础NER识别失败: {e}")
        else:
            # 规则匹配（简单版本）
            entities.extend(self._rule_based_base_ner(text))

        return entities

    def _map_base_entity_type(self, ner_label: str) -> EntityType:
        """映射NER标签到EntityType"""
        mapping = {
            'PER': EntityType.PERSON,
            'LOC': EntityType.LOCATION,
            'ORG': EntityType.ORGANIZATION,
        }
        return mapping.get(ner_label, EntityType.PERSON)

    def _rule_based_base_ner(self, text: str) -> List[Entity]:
        """基于规则的基础实体识别"""
        entities = []

        # 简单的人名模式（姓氏 + 1-2个字）
        person_pattern = r'(张|李|王|刘|陈|杨|赵|黄|周|吴|徐|孙|胡|朱|高|林|何|郭|马|罗|梁|宋|郑|谢|韩|唐|冯|于|董|萧|程|曹|袁|邓|许|傅|沈|曾|彭|吕|苏|卢|蒋|蔡|贾|丁|魏|薛|叶|阎|余|潘|杜|戴|夏|钟|汪|田|任|姜|范|方|石|姚|谭|廖|邹|熊|金|陆|郝|孔|白|崔|康|毛|邱|秦|江|史|顾|侯|邵|孟|龙|万|段|雷|钱|汤|尹|黎|易|常|武|乔|贺|赖|龚|文)([一-龥]{1,2})(?:师傅|老师|先生|女士|同志)?'

        for match in re.finditer(person_pattern, text):
            entity = Entity(
                text=match.group(0),
                type=EntityType.PERSON,
                start=match.start(),
                end=match.end(),
                confidence=0.7
            )
            entities.append(entity)

        # 地名模式（省、市、县、村等）
        location_pattern = r'([一-龥]{2,8})(省|市|县|区|镇|乡|村|寨|组)'
        for match in re.finditer(location_pattern, text):
            entity = Entity(
                text=match.group(0),
                type=EntityType.LOCATION,
                start=match.start(),
                end=match.end(),
                confidence=0.75
            )
            entities.append(entity)

        # 组织模式（协会、基金会、委会等）
        org_pattern = r'([一-龥]{2,15})(协会|基金会|委员会|村委会|合作社|公司|组织|NGO)'
        for match in re.finditer(org_pattern, text):
            entity = Entity(
                text=match.group(0),
                type=EntityType.ORGANIZATION,
                start=match.start(),
                end=match.end(),
                confidence=0.75
            )
            entities.append(entity)

        return entities

    def _recognize_heritage_entities(self, text: str) -> List[Entity]:
        """识别文化遗产实体 ⭐"""
        entities = []

        # 基于知识库匹配
        for heritage_name, heritage_info in self.heritage_kb.items():
            # 查找遗产名称在文本中的所有位置
            start = 0
            while True:
                pos = text.find(heritage_name, start)
                if pos == -1:
                    break

                # 映射遗产类型
                entity_type = self._map_heritage_type(heritage_info['type'])

                entity = Entity(
                    text=heritage_name,
                    type=entity_type,
                    start=pos,
                    end=pos + len(heritage_name),
                    confidence=0.95,  # 知识库匹配置信度高
                    category=heritage_info.get('category'),
                    subcategory=heritage_info.get('subcategory'),
                    region=heritage_info.get('region'),
                    ethnic_group=heritage_info.get('ethnic_group'),
                    unesco_id=heritage_info.get('unesco_id'),
                    heritage_level=heritage_info.get('level'),
                    cultural_context=heritage_info.get('description')
                )
                entities.append(entity)

                start = pos + len(heritage_name)

        # 通用遗产模式匹配（未在知识库中的）
        entities.extend(self._pattern_based_heritage_ner(text))

        return entities

    def _map_heritage_type(self, heritage_type: str) -> EntityType:
        """映射遗产类型到EntityType"""
        mapping = {
            'intangible_heritage': EntityType.INTANGIBLE_HERITAGE,
            'tangible_heritage': EntityType.TANGIBLE_HERITAGE,
            'natural_heritage': EntityType.NATURAL_HERITAGE,
            'festival': EntityType.FESTIVAL,
            'custom': EntityType.CUSTOM,
            'ritual': EntityType.RITUAL,
            'ceremony': EntityType.CEREMONY,
        }
        return mapping.get(heritage_type, EntityType.INTANGIBLE_HERITAGE)

    def _pattern_based_heritage_ner(self, text: str) -> List[Entity]:
        """基于模式的遗产实体识别"""
        entities = []

        # 民族 + 技艺/习俗
        ethnic_craft_pattern = r'(苗族|侗族|布依族|水族|彝族|土家族|瑶族|壮族|白族|傣族|哈尼族|藏族|回族|蒙古族|维吾尔族)([一-龥]{2,6})(技艺|工艺|蜡染|刺绣|银饰|服饰|建筑|音乐|舞蹈|歌曲)'
        for match in re.finditer(ethnic_craft_pattern, text):
            entity = Entity(
                text=match.group(0),
                type=EntityType.INTANGIBLE_HERITAGE,
                start=match.start(),
                end=match.end(),
                confidence=0.85,
                ethnic_group=match.group(1),
                category="传统技艺"
            )
            entities.append(entity)

        # 传统节日
        festival_pattern = r'([一-龥]{2,4})(节|年)'
        for match in re.finditer(festival_pattern, text):
            festival_name = match.group(0)
            # 过滤常见词（如"今年"、"明年"）
            if festival_name not in ['今年', '明年', '去年', '前年', '每年', '全年']:
                entity = Entity(
                    text=festival_name,
                    type=EntityType.FESTIVAL,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.75,
                    category="传统节日"
                )
                entities.append(entity)

        # 祭祀活动
        ritual_pattern = r'(祭[一-龥]{1,2})(仪式|活动)?'
        for match in re.finditer(ritual_pattern, text):
            entity = Entity(
                text=match.group(0),
                type=EntityType.RITUAL,
                start=match.start(),
                end=match.end(),
                confidence=0.80,
                category="祭祀"
            )
            entities.append(entity)

        return entities

    def _recognize_dialect_terms(self, text: str, region: Optional[str] = None) -> List[Entity]:
        """识别方言词 ⭐"""
        entities = []

        for dialect_word, info in self.dialect_dict.items():
            # 如果指定了地域，优先匹配该地域的方言
            if region and region not in info['region']:
                continue

            # 查找方言词在文本中的所有位置
            start = 0
            while True:
                pos = text.find(dialect_word, start)
                if pos == -1:
                    break

                entity = Entity(
                    text=dialect_word,
                    type=EntityType.DIALECT_TERM,
                    start=pos,
                    end=pos + len(dialect_word),
                    confidence=0.9,  # 词典匹配置信度高
                    standard_term=info['standard'],
                    dialect_region=info['region'],
                    cultural_context=info.get('cultural_meaning')
                )
                entities.append(entity)

                start = pos + len(dialect_word)

        return entities

    def _merge_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并重叠的实体"""
        if not entities:
            return []

        # 按起始位置排序
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.end))

        merged = []
        current = sorted_entities[0]

        for next_entity in sorted_entities[1:]:
            # 检查是否重叠
            if next_entity.start < current.end:
                # 重叠：选择置信度更高的
                if next_entity.confidence > current.confidence:
                    current = next_entity
            else:
                # 不重叠：保存当前，更新current
                merged.append(current)
                current = next_entity

        merged.append(current)
        return merged

    def _enrich_entities_with_context(self, entities: List[Entity]) -> List[Entity]:
        """为实体添加文化背景 ⭐"""
        for entity in entities:
            # 如果实体已有文化背景，跳过
            if entity.cultural_context:
                continue

            # 从知识库查询
            heritage_info = self.heritage_kb.get(entity.text)
            if heritage_info:
                entity.cultural_context = heritage_info.get('description')
                entity.category = heritage_info.get('category')
                entity.subcategory = heritage_info.get('subcategory')
                entity.heritage_level = heritage_info.get('level')

        return entities
