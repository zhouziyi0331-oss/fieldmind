"""
错误处理迁移脚本
Migration Script for Error Handling Standardization

自动将HTTPException迁移到FieldMind自定义异常
"""

import os
import re
from typing import List, Tuple

# 定义迁移映射规则
ERROR_MAPPING = {
    # HTTPException(status_code=404, ...) -> ResourceNotFoundException
    '404': {
        'exception': 'ResourceNotFoundException',
        'import': 'ResourceNotFoundException',
        'pattern': r'raise HTTPException\(status_code=404,\s*detail=["\']([^"\']+)["\']\)',
        'replacement': lambda msg: f'raise ResourceNotFoundException("resource", "unknown", "{msg}")'
    },
    # HTTPException(status_code=500, ...) -> 根据消息内容判断
    '500': {
        'exception': 'FieldMindException',
        'import': 'FieldMindException, ErrorCode',
        'patterns': [
            (r'raise HTTPException\(status_code=500,\s*detail=f?"?数据库[^"\']*', 'DatabaseException'),
            (r'raise HTTPException\(status_code=500,\s*detail=f?"?文件[^"\']*', 'FileException'),
            (r'raise HTTPException\(status_code=500,\s*detail=f?"?AI[^"\']*', 'AIServiceException'),
            (r'raise HTTPException\(status_code=500,\s*detail=f?"?向量[^"\']*', 'VectorStoreException'),
            (r'raise HTTPException\(status_code=500,\s*detail=f?"?图谱[^"\']*', 'GraphException'),
            (r'raise HTTPException\(status_code=500,\s*detail=f?"?工作流[^"\']*', 'WorkflowException'),
        ]
    },
    # HTTPException(status_code=400, ...) -> ValidationException
    '400': {
        'exception': 'ValidationException',
        'import': 'ValidationException',
    },
    # HTTPException(status_code=403, ...) -> PermissionDeniedException
    '403': {
        'exception': 'PermissionDeniedException',
        'import': 'PermissionDeniedException',
    },
}


def analyze_file(filepath: str) -> dict:
    """分析文件中的错误处理模式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'file': filepath,
        'has_http_exception': 'from fastapi import' in content and 'HTTPException' in content,
        'has_custom_exception': 'from app.core.exceptions import' in content,
        'http_exception_count': len(re.findall(r'raise HTTPException\(', content)),
        'generic_exception_count': len(re.findall(r'except Exception as', content)),
        'status_codes': {}
    }

    # 统计各类状态码
    for match in re.finditer(r'raise HTTPException\(status_code=(\d+)', content):
        status_code = match.group(1)
        result['status_codes'][status_code] = result['status_codes'].get(status_code, 0) + 1

    return result


def scan_api_directory() -> List[dict]:
    """扫描所有API文件"""
    results = []
    api_dir = 'app/api'

    for root, dirs, files in os.walk(api_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.join(root, file)
                results.append(analyze_file(filepath))

    return results


if __name__ == '__main__':
    print("=" * 60)
    print("错误处理迁移分析报告")
    print("=" * 60)
    print()

    results = scan_api_directory()

    # 按HTTPException使用频率排序
    results.sort(key=lambda x: x['http_exception_count'], reverse=True)

    total_files = len(results)
    files_with_http_exception = sum(1 for r in results if r['has_http_exception'])
    files_with_custom_exception = sum(1 for r in results if r['has_custom_exception'])
    total_http_exceptions = sum(r['http_exception_count'] for r in results)

    print(f"📊 总览:")
    print(f"  - 总文件数: {total_files}")
    print(f"  - 使用HTTPException: {files_with_http_exception}")
    print(f"  - 使用自定义异常: {files_with_custom_exception}")
    print(f"  - HTTPException总数: {total_http_exceptions}")
    print()

    print("📋 按优先级排序的迁移列表:")
    print()

    for i, result in enumerate(results[:10], 1):
        if result['http_exception_count'] > 0:
            filename = os.path.basename(result['file'])
            print(f"{i:2d}. {filename:30s} - {result['http_exception_count']:2d} HTTPExceptions")
            if result['status_codes']:
                codes_str = ', '.join(f"{code}({count})" for code, count in result['status_codes'].items())
                print(f"    状态码: {codes_str}")

    print()
    print("=" * 60)
    print("建议迁移策略:")
    print("  1. 先迁移使用频率最高的5-10个文件")
    print("  2. 每个文件迁移后运行语法检查")
    print("  3. 逐步推进，避免一次性修改过多文件")
    print("=" * 60)
