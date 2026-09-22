"""
Data Governance Validation API - 数据治理验证 API

提供你要求的3个强制验收查询：
1. 维度分布统计
2. chunk连续性检查
3. 缺失分析
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from sqlalchemy import text
from app.schemas.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/governance", tags=["数据治理"])


@router.get("/validation/dimension-distribution")
async def get_dimension_distribution(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    强制验收标准1：维度分布统计

    SQL: SELECT dimension_category, COUNT(*) FROM chunks GROUP BY dimension_category;

    验证：能看到6个维度的分布
    """
    try:
        if project_id:
            query = text("""
                SELECT
                    dimension_category,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM document_chunks WHERE project_id = :project_id), 2) as percentage
                FROM document_chunks
                WHERE project_id = :project_id
                GROUP BY dimension_category
                ORDER BY count DESC
            """)
            results = db.execute(query, {'project_id': project_id}).fetchall()
        else:
            query = text("""
                SELECT
                    dimension_category,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM document_chunks), 2) as percentage
                FROM document_chunks
                GROUP BY dimension_category
                ORDER BY count DESC
            """)
            results = db.execute(query).fetchall()

        distribution = []
        for row in results:
            distribution.append({
                'dimension': row[0] if row[0] else '未分类',
                'count': row[1],
                'percentage': row[2]
            })

        # 统计覆盖率
        total = sum(item['count'] for item in distribution)
        classified = sum(item['count'] for item in distribution if item['dimension'] != '未分类')
        coverage_rate = round(classified / total * 100, 2) if total > 0 else 0

        return success_response(
            data={
                'validation_type': '维度分布统计',
                'total_chunks': total,
                'classified_chunks': classified,
                'coverage_rate': coverage_rate,
                'distribution': distribution,
                'verdict': '✅ 通过' if coverage_rate >= 80 else '⚠️ 覆盖率不足80%'
            }
        )

    except Exception as e:
        logger.error(f"Error getting dimension distribution: {e}")
        return error_response(
            code="VALIDATION_FAILED",
            message=str(e)
        )


@router.get("/validation/chunk-continuity")
async def check_chunk_continuity(
    document_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    强制验收标准2：chunk连续性检查

    SQL: SELECT file_id, COUNT(*) FROM chunks GROUP BY file_id ORDER BY file_id;

    验证：每个文件的chunk_index是否连续
    """
    try:
        if document_id:
            # 检查单个文档
            query = text("""
                SELECT chunk_index
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY chunk_index
            """)
            results = db.execute(query, {'document_id': document_id}).fetchall()

            indices = [row[0] for row in results]
            gaps = []

            for i in range(len(indices) - 1):
                if indices[i+1] - indices[i] > 1:
                    gaps.append({
                        'from': indices[i],
                        'to': indices[i+1],
                        'missing': list(range(indices[i]+1, indices[i+1]))
                    })

            return success_response(
                data={
                    'validation_type': 'chunk连续性检查',
                    'document_id': document_id,
                    'total_chunks': len(indices),
                    'gaps_found': len(gaps),
                    'gaps': gaps,
                    'is_continuous': len(gaps) == 0,
                    'verdict': '✅ 连续' if len(gaps) == 0 else f'⚠️ 发现{len(gaps)}处断点'
                }
            )

        else:
            # 检查所有文档
            query = text("""
                SELECT
                    document_id,
                    COUNT(*) as chunk_count,
                    MIN(chunk_index) as min_index,
                    MAX(chunk_index) as max_index
                FROM document_chunks
                GROUP BY document_id
            """)
            results = db.execute(query).fetchall()

            documents = []
            problem_count = 0

            for row in results:
                doc_id = row[0]
                chunk_count = row[1]
                min_index = row[2]
                max_index = row[3]

                # 预期应该有 (max_index - min_index + 1) 个chunk
                expected_count = max_index - min_index + 1

                is_continuous = (chunk_count == expected_count)
                if not is_continuous:
                    problem_count += 1

                documents.append({
                    'document_id': doc_id,
                    'chunk_count': chunk_count,
                    'expected_count': expected_count,
                    'is_continuous': is_continuous
                })

            return success_response(
                data={
                    'validation_type': 'chunk连续性检查（所有文档）',
                    'total_documents': len(documents),
                    'problem_documents': problem_count,
                    'documents': documents,
                    'verdict': '✅ 全部连续' if problem_count == 0 else f'⚠️ {problem_count}个文档不连续'
                }
            )

    except Exception as e:
        logger.error(f"Error checking chunk continuity: {e}")
        return error_response(
            code="CONTINUITY_CHECK_FAILED",
            message=str(e)
        )


@router.get("/validation/missing-analysis")
async def analyze_missing_data(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    强制验收标准3：缺失分析

    验证：
    - 哪些维度覆盖不足
    - 哪些文件chunk不连续
    - 哪些chunk未标注维度
    """
    try:
        issues = []

        # 1. 检查维度覆盖率
        if project_id:
            query = text("""
                SELECT dimension_category, COUNT(*) as count
                FROM document_chunks
                WHERE project_id = :project_id
                GROUP BY dimension_category
            """)
            results = db.execute(query, {'project_id': project_id}).fetchall()
        else:
            query = text("""
                SELECT dimension_category, COUNT(*) as count
                FROM document_chunks
                GROUP BY dimension_category
            """)
            results = db.execute(query).fetchall()

        total = sum(row[1] for row in results)
        dimensions = {row[0]: row[1] for row in results}

        # 检查未分类
        unclassified = dimensions.get(None, 0) + dimensions.get('未分类', 0)
        if unclassified > 0:
            issues.append({
                'type': 'dimension',
                'severity': 'high' if unclassified > total * 0.2 else 'medium',
                'description': f'{unclassified}个chunk未标注维度',
                'percentage': round(unclassified / total * 100, 2)
            })

        # 检查维度覆盖不足（<5%）
        for dim in ['衣食住行', '民俗', '非物质文化遗产', '物质文化遗产', '政策', '历史']:
            count = dimensions.get(dim, 0)
            percentage = (count / total * 100) if total > 0 else 0
            if percentage < 5:
                issues.append({
                    'type': 'dimension',
                    'severity': 'low',
                    'description': f'{dim}维度覆盖率仅{percentage:.1f}%，建议补充相关材料',
                    'count': count
                })

        # 2. 检查chunk不连续的文档
        query2 = text("""
            SELECT
                document_id,
                COUNT(*) as chunk_count,
                MAX(chunk_index) - MIN(chunk_index) + 1 as expected_count
            FROM document_chunks
            GROUP BY document_id
            HAVING chunk_count != expected_count
        """)
        discontinuous = db.execute(query2).fetchall()

        if discontinuous:
            issues.append({
                'type': 'continuity',
                'severity': 'high',
                'description': f'{len(discontinuous)}个文件的chunk不连续（有跳段）',
                'affected_documents': [row[0] for row in discontinuous]
            })

        # 3. 检查缺少时间、地点信息的chunk
        query3 = text("""
            SELECT COUNT(*) FROM document_chunks WHERE time_period IS NULL
        """)
        no_time = db.execute(query3).fetchone()[0]

        if no_time > total * 0.5:
            issues.append({
                'type': 'metadata',
                'severity': 'medium',
                'description': f'{no_time}个chunk缺少时间区间信息',
                'percentage': round(no_time / total * 100, 2)
            })

        # 判断整体状态
        high_severity_count = sum(1 for issue in issues if issue['severity'] == 'high')

        if high_severity_count == 0:
            verdict = '✅ 数据治理良好'
            status = 'good'
        elif high_severity_count <= 2:
            verdict = '⚠️ 存在中等问题，需要改进'
            status = 'medium'
        else:
            verdict = '❌ 存在严重问题，需要立即处理'
            status = 'poor'

        return success_response(
            data={
                'validation_type': '缺失分析',
                'total_issues': len(issues),
                'high_severity': high_severity_count,
                'status': status,
                'verdict': verdict,
                'issues': issues
            }
        )

    except Exception as e:
        logger.error(f"Error analyzing missing data: {e}")
        return error_response(
            code="MISSING_ANALYSIS_FAILED",
            message=str(e)
        )


@router.get("/validation/document-coverage/{document_id}/")
async def get_document_coverage(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    查看单个文档的维度覆盖情况

    验证：这个文件覆盖了哪些维度
    """
    try:
        query = text("""
            SELECT
                dimension_category,
                COUNT(*) as count,
                GROUP_CONCAT(DISTINCT dimension_sub_category) as sub_categories
            FROM document_chunks
            WHERE document_id = :document_id
            GROUP BY dimension_category
        """)

        results = db.execute(query, {'document_id': document_id}).fetchall()

        if not results:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found"
            )

        coverage = []
        for row in results:
            coverage.append({
                'dimension': row[0] if row[0] else '未分类',
                'chunk_count': row[1],
                'sub_categories': row[2].split(',') if row[2] else []
            })

        total_chunks = sum(item['chunk_count'] for item in coverage)
        covered_dimensions = [item['dimension'] for item in coverage if item['dimension'] != '未分类']

        return success_response(
            data={
                'document_id': document_id,
                'total_chunks': total_chunks,
                'covered_dimensions': covered_dimensions,
                'dimension_count': len(covered_dimensions),
                'coverage_details': coverage,
                'verdict': f'✅ 覆盖{len(covered_dimensions)}个维度'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document coverage: {e}")
        return error_response(
            code="GET_COVERAGE_FAILED",
            message=str(e)
        )


@router.get("/validation/full-report")
async def get_full_validation_report(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    完整的数据治理验证报告

    包含所有3个强制验收标准的结果
    """
    try:
        # 1. 维度分布
        dimension_dist = await get_dimension_distribution(project_id, db)

        # 2. chunk连续性（所有文档）
        continuity = await check_chunk_continuity(None, db)

        # 3. 缺失分析
        missing = await analyze_missing_data(project_id, db)

        # 综合判断
        all_passed = (
            dimension_dist.get('data', {}).get('coverage_rate', 0) >= 80 and
            continuity.get('data', {}).get('problem_documents', 1) == 0 and
            missing.get('data', {}).get('high_severity', 1) == 0
        )

        return success_response(
            data={
                'report_type': '完整数据治理验证报告',
                'generated_at': None,  # 会自动填充
                'overall_verdict': '✅ 全部通过' if all_passed else '⚠️ 存在问题',
                'validations': {
                    'dimension_distribution': dimension_dist,
                    'chunk_continuity': continuity,
                    'missing_analysis': missing
                }
            }
        )

    except Exception as e:
        logger.error(f"Error generating full report: {e}")
        return error_response(
            code="REPORT_GENERATION_FAILED",
            message=str(e)
        )
