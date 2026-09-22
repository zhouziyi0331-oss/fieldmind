"""
九步流水线协调器
Knowledge Pipeline Orchestrator

功能：
1. 统一调度 Step 1-9
2. 管理步骤依赖关系
3. 错误处理和重试
4. 进度跟踪
5. 事件发布
6. 性能监控
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import Dict, Any, Callable
import time
from datetime import datetime

from app.core.database import SessionLocal
from app.services.event_bus import publish_event, EventTypes

# 导入所有步骤服务
from app.services.knowledge_pipeline.step1_text_cleaning import clean_document_text
from app.services.knowledge_pipeline.step2_structure_analysis import analyze_document_structure
from app.services.knowledge_pipeline.step3_entity_extraction import extract_document_entities
from app.services.knowledge_pipeline.step4_event_extraction import extract_document_events
from app.services.knowledge_pipeline.step5_relationship_discovery import discover_document_relationships
from app.services.knowledge_pipeline.step6_ontology_construction import build_document_ontology
from app.services.knowledge_pipeline.step7_logical_inference import perform_document_inference
from app.services.knowledge_pipeline.step8_knowledge_unitization import create_document_knowledge_units
from app.services.knowledge_pipeline.step9_reader_generation import generate_document_readers

logger = logging.getLogger(__name__)


class KnowledgePipeline:
    """九步流水线协调器"""

    def __init__(self, db: Session):
        self.db = db
        self.steps = {
            1: {'name': 'text_cleaning', 'func': clean_document_text, 'required': True},
            2: {'name': 'structure_analysis', 'func': analyze_document_structure, 'required': True},
            3: {'name': 'entity_extraction', 'func': extract_document_entities, 'required': True},
            4: {'name': 'event_extraction', 'func': extract_document_events, 'required': True},
            5: {'name': 'relationship_discovery', 'func': discover_document_relationships, 'required': True},
            6: {'name': 'ontology_construction', 'func': build_document_ontology, 'required': False},
            7: {'name': 'logical_inference', 'func': perform_document_inference, 'required': False},
            8: {'name': 'knowledge_unitization', 'func': create_document_knowledge_units, 'required': True},
            9: {'name': 'reader_generation', 'func': generate_document_readers, 'required': False}
        }

    def run(self, document_id: int, skip_steps: list = None) -> Dict[str, Any]:
        """
        运行完整的九步流水线

        Args:
            document_id: 文档 ID
            skip_steps: 要跳过的步骤列表（如 [6, 7]）

        Returns:
            流水线执行结果
        """
        logger.info(f"🚀 九步流水线启动 - 文档 {document_id}")

        start_time = time.time()
        skip_steps = skip_steps or []

        # 发布开始事件
        publish_event(
            event_type=EventTypes.PIPELINE_STARTED,
            payload={
                'document_id': document_id,
                'total_steps': 9,
                'skip_steps': skip_steps
            },
            publisher='KnowledgePipeline'
        )

        results = {}
        errors = {}

        try:
            # 获取项目 ID
            from app.models.project import ProjectDocument
            doc = self.db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc:
                raise Exception(f"文档 {document_id} 不存在")

            project_id = doc.project_id

            # 依次执行九步
            for step_num in range(1, 10):
                if step_num in skip_steps:
                    logger.info(f"⏭️ 跳过 Step {step_num}")
                    continue

                step_info = self.steps[step_num]
                step_name = step_info['name']
                step_func = step_info['func']
                is_required = step_info['required']

                try:
                    logger.info(f"▶️ 执行 Step {step_num}: {step_name}")

                    # 执行步骤
                    if step_num == 6:
                        # Step 6 需要 project_id
                        result = self._execute_step(
                            step_num, step_name, step_func,
                            self.db, project_id, document_id
                        )
                    else:
                        result = self._execute_step(
                            step_num, step_name, step_func,
                            self.db, document_id
                        )

                    results[step_num] = result

                    logger.info(f"✅ Step {step_num} 完成")

                except Exception as e:
                    error_msg = f"Step {step_num} ({step_name}) 失败: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors[step_num] = error_msg

                    # 如果是必需步骤，终止流水线
                    if is_required:
                        logger.error(f"❌ 必需步骤失败，终止流水线")
                        raise Exception(f"必需步骤 {step_num} 失败")
                    else:
                        logger.warning(f"⚠️ 可选步骤失败，继续执行")
                        continue

            # 计算总耗时
            elapsed_time = time.time() - start_time

            # 流水线成功完成
            final_result = {
                'success': True,
                'document_id': document_id,
                'project_id': project_id,
                'steps_completed': len(results),
                'steps_failed': len(errors),
                'total_steps': 9,
                'elapsed_time': round(elapsed_time, 2),
                'results': results,
                'errors': errors if errors else None
            }

            logger.info(
                f"🎉 九步流水线完成 - 文档 {document_id}, "
                f"耗时 {elapsed_time:.2f}秒, "
                f"成功 {len(results)}/{9} 步"
            )

            # 发布完成事件
            publish_event(
                event_type=EventTypes.PIPELINE_COMPLETED,
                payload=final_result,
                publisher='KnowledgePipeline'
            )

            return final_result

        except Exception as e:
            elapsed_time = time.time() - start_time

            error_result = {
                'success': False,
                'document_id': document_id,
                'steps_completed': len(results),
                'steps_failed': len(errors) + 1,
                'elapsed_time': round(elapsed_time, 2),
                'error': str(e),
                'results': results,
                'errors': errors
            }

            logger.error(f"❌ 九步流水线失败 - 文档 {document_id}: {e}")

            # 发布失败事件
            publish_event(
                event_type=EventTypes.PIPELINE_FAILED,
                payload=error_result,
                publisher='KnowledgePipeline'
            )

            return error_result

    def _execute_step(
        self,
        step_num: int,
        step_name: str,
        step_func: Callable,
        *args
    ) -> Dict[str, Any]:
        """
        执行单个步骤

        Args:
            step_num: 步骤编号
            step_name: 步骤名称
            step_func: 步骤函数
            *args: 步骤函数的参数

        Returns:
            步骤执行结果
        """
        step_start = time.time()

        try:
            # 执行步骤函数
            result = step_func(*args)

            step_elapsed = time.time() - step_start

            # 添加执行时间
            if isinstance(result, dict):
                result['step_elapsed_time'] = round(step_elapsed, 2)

            return result

        except Exception as e:
            logger.error(f"步骤 {step_num} 执行失败: {e}", exc_info=True)
            raise


# ============================================================
# 便捷函数
# ============================================================

def run_knowledge_pipeline(document_id: int, skip_steps: list = None) -> Dict[str, Any]:
    """
    运行九步流水线的便捷函数

    Args:
        document_id: 文档 ID
        skip_steps: 要跳过的步骤列表

    Returns:
        流水线执行结果
    """
    db = SessionLocal()

    try:
        pipeline = KnowledgePipeline(db)
        result = pipeline.run(document_id, skip_steps)
        return result
    finally:
        db.close()


def run_pipeline_for_project(project_id: int, skip_steps: list = None) -> Dict[str, Any]:
    """
    为项目中所有文档运行流水线

    Args:
        project_id: 项目 ID
        skip_steps: 要跳过的步骤列表

    Returns:
        批量执行结果
    """
    db = SessionLocal()

    try:
        from app.models.project import ProjectDocument

        # 获取项目下所有文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

        logger.info(f"📋 为项目 {project_id} 的 {len(documents)} 个文档运行流水线")

        results = []
        success_count = 0
        failed_count = 0

        for doc in documents:
            logger.info(f"处理文档 {doc.id}: {doc.original_filename}")

            try:
                result = run_knowledge_pipeline(doc.id, skip_steps)

                if result.get('success'):
                    success_count += 1
                else:
                    failed_count += 1

                results.append({
                    'document_id': doc.id,
                    'filename': doc.original_filename,
                    'result': result
                })

            except Exception as e:
                logger.error(f"文档 {doc.id} 处理失败: {e}")
                failed_count += 1
                results.append({
                    'document_id': doc.id,
                    'filename': doc.original_filename,
                    'error': str(e)
                })

        return {
            'success': True,
            'project_id': project_id,
            'total_documents': len(documents),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }

    finally:
        db.close()


# ============================================================
# 测试函数
# ============================================================

def test_pipeline(document_id: int):
    """
    测试九步流水线

    Args:
        document_id: 文档 ID
    """
    print(f"\n{'='*60}")
    print(f"测试九步流水线 - 文档 {document_id}")
    print(f"{'='*60}\n")

    result = run_knowledge_pipeline(document_id)

    print(f"\n{'='*60}")
    print(f"流水线执行结果")
    print(f"{'='*60}")
    print(f"成功: {result['success']}")
    print(f"完成步骤: {result['steps_completed']}/{result['total_steps']}")
    print(f"失败步骤: {result['steps_failed']}")
    print(f"总耗时: {result['elapsed_time']}秒")

    if result.get('errors'):
        print(f"\n错误信息:")
        for step_num, error in result['errors'].items():
            print(f"  Step {step_num}: {error}")

    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python pipeline_orchestrator.py <document_id>")
        sys.exit(1)

    document_id = int(sys.argv[1])
    test_pipeline(document_id)
