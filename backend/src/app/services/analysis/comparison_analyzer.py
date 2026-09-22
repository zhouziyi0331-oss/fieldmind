"""
分组对比分析器

基于t检验实现分组对比分析：
1. 比较两个组在数值特征上的差异
2. 计算t统计量和p值
3. 判断是否存在显著差异
4. 保存对比结果到数据库
"""

import logging
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def compare_groups(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    group1: int,
    group2: int
) -> Dict[str, Any]:
    """
    基于t检验比较两个组的差异

    Args:
        df: 数据DataFrame
        group_col: 分组列名（如'cluster_label'）
        value_col: 数值列名（如'emotion_polarity'）
        group1: 组1的标签
        group2: 组2的标签

    Returns:
        {
            't_statistic': float,
            'p_value': float,
            'significant': bool,
            'group1_mean': float,
            'group2_mean': float,
            'diff': float
        }
    """
    if df.empty:
        logger.warning("数据为空，无法进行对比分析")
        return get_empty_comparison()

    try:
        from scipy.stats import ttest_ind

        # 提取两组数据
        group1_vals = df[df[group_col] == group1][value_col].dropna()
        group2_vals = df[df[group_col] == group2][value_col].dropna()

        if len(group1_vals) < 2 or len(group2_vals) < 2:
            logger.warning(f"样本量不足：组{group1}={len(group1_vals)}, 组{group2}={len(group2_vals)}")
            return get_empty_comparison()

        # t检验
        t_stat, p_val = ttest_ind(group1_vals, group2_vals)

        # 计算均值和差异
        group1_mean = float(group1_vals.mean())
        group2_mean = float(group2_vals.mean())
        diff = group1_mean - group2_mean

        return {
            't_statistic': round(float(t_stat), 4),
            'p_value': round(float(p_val), 4),
            'significant': p_val < 0.05,
            'group1_mean': round(group1_mean, 4),
            'group2_mean': round(group2_mean, 4),
            'diff': round(diff, 4),
            'group1_size': len(group1_vals),
            'group2_size': len(group2_vals)
        }

    except ImportError:
        logger.error("scipy未安装，无法执行t检验")
        return get_empty_comparison()

    except Exception as e:
        logger.error(f"分组对比失败: {e}")
        return get_empty_comparison()


def get_empty_comparison() -> Dict[str, Any]:
    """返回空的对比结果"""
    return {
        't_statistic': 0.0,
        'p_value': 1.0,
        'significant': False,
        'group1_mean': 0.0,
        'group2_mean': 0.0,
        'diff': 0.0,
        'group1_size': 0,
        'group2_size': 0
    }


def compare_all_clusters(
    df: pd.DataFrame,
    value_cols: List[str]
) -> List[Dict[str, Any]]:
    """
    对所有聚类对进行对比分析

    Args:
        df: 包含cluster_label和数值列的DataFrame
        value_cols: 需要对比的数值列列表

    Returns:
        对比结果列表
    """
    results = []

    # 获取所有聚类标签
    clusters = df['cluster_label'].unique()
    clusters = sorted([c for c in clusters if pd.notna(c)])

    if len(clusters) < 2:
        logger.warning(f"聚类数量不足（{len(clusters)}），无法进行对比")
        return results

    # 对每个聚类对进行对比
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            cluster1 = clusters[i]
            cluster2 = clusters[j]

            for value_col in value_cols:
                if value_col not in df.columns:
                    continue

                comparison = compare_groups(
                    df, 'cluster_label', value_col, cluster1, cluster2
                )

                results.append({
                    'analysis_name': f'{value_col}: 聚类{cluster1} vs 聚类{cluster2}',
                    'group_col': 'cluster_label',
                    'value_col': value_col,
                    'group1_label': f'聚类{cluster1}',
                    'group2_label': f'聚类{cluster2}',
                    **comparison
                })

    logger.info(f"✅ 完成 {len(results)} 个对比分析")
    return results


def save_comparison_results(
    conn,
    project_id: int,
    comparisons: List[Dict[str, Any]]
) -> int:
    """
    保存对比结果到数据库

    Args:
        conn: 数据库连接
        project_id: 项目ID
        comparisons: 对比结果列表

    Returns:
        保存的记录数
    """
    cursor = conn.cursor()
    saved_count = 0

    try:
        # 清空该项目的旧对比结果
        cursor.execute("""
            DELETE FROM comparison_results WHERE project_id = ?
        """, (project_id,))

        # 插入新结果
        for comp in comparisons:
            cursor.execute("""
                INSERT INTO comparison_results
                (project_id, analysis_name, group_col, value_col,
                 group1_label, group2_label, t_statistic, p_value,
                 significant, group1_mean, group2_mean, diff, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                comp['analysis_name'],
                comp['group_col'],
                comp['value_col'],
                comp['group1_label'],
                comp['group2_label'],
                comp['t_statistic'],
                comp['p_value'],
                comp['significant'],
                comp['group1_mean'],
                comp['group2_mean'],
                comp['diff'],
                datetime.utcnow().isoformat()
            ))

            saved_count += 1

        conn.commit()
        logger.info(f"✅ 保存了 {saved_count} 条对比结果")
        return saved_count

    except Exception as e:
        logger.error(f"保存对比结果失败: {e}")
        conn.rollback()
        return 0


def get_significant_comparisons(conn, project_id: int) -> List[Dict[str, Any]]:
    """
    获取显著差异的对比结果

    Args:
        conn: 数据库连接
        project_id: 项目ID

    Returns:
        显著差异的对比列表
    """
    cursor = conn.cursor()
    cursor.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    try:
        cursor.execute("""
            SELECT *
            FROM comparison_results
            WHERE project_id = ? AND significant = 1
            ORDER BY p_value ASC
        """, (project_id,))

        results = cursor.fetchall()
        logger.info(f"找到 {len(results)} 个显著差异")
        return results

    except Exception as e:
        logger.error(f"获取显著对比失败: {e}")
        return []



# ==================== WorkflowEngine 包装类 ====================

class ComparisonAnalyzerWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_compare_groups(self, _context: dict) -> dict:
        """任务: 比较两个组的差异"""
        df = _context.get('df')
        group_col = _context.get('group_col')
        value_col = _context.get('value_col')
        group1 = _context.get('group1')
        group2 = _context.get('group2')
        result = compare_groups(df, group_col, value_col, group1, group2)
        return {"comparison_result": result}

    def _task_batch_compare(self, _context: dict) -> dict:
        """任务: 批量对比分析"""
        df = _context.get('df')
        group_col = _context.get('group_col')
        value_cols = _context.get('value_cols')
        group_pairs = _context.get('group_pairs')

        results = []
        for g1, g2 in group_pairs:
            for col in value_cols:
                result = compare_groups(df, group_col, col, g1, g2)
                result['value_col'] = col
                result['group1'] = g1
                result['group2'] = g2
                results.append(result)

        return {"results": results, "count": len(results)}

    def compare_groups_workflow(self, df: pd.DataFrame, group_col: str, value_col: str,
                                group1: int, group2: int) -> Dict[str, Any]:
        """工作流: 使用 WorkflowEngine 比较两组差异"""
        if not self.use_workflow_engine:
            return compare_groups(df, group_col, value_col, group1, group2)

        tasks = {
            "compare": {
                "function": self._task_compare_groups,
                "args": {},
                "context": {
                    "df": df,
                    "group_col": group_col,
                    "value_col": value_col,
                    "group1": group1,
                    "group2": group2
                }
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["compare"]["comparison_result"]

    def batch_compare_workflow(self, df: pd.DataFrame, group_col: str, value_cols: List[str],
                               group_pairs: List[tuple]) -> List[Dict[str, Any]]:
        """工作流: 使用 WorkflowEngine 批量对比分析"""
        if not self.use_workflow_engine:
            results = []
            for g1, g2 in group_pairs:
                for col in value_cols:
                    result = compare_groups(df, group_col, col, g1, g2)
                    result['value_col'] = col
                    result['group1'] = g1
                    result['group2'] = g2
                    results.append(result)
            return results

        tasks = {
            "batch_compare": {
                "function": self._task_batch_compare,
                "args": {},
                "context": {
                    "df": df,
                    "group_col": group_col,
                    "value_cols": value_cols,
                    "group_pairs": group_pairs
                }
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_compare"]["results"]
