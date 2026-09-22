#!/usr/bin/env python3
"""
FieldMind 技术债全面排查脚本

扫描范围：
1. 空表
2. 断联的API
3. 未被调用的函数
4. 半成品功能
5. 前端事件未绑定
6. 零数据API
7. 数据模型不一致
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
import re
from datetime import datetime
from collections import defaultdict

# 输出格式
REPORT = []

def add_section(title):
    REPORT.append("")
    REPORT.append("="*70)
    REPORT.append(title)
    REPORT.append("="*70)

def add_item(category, name, details, status):
    icon = "❌" if status == "FAIL" else "⚠️" if status == "WARN" else "✅"
    REPORT.append(f"\n{icon} [{category}] {name}")
    for key, value in details.items():
        REPORT.append(f"   {key}: {value}")

def scan_empty_tables():
    """扫描空表"""
    add_section("类别1：空表检查")

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    empty_tables = []
    partial_empty = []

    for table in tables:
        if table.startswith('sqlite_'):
            continue

        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]

            if count == 0:
                empty_tables.append(table)
                add_item("空表", table, {
                    "记录数": 0,
                    "位置": "data/fieldmind.db"
                }, "FAIL")
            elif count < 5:
                partial_empty.append((table, count))
                add_item("数据稀少", table, {
                    "记录数": count,
                    "状态": "可能是测试数据"
                }, "WARN")
        except Exception as e:
            add_item("表错误", table, {
                "错误": str(e)
            }, "FAIL")

    conn.close()

    return {"empty": empty_tables, "sparse": partial_empty}

def scan_null_fields():
    """扫描关键字段为NULL的记录"""
    add_section("类别2：关键字段空值检查")

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # document_chunks表
    checks = [
        ("document_chunks", "word_count", "量化字段未填充"),
        ("document_chunks", "emotion_polarity", "情感分析未执行"),
        ("document_chunks", "cluster_label", "聚类未执行"),
        ("document_chunks", "tfidf_keywords", "TF-IDF未计算"),
    ]

    for table, field, desc in checks:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field} IS NULL")
            null_count = cursor.fetchone()[0]

            if null_count > 0:
                add_item("空字段", f"{table}.{field}", {
                    "描述": desc,
                    "空值数量": f"{null_count}/{total}",
                    "比例": f"{null_count/total*100:.1f}%" if total > 0 else "N/A"
                }, "FAIL" if null_count == total else "WARN")
        except Exception as e:
            pass

    conn.close()

def scan_api_routes():
    """扫描API路由完整性"""
    add_section("类别3：API路由检查")

    # 读取API定义
    api_files = [
        "app/api/quantification.py",
        "api_server.py"
    ]

    defined_routes = []

    for api_file in api_files:
        path = Path(api_file)
        if path.exists():
            content = path.read_text()
            # 查找所有@router或@app装饰的路由
            routes = re.findall(r'@(?:router|app)\.(get|post|put|delete)\(["\']([^"\']+)', content)
            defined_routes.extend([(method, route) for method, route in routes])

    add_item("已定义路由", f"共{len(defined_routes)}个", {
        "文件": ", ".join(api_files),
        "示例": str(defined_routes[:3]) if defined_routes else "无"
    }, "OK")

    # TODO: 对比前端调用和后端定义的差异

def scan_unused_functions():
    """扫描未被调用的函数"""
    add_section("类别4：未被调用的函数")

    # 量化服务的函数
    quantification_funcs = [
        ("extract_structural_features", "app/services/quantification/structural_features.py"),
        ("extract_emotional_features", "app/services/quantification/emotional_features.py"),
        ("extract_style_features", "app/services/quantification/style_features.py"),
        ("cluster_chunks", "app/services/analysis/cluster_analyzer.py"),
    ]

    for func_name, file_path in quantification_funcs:
        path = Path(file_path)
        if not path.exists():
            add_item("函数文件不存在", func_name, {
                "预期位置": file_path
            }, "FAIL")
            continue

        # 搜索调用位置
        import_count = 0
        call_count = 0

        for py_file in Path("app").rglob("*.py"):
            if py_file.name == path.name:
                continue
            try:
                content = py_file.read_text()
                if f"import {func_name}" in content or f"from {path.stem} import" in content:
                    import_count += 1
                if f"{func_name}(" in content:
                    call_count += 1
            except:
                pass

        status = "OK" if call_count > 0 else "WARN" if import_count > 0 else "FAIL"
        add_item("函数调用检查", func_name, {
            "位置": file_path,
            "导入次数": import_count,
            "调用次数": call_count,
            "状态": "已使用" if call_count > 0 else "未调用"
        }, status)

def scan_data_model_consistency():
    """扫描数据模型一致性"""
    add_section("类别5：数据模型一致性")

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查documents和document_chunks的关联
    cursor.execute("""
        SELECT COUNT(DISTINCT document_id) FROM document_chunks
    """)
    chunks_docs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    if chunks_docs < total_docs:
        add_item("数据关联", "documents <-> document_chunks", {
            "documents总数": total_docs,
            "有chunks的文档": chunks_docs,
            "孤立文档": total_docs - chunks_docs,
            "问题": "部分文档没有chunks"
        }, "WARN")

    # 检查cluster_results和document_chunks的关联
    cursor.execute("SELECT COUNT(*) FROM cluster_results")
    cluster_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM document_chunks")
    chunk_count = cursor.fetchone()[0]

    if cluster_count < chunk_count:
        add_item("聚类覆盖", "cluster_results vs document_chunks", {
            "总chunks": chunk_count,
            "已聚类": cluster_count,
            "未聚类": chunk_count - cluster_count,
            "覆盖率": f"{cluster_count/chunk_count*100:.1f}%" if chunk_count > 0 else "0%"
        }, "WARN" if cluster_count > 0 else "FAIL")

    conn.close()

def scan_processing_pipeline():
    """扫描处理链路完整性"""
    add_section("类别6：处理链路检查")

    # 检查关键脚本是否存在
    key_scripts = [
        ("批量量化", "scripts/batch_quantify_all_chunks.py"),
        ("完整数据填充", "scripts/complete_data_fill.py"),
        ("同步统计", "scripts/sync_document_stats.py"),
    ]

    for name, script_path in key_scripts:
        path = Path(script_path)
        if path.exists():
            add_item("处理脚本", name, {
                "位置": script_path,
                "大小": f"{path.stat().st_size} bytes"
            }, "OK")
        else:
            add_item("处理脚本缺失", name, {
                "预期位置": script_path
            }, "FAIL")

def generate_summary(scan_results):
    """生成总结"""
    add_section("技术债总结")

    total_issues = 0
    critical_issues = 0

    for line in REPORT:
        if line.startswith("❌"):
            total_issues += 1
            critical_issues += 1
        elif line.startswith("⚠️"):
            total_issues += 1

    REPORT.append(f"\n总计发现问题: {total_issues}")
    REPORT.append(f"  严重问题(❌): {critical_issues}")
    REPORT.append(f"  警告(⚠️): {total_issues - critical_issues}")

    # 生成修复优先级
    add_section("修复优先级建议")

    REPORT.append("\nP0（立即修复）：")
    REPORT.append("  1. 填充所有空表（tfidf_global等）")
    REPORT.append("  2. 同步documents统计字段")
    REPORT.append("  3. 完成所有chunks的聚类")

    REPORT.append("\nP1（本周修复）：")
    REPORT.append("  1. 统一API路由")
    REPORT.append("  2. 验证所有函数被正确调用")
    REPORT.append("  3. 修复数据模型关联")

    REPORT.append("\nP2（后续优化）：")
    REPORT.append("  1. 清理测试数据")
    REPORT.append("  2. 优化处理链路")
    REPORT.append("  3. 完善文档")

def main():
    """主函数"""
    print("="*70)
    print("FieldMind 技术债全面排查")
    print(f"生成时间: {datetime.now().isoformat()}")
    print("="*70)

    # 执行所有扫描
    scan_empty_tables()
    scan_null_fields()
    scan_api_routes()
    scan_unused_functions()
    scan_data_model_consistency()
    scan_processing_pipeline()

    # 生成总结
    generate_summary(None)

    # 输出报告
    report_text = "\n".join(REPORT)
    print(report_text)

    # 保存到文件
    report_file = f"technical_debt_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    Path(report_file).write_text(report_text)
    print(f"\n报告已保存到: {report_file}")

if __name__ == "__main__":
    main()
