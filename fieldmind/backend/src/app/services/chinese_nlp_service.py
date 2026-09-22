#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中文NLP深度优化服务

整合三大中文NLP工具：
- jieba: 中文分词、关键词提取
- LAC: 百度词法分析、实体识别
- HanLP: 多任务NLP处理

作者: FieldMind AI Team
日期: 2026-08-09
版本: 1.0.0
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# 全局服务实例
# ============================================================================
_chinese_nlp_service = None


# ============================================================================
# ChineseNLPService - 中文NLP服务主类
# ============================================================================

class ChineseNLPService:
    """
    中文NLP深度优化服务

    整合三大工具：
    1. jieba - 分词、关键词提取、词性标注
    2. LAC - 百度词法分析、专名识别
    3. HanLP - 多任务NLP、依存分析
    """

    def __init__(
        self,
        enable_jieba: bool = True,
        enable_lac: bool = True,
        enable_hanlp: bool = True,
        custom_dict_path: Optional[str] = None
    ):
        """
        初始化中文NLP服务

        Args:
            enable_jieba: 是否启用jieba
            enable_lac: 是否启用LAC
            enable_hanlp: 是否启用HanLP
            custom_dict_path: 自定义词典路径
        """
        self.enable_jieba = enable_jieba
        self.enable_lac = enable_lac
        self.enable_hanlp = enable_hanlp
        self.custom_dict_path = custom_dict_path

        # 延迟加载的工具实例
        self._jieba = None
        self._lac = None
        self._hanlp = None

        logger.info(f"🇨🇳 中文NLP服务初始化: jieba={enable_jieba}, LAC={enable_lac}, HanLP={enable_hanlp}")

    # ========================================================================
    # jieba 分词工具
    # ========================================================================

    def _get_jieba(self):
        """延迟加载jieba"""
        if self._jieba is None and self.enable_jieba:
            try:
                import jieba
                import jieba.posseg as pseg
                import jieba.analyse

                # 加载自定义词典
                if self.custom_dict_path and os.path.exists(self.custom_dict_path):
                    jieba.load_userdict(self.custom_dict_path)
                    logger.info(f"✅ jieba已加载自定义词典: {self.custom_dict_path}")

                # jieba 的部分发行版没有公开 lcut，统一在这里提供兼容实现，
                # 让关键词、健康检查和主流程使用同一套分词入口。
                lcut = getattr(jieba, "lcut", lambda text: list(jieba.cut(text)))
                self._jieba = {
                    'cut': jieba.cut,
                    'lcut': lcut,
                    'cut_for_search': jieba.cut_for_search,
                    'posseg': pseg,
                    'analyse': jieba.analyse
                }

                logger.info("✅ jieba分词工具已加载")

            except ImportError as e:
                logger.warning(f"⚠️ jieba未安装: {e}")
                self.enable_jieba = False
            except Exception as e:
                logger.error(f"❌ jieba加载失败: {e}")
                self.enable_jieba = False

        return self._jieba

    def jieba_cut(self, text: str, mode: str = 'default') -> List[str]:
        """
        jieba分词

        Args:
            text: 待分词文本
            mode: 分词模式 ('default', 'search', 'full')

        Returns:
            分词结果列表
        """
        jieba_tools = self._get_jieba()
        if not jieba_tools:
            return []

        try:
            if mode == 'search':
                # 搜索引擎模式
                return list(jieba_tools['cut_for_search'](text))
            else:
                # 精确模式
                return jieba_tools['lcut'](text)

        except Exception as e:
            logger.error(f"❌ jieba分词失败: {e}")
            return []

    def jieba_posseg(self, text: str) -> List[Tuple[str, str]]:
        """
        jieba词性标注

        Args:
            text: 待分析文本

        Returns:
            [(词, 词性), ...] 列表
        """
        jieba_tools = self._get_jieba()
        if not jieba_tools:
            return []

        try:
            words = jieba_tools['posseg'].cut(text)
            return [(word.word, word.flag) for word in words]

        except Exception as e:
            logger.error(f"❌ jieba词性标注失败: {e}")
            return []

    def jieba_extract_keywords(
        self,
        text: str,
        topk: int = 10,
        method: str = 'tfidf'
    ) -> List[Dict[str, Any]]:
        """
        jieba关键词提取

        Args:
            text: 待分析文本
            topk: 提取关键词数量
            method: 提取方法 ('tfidf', 'textrank')

        Returns:
            [{'keyword': str, 'weight': float}, ...]
        """
        jieba_tools = self._get_jieba()
        if not jieba_tools:
            return []

        try:
            analyse = jieba_tools['analyse']

            if method == 'textrank':
                # TextRank算法
                keywords = analyse.textrank(text, topK=topk, withWeight=True)
            else:
                # TF-IDF算法（默认）
                keywords = analyse.extract_tags(text, topK=topk, withWeight=True)

            return [
                {'keyword': kw, 'weight': weight}
                for kw, weight in keywords
            ]

        except Exception as e:
            logger.error(f"❌ jieba关键词提取失败: {e}")
            return []

    # ========================================================================
    # LAC 词法分析工具
    # ========================================================================

    def _get_lac(self):
        """延迟加载LAC"""
        if self._lac is None and self.enable_lac:
            try:
                from LAC import LAC

                # 初始化LAC模型
                self._lac = LAC(mode='lac')

                logger.info("✅ LAC词法分析工具已加载")

            except ImportError as e:
                logger.warning(f"⚠️ LAC未安装: {e}")
                self.enable_lac = False
            except Exception as e:
                logger.error(f"❌ LAC加载失败: {e}")
                self.enable_lac = False

        return self._lac

    def lac_analyse(self, text: str) -> Dict[str, Any]:
        """
        LAC词法分析

        Args:
            text: 待分析文本

        Returns:
            {
                'words': List[str],           # 分词结果
                'tags': List[str],            # 词性标注
                'entities': List[Dict]        # 命名实体
            }
        """
        lac_model = self._get_lac()
        if not lac_model:
            return {'words': [], 'tags': [], 'entities': []}

        try:
            # LAC分析
            result = lac_model.run(text)

            words = result[0]  # 分词结果
            tags = result[1]   # 词性标注

            # 提取命名实体
            entities = []
            for i, tag in enumerate(tags):
                # LAC实体标签: PER(人名), LOC(地名), ORG(机构名), TIME(时间)
                if tag in ['PER', 'LOC', 'ORG', 'TIME']:
                    entities.append({
                        'text': words[i],
                        'type': tag,
                        'position': i
                    })

            return {
                'words': words,
                'tags': tags,
                'entities': entities
            }

        except Exception as e:
            logger.error(f"❌ LAC词法分析失败: {e}")
            return {'words': [], 'tags': [], 'entities': []}

    # ========================================================================
    # HanLP 多任务NLP工具
    # ========================================================================

    def _get_hanlp(self):
        """延迟加载HanLP"""
        if self._hanlp is None and self.enable_hanlp:
            try:
                import hanlp

                # 使用多任务模型
                # 注意: 首次使用会下载模型，可能较慢
                self._hanlp = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH)

                logger.info("✅ HanLP多任务模型已加载")

            except ImportError as e:
                logger.warning(f"⚠️ HanLP未安装: {e}")
                self.enable_hanlp = False
            except Exception as e:
                logger.error(f"❌ HanLP加载失败: {e}")
                self.enable_hanlp = False

        return self._hanlp

    def hanlp_parse(self, text: str) -> Dict[str, Any]:
        """
        HanLP深度解析

        Args:
            text: 待分析文本

        Returns:
            {
                'tok': List[str],             # 分词
                'pos': List[str],             # 词性标注
                'ner': List[Tuple],           # 命名实体识别
                'dep': Dict,                  # 依存句法分析
                'srl': Dict                   # 语义角色标注
            }
        """
        hanlp_model = self._get_hanlp()
        if not hanlp_model:
            return {}

        try:
            # HanLP多任务分析
            result = hanlp_model(text)

            return {
                'tok': result.get('tok/fine', []),
                'pos': result.get('pos/ctb', []),
                'ner': result.get('ner/msra', []),
                'dep': result.get('dep', {}),
                'srl': result.get('srl', {})
            }

        except Exception as e:
            logger.error(f"❌ HanLP深度解析失败: {e}")
            return {}

    # ========================================================================
    # 统一接口 - 综合分析
    # ========================================================================

    def analyse_text(self, text: str) -> Dict[str, Any]:
        """
        综合文本分析（整合三个工具）

        Args:
            text: 待分析文本

        Returns:
            {
                'jieba': {
                    'words': List[str],
                    'pos': List[Tuple[str, str]],
                    'keywords': List[Dict]
                },
                'lac': {
                    'words': List[str],
                    'tags': List[str],
                    'entities': List[Dict]
                },
                'hanlp': {
                    'tok': List[str],
                    'pos': List[str],
                    'ner': List[Tuple]
                }
            }
        """
        result = {}

        # jieba分析
        if self.enable_jieba:
            result['jieba'] = {
                'words': self.jieba_cut(text),
                'pos': self.jieba_posseg(text),
                'keywords': self.jieba_extract_keywords(text, topk=5)
            }

        # LAC分析
        if self.enable_lac:
            result['lac'] = self.lac_analyse(text)

        # HanLP分析
        if self.enable_hanlp:
            hanlp_result = self.hanlp_parse(text)
            result['hanlp'] = {
                'tok': hanlp_result.get('tok', []),
                'pos': hanlp_result.get('pos', []),
                'ner': hanlp_result.get('ner', [])
            }

        return result

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        提取命名实体（融合LAC和HanLP结果）

        Args:
            text: 待分析文本

        Returns:
            [
                {
                    'text': str,
                    'type': str,
                    'source': str,  # 'lac' or 'hanlp'
                    'confidence': float
                },
                ...
            ]
        """
        entities = []

        # LAC实体
        if self.enable_lac:
            lac_result = self.lac_analyse(text)
            for entity in lac_result.get('entities', []):
                entities.append({
                    'text': entity['text'],
                    'type': entity['type'],
                    'source': 'lac',
                    'confidence': 0.85
                })

        # HanLP实体
        if self.enable_hanlp:
            hanlp_result = self.hanlp_parse(text)
            ner_list = hanlp_result.get('ner', [])
            for ner_item in ner_list:
                if isinstance(ner_item, tuple) and len(ner_item) >= 2:
                    entities.append({
                        'text': ner_item[0],
                        'type': ner_item[1],
                        'source': 'hanlp',
                        'confidence': 0.90
                    })

        return entities

    # ========================================================================
    # 健康检查
    # ========================================================================

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            {
                'status': str,
                'available': bool,
                'components': {
                    'jieba': bool,
                    'lac': bool,
                    'hanlp': bool
                }
            }
        """
        components = {
            'jieba': False,
            'lac': False,
            'hanlp': False
        }

        # 测试jieba
        if self.enable_jieba:
            try:
                jieba_tools = self._get_jieba()
                if jieba_tools:
                    test_words = list(jieba_tools['lcut']("测试"))
                    components['jieba'] = len(test_words) > 0
            except Exception as e:
                logger.warning(f"Jieba 组件测试失败: {e}")
                pass

        # 测试LAC
        if self.enable_lac:
            try:
                lac_model = self._get_lac()
                if lac_model:
                    result = lac_model.run("测试")
                    components['lac'] = len(result) > 0
            except Exception as e:
                logger.warning(f"LAC 组件测试失败: {e}")
                pass

        # 测试HanLP
        if self.enable_hanlp:
            try:
                hanlp_model = self._get_hanlp()
                if hanlp_model:
                    result = hanlp_model("测试")
                    components['hanlp'] = result is not None
            except Exception as e:
                logger.warning(f"HanLP 组件测试失败: {e}")
                pass

        available = any(components.values())

        return {
            'status': 'ok' if available else 'unavailable',
            'available': available,
            'components': components
        }


# ============================================================================
# 全局服务获取函数
# ============================================================================

def get_chinese_nlp_service() -> ChineseNLPService:
    """获取全局中文NLP服务实例"""
    global _chinese_nlp_service

    if _chinese_nlp_service is None:
        _chinese_nlp_service = ChineseNLPService()

    return _chinese_nlp_service
