"""
统一业务分析服务注册器和调度器
集成15个商业分析服务（3个已有 + 12个新增）
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
import asyncio
import logging

logger = logging.getLogger(__name__)


class BusinessAnalysisOrchestrator:
    """15个商业分析服务的统一调度器"""

    def __init__(self, db: Session):
        self.db = db
        self._services = {}
        self._initialize_services()

    def _initialize_services(self):
        """初始化所有15个服务"""
        # 已有的3个服务
        try:
            from app.tools.report.business_analysis_service import BusinessAnalysisService
            self._services['01_business_formats'] = BusinessAnalysisService(self.db)
        except Exception as e:
            logger.warning(f"服务01加载失败: {e}")

        try:
            from app.tools.report.creative_analysis_service import CreativeAnalysisService
            self._services['02_creative_analysis'] = CreativeAnalysisService(self.db)
        except Exception as e:
            logger.warning(f"服务02加载失败: {e}")

        try:
            from app.services.skills.business_feasibility import BusinessFeasibilitySkill
            # Skill需要特殊处理，暂时跳过
            logger.info("服务03 BusinessFeasibilitySkill 需要特殊集成")
        except Exception as e:
            logger.warning(f"服务03加载失败: {e}")

        # 新增的12个服务
        try:
            from app.tools.report.market_demand_service import MarketDemandAnalysisService
            self._services['04_market_demand'] = MarketDemandAnalysisService(self.db)
        except Exception as e:
            logger.warning(f"服务04加载失败: {e}")

        try:
            from app.tools.report.competitor_analysis_service import CompetitorAnalysisService
            self._services['05_competitor'] = CompetitorAnalysisService(self.db)
        except Exception as e:
            logger.warning(f"服务05加载失败: {e}")

        # 服务06：定价策略
        try:
            from app.tools.report.pricing_strategy_service import PricingStrategyService
            self._services['06_pricing'] = PricingStrategyService(self.db)
        except Exception as e:
            logger.warning(f"服务06加载失败: {e}")

        # 服务07-15：批量加载
        try:
            from app.tools.report.batch_services_07_15 import (
                CustomerSegmentationService,
                RevenueModelService,
                OperationalCostService,
                RiskAssessmentService,
                GrowthStrategyService,
                PartnershipAnalysisService,
                SustainabilityService,
                RegulationComplianceService,
                InvestmentROIService
            )

            self._services['07_customer_segmentation'] = CustomerSegmentationService(self.db)
            self._services['08_revenue_model'] = RevenueModelService(self.db)
            self._services['09_operational_cost'] = OperationalCostService(self.db)
            self._services['10_risk_assessment'] = RiskAssessmentService(self.db)
            self._services['11_growth_strategy'] = GrowthStrategyService(self.db)
            self._services['12_partnership'] = PartnershipAnalysisService(self.db)
            self._services['13_sustainability'] = SustainabilityService(self.db)
            self._services['14_regulation'] = RegulationComplianceService(self.db)
            self._services['15_investment_roi'] = InvestmentROIService(self.db)

            logger.info("✅ 服务07-15批量加载成功")
        except Exception as e:
            logger.warning(f"服务07-15批量加载失败: {e}")

    async def run_all_services(
        self,
        project_id: int,
        selected_services: List[str] = None
    ) -> Dict[str, Any]:
        """
        运行所有或指定的商业分析服务

        Args:
            project_id: 项目ID
            selected_services: 指定运行的服务列表，如 ['04_market_demand', '05_competitor']
                              如果为None，则运行所有已加载的服务

        Returns:
            {
                'total_services': 15,
                'executed_services': 5,
                'results': {
                    '01_business_formats': {...},
                    '04_market_demand': {...},
                    ...
                },
                'errors': {...}
            }
        """
        logger.info(f"🎯 开始运行商业分析服务 - 项目: {project_id}")

        # 确定要运行的服务
        if selected_services:
            services_to_run = {k: v for k, v in self._services.items() if k in selected_services}
        else:
            services_to_run = self._services

        results = {}
        errors = {}

        # 并发执行所有服务
        tasks = []
        for service_key, service_instance in services_to_run.items():
            tasks.append(self._run_single_service(service_key, service_instance, project_id))

        # 等待所有任务完成
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        for i, (service_key, _) in enumerate(services_to_run.items()):
            result = completed_results[i]
            if isinstance(result, Exception):
                errors[service_key] = str(result)
                logger.error(f"❌ 服务 {service_key} 执行失败: {result}")
            else:
                results[service_key] = result
                logger.info(f"✅ 服务 {service_key} 执行成功")

        return {
            'total_services': 15,
            'executed_services': len(results),
            'failed_services': len(errors),
            'results': results,
            'errors': errors if errors else None
        }

    async def _run_single_service(
        self,
        service_key: str,
        service_instance: Any,
        project_id: int
    ) -> Dict[str, Any]:
        """运行单个服务"""
        try:
            # 检查服务实例的方法
            if hasattr(service_instance, 'analyze'):
                return await service_instance.analyze(project_id)
            elif hasattr(service_instance, 'analyze_business_formats'):
                # BusinessAnalysisService 的特殊方法
                return await service_instance.analyze_business_formats(project_id)
            elif hasattr(service_instance, 'analyze_creative_possibilities'):
                # CreativeAnalysisService 的特殊方法
                keywords = ['文化', '遗产', '传统']  # 默认关键词
                return await service_instance.analyze_creative_possibilities(project_id, keywords)
            else:
                return {
                    'service_id': service_key,
                    'status': 'not_implemented',
                    'message': f'服务 {service_key} 未实现标准接口'
                }
        except Exception as e:
            logger.error(f"服务 {service_key} 执行异常: {e}")
            raise

    def get_service_catalog(self) -> List[Dict[str, str]]:
        """获取15个服务的目录"""
        return [
            {'id': '01', 'name': '商业格式分析', 'key': '01_business_formats', 'status': 'implemented'},
            {'id': '02', 'name': '创意文创分析', 'key': '02_creative_analysis', 'status': 'implemented'},
            {'id': '03', 'name': '商业可行性验证', 'key': '03_business_feasibility', 'status': 'skill_based'},
            {'id': '04', 'name': '市场需求分析', 'key': '04_market_demand', 'status': 'implemented'},
            {'id': '05', 'name': '竞争对手分析', 'key': '05_competitor', 'status': 'implemented'},
            {'id': '06', 'name': '定价策略', 'key': '06_pricing', 'status': 'implemented'},
            {'id': '07', 'name': '客户细分', 'key': '07_customer_segmentation', 'status': 'implemented'},
            {'id': '08', 'name': '收入模型', 'key': '08_revenue_model', 'status': 'implemented'},
            {'id': '09', 'name': '运营成本', 'key': '09_operational_cost', 'status': 'implemented'},
            {'id': '10', 'name': '风险评估', 'key': '10_risk_assessment', 'status': 'implemented'},
            {'id': '11', 'name': '增长策略', 'key': '11_growth_strategy', 'status': 'implemented'},
            {'id': '12', 'name': '合作伙伴', 'key': '12_partnership', 'status': 'implemented'},
            {'id': '13', 'name': '可持续发展', 'key': '13_sustainability', 'status': 'implemented'},
            {'id': '14', 'name': '法规合规', 'key': '14_regulation', 'status': 'implemented'},
            {'id': '15', 'name': '投资回报率', 'key': '15_investment_roi', 'status': 'implemented'}
        ]


# 便捷函数：供SynthesisAgent调用
async def run_business_analysis_suite(
    db_session: Session,
    project_id: int,
    selected_services: List[str] = None
) -> Dict[str, Any]:
    """
    运行完整的15个商业分析服务套件

    Args:
        db_session: 数据库会话
        project_id: 项目ID
        selected_services: 可选，指定要运行的服务列表

    Returns:
        包含所有服务结果的字典
    """
    orchestrator = BusinessAnalysisOrchestrator(db_session)
    return await orchestrator.run_all_services(project_id, selected_services)
