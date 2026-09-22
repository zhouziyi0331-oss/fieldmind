"""
评测引擎 (Evaluation Engine)

核心功能：
1. 固定测试集：每次迭代跑同一套题
2. 四项指标：准确率、召回率、引用正确率、回答完整度
3. 版本对比：自动检测回归
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
from datetime import datetime
from difflib import SequenceMatcher

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EvaluationEngine:
    """
    评测引擎

    使用方法：
    1. 创建测试集：create_test_cases()
    2. 运行评测：run_evaluation()
    3. 查看报告：get_evaluation_report()
    4. 版本对比：compare_versions()
    """

    def __init__(self, db: Session):
        """初始化"""
        self.db = db

    # ============================================================================
    # 一、测试集管理
    # ============================================================================

    def create_test_case(
        self,
        project_id: int,
        question: str,
        expected_answer: str,
        expected_source: Dict[str, Any],
        expected_aspects: List[str],
        category: str = "fact",
        difficulty: str = "medium"
    ) -> int:
        """
        创建单个测试用例

        Args:
            project_id: 项目ID
            question: 问题
            expected_answer: 标准答案
            expected_source: 标准来源 {chunk_id: int, file_id: int, position: str}
            expected_aspects: 标准答案的关键点 ["要点1", "要点2", ...]
            category: 分类 fact/relation/reasoning/summary
            difficulty: 难度 easy/medium/hard

        Returns:
            test_case_id
        """
        insert_sql = text("""
            INSERT INTO evaluation_test_cases (
                project_id, question, expected_answer, expected_source,
                expected_aspects, category, difficulty, created_at
            ) VALUES (
                :project_id, :question, :expected_answer, :expected_source,
                :expected_aspects, :category, :difficulty, CURRENT_TIMESTAMP
            )
        """)

        result = self.db.execute(insert_sql, {
            'project_id': project_id,
            'question': question,
            'expected_answer': expected_answer,
            'expected_source': json.dumps(expected_source, ensure_ascii=False),
            'expected_aspects': json.dumps(expected_aspects, ensure_ascii=False),
            'category': category,
            'difficulty': difficulty
        })

        self.db.commit()
        test_case_id = result.lastrowid

        logger.info(f"创建测试用例 {test_case_id}: {question[:30]}...")
        return test_case_id

    def load_test_cases(self, project_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """加载测试集"""
        query_sql = text("""
            SELECT
                id, question, expected_answer, expected_source,
                expected_aspects, category, difficulty
            FROM evaluation_test_cases
            WHERE project_id = :project_id
              AND (:active_only = 0 OR active = 1)
            ORDER BY category, difficulty, id
        """)

        results = self.db.execute(query_sql, {
            'project_id': project_id,
            'active_only': 1 if active_only else 0
        }).fetchall()

        test_cases = []
        for row in results:
            test_cases.append({
                'id': row.id,
                'question': row.question,
                'expected_answer': row.expected_answer,
                'expected_source': json.loads(row.expected_source) if row.expected_source else {},
                'expected_aspects': json.loads(row.expected_aspects) if row.expected_aspects else [],
                'category': row.category,
                'difficulty': row.difficulty
            })

        logger.info(f"加载项目 {project_id} 的测试集: {len(test_cases)} 个用例")
        return test_cases

    # ============================================================================
    # 二、四项指标计算
    # ============================================================================

    def calc_accuracy(self, agent_answer: str, expected_answer: str) -> float:
        """
        计算准确率：Agent回答与标准答案的相似度

        使用 SequenceMatcher 计算文本相似度
        阈值: >= 0.8 视为正确

        Args:
            agent_answer: Agent实际回答
            expected_answer: 标准答案

        Returns:
            准确率 0-1
        """
        if not agent_answer or not expected_answer:
            return 0.0

        # 文本相似度
        similarity = SequenceMatcher(None, agent_answer, expected_answer).ratio()

        logger.debug(f"准确率: {similarity:.3f} (Agent: {agent_answer[:30]}... vs 标准: {expected_answer[:30]}...)")
        return similarity

    def calc_recall(self, retrieved_sources: List[Dict[str, Any]], expected_source: Dict[str, Any]) -> float:
        """
        计算召回率：标准来源是否被Agent检索到

        Args:
            retrieved_sources: Agent检索到的来源列表 [{chunk_id: int, score: float}, ...]
            expected_source: 标准来源 {chunk_id: int, file_id: int}

        Returns:
            召回率 0-1
        """
        if not retrieved_sources or not expected_source:
            return 0.0

        expected_chunk_id = expected_source.get('chunk_id')
        if not expected_chunk_id:
            return 0.0

        # 检查标准来源是否在检索结果中
        retrieved_chunk_ids = [s.get('chunk_id') for s in retrieved_sources]

        if expected_chunk_id in retrieved_chunk_ids:
            # 在检索结果中找到了，计算排名加权
            rank = retrieved_chunk_ids.index(expected_chunk_id) + 1
            # 排名越靠前，召回率越高
            recall = 1.0 / rank if rank <= 10 else 0.1
        else:
            recall = 0.0

        logger.debug(f"召回率: {recall:.3f} (标准chunk_id: {expected_chunk_id}, 是否找到: {recall > 0})")
        return recall

    def calc_citation_correctness(
        self,
        agent_citations: List[Dict[str, Any]],
        expected_source: Dict[str, Any]
    ) -> float:
        """
        计算引用正确率：Agent引用的来源是否与标准来源一致

        Args:
            agent_citations: Agent的引用列表 [{chunk_id: int, confidence: float}, ...]
            expected_source: 标准来源 {chunk_id: int}

        Returns:
            引用正确率 0-1
        """
        if not agent_citations or not expected_source:
            return 0.0

        expected_chunk_id = expected_source.get('chunk_id')
        if not expected_chunk_id:
            return 0.0

        # 检查引用中是否包含标准来源
        cited_chunk_ids = [c.get('chunk_id') or c.get('source_fragment', {}).get('doc_id') for c in agent_citations]

        # 完全匹配
        if expected_chunk_id in cited_chunk_ids:
            return 1.0

        # 部分匹配（文件级别）
        expected_file_id = expected_source.get('file_id')
        if expected_file_id:
            cited_file_ids = [c.get('file_id') for c in agent_citations]
            if expected_file_id in cited_file_ids:
                return 0.7  # 文件对了，但chunk不对

        logger.debug(f"引用正确率: 0.0 (标准chunk_id: {expected_chunk_id}, Agent引用: {cited_chunk_ids})")
        return 0.0

    def calc_completeness(self, agent_answer: str, expected_aspects: List[str]) -> float:
        """
        计算回答完整度：Agent回答覆盖了多少关键点

        Args:
            agent_answer: Agent实际回答
            expected_aspects: 标准答案的关键点列表

        Returns:
            完整度 0-1
        """
        if not agent_answer or not expected_aspects:
            return 0.0

        agent_answer_lower = agent_answer.lower()
        covered_count = 0

        for aspect in expected_aspects:
            # 检查关键点是否出现在回答中
            if aspect.lower() in agent_answer_lower:
                covered_count += 1

        completeness = covered_count / len(expected_aspects) if expected_aspects else 0.0

        logger.debug(f"完整度: {completeness:.3f} (覆盖 {covered_count}/{len(expected_aspects)} 个关键点)")
        return completeness

    def calc_overall_score(
        self,
        accuracy: float,
        recall: float,
        citation_correctness: float,
        completeness: float
    ) -> float:
        """
        计算综合得分

        权重分配：
        - 准确率: 30%
        - 召回率: 25%
        - 引用正确率: 25%
        - 完整度: 20%

        Returns:
            综合得分 0-1
        """
        overall = (
            accuracy * 0.3 +
            recall * 0.25 +
            citation_correctness * 0.25 +
            completeness * 0.2
        )

        return overall

    # ============================================================================
    # 三、评测运行
    # ============================================================================

    def run_evaluation(
        self,
        project_id: int,
        version: str,
        agent_callable
    ) -> Dict[str, Any]:
        """
        运行完整评测

        Args:
            project_id: 项目ID
            version: 版本号 (如 v1.0)
            agent_callable: Agent调用函数 query -> response

        Returns:
            {
                total_cases: int,
                passed: int,
                failed: int,
                avg_accuracy: float,
                avg_recall: float,
                avg_citation_correctness: float,
                avg_completeness: float,
                avg_overall_score: float,
                pass_rate: float,
                details: [...]
            }
        """
        logger.info(f"开始评测: 项目 {project_id}, 版本 {version}")

        # 加载测试集
        test_cases = self.load_test_cases(project_id)

        if not test_cases:
            logger.warning(f"项目 {project_id} 没有测试用例")
            return {
                'total_cases': 0,
                'error': '没有测试用例'
            }

        results = []
        total_accuracy = 0.0
        total_recall = 0.0
        total_citation = 0.0
        total_completeness = 0.0
        total_overall = 0.0
        passed_count = 0

        # 逐个测试用例
        for case in test_cases:
            try:
                start_time = time.time()

                # 调用Agent
                agent_response = agent_callable(case['question'])

                execution_time = int((time.time() - start_time) * 1000)

                # 提取Agent回答和来源
                agent_answer = agent_response.get('answer', '')
                retrieved_sources = agent_response.get('retrieval_results', [])
                agent_citations = agent_response.get('citations', [])

                # 计算四项指标
                accuracy = self.calc_accuracy(agent_answer, case['expected_answer'])
                recall = self.calc_recall(retrieved_sources, case['expected_source'])
                citation_correctness = self.calc_citation_correctness(
                    agent_citations,
                    case['expected_source']
                )
                completeness = self.calc_completeness(agent_answer, case['expected_aspects'])
                overall_score = self.calc_overall_score(
                    accuracy, recall, citation_correctness, completeness
                )

                # 累加统计
                total_accuracy += accuracy
                total_recall += recall
                total_citation += citation_correctness
                total_completeness += completeness
                total_overall += overall_score

                # 通过判断
                passed = overall_score >= 0.7
                if passed:
                    passed_count += 1

                # 保存评测记录
                self._save_evaluation_run(
                    test_case_id=case['id'],
                    version=version,
                    agent_response=agent_answer,
                    retrieved_sources=retrieved_sources,
                    accuracy=accuracy,
                    recall=recall,
                    citation_correctness=citation_correctness,
                    completeness=completeness,
                    overall_score=overall_score,
                    execution_time=execution_time
                )

                results.append({
                    'test_case_id': case['id'],
                    'question': case['question'],
                    'passed': passed,
                    'accuracy': accuracy,
                    'recall': recall,
                    'citation_correctness': citation_correctness,
                    'completeness': completeness,
                    'overall_score': overall_score
                })

            except Exception as e:
                logger.error(f"测试用例 {case['id']} 执行失败: {str(e)}")
                self._save_evaluation_run(
                    test_case_id=case['id'],
                    version=version,
                    agent_response='',
                    retrieved_sources=[],
                    accuracy=0.0,
                    recall=0.0,
                    citation_correctness=0.0,
                    completeness=0.0,
                    overall_score=0.0,
                    execution_time=0,
                    error_message=str(e)
                )

                results.append({
                    'test_case_id': case['id'],
                    'question': case['question'],
                    'passed': False,
                    'error': str(e)
                })

        # 计算平均值
        total_cases = len(test_cases)
        avg_accuracy = total_accuracy / total_cases
        avg_recall = total_recall / total_cases
        avg_citation = total_citation / total_cases
        avg_completeness = total_completeness / total_cases
        avg_overall = total_overall / total_cases
        pass_rate = passed_count / total_cases

        # 保存批次汇总
        self._save_evaluation_batch(
            project_id=project_id,
            version=version,
            total_cases=total_cases,
            avg_accuracy=avg_accuracy,
            avg_recall=avg_recall,
            avg_citation=avg_citation,
            avg_completeness=avg_completeness,
            avg_overall=avg_overall,
            pass_rate=pass_rate
        )

        logger.info(f"评测完成: 版本 {version}, 通过率 {pass_rate:.2%}, 综合得分 {avg_overall:.3f}")

        return {
            'total_cases': total_cases,
            'passed': passed_count,
            'failed': total_cases - passed_count,
            'avg_accuracy': avg_accuracy,
            'avg_recall': avg_recall,
            'avg_citation_correctness': avg_citation,
            'avg_completeness': avg_completeness,
            'avg_overall_score': avg_overall,
            'pass_rate': pass_rate,
            'details': results
        }

    def _save_evaluation_run(
        self,
        test_case_id: int,
        version: str,
        agent_response: str,
        retrieved_sources: List[Dict[str, Any]],
        accuracy: float,
        recall: float,
        citation_correctness: float,
        completeness: float,
        overall_score: float,
        execution_time: int,
        error_message: str = None
    ):
        """保存单次评测记录"""
        insert_sql = text("""
            INSERT INTO evaluation_runs (
                test_case_id, run_version, agent_response, retrieved_sources,
                accuracy, recall, citation_correctness, completeness,
                overall_score, execution_time_ms, error_message, run_at
            ) VALUES (
                :test_case_id, :run_version, :agent_response, :retrieved_sources,
                :accuracy, :recall, :citation_correctness, :completeness,
                :overall_score, :execution_time_ms, :error_message, CURRENT_TIMESTAMP
            )
        """)

        self.db.execute(insert_sql, {
            'test_case_id': test_case_id,
            'run_version': version,
            'agent_response': agent_response,
            'retrieved_sources': json.dumps(retrieved_sources, ensure_ascii=False),
            'accuracy': accuracy,
            'recall': recall,
            'citation_correctness': citation_correctness,
            'completeness': completeness,
            'overall_score': overall_score,
            'execution_time_ms': execution_time,
            'error_message': error_message
        })

        self.db.commit()

    def _save_evaluation_batch(
        self,
        project_id: int,
        version: str,
        total_cases: int,
        avg_accuracy: float,
        avg_recall: float,
        avg_citation: float,
        avg_completeness: float,
        avg_overall: float,
        pass_rate: float
    ):
        """保存批次汇总"""
        insert_sql = text("""
            INSERT INTO evaluation_batches (
                project_id, run_version, total_cases,
                avg_accuracy, avg_recall, avg_citation_correctness,
                avg_completeness, avg_overall_score, pass_rate, run_at
            ) VALUES (
                :project_id, :run_version, :total_cases,
                :avg_accuracy, :avg_recall, :avg_citation,
                :avg_completeness, :avg_overall, :pass_rate, CURRENT_TIMESTAMP
            )
        """)

        self.db.execute(insert_sql, {
            'project_id': project_id,
            'run_version': version,
            'total_cases': total_cases,
            'avg_accuracy': avg_accuracy,
            'avg_recall': avg_recall,
            'avg_citation': avg_citation,
            'avg_completeness': avg_completeness,
            'avg_overall': avg_overall,
            'pass_rate': pass_rate
        })

        self.db.commit()

    # ============================================================================
    # 四、版本对比
    # ============================================================================

    def compare_versions(
        self,
        project_id: int,
        version_old: str,
        version_new: str
    ) -> Dict[str, Any]:
        """
        版本对比：检测回归

        Args:
            project_id: 项目ID
            version_old: 旧版本号
            version_new: 新版本号

        Returns:
            {
                regression_detected: bool,
                metrics: {
                    accuracy: {old: float, new: float, change: float},
                    recall: {...},
                    citation: {...},
                    completeness: {...}
                },
                recommendation: str
            }
        """
        logger.info(f"版本对比: {version_old} vs {version_new}")

        # 查询两个版本的评测结果
        query_sql = text("""
            SELECT
                run_version,
                avg_accuracy,
                avg_recall,
                avg_citation_correctness,
                avg_completeness,
                avg_overall_score
            FROM evaluation_batches
            WHERE project_id = :project_id
              AND run_version IN (:version_old, :version_new)
            ORDER BY run_at DESC
        """)

        results = self.db.execute(query_sql, {
            'project_id': project_id,
            'version_old': version_old,
            'version_new': version_new
        }).fetchall()

        if len(results) < 2:
            return {
                'error': f'没有找到两个版本的评测数据'
            }

        old_data = None
        new_data = None

        for row in results:
            if row.run_version == version_old:
                old_data = row
            elif row.run_version == version_new:
                new_data = row

        if not old_data or not new_data:
            return {'error': '数据不完整'}

        # 计算变化
        metrics = {
            'accuracy': {
                'old': old_data.avg_accuracy,
                'new': new_data.avg_accuracy,
                'change': new_data.avg_accuracy - old_data.avg_accuracy,
                'change_percent': (new_data.avg_accuracy - old_data.avg_accuracy) / old_data.avg_accuracy * 100
                if old_data.avg_accuracy > 0 else 0
            },
            'recall': {
                'old': old_data.avg_recall,
                'new': new_data.avg_recall,
                'change': new_data.avg_recall - old_data.avg_recall,
                'change_percent': (new_data.avg_recall - old_data.avg_recall) / old_data.avg_recall * 100
                if old_data.avg_recall > 0 else 0
            },
            'citation_correctness': {
                'old': old_data.avg_citation_correctness,
                'new': new_data.avg_citation_correctness,
                'change': new_data.avg_citation_correctness - old_data.avg_citation_correctness,
                'change_percent': (new_data.avg_citation_correctness - old_data.avg_citation_correctness) / old_data.avg_citation_correctness * 100
                if old_data.avg_citation_correctness > 0 else 0
            },
            'completeness': {
                'old': old_data.avg_completeness,
                'new': new_data.avg_completeness,
                'change': new_data.avg_completeness - old_data.avg_completeness,
                'change_percent': (new_data.avg_completeness - old_data.avg_completeness) / old_data.avg_completeness * 100
                if old_data.avg_completeness > 0 else 0
            },
            'overall_score': {
                'old': old_data.avg_overall_score,
                'new': new_data.avg_overall_score,
                'change': new_data.avg_overall_score - old_data.avg_overall_score,
                'change_percent': (new_data.avg_overall_score - old_data.avg_overall_score) / old_data.avg_overall_score * 100
                if old_data.avg_overall_score > 0 else 0
            }
        }

        # 回归检测（任一指标下降超过5%视为回归）
        regression_detected = any(
            m['change'] < -0.05 for m in metrics.values()
        )

        # 生成建议
        if regression_detected:
            recommendation = "⚠️ 检测到性能回归，建议回滚或修复"
        elif metrics['overall_score']['change'] > 0.05:
            recommendation = "✅ 性能提升，可以合并代码"
        else:
            recommendation = "➡️ 性能基本持平"

        logger.info(f"版本对比结果: 回归={regression_detected}, 综合得分变化={metrics['overall_score']['change']:.3f}")

        return {
            'regression_detected': regression_detected,
            'metrics': metrics,
            'recommendation': recommendation
        }


def get_evaluation_engine(db: Session) -> EvaluationEngine:
    """获取评测引擎实例"""
    return EvaluationEngine(db)
