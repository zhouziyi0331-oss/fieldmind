"""
FieldDimensionAgent - 田野维度解构专员

职责：
1. 根据学术框架对田野资料进行多维度分析
2. 整合项目启用的Skill进行专业维度解构
3. 分析治理、生计、文化、生态等维度
4. 结合实体关系提供更深入的上下文分析
"""

import logging
import importlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class DimensionAnalysis:
    """单个维度的分析结果"""
    dimension_id: str
    dimension_name: str
    matched_count: int
    contexts: List[str]
    entities: List[str]  # 相关实体
    confidence: float


class FieldDimensionAgent(BaseAgent):
    """
    田野维度解构专员

    根据项目启用的Skill对文本进行多维度专业分析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.loaded_skills = {}  # 缓存已加载的skill模块

    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行田野维度解构

        输入:
            - text_content: 文本内容
            - enabled_skills: 启用的skill列表
            - entity_relations: EntityRelationAgent的输出（可选）

        输出:
            - dimensions: 各维度分析结果
            - skill_results: 各skill的完整输出
            - summary: 总体摘要
        """
        text_content = input_data.get('text_content', '')
        enabled_skills = input_data.get('enabled_skills', [])
        entity_relations = input_data.get('entity_relations', {})

        if not text_content:
            raise ValueError("text_content不能为空")

        logger.info(f"🔍 开始田野维度解构 - 启用Skill: {enabled_skills}")

        # 提取实体信息（用于增强分析）
        entities = entity_relations.get('entities', [])
        entity_names = [e.get('name', '') for e in entities]
        entity_types = entity_relations.get('entity_types', {})

        # 执行各个Skill的分析
        skill_results = {}
        all_dimensions = {}

        for skill_id in enabled_skills:
            try:
                skill_result = self._run_skill(skill_id, text_content, entity_relations)
                if skill_result:
                    skill_results[skill_id] = skill_result
                    # 合并维度分析
                    for dim_id, dim_data in skill_result.get('dimensions', {}).items():
                        full_dim_id = f"{skill_id}.{dim_id}"
                        all_dimensions[full_dim_id] = {
                            'skill_id': skill_id,
                            'skill_name': skill_result.get('skill_name', skill_id),
                            'dimension_id': dim_id,
                            'dimension_name': dim_data.get('name', dim_id),
                            'matched_count': dim_data.get('matched_count', 0),
                            'contexts': dim_data.get('contexts', []),
                            'related_entities': self._find_related_entities(
                                dim_data.get('contexts', []),
                                entity_names
                            )
                        }
            except Exception as e:
                logger.error(f"Skill {skill_id} 执行失败: {e}")
                continue

        # 计算总体置信度
        total_matches = sum(
            dim.get('matched_count', 0)
            for dim in all_dimensions.values()
        )
        confidence = min(0.9, total_matches / (len(all_dimensions) * 3)) if all_dimensions else 0.0

        # 生成摘要
        summary = self._generate_summary(all_dimensions, entities)

        result = {
            'dimensions': all_dimensions,
            'skill_results': skill_results,
            'summary': summary,
            'total_dimensions': len(all_dimensions),
            'total_matches': total_matches,
            'entity_count': len(entities)
        }

        logger.info(
            f"✅ 田野维度解构完成 - "
            f"维度数: {len(all_dimensions)}, "
            f"匹配数: {total_matches}, "
            f"置信度: {confidence:.2f}"
        )

        return result

    def _run_skill(
        self,
        skill_id: str,
        text_content: str,
        entity_relations: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        运行单个Skill

        Args:
            skill_id: Skill标识符
            text_content: 文本内容
            entity_relations: 实体关系数据

        Returns:
            Skill分析结果，失败返回None
        """
        try:
            # 加载Skill模块（带缓存）
            if skill_id not in self.loaded_skills:
                module_path = f"app.services.skills.{skill_id}"
                skill_module = importlib.import_module(module_path)
                self.loaded_skills[skill_id] = skill_module
                logger.info(f"📦 加载Skill模块: {module_path}")
            else:
                skill_module = self.loaded_skills[skill_id]

            # 调用Skill的analyze函数
            if hasattr(skill_module, 'analyze'):
                metadata = {'entity_relations': entity_relations}
                result = skill_module.analyze(text_content, metadata)
                return result
            else:
                logger.warning(f"Skill {skill_id} 没有analyze函数")
                return None

        except ModuleNotFoundError:
            logger.error(f"Skill模块不存在: {skill_id}")
            return None
        except Exception as e:
            logger.error(f"运行Skill {skill_id} 时出错: {e}")
            return None

    def _find_related_entities(
        self,
        contexts: List[str],
        entity_names: List[str]
    ) -> List[str]:
        """
        从上下文中找出相关的实体

        Args:
            contexts: 上下文句子列表
            entity_names: 所有实体名称

        Returns:
            出现在上下文中的实体列表
        """
        related = []
        context_text = ' '.join(contexts)

        for entity_name in entity_names:
            if entity_name in context_text:
                related.append(entity_name)

        return related

    def _generate_summary(
        self,
        dimensions: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成维度分析总体摘要

        Args:
            dimensions: 所有维度分析结果
            entities: 实体列表

        Returns:
            摘要信息
        """
        # 按Skill分组统计
        skill_stats = {}
        for dim_id, dim_data in dimensions.items():
            skill_id = dim_data['skill_id']
            if skill_id not in skill_stats:
                skill_stats[skill_id] = {
                    'skill_name': dim_data['skill_name'],
                    'dimension_count': 0,
                    'total_matches': 0,
                    'dimensions': []
                }

            skill_stats[skill_id]['dimension_count'] += 1
            skill_stats[skill_id]['total_matches'] += dim_data['matched_count']
            skill_stats[skill_id]['dimensions'].append({
                'name': dim_data['dimension_name'],
                'matches': dim_data['matched_count']
            })

        # 找出最活跃的维度
        top_dimensions = sorted(
            dimensions.items(),
            key=lambda x: x[1]['matched_count'],
            reverse=True
        )[:5]

        return {
            'skill_stats': skill_stats,
            'top_dimensions': [
                {
                    'id': dim_id,
                    'name': dim_data['dimension_name'],
                    'matches': dim_data['matched_count'],
                    'skill': dim_data['skill_name']
                }
                for dim_id, dim_data in top_dimensions
            ],
            'total_skills': len(skill_stats),
            'total_entities': len(entities)
        }
