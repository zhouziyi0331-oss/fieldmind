"""
业务服务07：客户细分服务 (CustomerSegmentationService)
业务服务08：收入模型服务 (RevenueModelService)
业务服务09：运营成本服务 (OperationalCostService)
业务服务10：风险评估服务 (RiskAssessmentService)
业务服务11：增长策略服务 (GrowthStrategyService)
业务服务12：合作伙伴分析服务 (PartnershipAnalysisService)
业务服务13：可持续发展服务 (SustainabilityService)
业务服务14：法规合规服务 (RegulationComplianceService)
业务服务15：投资回报率服务 (InvestmentROIService)

所有服务采用统一接口设计，快速实现核心功能
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session


# ==================== 服务07：客户细分 ====================
class CustomerSegmentationService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        from app.models.project import ProjectDocument
        docs = self.db.query(ProjectDocument).filter_by(project_id=project_id).all()
        context = " ".join([d.text_content[:500] for d in docs[:3] if d.text_content])

        segments = []
        # 遗产专有：文化认同深度分群
        if any(kw in context for kw in ['宗祠', '族谱', '祖先']):
            segments.append({
                'segment': '寻根问祖客（有记忆关联）',
                'cultural_identity': '高',
                'willingness_to_pay': 'very_high',
                'frequency': '年度回访',
                'note': '乡愁客是隐形翅膀，记忆关联是核心驱动'
            })

        segments.append({
            'segment': '文化遗产爱好者',
            'cultural_identity': '中',
            'willingness_to_pay': 'medium',
            'frequency': '偶尔'
        })

        # RFM遗产改造
        rfm_note = "遗产地多访以'年'计（祭祖、节庆），Frequency用年度节庆参与度计算"

        return {
            'service_id': 'customer_segmentation',
            'service_name': '客户细分',
            'segments': segments,
            'core_segment': segments[0] if segments else None,
            'rfm_heritage_adaptation': rfm_note,
            'status': 'completed'
        }


# ==================== 服务08：收入模型 ====================
class RevenueModelService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        revenue_sources = [
            {'source': '门票', 'proportion': 0.3, 'stability': 'high'},
            {'source': '体验课程', 'proportion': 0.25, 'stability': 'medium'},
            {'source': '住宿餐饮', 'proportion': 0.25, 'stability': 'medium'},
            {'source': '文创产品', 'proportion': 0.1, 'stability': 'low'},
            {'source': '遗产专有：谱书档案内容授权', 'proportion': 0.05, 'stability': 'stable'},
            {'source': '遗产专有：政府购买公共文化服务', 'proportion': 0.05, 'stability': 'stable'}
        ]

        return {
            'service_id': 'revenue_model',
            'service_name': '收入模型',
            'revenue_sources': revenue_sources,
            'annual_forecast': {
                'year_1': '保守估算',
                'year_3': '稳定增长',
                'year_5': '成熟运营'
            },
            'heritage_note': '文化保护的公共价值不在收入表里，但需单独说明',
            'status': 'completed'
        }


# ==================== 服务09：运营成本 ====================
class OperationalCostService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        cost_structure = {
            'fixed_costs': [
                {'item': '租金/折旧', 'annual': 'estimated'},
                {'item': '基本人员工资', 'annual': 'estimated'},
                {'item': '遗产专有：文保维护费', 'annual': 'higher_than_modern', 'note': '传统工艺修复成本高'}
            ],
            'variable_costs': [
                {'item': '每客物料成本', 'per_visitor': 'estimated'},
                {'item': '遗产专有：传承人津贴', 'note': '稳定收入是活态传承前提'}
            ],
            'heritage_specific_costs': [
                {'item': '仪式筹备费', 'note': '祭祀、节庆筹备年度固定预算'},
                {'item': '治理成本', 'note': '公共空间维护、共识组织、矛盾调解'}
            ]
        }

        return {
            'service_id': 'operational_cost',
            'service_name': '运营成本',
            'cost_structure': cost_structure,
            'annual_budget': 'to_be_calculated',
            'cost_control_kpis': ['per_visitor_cost', 'labor_efficiency'],
            'status': 'completed'
        }


# ==================== 服务10：风险评估 ====================
class RiskAssessmentService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        from app.models.project import ProjectDocument
        docs = self.db.query(ProjectDocument).filter_by(project_id=project_id).all()
        context = " ".join([d.text_content[:500] for d in docs[:3] if d.text_content])

        risks = []

        # 遗产特有风险清单
        heritage_risks = [
            {
                'risk': '文化失真风险',
                'description': '过度商业化导致传统变形',
                'severity': 'high',
                'mitigation': '传承人伦理第一位，利润分配纳入文化保护基金'
            },
            {
                'risk': '神圣性流失风险',
                'description': '仪式娱乐化、祠堂失去庄严',
                'severity': 'critical',
                'mitigation': '核心祭仪无价、外围观礼可定价'
            },
            {
                'risk': '传承断代风险',
                'description': '传承人离世、无人继承',
                'severity': 'high',
                'mitigation': '建立传承人培养机制'
            },
            {
                'risk': '记忆断代风险',
                'description': '老人离世带走口述记忆',
                'severity': 'high',
                'mitigation': '抢救性建档，年度必做工作'
            }
        ]

        if any(kw in context for kw in ['祠堂', '祭祀', '仪式']):
            risks.extend(heritage_risks)

        # 通用风险
        risks.append({
            'risk': '市场风险',
            'description': '客流不及预期',
            'severity': 'medium',
            'mitigation': '多渠道获客，建立口碑'
        })

        return {
            'service_id': 'risk_assessment',
            'service_name': '风险评估',
            'risk_registry': risks,
            'high_priority_risks': [r for r in risks if r.get('severity') in ['high', 'critical']],
            'contingency_plan': '针对每项高风险制定应急预案',
            'status': 'completed'
        }


# ==================== 服务11：增长策略 ====================
class GrowthStrategyService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        growth_paths = {
            'customer_acquisition': {
                'online': ['社交媒体', 'OTA平台', 'KOL合作'],
                'offline': ['旅行社', '学校研学', '企业团建']
            },
            'brand_building': {
                'strategy': '基于文化遗产内涵打造可传播的故事',
                'heritage_note': '从"流量增长"到"记忆增长"——多访和社群粘性'
            },
            'expansion_strategy': {
                'phase_1': '单点深耕',
                'phase_2': '周边拓展',
                'phase_3': '模式输出（运营模式，非文化符号）'
            },
            'heritage_specific_growth': {
                'strategy': '增长天花板=文化承载量',
                'note': '热闹不能超出村庄严肃，超载的"增长"是自毁式增长',
                'kpi_adjustment': '增加"多访率""仪式参与人数"等记忆型指标'
            }
        }

        return {
            'service_id': 'growth_strategy',
            'service_name': '增长策略',
            'three_year_roadmap': growth_paths,
            'marketing_budget': 'to_be_allocated',
            'growth_kpis': ['CAC', 'LTV', '多访率', '仪式参与度'],
            'status': 'completed'
        }


# ==================== 服务12：合作伙伴 ====================
class PartnershipAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        partner_map = [
            {
                'type': '政府',
                'resources': ['土地/补贴', '政策支持', '审批协调'],
                'value_exchange': '政府给土地，项目给就业和税收'
            },
            {
                'type': '遗产专有：传承人',
                'resources': ['文化内容', '技艺传授', '仪式主持'],
                'ethics': '传承人不是"内容供应商"而是"文化主人"',
                'note': '讲述权、祠堂记忆所有权、知识产权归属必须明确'
            },
            {
                'type': '遗产专有：宗教/信仰组织',
                'resources': ['仪式筹备', '信徒动员', '神圣空间管理'],
                'note': '协作伦理第一位'
            },
            {
                'type': '高校/研究机构',
                'resources': ['学术支持', '研学对接', '深度研究'],
                'value': '学术合作带来身份认证和内容深度'
            },
            {
                'type': '旅行社/OTA',
                'resources': ['流量渠道'],
                'note': '渠道伙伴，但避免过度依赖'
            }
        ]

        return {
            'service_id': 'partnership_analysis',
            'service_name': '合作伙伴分析',
            'partner_map': partner_map,
            'priority_partners': ['传承人', '政府', '高校'],
            'partnership_ethics': '遗产地特殊伙伴差序格局：先本地信任圈，后外部资本',
            'status': 'completed'
        }


# ==================== 服务13：可持续发展 ====================
class SustainabilityService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        sustainability_dimensions = {
            'environmental': {
                'carbon_footprint': 'to_estimate',
                'waste_management': '垃圾处理方案',
                'capacity_limit': '环境承载量测算'
            },
            'cultural': {
                'heritage_protection': '文化遗产底线是遗产项目生命线',
                'living_heritage_kpi': '活态传承指标（传承人数、仪式频次、年轻人参与率）',
                'memory_sustainability': '建立口述档案年度更新机制——记忆是逐年累积的资产'
            },
            'social': {
                'community_benefit': '社区受益方案（本地就业、合作社分红）',
                'local_governance': '治理可持续（差序格局共治）'
            },
            'economic': {
                'financial_viability': '长期财务可行性',
                'subsidy_dependency': '避免过度依赖补贴'
            },
            'heritage_specific_sustainability': {
                'cultural_baseline': '文化底线监控指标独立成章',
                'memory_renewal': '记忆可持续=建档+年度更新',
                'certification_path': '考虑申请中国传统村落、UNWTO Best Tourism Villages等认证'
            }
        }

        return {
            'service_id': 'sustainability',
            'service_name': '可持续发展分析',
            'sustainability_assessment': sustainability_dimensions,
            'monitoring_kpis': ['本地雇工比例', '非遗产品收入占比', '能耗强度', '传承人稳定率'],
            'certification_roadmap': ['绿色旅游认证', '世界最佳旅游乡村'],
            'status': 'completed'
        }


# ==================== 服务14：法规合规 ====================
class RegulationComplianceService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        compliance_checklist = {
            'heritage_specific_regulations': [
                {'regulation': '文物保护法', 'scope': '物质类遗产', 'note': '改造需文保审批'},
                {'regulation': '非物质文化遗产法', 'scope': '非遗类', 'note': '传统技能保护、传承人权益'},
                {'regulation': '历史文化名村名镇保护条例', 'scope': '传统村落', 'note': '建设控制地带内任何改造先审批后动工'},
                {'regulation': '非遗法、商标法', 'scope': '非遗标识使用', 'note': '乱用"非遗"字样有处罚风险'}
            ],
            'operational_permits': [
                {'permit': '消防许可', 'department': '消防局'},
                {'permit': '食品安全许可', 'department': '市场监管局'},
                {'permit': '卫生许可', 'department': '卫健委'}
            ],
            'special_space_compliance': {
                'note': '祠堂庙宇的宗教活动vs经营边界——祭仪属民俗保护活动还是宗教活动需认定清楚'
            },
            'red_lines': [
                '文保红线：先审批后动工，顺序反了无法补救',
                '承载量红线：超载破坏环境和文化'
            ]
        }

        return {
            'service_id': 'regulation_compliance',
            'service_name': '法规合规',
            'compliance_checklist': compliance_checklist,
            'compliance_timeline': '审批周期纳入项目时间表',
            'compliance_cost': '审批费用纳入服务09预算',
            'status': 'completed'
        }


# ==================== 服务15：投资回报率 ====================
class InvestmentROIService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        financial_model = {
            'total_investment': 'to_be_estimated',
            'operating_cost_annual': 'from_service_09',
            'revenue_forecast': 'from_service_08',
            'cash_flow_projection': {
                'year_1': '初期投入期，现金流负',
                'year_2': '运营稳定，现金流转正',
                'year_3_5': '回收期'
            },
            'key_financial_metrics': {
                'static_payback_period': '累计净现金流转正时间',
                'dynamic_payback_period': '考虑贴现的回收期',
                'NPV': '净现值（用行业基准或平均资本成本贴现）',
                'IRR': '内部收益率',
                'ROI': '年均净利润/总投资'
            },
            'heritage_dual_accounting': {
                'financial_roi': '财务ROI',
                'cultural_social_roi': '文化/社区ROI',
                'note': '遗产项目需要双账本：公益性投入+经营性回报，只算财务的把遗产项目永远算不过来账'
            },
            'sensitivity_analysis': {
                'scenarios': ['收入±20%', '成本±20%', '投资额±20%'],
                'heritage_black_swan': '文化事件风险（传承人离世、记忆IP断代）对收入冲击测试'
            },
            'subsidy_accounting': {
                'note': '专项资金、补贴纳入现金流但明确标注占比——警惕"去掉补贴后不成立"的项目'
            }
        }

        return {
            'service_id': 'investment_roi',
            'service_name': '投资回报率分析',
            'financial_model': financial_model,
            'investment_decision': '基于指标和行业对比给出"推荐投资""有条件投资""不建议投资"结论',
            'dual_value_assessment': '财务ROI + 文化/社会ROI并行评估',
            'status': 'completed'
        }
