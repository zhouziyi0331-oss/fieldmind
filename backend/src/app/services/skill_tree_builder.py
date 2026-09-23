"""
技能树构建器

从SBPACK技能自动构建交互式技能树：
- 基于技能关系自动布局
- 前置技能识别
- 技能等级分层
- 学习路径推荐
- 完全兼容obsidian-skills可视化
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import json
import logging
from collections import defaultdict, deque

from app.models.sbpack import SkillItem
from app.models.skill_system import SkillNode, SkillRelation

logger = logging.getLogger(__name__)


class SkillTreeBuilder:
    """
    技能树构建器

    将SBPACK的扁平技能列表转换为层次化的技能树
    """

    def __init__(self, db: Session):
        self.db = db

    def build_from_sbpack(self, package_id: int) -> Dict[str, Any]:
        """
        从SBPACK构建完整的技能树

        返回：技能树结构和可视化数据
        """
        logger.info(f"开始构建技能树，package_id={package_id}")

        # 1. 加载SBPACK技能
        sbpack_skills = self.db.query(SkillItem).filter(
            SkillItem.package_id == package_id
        ).all()

        if not sbpack_skills:
            logger.warning(f"Package {package_id} 没有技能")
            return {"nodes": [], "edges": []}

        # 2. 转换为技能节点
        skill_nodes = []
        for sbpack_skill in sbpack_skills:
            node = self._create_skill_node(sbpack_skill)
            skill_nodes.append(node)
            self.db.add(node)

        self.db.commit()

        # 3. 分析技能关系
        relations = self._analyze_relations(skill_nodes, sbpack_skills)

        # 4. 保存关系
        for relation in relations:
            self.db.add(relation)

        self.db.commit()

        # 5. 构建层级结构
        tree_structure = self._build_hierarchy(skill_nodes, relations)

        # 6. 自动布局
        layout = self._auto_layout(tree_structure)

        # 7. 更新节点位置
        self._update_node_positions(layout)

        # 8. 生成可视化数据
        viz_data = self._generate_visualization_data(skill_nodes, relations)

        logger.info(f"技能树构建完成：{len(skill_nodes)}个节点，{len(relations)}条关系")

        return viz_data

    def _create_skill_node(self, sbpack_skill: SkillItem) -> SkillNode:
        """从SBPACK技能创建技能节点"""
        # 从RIA++结构提取信息
        execution_steps = sbpack_skill.execution if isinstance(sbpack_skill.execution, list) else []

        # 估算难度（基于压力测试复杂度）
        difficulty = self._estimate_difficulty(sbpack_skill)

        # 估算学习时长（基于执行步骤数量）
        estimated_hours = len(execution_steps) * 0.5  # 每步30分钟

        node = SkillNode(
            sbpack_skill_id=sbpack_skill.id,
            skill_id=sbpack_skill.skill_id,
            name=sbpack_skill.name,
            display_name=sbpack_skill.display_name or sbpack_skill.name,
            description=sbpack_skill.description,
            category=self._extract_category(sbpack_skill),
            rationale=sbpack_skill.rationale,
            interpretation=sbpack_skill.interpretation,
            application_original=sbpack_skill.application_original,
            application_future=sbpack_skill.application_future,
            execution_steps=execution_steps,
            boundaries=sbpack_skill.boundaries,
            difficulty=difficulty,
            estimated_hours=estimated_hours,
            status='locked',  # 默认锁定
            level=0,
            xp=0,
            xp_to_next_level=100
        )

        return node

    def _analyze_relations(
        self,
        nodes: List[SkillNode],
        sbpack_skills: List[SkillItem]
    ) -> List[SkillRelation]:
        """
        分析技能间关系

        基于：
        1. RIA++的I字段（解释）- 查找提及的其他技能
        2. B字段（边界）- 识别前置条件
        3. 名称相似度 - 发现相关技能
        """
        relations = []

        # 创建技能名称到节点的映射
        name_to_node = {node.name: node for node in nodes}
        id_to_node = {node.skill_id: node for node in nodes}

        for i, node in enumerate(nodes):
            sbpack_skill = sbpack_skills[i]

            # 从I字段分析前置关系
            interpretation = sbpack_skill.interpretation or ""
            prerequisites = self._extract_prerequisites_from_text(interpretation, name_to_node)

            for prereq_name in prerequisites:
                if prereq_name in name_to_node:
                    prereq_node = name_to_node[prereq_name]
                    relation = SkillRelation(
                        source_id=prereq_node.id,
                        target_id=node.id,
                        relation_type='prerequisite',
                        strength=0.8,
                        edge_style='solid'
                    )
                    relations.append(relation)

            # 从B字段分析边界关系
            boundaries = sbpack_skill.boundaries or ""
            related_skills = self._extract_related_from_text(boundaries, name_to_node)

            for related_name in related_skills:
                if related_name in name_to_node:
                    related_node = name_to_node[related_name]
                    relation = SkillRelation(
                        source_id=node.id,
                        target_id=related_node.id,
                        relation_type='related',
                        strength=0.5,
                        edge_style='dashed'
                    )
                    relations.append(relation)

        # 基于相似度添加额外关系
        similarity_relations = self._find_similar_skills(nodes)
        relations.extend(similarity_relations)

        return relations

    def _extract_prerequisites_from_text(
        self,
        text: str,
        name_to_node: Dict[str, SkillNode]
    ) -> List[str]:
        """从文本中提取前置技能"""
        prerequisites = []

        # 查找"需要"、"依赖"、"基于"等关键词
        keywords = ["需要", "依赖", "基于", "前提", "prerequisite", "require", "depend"]

        for keyword in keywords:
            if keyword in text:
                # 简单启发式：查找关键词后提到的技能名称
                for skill_name in name_to_node.keys():
                    if skill_name in text:
                        prerequisites.append(skill_name)

        return list(set(prerequisites))

    def _extract_related_from_text(
        self,
        text: str,
        name_to_node: Dict[str, SkillNode]
    ) -> List[str]:
        """从边界文本中提取相关技能"""
        related = []

        # 查找文本中提到的其他技能名称
        for skill_name in name_to_node.keys():
            if skill_name in text and len(skill_name) > 3:  # 避免误匹配短词
                related.append(skill_name)

        return list(set(related))

    def _find_similar_skills(self, nodes: List[SkillNode]) -> List[SkillRelation]:
        """基于名称和描述相似度查找相关技能"""
        relations = []

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                similarity = self._calculate_similarity(node1, node2)

                if similarity > 0.6:  # 相似度阈值
                    relation = SkillRelation(
                        source_id=node1.id,
                        target_id=node2.id,
                        relation_type='related',
                        strength=similarity,
                        edge_style='dotted'
                    )
                    relations.append(relation)

        return relations

    def _calculate_similarity(self, node1: SkillNode, node2: SkillNode) -> float:
        """计算两个技能的相似度"""
        # 简单的词汇重叠相似度
        words1 = set(node1.name.lower().split() + (node1.description or "").lower().split())
        words2 = set(node2.name.lower().split() + (node2.description or "").lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _build_hierarchy(
        self,
        nodes: List[SkillNode],
        relations: List[SkillRelation]
    ) -> Dict[str, Any]:
        """
        构建层级结构

        使用拓扑排序确定技能的层级
        """
        # 构建邻接表
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        node_ids = {node.id for node in nodes}

        for relation in relations:
            if relation.relation_type == 'prerequisite':
                graph[relation.source_id].append(relation.target_id)
                in_degree[relation.target_id] += 1

        # 确保所有节点都在in_degree中
        for node in nodes:
            if node.id not in in_degree:
                in_degree[node.id] = 0

        # 拓扑排序（BFS）
        queue = deque([node_id for node_id in node_ids if in_degree[node_id] == 0])
        tiers = {}
        current_tier = 1

        while queue:
            level_size = len(queue)

            for _ in range(level_size):
                node_id = queue.popleft()
                tiers[node_id] = current_tier

                for neighbor in graph[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            current_tier += 1

        # 处理环（如果有）
        for node_id in node_ids:
            if node_id not in tiers:
                tiers[node_id] = current_tier

        # 按层级分组
        tier_groups = defaultdict(list)
        for node in nodes:
            tier = tiers.get(node.id, 1)
            node.tree_tier = tier
            tier_groups[tier].append(node)

        return {
            "tiers": tiers,
            "tier_groups": dict(tier_groups),
            "max_tier": current_tier
        }

    def _auto_layout(self, tree_structure: Dict[str, Any]) -> Dict[int, Tuple[float, float]]:
        """
        自动布局算法

        返回每个节点的(x, y)坐标
        """
        tier_groups = tree_structure["tier_groups"]
        max_tier = tree_structure["max_tier"]

        layout = {}

        # 垂直间距和水平间距
        vertical_spacing = 150
        horizontal_spacing = 200

        for tier, nodes in tier_groups.items():
            # 计算该层的起始X坐标（居中）
            total_width = (len(nodes) - 1) * horizontal_spacing
            start_x = -total_width / 2

            # Y坐标基于层级
            y = tier * vertical_spacing

            for i, node in enumerate(nodes):
                x = start_x + i * horizontal_spacing
                layout[node.id] = (x, y)

        return layout

    def _update_node_positions(self, layout: Dict[int, Tuple[float, float]]):
        """更新数据库中的节点位置"""
        for node_id, (x, y) in layout.items():
            node = self.db.query(SkillNode).filter(SkillNode.id == node_id).first()
            if node:
                node.tree_position_x = x
                node.tree_position_y = y

        self.db.commit()

    def _generate_visualization_data(
        self,
        nodes: List[SkillNode],
        relations: List[SkillRelation]
    ) -> Dict[str, Any]:
        """
        生成前端可视化所需的数据格式

        兼容D3.js, Cytoscape.js等图可视化库
        """
        viz_nodes = []
        for node in nodes:
            viz_nodes.append({
                "id": node.skill_id,
                "label": node.name,
                "description": node.description[:100] if node.description else "",
                "tier": node.tree_tier,
                "position": {
                    "x": node.tree_position_x or 0,
                    "y": node.tree_position_y or 0
                },
                "status": node.status,
                "level": node.level,
                "difficulty": node.difficulty,
                "category": node.category,
                "color": self._get_node_color(node),
                "size": self._get_node_size(node)
            })

        viz_edges = []
        for i, relation in enumerate(relations):
            source_node = next((n for n in nodes if n.id == relation.source_id), None)
            target_node = next((n for n in nodes if n.id == relation.target_id), None)

            if source_node and target_node:
                viz_edges.append({
                    "id": f"e{i}",
                    "source": source_node.skill_id,
                    "target": target_node.skill_id,
                    "type": relation.relation_type,
                    "strength": relation.strength,
                    "style": relation.edge_style or 'solid'
                })

        return {
            "nodes": viz_nodes,
            "edges": viz_edges,
            "metadata": {
                "totalNodes": len(viz_nodes),
                "totalEdges": len(viz_edges),
                "maxTier": max((n.tree_tier for n in nodes), default=1)
            }
        }

    def _get_node_color(self, node: SkillNode) -> str:
        """根据节点状态获取颜色"""
        status_colors = {
            'locked': '#cccccc',
            'available': '#4CAF50',
            'learning': '#2196F3',
            'mastered': '#FFD700'
        }
        return status_colors.get(node.status, '#cccccc')

    def _get_node_size(self, node: SkillNode) -> int:
        """根据节点重要性获取大小"""
        # 基于入度和出度
        return 30  # 默认大小，可以后续根据关系数量调整

    def _estimate_difficulty(self, skill: SkillItem) -> str:
        """估算技能难度"""
        # 基于验证通过情况和压力测试复杂度
        if not skill.v3_passed:
            return 'beginner'
        elif skill.v1_passed and skill.v2_passed and skill.v3_passed:
            # 检查压力测试数量
            tests = skill.pressure_tests or {}
            total_tests = (
                len(tests.get('should_trigger', [])) +
                len(tests.get('should_not_trigger', [])) +
                len(tests.get('boundary_cases', []))
            )
            if total_tests > 10:
                return 'expert'
            elif total_tests > 5:
                return 'advanced'
            else:
                return 'intermediate'
        return 'beginner'

    def _extract_category(self, skill: SkillItem) -> str:
        """从技能中提取分类"""
        # 从技能名称或描述中推断分类
        name_lower = skill.name.lower()

        categories = {
            '编程': ['code', 'program', 'dev', 'script', '编程', '代码'],
            '设计': ['design', 'ui', 'ux', '设计'],
            '管理': ['manage', 'lead', 'plan', '管理', '领导'],
            '分析': ['analyze', 'data', 'research', '分析', '研究'],
            '沟通': ['communicate', 'present', 'write', '沟通', '表达']
        }

        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category

        return '其他'
