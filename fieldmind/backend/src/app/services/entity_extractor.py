"""
实体识别服务
从文本中提取实体（人名、地名、组织、时间等）
"""

import os
from typing import List, Dict, Any, Optional
from app.core.logging import logger


class EntityExtractor:
    """实体提取器"""

    def __init__(self):
        self.model = None

    def extract(self, text: str) -> List[Dict[str, Any]]:
        """
        提取实体

        Args:
            text: 文本内容

        Returns:
            List[Dict]: 实体列表
                [
                    {
                        "text": "十八洞村",
                        "type": "LOCATION",
                        "start": 0,
                        "end": 4,
                        "confidence": 0.95
                    }
                ]
        """
        # 尝试使用不同的NER引擎
        try:
            return self._extract_with_spacy(text)
        except (ImportError, OSError) as exc:
            # spaCy 已安装但中文模型缺失时也必须回退，不能让整条上传链失败。
            logger.warning("spaCy模型不可用，使用规则提取: %s", exc)
            return self._extract_with_rules(text)

    def _extract_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """使用 spaCy 提取实体"""
        import spacy

        # 延迟加载模型
        if self.model is None:
            # 中文模型: zh_core_web_sm
            # 英文模型: en_core_web_sm
            try:
                self.model = spacy.load("zh_core_web_sm")
            except OSError:
                logger.warning("中文模型未安装，尝试英文模型")
                self.model = spacy.load("en_core_web_sm")

        doc = self.model(text)

        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 1.0  # spaCy 不直接提供置信度
            })

        return entities

    def _extract_with_rules(self, text: str) -> List[Dict[str, Any]]:
        """使用规则提取实体（简单版）"""
        import re

        entities = []

        # 规则1: 地名（村/市/省/县/镇）
        location_pattern = r'[一-龥]{2,6}(?:村|市|省|县|镇|区)'
        for match in re.finditer(location_pattern, text):
            entities.append({
                "text": match.group(),
                "type": "LOCATION",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.6
            })

        # 规则2: 人名（简单：姓+名）
        person_pattern = r'(?:张|李|王|刘|陈|杨|黄|赵|周|吴|徐|孙|马|朱|胡|郭|何|高|林|罗|郑|梁|谢|宋|唐|许|韩|冯|邓|曹|彭|曾|肖|田|董|袁|潘|于|蒋|蔡|余|杜|叶|程|苏|魏|吕|丁|任|沈|姚|卢|姜|崔|钟|谭|陆|汪|范|金|石|廖|贾|夏|韦|付|方|白|邹|孟|熊|秦|邱|江|尹|薛|闫|段|雷|侯|龙|史|陶|黎|贺|顾|毛|郝|龚|邵|万|钱|严|覃|武|戴|莫|孔|向)[一-龥]{1,2}'
        for match in re.finditer(person_pattern, text):
            # 避免与地名重复
            if not any(e['start'] == match.start() for e in entities):
                entities.append({
                    "text": match.group(),
                    "type": "PERSON",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.5
                })

        # 规则3: 组织（公司/学校/政府）
        org_pattern = r'[一-龥]{2,10}(?:公司|学校|大学|政府|部门|组织|协会|中心)'
        for match in re.finditer(org_pattern, text):
            if not any(e['start'] == match.start() for e in entities):
                entities.append({
                    "text": match.group(),
                    "type": "ORGANIZATION",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.6
                })

        # 规则4: 时间（简单版）
        time_pattern = r'\d{4}年(?:\d{1,2}月)?(?:\d{1,2}日)?'
        for match in re.finditer(time_pattern, text):
            entities.append({
                "text": match.group(),
                "type": "DATE",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8
            })

        return entities


class EntityDeduplicator:
    """实体去重和标准化"""

    @staticmethod
    def deduplicate(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重实体

        Args:
            entities: 原始实体列表

        Returns:
            List[Dict]: 去重后的实体
        """
        # 按位置去重（保留置信度高的）
        unique = {}

        for entity in entities:
            key = (entity['start'], entity['end'])

            if key not in unique or entity['confidence'] > unique[key]['confidence']:
                unique[key] = entity

        return list(unique.values())

    @staticmethod
    def normalize(entity_text: str, entity_type: str) -> str:
        """
        标准化实体文本

        Args:
            entity_text: 实体文本
            entity_type: 实体类型

        Returns:
            str: 标准化后的文本
        """
        # 去除空白
        text = entity_text.strip()

        # 类型特定的标准化
        if entity_type == "LOCATION":
            # 地名：保持原样
            pass

        elif entity_type == "PERSON":
            # 人名：保持原样
            pass

        elif entity_type == "DATE":
            # 时间：可以转换为标准格式
            pass

        return text
