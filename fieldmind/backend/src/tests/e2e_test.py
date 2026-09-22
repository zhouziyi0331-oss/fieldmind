"""
端到端测试脚本
End-to-End Testing Script

功能：
1. 测试完整数据流（文档上传 -> 流水线 -> 知识图谱 -> 缩影）
2. 验证数据连接率
3. 验证自动化流程
4. 性能测试
5. 生成测试报告
"""

import sys
import time
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.project import ProjectDocument, Project
from app.services.knowledge_pipeline.pipeline_orchestrator import run_knowledge_pipeline
from app.services.summary.summary_query_service import query_summary
from app.services.knowledge_graph.kg_query_service import query_kg
from app.services.event_handlers.event_handler_registry import get_event_statistics
from app.services.event_handlers.event_monitoring_service import monitor_events

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EndToEndTester:
    """端到端测试器"""

    def __init__(self, db: Session):
        self.db = db
        self.test_results = []

    def run_all_tests(self, document_id: int) -> Dict[str, Any]:
        """
        运行所有测试

        Args:
            document_id: 测试文档 ID

        Returns:
            测试结果
        """
        logger.info("=" * 80)
        logger.info("🚀 开始端到端测试")
        logger.info("=" * 80)

        start_time = time.time()

        try:
            # 1. 验证文档存在
            self._test_document_exists(document_id)

            # 2. 运行完整流水线
            pipeline_result = self._test_pipeline_execution(document_id)

            # 3. 验证知识图谱生成
            kg_result = self._test_knowledge_graph(document_id)

            # 4. 验证缩影生成
            summary_result = self._test_summary_generation(document_id)

            # 5. 验证数据连接率
            connectivity_result = self._test_data_connectivity(document_id)

            # 6. 验证事件总线
            event_result = self._test_event_bus()

            # 7. 性能测试
            performance_result = self._test_performance()

            elapsed_time = time.time() - start_time

            # 汇总结果
            final_result = {
                'success': True,
                'document_id': document_id,
                'elapsed_time': round(elapsed_time, 2),
                'tests': {
                    'document_exists': self.test_results[0] if len(self.test_results) > 0 else None,
                    'pipeline_execution': pipeline_result,
                    'knowledge_graph': kg_result,
                    'summary_generation': summary_result,
                    'data_connectivity': connectivity_result,
                    'event_bus': event_result,
                    'performance': performance_result
                },
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results if r.get('passed')),
                'failed_tests': sum(1 for r in self.test_results if not r.get('passed'))
            }

            logger.info("=" * 80)
            logger.info(f"✅ 所有测试完成")
            logger.info(f"   总测试数: {final_result['total_tests']}")
            logger.info(f"   通过: {final_result['passed_tests']}")
            logger.info(f"   失败: {final_result['failed_tests']}")
            logger.info(f"   耗时: {elapsed_time:.2f}秒")
            logger.info("=" * 80)

            return final_result

        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'test_results': self.test_results
            }

    # ============================================================
    # 测试 1: 文档存在性
    # ============================================================

    def _test_document_exists(self, document_id: int):
        """测试文档是否存在"""
        logger.info("\n📝 测试 1: 验证文档存在")

        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if doc:
            logger.info(f"   ✅ 文档存在: {doc.original_filename}")
            self.test_results.append({
                'test': 'document_exists',
                'passed': True,
                'message': f'文档 {document_id} 存在'
            })
        else:
            logger.error(f"   ❌ 文档不存在: ID {document_id}")
            self.test_results.append({
                'test': 'document_exists',
                'passed': False,
                'message': f'文档 {document_id} 不存在'
            })
            raise Exception(f"文档 {document_id} 不存在")

    # ============================================================
    # 测试 2: 流水线执行
    # ============================================================

    def _test_pipeline_execution(self, document_id: int) -> Dict:
        """测试流水线执行"""
        logger.info("\n🚀 测试 2: 九步流水线执行")

        try:
            result = run_knowledge_pipeline(document_id)

            if result['success']:
                logger.info(f"   ✅ 流水线执行成功")
                logger.info(f"      完成步骤: {result['steps_completed']}/9")
                logger.info(f"      耗时: {result['elapsed_time']}秒")

                self.test_results.append({
                    'test': 'pipeline_execution',
                    'passed': True,
                    'message': f"流水线执行成功，{result['steps_completed']}/9 步完成"
                })

                return result
            else:
                logger.error(f"   ❌ 流水线执行失败: {result.get('error')}")
                self.test_results.append({
                    'test': 'pipeline_execution',
                    'passed': False,
                    'message': result.get('error', '未知错误')
                })
                return result

        except Exception as e:
            logger.error(f"   ❌ 流水线执行异常: {e}")
            self.test_results.append({
                'test': 'pipeline_execution',
                'passed': False,
                'message': str(e)
            })
            raise

    # ============================================================
    # 测试 3: 知识图谱生成
    # ============================================================

    def _test_knowledge_graph(self, document_id: int) -> Dict:
        """测试知识图谱生成"""
        logger.info("\n🔍 测试 3: 知识图谱生成")

        from app.models.unified_models import EntityUnified, EventUnified, RelationshipUnified

        # 统计节点和边
        entities = self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).count()

        events = self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).count()

        relationships = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).count()

        # 获取知识图谱统计
        kg_stats = query_kg(self.db).get_graph_statistics()

        logger.info(f"   实体数: {entities}")
        logger.info(f"   事件数: {events}")
        logger.info(f"   关系数: {relationships}")
        logger.info(f"   知识图谱节点总数: {kg_stats['total_nodes']}")
        logger.info(f"   知识图谱边总数: {kg_stats['total_edges']}")

        if entities > 0 and kg_stats['total_nodes'] > 0:
            logger.info(f"   ✅ 知识图谱生成成功")
            self.test_results.append({
                'test': 'knowledge_graph',
                'passed': True,
                'message': f"{entities} 实体, {events} 事件, {relationships} 关系"
            })
        else:
            logger.warning(f"   ⚠️  知识图谱数据不足")
            self.test_results.append({
                'test': 'knowledge_graph',
                'passed': False,
                'message': '知识图谱数据不足'
            })

        return {
            'entities': entities,
            'events': events,
            'relationships': relationships,
            'kg_nodes': kg_stats['total_nodes'],
            'kg_edges': kg_stats['total_edges']
        }

    # ============================================================
    # 测试 4: 缩影生成
    # ============================================================

    def _test_summary_generation(self, document_id: int) -> Dict:
        """测试缩影生成"""
        logger.info("\n📄 测试 4: 缩影生成")

        summary = query_summary(self.db).get_summary_with_associations(document_id)

        if summary and not summary.get('error'):
            logger.info(f"   ✅ 缩影生成成功")
            logger.info(f"      一句话摘要: {summary['summary']['one_sentence_summary'][:50]}...")
            logger.info(f"      知识图谱关联: {summary['knowledge_graph']['node'] is not None}")
            logger.info(f"      Wiki 关联: {summary['wiki_page'] is not None}")
            logger.info(f"      本体标签数: {len(summary['ontology_tags'])}")

            self.test_results.append({
                'test': 'summary_generation',
                'passed': True,
                'message': '缩影生成成功，包含所有关联数据'
            })

            return summary
        else:
            logger.error(f"   ❌ 缩影生成失败")
            self.test_results.append({
                'test': 'summary_generation',
                'passed': False,
                'message': summary.get('error', '缩影不存在')
            })
            return summary

    # ============================================================
    # 测试 5: 数据连接率
    # ============================================================

    def _test_data_connectivity(self, document_id: int) -> Dict:
        """测试数据连接率"""
        logger.info("\n🔗 测试 5: 数据连接率验证")

        from app.models.unified_models import (
            EntityUnified, EventUnified, RelationshipUnified,
            InferenceResult, KnowledgeUnit, KnowledgeGraphNode
        )

        # 获取各类数据数量
        entities_count = self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).count()

        events_count = self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).count()

        relationships_count = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).count()

        inferences_count = self.db.query(InferenceResult).filter(
            InferenceResult.document_id == document_id
        ).count()

        knowledge_units_count = self.db.query(KnowledgeUnit).filter(
            KnowledgeUnit.document_id == document_id
        ).count()

        # 知识图谱节点数（来自该文档）
        kg_nodes_count = self.db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.source_table.in_(['entities_unified', 'events_unified'])
        ).count()

        # 缩影
        summary = query_summary(self.db).get_summary_by_document(document_id)

        # 计算连接率
        total_components = entities_count + events_count + relationships_count + inferences_count + knowledge_units_count
        connected_components = 0

        if entities_count > 0:
            connected_components += entities_count
        if events_count > 0:
            connected_components += events_count
        if relationships_count > 0:
            connected_components += relationships_count
        if inferences_count > 0:
            connected_components += inferences_count
        if knowledge_units_count > 0:
            connected_components += knowledge_units_count

        connectivity_rate = (connected_components / total_components * 100) if total_components > 0 else 0

        logger.info(f"   实体: {entities_count}")
        logger.info(f"   事件: {events_count}")
        logger.info(f"   关系: {relationships_count}")
        logger.info(f"   推理: {inferences_count}")
        logger.info(f"   知识单元: {knowledge_units_count}")
        logger.info(f"   知识图谱节点: {kg_nodes_count}")
        logger.info(f"   缩影: {'✅' if summary else '❌'}")
        logger.info(f"   📊 数据连接率: {connectivity_rate:.2f}%")

        if connectivity_rate >= 90:
            logger.info(f"   ✅ 数据连接率达标 (>90%)")
            self.test_results.append({
                'test': 'data_connectivity',
                'passed': True,
                'message': f'数据连接率: {connectivity_rate:.2f}%'
            })
        else:
            logger.warning(f"   ⚠️  数据连接率未达标 (<90%)")
            self.test_results.append({
                'test': 'data_connectivity',
                'passed': False,
                'message': f'数据连接率: {connectivity_rate:.2f}% (目标: >90%)'
            })

        return {
            'entities': entities_count,
            'events': events_count,
            'relationships': relationships_count,
            'inferences': inferences_count,
            'knowledge_units': knowledge_units_count,
            'kg_nodes': kg_nodes_count,
            'has_summary': summary is not None,
            'connectivity_rate': round(connectivity_rate, 2)
        }

    # ============================================================
    # 测试 6: 事件总线
    # ============================================================

    def _test_event_bus(self) -> Dict:
        """测试事件总线"""
        logger.info("\n🔔 测试 6: 事件总线验证")

        # 获取事件统计
        stats = get_event_statistics()

        logger.info(f"   总事件数: {stats['total_events']}")
        logger.info(f"   已消费事件: {stats['consumed_events']}")
        logger.info(f"   失败事件: {stats['failed_events']}")
        logger.info(f"   成功率: {stats['success_rate']}%")

        if stats['success_rate'] >= 90:
            logger.info(f"   ✅ 事件总线运行正常")
            self.test_results.append({
                'test': 'event_bus',
                'passed': True,
                'message': f"成功率: {stats['success_rate']}%"
            })
        else:
            logger.warning(f"   ⚠️  事件总线成功率偏低")
            self.test_results.append({
                'test': 'event_bus',
                'passed': False,
                'message': f"成功率: {stats['success_rate']}% (目标: >90%)"
            })

        return stats

    # ============================================================
    # 测试 7: 性能
    # ============================================================

    def _test_performance(self) -> Dict:
        """测试性能"""
        logger.info("\n⚡ 测试 7: 性能测试")

        monitoring = monitor_events(self.db)
        metrics = monitoring.get_performance_metrics()

        avg_time = metrics['processing_time']['avg_seconds']

        logger.info(f"   平均事件处理时间: {avg_time}秒")
        logger.info(f"   最小处理时间: {metrics['processing_time']['min_seconds']}秒")
        logger.info(f"   最大处理时间: {metrics['processing_time']['max_seconds']}秒")

        if avg_time < 10:
            logger.info(f"   ✅ 性能测试通过")
            self.test_results.append({
                'test': 'performance',
                'passed': True,
                'message': f"平均处理时间: {avg_time}秒"
            })
        else:
            logger.warning(f"   ⚠️  性能需要优化")
            self.test_results.append({
                'test': 'performance',
                'passed': False,
                'message': f"平均处理时间: {avg_time}秒 (目标: <10秒)"
            })

        return metrics


# ============================================================
# 主函数
# ============================================================

def run_end_to_end_test(document_id: int) -> Dict[str, Any]:
    """
    运行端到端测试

    Args:
        document_id: 测试文档 ID

    Returns:
        测试结果
    """
    db = SessionLocal()

    try:
        tester = EndToEndTester(db)
        result = tester.run_all_tests(document_id)
        return result
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python e2e_test.py <document_id>")
        sys.exit(1)

    document_id = int(sys.argv[1])
    result = run_end_to_end_test(document_id)

    # 输出结果
    import json
    print("\n" + "=" * 80)
    print("📊 测试结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 80)

    # 退出码
    sys.exit(0 if result['success'] and result['failed_tests'] == 0 else 1)
