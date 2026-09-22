"""
商业可行性验证 Skill

基于村庄整体分析，生成经过严格验证的商业方案。
核心立场：不做冰箱贴式伪创意，只做从村庄分析中生长出来、经得起商业验证的在地方案。

输入: ReportMaterial (包含关键词、实体、关系、引用池等)
输出: 商业可行性验证报告 (机会识别 + 创意方案 + 六维打分 + 验证路径)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class AntiPattern:
    """反模式"""
    name: str
    manifestation: str
    fatal_flaw: str


@dataclass
class CommercialOpportunity:
    """商业机会"""
    opportunity_type: str  # 文化空间运营/研学产品/在地风物等
    description: str
    cultural_root: str  # 绑定的文化母题
    evidence: List[str]  # 支撑证据


@dataclass
class CreativeIdea:
    """创意方案"""
    name: str
    four_elements: Dict[str, str]  # 母题/载体/付费点/运营者
    creative_levers: List[str]  # 使用的创意杠杆
    six_dimensions: Dict[str, Dict[str, Any]]  # 六维打分
    total_score: int
    grade: str  # A/B/C
    veto: bool  # 是否一票否决
    next_step: str


@dataclass
class MVPExperiment:
    """最小验证实验"""
    idea_name: str
    experiment_type: str
    validation_method: str
    success_criteria: Dict[str, str]
    estimated_cost: str
    timeline: str


class CommercialFeasibilitySkill:
    """
    商业可行性验证 Skill

    从村庄整体分析出发，识别商业机会、生成创意方案、进行六维验证、设计MVP实验。
    遵循"统筹为纲、跨界赋能、多方共赢、长效为要"四大原则。
    """

    def __init__(self, use_workflow_engine: bool = True):
        """初始化商业可行性验证框架"""



        self.use_workflow_engine = use_workflow_engine



        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

        # 反模式清单
        self.anti_patterns = {
            "符号贴牌": {
                "表现": "文化元素印在通用商品上（冰箱贴、帆布袋、钥匙扣）",
                "死因": "价值独特性为零，任何村都能做"
            },
            "无付费点": {
                "表现": "好看、好拍、有故事，但不产生交易",
                "死因": "需求真实性为零"
            },
            "一次性活动": {
                "表现": "节庆热闹三天，日常无人承接",
                "死因": "规模与持续为零"
            },
            "伪在地": {
                "表现": "换哪个村都能做，与本地文化母题无绑定",
                "死因": "资源真实性为零"
            },
            "自嗨": {
                "表现": "村民与策划者觉得好，市场无人买单",
                "死因": "需求真实性为零"
            },
            "越界": {
                "表现": "违反保护红线或损害社区利益",
                "死因": "一票否决"
            }
        }

        # 四大指导原则
        self.guiding_principles = {
            "统筹为纲": "保护、旅游、商业、社区发展必须纳入同一张蓝图统筹编制",
            "跨界赋能": "打破行业边界，引入文旅、文创、科技、商业等领域资源",
            "多方共赢": "保护成效、商业成功与社区发展三者缺一不可",
            "长效为要": "内容供给与精细运营的持续性，而非一次性投入"
        }

        # 九大商业机会类型
        self.opportunity_types = {
            "文化空间运营": {
                "描述": "老建筑改造为复合型文化空间",
                "典型案例": "古宅书店、祠堂咖啡馆、粮仓美术馆",
                "关键词": ["古建筑", "祠堂", "老屋", "空间", "闲置"]
            },
            "深度研学产品": {
                "描述": "依托在地文化遗产开发研学课程",
                "典型案例": "古法造纸研学、古建测绘营、农耕文明体验",
                "关键词": ["技艺", "传承", "教育", "体验", "学习"]
            },
            "在地风物开发": {
                "描述": "将地方物产与文化IP结合",
                "典型案例": "非遗食材品牌化、传统食养产品化",
                "关键词": ["物产", "食材", "特产", "手工艺", "农产品"]
            },
            "节庆活动策划": {
                "描述": "重构或活化传统节庆",
                "典型案例": "乡村庙会IP化、二十四节气农耕节",
                "关键词": ["节日", "庆典", "仪式", "节气", "庙会"]
            },
            "数字内容生产": {
                "描述": "文化遗产的数字化表达",
                "典型案例": "村落纪录片、非遗短视频、数字文旅地图",
                "关键词": ["故事", "传说", "历史", "记忆", "影像"]
            },
            "场景化餐饮": {
                "描述": "文化与餐饮的深度融合",
                "典型案例": "家宴体验、田野餐桌、传统食养工坊",
                "关键词": ["美食", "饮食", "食俗", "宴席", "厨艺"]
            },
            "主题民宿集群": {
                "描述": "以文化主题统领住宿业态",
                "典型案例": "匠人工作室民宿、书香民宿、农耕主题院落",
                "关键词": ["民居", "院落", "建筑", "居住", "空间"]
            },
            "文创产品体系": {
                "描述": "超越冰箱贴的文化消费级产品",
                "典型案例": "可体验的材料包、有故事的生活器物",
                "关键词": ["器物", "工艺", "手作", "设计", "产品"]
            },
            "社群与会员运营": {
                "描述": "构建文化遗产爱好者社群",
                "典型案例": "村落守护人计划、年卡会员体系",
                "关键词": ["社区", "组织", "网络", "关系", "群体"]
            }
        }

        # 五个创意杠杆
        self.creative_levers = {
            "时间杠杆": "把一年一次的节庆变成日常可体验",
            "空间杠杆": "把闲置空间变成功能场景",
            "角色杠杆": "让村民成为体验的一部分",
            "组合杠杆": "文化A × 现代消费场景B",
            "反向杠杆": "把'日常'变成稀缺商品"
        }

        # 六维验证框架
        self.validation_dimensions = {
            "资源真实性": {
                "核心问题": "创意是否扎根真实文化？",
                "子问题": ["有历史依据吗？", "能自圆其说吗？", "去掉故事包装后还成立吗？"]
            },
            "需求真实性": {
                "核心问题": "有真实付费人群吗？",
                "子问题": ["谁来买？", "为什么现在愿意买？", "愿付多少？", "是刚需还是情怀单？"]
            },
            "供给可行性": {
                "核心问题": "村里做得出来吗？",
                "子问题": ["技能在哪？", "人力在哪？", "成本多高？", "供应链在哪？", "场地在哪？"]
            },
            "价值独特性": {
                "核心问题": "壁垒在哪里？",
                "子问题": ["别人复制要多久？", "本地独占资源是什么？"]
            },
            "规模与持续": {
                "核心问题": "能赚钱且活得久吗？",
                "子问题": ["收入规模与毛利？", "复购/复访？", "季节性平衡？", "三年后靠什么？"]
            },
            "利益兼容": {
                "核心问题": "三方共赢吗？",
                "子问题": ["保护红线？", "社区受益机制？", "商业可持续性？"]
            }
        }

        # MVP验证方式
        self.mvp_methods = {
            "体验类": "不做民宿，先做一日体验；不开课程，先做一场付费测试",
            "产品类": "不铺渠道，先做限量预售 / 定金盲测",
            "IP类": "不做全套VI，先做一款产品测复购",
            "空间类": "不改造，先用临时装置 / 快闪测试人流与停留"
        }

    def extract_cultural_motif(self, report_material: Dict[str, Any]) -> str:
        """
        提取文化母题

        从关键词、实体、引用池中识别核心文化叙事线索
        """
        main_keywords = report_material.get('main_keywords', [])
        core_entities = report_material.get('core_entities', {})
        citation_pool = report_material.get('citation_pool', [])

        # 从主关键词中提取文化线索
        cultural_keywords = []
        for kw_obj in main_keywords[:5]:  # 前5个主关键词
            kw = kw_obj.get('keyword', '') if isinstance(kw_obj, dict) else str(kw_obj)
            if any(marker in kw for marker in ['文化', '传统', '历史', '遗产', '习俗', '民俗', '技艺']):
                cultural_keywords.append(kw)

        # 从实体中提取文化符号（core_entities 是字典）
        cultural_entities = []
        if isinstance(core_entities, dict):
            for entity_type, entity_list in core_entities.items():
                for entity_obj in entity_list[:5]:
                    entity_text = entity_obj.get('entity', '') if isinstance(entity_obj, dict) else str(entity_obj)
                    if any(marker in entity_text for marker in ['族', '村', '寨', '寺', '庙', '祠堂', '古', '传统']):
                        cultural_entities.append(entity_text)

        # 从引用池中提取文化叙事
        cultural_narratives = []
        for citation in citation_pool[:20]:
            text = citation.get('content', '') or citation.get('text', '')
            # 查找包含文化叙事的句子
            if any(marker in text for marker in ['年', '代', '历史', '传承', '传统', '文化', '风俗']):
                # 提取关键信息
                if len(text) < 100:
                    cultural_narratives.append(text)

        # 综合生成文化母题
        motif_parts = []

        if cultural_keywords:
            motif_parts.append(f"以{cultural_keywords[0]}为核心")

        if cultural_entities:
            motif_parts.append(f"的{cultural_entities[0]}")

        if cultural_narratives:
            # 尝试提取时间跨度
            time_match = re.search(r'(\d+)\s*[年代]', cultural_narratives[0])
            if time_match:
                motif_parts.insert(0, f"{time_match.group(1)}年")

        if motif_parts:
            return "".join(motif_parts)
        else:
            return "本地特色文化"

    def identify_commercial_opportunities(
        self,
        report_material: Dict[str, Any],
        cultural_motif: str
    ) -> List[CommercialOpportunity]:
        """
        识别商业机会

        基于村庄资源与九大机会类型，识别潜在商业机会
        """
        opportunities = []

        main_keywords = report_material.get('main_keywords', [])
        core_entities = report_material.get('core_entities', {})
        citation_pool = report_material.get('citation_pool', [])

        # 为每种机会类型评分
        for opp_type, opp_info in self.opportunity_types.items():
            score = 0
            evidence = []

            # 检查关键词匹配
            for kw_obj in main_keywords[:10]:
                kw = kw_obj.get('keyword', '') if isinstance(kw_obj, dict) else str(kw_obj)
                if any(marker in kw for marker in opp_info['关键词']):
                    score += 2
                    if len(evidence) < 3:
                        evidence.append(f"关键资源：{kw}")

            # 检查实体匹配（core_entities 是字典）
            if isinstance(core_entities, dict):
                for entity_type, entity_list in core_entities.items():
                    for entity_obj in entity_list[:10]:
                        entity_text = entity_obj.get('entity', '') if isinstance(entity_obj, dict) else str(entity_obj)
                        if any(marker in entity_text for marker in opp_info['关键词']):
                            score += 1
                            if len(evidence) < 3:
                                evidence.append(f"实体资源：{entity_text}")

            # 从引用池提取支撑证据
            for citation in citation_pool[:30]:
                text = citation.get('content', '') or citation.get('text', '')
                if any(marker in text for marker in opp_info['关键词']):
                    if len(evidence) < 3:
                        evidence.append(f"实例：{text[:50]}...")
                    score += 0.5

            # 如果得分足够高，添加为商业机会
            if score >= 2 and evidence:
                opportunities.append(CommercialOpportunity(
                    opportunity_type=opp_type,
                    description=opp_info['描述'],
                    cultural_root=cultural_motif,
                    evidence=evidence
                ))

        # 按证据数量排序，返回前4个最有潜力的机会
        opportunities.sort(key=lambda x: len(x.evidence), reverse=True)
        return opportunities[:4]

    def generate_creative_ideas(
        self,
        opportunities: List[CommercialOpportunity],
        report_material: Dict[str, Any]
    ) -> List[CreativeIdea]:
        """
        生成创意方案

        基于商业机会，生成具体的创意方案，并进行四要素完整性筛查
        """
        ideas = []

        citation_pool = report_material.get('citation_pool', [])
        core_entities = report_material.get('core_entities', [])

        for opp in opportunities[:3]:  # 对前3个机会生成创意
            # 根据机会类型生成创意方案
            if opp.opportunity_type == "深度研学产品":
                idea_name = self._generate_research_study_idea(opp, citation_pool, core_entities)
                four_elements = self._extract_four_elements_research(opp, citation_pool)
                levers = ["时间杠杆", "角色杠杆"]

            elif opp.opportunity_type == "文化空间运营":
                idea_name = self._generate_space_operation_idea(opp, citation_pool, core_entities)
                four_elements = self._extract_four_elements_space(opp, citation_pool)
                levers = ["空间杠杆", "组合杠杆"]

            elif opp.opportunity_type == "在地风物开发":
                idea_name = self._generate_local_product_idea(opp, citation_pool, core_entities)
                four_elements = self._extract_four_elements_product(opp, citation_pool)
                levers = ["反向杠杆", "组合杠杆"]

            elif opp.opportunity_type == "节庆活动策划":
                idea_name = self._generate_festival_idea(opp, citation_pool, core_entities)
                four_elements = self._extract_four_elements_festival(opp, citation_pool)
                levers = ["时间杠杆", "角色杠杆"]

            else:
                # 通用方案生成
                idea_name = f"{opp.opportunity_type}方案"
                four_elements = {
                    "母题": opp.cultural_root,
                    "载体": opp.description,
                    "付费点": "待明确目标客群",
                    "运营者": "待确定运营主体"
                }
                levers = ["组合杠杆"]

            # 四要素完整性检查
            if self._check_four_elements_completeness(four_elements):
                # 进行六维打分
                six_dimensions = self._validate_six_dimensions(
                    idea_name,
                    four_elements,
                    opp,
                    report_material
                )

                total_score = sum(dim['分数'] for dim in six_dimensions.values())

                # 判断是否一票否决
                veto = (
                    six_dimensions['资源真实性']['分数'] <= 1 or
                    six_dimensions['利益兼容']['分数'] <= 1
                )

                # 分级
                if veto:
                    grade = "否决"
                    next_step = f"一票否决：{self._get_veto_reason(six_dimensions)}"
                elif total_score >= 22 and all(dim['分数'] > 2 for dim in six_dimensions.values()):
                    grade = "A"
                    next_step = "进入最小验证实验设计"
                elif total_score >= 16:
                    grade = "B"
                    next_step = self._get_improvement_suggestions(six_dimensions)
                else:
                    grade = "C"
                    next_step = "暂缓或放弃"

                ideas.append(CreativeIdea(
                    name=idea_name,
                    four_elements=four_elements,
                    creative_levers=levers,
                    six_dimensions=six_dimensions,
                    total_score=total_score,
                    grade=grade,
                    veto=veto,
                    next_step=next_step
                ))

        return ideas

    def _generate_research_study_idea(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict],
        core_entities: Dict[str, List]
    ) -> str:
        """生成研学产品创意名称"""
        # 从证据中提取关键要素
        key_element = ""
        for evidence in opp.evidence:
            if "关键资源" in evidence or "实体资源" in evidence:
                key_element = evidence.split("：")[-1]
                break

        if not key_element and isinstance(core_entities, dict):
            for entity_list in core_entities.values():
                if entity_list:
                    key_element = entity_list[0].get('entity', '') if isinstance(entity_list[0], dict) else str(entity_list[0])
                    break

        return f"{key_element}深度研学体验营" if key_element else "深度研学体验营"

    def _generate_space_operation_idea(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict],
        core_entities: Dict[str, List]
    ) -> str:
        """生成空间运营创意名称"""
        space_type = "文化空间"
        if isinstance(core_entities, dict):
            for entity_list in core_entities.values():
                for entity_obj in entity_list[:5]:
                    entity_text = entity_obj.get('entity', '') if isinstance(entity_obj, dict) else str(entity_obj)
                    if any(marker in entity_text for marker in ['祠堂', '古建', '老屋', '院落', '学校']):
                        space_type = entity_text
                        break
                if space_type != "文化空间":
                    break

        return f"{space_type}复合文化运营"

    def _generate_local_product_idea(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict],
        core_entities: Dict[str, List]
    ) -> str:
        """生成在地风物创意名称"""
        product_type = "在地物产"
        for evidence in opp.evidence:
            if "关键资源" in evidence:
                product_type = evidence.split("：")[-1]
                break

        return f"{product_type}文化品牌化"

    def _generate_festival_idea(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict],
        core_entities: Dict[str, List]
    ) -> str:
        """生成节庆活动创意名称"""
        festival_name = "传统节庆"
        for citation in citation_pool[:20]:
            text = citation.get('content', '') or citation.get('text', '')
            if any(marker in text for marker in ['节', '会', '祭', '庆']):
                # 尝试提取节日名称
                if isinstance(core_entities, dict):
                    for entity_list in core_entities.values():
                        for entity_obj in entity_list:
                            entity_text = entity_obj.get('entity', '') if isinstance(entity_obj, dict) else str(entity_obj)
                            if entity_text in text:
                                festival_name = entity_text
                                break
                        if festival_name != "传统节庆":
                            break
                if festival_name != "传统节庆":
                    break

        return f"{festival_name}日常化体验设计"

    def _extract_four_elements_research(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict]
    ) -> Dict[str, str]:
        """提取研学产品的四要素"""
        return {
            "母题": opp.cultural_root,
            "载体": f"{opp.evidence[0].split('：')[-1] if opp.evidence else '研学场地'} + 传习人带教",
            "付费点": "城市亲子家庭研学市场（学校/机构合作）",
            "运营者": "村集体/合作社 + 返乡青年/文化传承人"
        }

    def _extract_four_elements_space(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict]
    ) -> Dict[str, str]:
        """提取空间运营的四要素"""
        return {
            "母题": opp.cultural_root,
            "载体": f"闲置{opp.evidence[0].split('：')[-1] if opp.evidence else '文化空间'}改造",
            "付费点": "文化体验消费（咖啡/书店/展览/工作坊）",
            "运营者": "社会企业/文创团队 + 村集体"
        }

    def _extract_four_elements_product(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict]
    ) -> Dict[str, str]:
        """提取产品开发的四要素"""
        return {
            "母题": opp.cultural_root,
            "载体": f"{opp.evidence[0].split('：')[-1] if opp.evidence else '在地物产'} + 文化故事包装",
            "付费点": "文化消费品（电商/文旅渠道）",
            "运营者": "村合作社 + 品牌设计团队"
        }

    def _extract_four_elements_festival(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict]
    ) -> Dict[str, str]:
        """提取节庆活动的四要素"""
        return {
            "母题": opp.cultural_root,
            "载体": "传统节庆仪式日常化 + 游客参与设计",
            "付费点": "节庆体验套票（含餐饮/住宿/纪念品）",
            "运营者": "村两委 + 活动策划团队"
        }

    def _check_four_elements_completeness(self, four_elements: Dict[str, str]) -> bool:
        """检查四要素完整性"""
        required = ["母题", "载体", "付费点", "运营者"]
        for key in required:
            if key not in four_elements or not four_elements[key] or "待" in four_elements[key]:
                return False
        return True

    def _validate_six_dimensions(
        self,
        idea_name: str,
        four_elements: Dict[str, str],
        opp: CommercialOpportunity,
        report_material: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        六维验证打分

        基于村庄实际资源和市场逻辑进行打分
        """
        dimensions = {}

        citation_pool = report_material.get('citation_pool', [])

        # 1. 资源真实性
        resource_score = self._score_resource_authenticity(four_elements, opp, citation_pool)
        dimensions['资源真实性'] = {
            '分数': resource_score,
            '依据': self._explain_resource_score(resource_score, opp)
        }

        # 2. 需求真实性
        demand_score = self._score_demand_authenticity(idea_name, four_elements)
        dimensions['需求真实性'] = {
            '分数': demand_score,
            '依据': self._explain_demand_score(demand_score, idea_name)
        }

        # 3. 供给可行性
        supply_score = self._score_supply_feasibility(four_elements, report_material)
        dimensions['供给可行性'] = {
            '分数': supply_score,
            '依据': self._explain_supply_score(supply_score, four_elements)
        }

        # 4. 价值独特性
        uniqueness_score = self._score_value_uniqueness(opp, citation_pool)
        dimensions['价值独特性'] = {
            '分数': uniqueness_score,
            '依据': self._explain_uniqueness_score(uniqueness_score, opp)
        }

        # 5. 规模与持续
        sustainability_score = self._score_sustainability(idea_name, four_elements)
        dimensions['规模与持续'] = {
            '分数': sustainability_score,
            '依据': self._explain_sustainability_score(sustainability_score, idea_name)
        }

        # 6. 利益兼容
        compatibility_score = self._score_benefit_compatibility(four_elements, opp)
        dimensions['利益兼容'] = {
            '分数': compatibility_score,
            '依据': self._explain_compatibility_score(compatibility_score, four_elements)
        }

        return dimensions

    def _score_resource_authenticity(
        self,
        four_elements: Dict[str, str],
        opp: CommercialOpportunity,
        citation_pool: List[Dict]
    ) -> int:
        """评分：资源真实性"""
        score = 3  # 基础分

        # 有明确的文化母题绑定 +1
        if opp.cultural_root and len(opp.cultural_root) > 5:
            score += 1

        # 有实证支撑 +1
        if len(opp.evidence) >= 2:
            score += 1

        return min(score, 5)

    def _score_demand_authenticity(self, idea_name: str, four_elements: Dict[str, str]) -> int:
        """评分：需求真实性"""
        score = 3  # 基础分

        paypoint = four_elements.get('付费点', '')

        # 明确目标客群 +1
        if any(marker in paypoint for marker in ['亲子', '研学', '城市', '游客', '会员']):
            score += 1

        # 有清晰的付费场景 +0.5
        if any(marker in paypoint for marker in ['体验', '产品', '门票', '套票', '会员']):
            score += 0.5

        # 研学市场相对成熟 +0.5
        if '研学' in idea_name:
            score += 0.5

        return min(int(score), 5)

    def _score_supply_feasibility(
        self,
        four_elements: Dict[str, str],
        report_material: Dict[str, Any]
    ) -> int:
        """评分：供给可行性"""
        score = 3  # 基础分

        operator = four_elements.get('运营者', '')

        # 有明确运营主体 +1
        if any(marker in operator for marker in ['村集体', '合作社', '村委', '传承人']):
            score += 1

        # 有外部专业团队支持 +0.5
        if any(marker in operator for marker in ['团队', '企业', '机构']):
            score += 0.5

        # 从引用池判断是否有人才资源
        citation_pool = report_material.get('citation_pool', [])
        has_talent = any(
            any(marker in c.get('text', '') for marker in ['传承人', '手艺人', '能人', '青年'])
            for c in citation_pool[:20]
        )
        if has_talent:
            score += 0.5

        return min(int(score), 5)

    def _score_value_uniqueness(
        self,
        opp: CommercialOpportunity,
        citation_pool: List[Dict]
    ) -> int:
        """评分：价值独特性"""
        score = 3  # 基础分

        # 有明确的独占资源 +1
        if len(opp.evidence) >= 3:
            score += 1

        # 文化根深（时间跨度长）+0.5
        if any(re.search(r'[0-9]{2,}年', e) for e in opp.evidence):
            score += 0.5

        # 有非遗/保护级别 +0.5
        if any(
            any(marker in c.get('text', '') for marker in ['非遗', '文保', '保护', '级'])
            for c in citation_pool[:20]
        ):
            score += 0.5

        return min(int(score), 5)

    def _score_sustainability(self, idea_name: str, four_elements: Dict[str, str]) -> int:
        """评分：规模与持续"""
        score = 3  # 基础分

        # 研学产品可复购 +1
        if '研学' in idea_name:
            score += 1

        # 空间运营可持续 +0.5
        if '空间' in idea_name or '运营' in idea_name:
            score += 0.5

        # 有明确运营者 +0.5
        if '运营者' in four_elements and four_elements['运营者']:
            score += 0.5

        return min(int(score), 5)

    def _score_benefit_compatibility(
        self,
        four_elements: Dict[str, str],
        opp: CommercialOpportunity
    ) -> int:
        """评分：利益兼容"""
        score = 4  # 基础分（假设没有明显冲突）

        operator = four_elements.get('运营者', '')

        # 村集体参与 +1
        if '村集体' in operator or '合作社' in operator:
            score += 1

        # 无明显违规风险 +0（保持4分）
        # 如果有风险会扣分，这里默认无风险

        return min(score, 5)

    def _explain_resource_score(self, score: int, opp: CommercialOpportunity) -> str:
        """解释资源真实性得分"""
        if score >= 4:
            return f"有明确文化根（{opp.cultural_root}），有{len(opp.evidence)}条实证支撑"
        elif score == 3:
            return "有文化依据，但需进一步梳理历史脉络"
        else:
            return "文化根基不明确，存在拼贴风险"

    def _explain_demand_score(self, score: int, idea_name: str) -> str:
        """解释需求真实性得分"""
        if score >= 4:
            return "目标客群明确，付费场景清晰，市场已被验证"
        elif score == 3:
            return "市场需求存在，但需通过MVP验证付费意愿"
        else:
            return "付费点不清晰，需求仅凭感觉"

    def _explain_supply_score(self, score: int, four_elements: Dict[str, str]) -> str:
        """解释供给可行性得分"""
        operator = four_elements.get('运营者', '')
        if score >= 4:
            return f"有运营主体（{operator}），人力与技能缺口可通过培训补足"
        elif score == 3:
            return "基本可行，需引入外部专业团队辅助"
        else:
            return "供给能力不足，需大幅度外部支持"

    def _explain_uniqueness_score(self, score: int, opp: CommercialOpportunity) -> str:
        """解释价值独特性得分"""
        if score >= 4:
            return f"有本地独占资源，他人复制难度高"
        elif score == 3:
            return "有一定独特性，但需强化文化壁垒"
        else:
            return "独特性不足，容易被复制"

    def _explain_sustainability_score(self, score: int, idea_name: str) -> str:
        """解释规模与持续得分"""
        if score >= 4:
            return "有复购/复访机制，可持续运营"
        elif score == 3:
            return "基本可持续，需解决季节性问题"
        else:
            return "持续性存疑，可能一次性活动"

    def _explain_compatibility_score(self, score: int, four_elements: Dict[str, str]) -> str:
        """解释利益兼容得分"""
        if score >= 4:
            return "村集体/社区参与，三方利益平衡"
        elif score == 3:
            return "需进一步设计社区受益机制"
        else:
            return "存在利益冲突或违规风险"

    def _get_veto_reason(self, six_dimensions: Dict[str, Dict[str, Any]]) -> str:
        """获取一票否决原因"""
        if six_dimensions['资源真实性']['分数'] <= 1:
            return "资源真实性不足（文化拼贴）"
        if six_dimensions['利益兼容']['分数'] <= 1:
            return "违反保护红线或损害社区利益"
        return "未知原因"

    def _get_improvement_suggestions(self, six_dimensions: Dict[str, Dict[str, Any]]) -> str:
        """获取改进建议（B级方案）"""
        weak_dimensions = [
            name for name, dim in six_dimensions.items()
            if dim['分数'] <= 2
        ]

        if weak_dimensions:
            return f"需补强：{', '.join(weak_dimensions)}"
        else:
            return "整体可行，建议优化细节后推进"

    def design_mvp_experiments(self, a_grade_ideas: List[CreativeIdea]) -> List[MVPExperiment]:
        """
        设计最小验证实验

        为A级创意方案设计MVP实验
        """
        experiments = []

        for idea in a_grade_ideas:
            # 根据创意类型选择验证方式
            if "研学" in idea.name:
                experiment_type = "体验类"
                validation_method = "面向本地研学机构做一场付费试课，20组家庭"
                success_criteria = {
                    "付费转化率": "≥60%",
                    "复购意向": "≥60%",
                    "NPS净推荐值": "≥40"
                }
                estimated_cost = "5,000-10,000元"
                timeline = "1个月"

            elif "空间" in idea.name or "运营" in idea.name:
                experiment_type = "空间类"
                validation_method = "不改造，先用临时装置/快闪测试人流与停留"
                success_criteria = {
                    "日均人流": "≥50人次",
                    "平均停留时间": "≥30分钟",
                    "消费转化率": "≥20%"
                }
                estimated_cost = "10,000-20,000元"
                timeline = "2个月"

            elif "产品" in idea.name or "品牌" in idea.name:
                experiment_type = "产品类"
                validation_method = "不铺渠道，先做限量预售/定金盲测（100份）"
                success_criteria = {
                    "预售完成率": "≥80%",
                    "客单价": "≥80元",
                    "复购意向": "≥40%"
                }
                estimated_cost = "8,000-15,000元"
                timeline = "1.5个月"

            elif "节庆" in idea.name or "活动" in idea.name:
                experiment_type = "体验类"
                validation_method = "先做一场小型活动测试参与度与付费意愿"
                success_criteria = {
                    "参与人数": "≥100人",
                    "付费转化率": "≥50%",
                    "自发传播量": "≥500次曝光"
                }
                estimated_cost = "15,000-30,000元"
                timeline = "2个月"

            else:
                experiment_type = "综合"
                validation_method = "小规模试运营"
                success_criteria = {
                    "用户满意度": "≥80%",
                    "付费转化率": "≥30%"
                }
                estimated_cost = "10,000-20,000元"
                timeline = "2个月"

            experiments.append(MVPExperiment(
                idea_name=idea.name,
                experiment_type=experiment_type,
                validation_method=validation_method,
                success_criteria=success_criteria,
                estimated_cost=estimated_cost,
                timeline=timeline
            ))

        return experiments

    def generate_report(self, report_material: Dict[str, Any]) -> str:
        """
        生成完整的商业可行性验证报告

        Args:
            report_material: 从 DataDrivenReportBuilder 提取的报告材料

        Returns:
            Markdown 格式的商业可行性验证报告
        """
        # 第一步：提取文化母题
        cultural_motif = self.extract_cultural_motif(report_material)

        # 第二步：识别商业机会
        opportunities = self.identify_commercial_opportunities(report_material, cultural_motif)

        # 第三步：生成创意方案
        creative_ideas = self.generate_creative_ideas(opportunities, report_material)

        # 第四步：为A级方案设计MVP实验
        a_grade_ideas = [idea for idea in creative_ideas if idea.grade == "A"]
        mvp_experiments = self.design_mvp_experiments(a_grade_ideas)

        # 开始构建报告
        content = "# 商业可行性验证报告\n\n"
        content += "> 基于村庄整体分析的商业方案验证\n\n"
        content += "---\n\n"

        # 一、文化母题
        content += "## 一、文化母题识别\n\n"
        content += f"**核心文化叙事**：{cultural_motif}\n\n"
        content += "这是从村庄历史、文化、资源中提炼出的核心叙事线索，是所有商业创意的文化根基。\n\n"
        content += "---\n\n"

        # 二、商业机会识别
        content += "## 二、商业机会图谱\n\n"
        content += f"基于村庄资源盘点，识别出 **{len(opportunities)} 类商业机会**：\n\n"

        for i, opp in enumerate(opportunities, 1):
            content += f"### {i}. {opp.opportunity_type}\n\n"
            content += f"**机会描述**：{opp.description}\n\n"
            content += f"**文化根基**：{opp.cultural_root}\n\n"
            content += "**支撑证据**：\n"
            for evidence in opp.evidence:
                content += f"- {evidence}\n"
            content += "\n"

        content += "---\n\n"

        # 三、创意方案与验证
        content += "## 三、创意方案验证\n\n"
        content += "### 核心立场：不做冰箱贴式伪创意\n\n"
        content += "所有方案必须满足：\n"
        content += "1. **有文化根** - 绑定文化母题\n"
        content += "2. **有付费点** - 明确付费场景与人群\n"
        content += "3. **有运营者** - 村里有人能持续做\n"
        content += "4. **有差异** - 他人难以快速复制\n\n"

        # 分级展示创意方案
        a_grade = [idea for idea in creative_ideas if idea.grade == "A"]
        b_grade = [idea for idea in creative_ideas if idea.grade == "B"]
        c_grade = [idea for idea in creative_ideas if idea.grade == "C"]
        veto_grade = [idea for idea in creative_ideas if idea.grade == "否决"]

        if a_grade:
            content += f"### ✅ A级方案（{len(a_grade)}个）- 可直接推进\n\n"
            for i, idea in enumerate(a_grade, 1):
                content += self._format_idea_detail(idea, i)

        if b_grade:
            content += f"### ⚠️ B级方案（{len(b_grade)}个）- 需补强后推进\n\n"
            for i, idea in enumerate(b_grade, 1):
                content += self._format_idea_summary(idea, i)

        if c_grade:
            content += f"### ❌ C级方案（{len(c_grade)}个）- 暂缓或放弃\n\n"
            for i, idea in enumerate(c_grade, 1):
                content += f"**{i}. {idea.name}**（总分 {idea.total_score}/30）\n\n"
                content += f"- 下一步：{idea.next_step}\n\n"

        if veto_grade:
            content += f"### 🚫 一票否决方案（{len(veto_grade)}个）\n\n"
            for i, idea in enumerate(veto_grade, 1):
                content += f"**{i}. {idea.name}**\n"
                content += f"- 否决原因：{idea.next_step}\n\n"

        content += "---\n\n"

        # 四、最小验证实验设计
        if mvp_experiments:
            content += "## 四、最小验证实验（MVP）\n\n"
            content += "**核心原则**：先验证真实需求，再投入建设。用最小成本买'需求真相'。\n\n"

            for i, exp in enumerate(mvp_experiments, 1):
                content += f"### 实验 {i}：{exp.idea_name}\n\n"
                content += f"**实验类型**：{exp.experiment_type}\n\n"
                content += f"**验证方式**：{exp.validation_method}\n\n"
                content += "**通过标准**：\n"
                for criterion, value in exp.success_criteria.items():
                    content += f"- {criterion}：{value}\n"
                content += f"\n**预算**：{exp.estimated_cost}\n\n"
                content += f"**周期**：{exp.timeline}\n\n"

        content += "---\n\n"

        # 五、四大指导原则检验
        content += "## 五、四大原则检验\n\n"
        content += "所有方案遵循以下原则：\n\n"
        for principle, description in self.guiding_principles.items():
            content += f"**{principle}**：{description}\n\n"

        content += "---\n\n"

        # 六、下一步行动
        content += "## 六、下一步行动\n\n"

        if a_grade:
            content += "### 短期（1个月内）\n\n"
            for idea in a_grade:
                content += f"- [ ] 启动「{idea.name}」最小验证实验\n"
            content += "\n"

        if b_grade:
            content += "### 中期（1-3个月）\n\n"
            for idea in b_grade:
                content += f"- [ ] 补强「{idea.name}」：{idea.next_step}\n"
            content += "\n"

        content += "### 长期（3-6个月）\n\n"
        content += "- [ ] 根据MVP验证结果，启动正式项目设计\n"
        content += "- [ ] 建立内容更新机制与运营接续机制\n"
        content += "- [ ] 构建跨界合作网络（文旅/文创/科技/商业）\n\n"

        return content

    def _format_idea_detail(self, idea: CreativeIdea, index: int) -> str:
        """格式化创意方案详细信息（A级）"""
        content = f"#### 方案 {index}：{idea.name}\n\n"
        content += f"**总分**：{idea.total_score}/30\n\n"

        # 四要素
        content += "**四要素**：\n"
        for key, value in idea.four_elements.items():
            content += f"- **{key}**：{value}\n"
        content += "\n"

        # 创意杠杆
        content += f"**创意杠杆**：{' + '.join(idea.creative_levers)}\n\n"

        # 六维打分
        content += "**六维验证**：\n\n"
        content += "| 维度 | 得分 | 依据 |\n"
        content += "|------|------|------|\n"
        for dim_name, dim_data in idea.six_dimensions.items():
            content += f"| {dim_name} | {dim_data['分数']}/5 | {dim_data['依据']} |\n"
        content += "\n"

        # 下一步
        content += f"**✅ 下一步**：{idea.next_step}\n\n"

        return content

    def _format_idea_summary(self, idea: CreativeIdea, index: int) -> str:
        """格式化创意方案摘要信息（B/C级）"""
        content = f"**{index}. {idea.name}**（总分 {idea.total_score}/30）\n\n"

        # 找出得分最低的维度
        weak_dims = [
            f"{name}({data['分数']}分)"
            for name, data in idea.six_dimensions.items()
            if data['分数'] <= 2
        ]

        if weak_dims:
            content += f"- 短板：{', '.join(weak_dims)}\n"

        content += f"- 下一步：{idea.next_step}\n\n"

        return content


def create_skill():
    """创建 Skill 实例的工厂函数"""
    return CommercialFeasibilitySkill()
