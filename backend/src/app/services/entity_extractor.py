"""实体提取服务 - 基于HanLP的中文NER"""
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class EntityExtractor:
    """实体提取服务"""

    def __init__(self):
        self.hanlp_model = None
        self.entity_type_map = {
            'PERSON': 'person',
            'LOCATION': 'location',
            'ORGANIZATION': 'organization',
            'TIME': 'time',
            'DATE': 'time',
        }

    def load_model(self):
        """延迟加载HanLP模型"""
        if self.hanlp_model is None:
            try:
                import hanlp
                # 使用多任务模型（包含NER）
                self.hanlp_model = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)
                logger.info("HanLP模型加载成功")
            except Exception as e:
                logger.warning(f"HanLP加载失败，将使用规则方法: {str(e)}")
                self.hanlp_model = None

    def extract_entities(
        self,
        text: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        从文本中提取实体

        Args:
            text: 输入文本
            min_confidence: 最小置信度阈值

        Returns:
            实体列表
        """
        self.load_model()

        if self.hanlp_model:
            return self._extract_with_hanlp(text, min_confidence)
        else:
            return self._extract_with_rules(text)

    def _extract_with_hanlp(
        self,
        text: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """使用HanLP提取实体"""
        try:
            # 处理文本
            result = self.hanlp_model(text, tasks='ner')
            ner_result = result.get('ner/msra', []) or result.get('ner', [])

            entities = []
            entity_names = set()  # 去重

            for entity_list in ner_result:
                for entity, entity_type in entity_list:
                    # 映射实体类型
                    mapped_type = self.entity_type_map.get(entity_type, 'custom')

                    # 去重
                    if entity in entity_names:
                        continue
                    entity_names.add(entity)

                    entities.append({
                        'name': entity,
                        'type': mapped_type,
                        'original_type': entity_type,
                        'confidence': 0.85,  # HanLP没有直接给置信度，设置默认值
                        'method': 'hanlp'
                    })

            logger.info(f"HanLP提取了 {len(entities)} 个实体")
            return entities

        except Exception as e:
            logger.error(f"HanLP提取失败: {str(e)}")
            return self._extract_with_rules(text)

    def _extract_with_rules(self, text: str) -> List[Dict[str, Any]]:
        """使用规则方法提取实体（备用）"""
        entities = []

        # 1. 提取时间实体
        time_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}年\d{1,2}月',
            r'\d{4}年',
            r'\d{1,2}月\d{1,2}日',
        ]

        for pattern in time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'name': match.group(),
                    'type': 'time',
                    'confidence': 0.9,
                    'method': 'regex'
                })

        # 2. 提取可能的地名（包含"村"、"县"、"市"等）
        location_pattern = r'[一-龥]{2,10}[村|镇|乡|县|市|省|区|州]'
        location_matches = re.finditer(location_pattern, text)
        for match in location_matches:
            entities.append({
                'name': match.group(),
                'type': 'location',
                'confidence': 0.7,
                'method': 'regex'
            })

        # 3. 提取可能的组织机构（包含"公司"、"合作社"等）
        org_pattern = r'[一-龥]{2,20}[公司|合作社|协会|中心|局|委员会|学校|医院]'
        org_matches = re.finditer(org_pattern, text)
        for match in org_matches:
            entities.append({
                'name': match.group(),
                'type': 'organization',
                'confidence': 0.7,
                'method': 'regex'
            })

        # 去重
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity['name'] not in seen:
                seen.add(entity['name'])
                unique_entities.append(entity)

        logger.info(f"规则方法提取了 {len(unique_entities)} 个实体")
        return unique_entities

    def extract_and_merge(
        self,
        texts: List[str],
        merge_similar: bool = True
    ) -> List[Dict[str, Any]]:
        """
        从多个文本中提取实体并合并

        Args:
            texts: 文本列表
            merge_similar: 是否合并相似实体

        Returns:
            合并后的实体列表
        """
        all_entities = []

        for text in texts:
            entities = self.extract_entities(text)
            all_entities.extend(entities)

        if merge_similar:
            return self._merge_entities(all_entities)
        else:
            return all_entities

    def _merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并相似实体"""
        merged = {}

        for entity in entities:
            name = entity['name']
            entity_type = entity['type']
            key = f"{entity_type}:{name}"

            if key in merged:
                # 更新统计
                merged[key]['mention_count'] += 1
                # 取最高置信度
                merged[key]['confidence'] = max(
                    merged[key]['confidence'],
                    entity['confidence']
                )
            else:
                merged[key] = {
                    **entity,
                    'mention_count': 1
                }

        return list(merged.values())

    def extract_relationships(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        提取实体之间的关系（简单实现）

        Args:
            text: 文本
            entities: 已提取的实体

        Returns:
            关系列表
        """
        relationships = []

        # 简单的共现关系
        entity_names = [e['name'] for e in entities]

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # 检查两个实体是否在同一句话中
                sentences = re.split(r'[。！？\n]', text)
                for sentence in sentences:
                    if entity1['name'] in sentence and entity2['name'] in sentence:
                        relationships.append({
                            'from': entity1['name'],
                            'from_type': entity1['type'],
                            'to': entity2['name'],
                            'to_type': entity2['type'],
                            'relation': 'co-occurrence',
                            'context': sentence.strip(),
                            'confidence': 0.6
                        })
                        break

        logger.info(f"提取了 {len(relationships)} 个关系")
        return relationships

    def categorize_entity(self, entity_name: str, context: str = "") -> str:
        """
        根据实体名称和上下文推断实体类型

        Args:
            entity_name: 实体名称
            context: 上下文

        Returns:
            实体类型
        """
        # 简单的规则判断
        if any(suffix in entity_name for suffix in ['村', '镇', '乡', '县', '市', '省']):
            return 'location'
        elif any(suffix in entity_name for suffix in ['公司', '合作社', '协会', '中心']):
            return 'organization'
        elif re.match(r'\d{4}', entity_name):
            return 'time'
        else:
            return 'custom'


# 全局实例
entity_extractor = EntityExtractor()
