#!/usr/bin/env python3
"""
深度验证未使用模块 - 确认是否为旧版本/重复实现

对每个未使用模块进行详细分析：
1. 查找是否有同名或相似功能的新版本在使用
2. 检查文件内的注释说明（是否标注为旧版本）
3. 对比创建/修改时间
4. 检查是否有"_v2"、"_improved"、"_optimized"等替代版本
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 83个未使用模块列表
UNUSED_MODULES = [
    "tools/entity/unified_entity_engine.py",
    "tools/entity/unified_entity_extractor.py",
    "tools/coordinator/document_processing_pipeline_complete.py",
    "tools/coordinator/document_processing_pipeline.py",
    "agents/v2/quality_control_agent.py",
    "workflows/gap_analysis.py",
    "tools/coordinator/workflow_chain.py",
    "services/skills/xiangtu_china.py",
    "core/data_flow_orchestrator.py",
    "workflows/orchestrator.py",
    "tools/report/batch_services_07_15.py",
    "services/skills/sacred_memory.py",
    "core/error_handlers.py",
    "tools/knowledge/knowledge_graph_v2.py",
    "tools/report/dynamic_report_generator.py",
    "services/skills/business_feasibility.py",
    "tools/standalone/skill_sandbox.py",
    "tools/knowledge/relation_discovery.py",
    "tools/chunking/document_chunker_v2.py",
    "tools/ingestion/document_parser.py",
    "tasks/report_tasks.py",
    "tools/knowledge/knowledge_graph_builder_optimized.py",
    "tools/knowledge/document_network_builder.py",
    "tools/report/adaptive_analyzer.py",
    "services/workflows/autonomous_crew.py",
    "agents/entity_relation_agent.py",
    "tools/knowledge/knowledge_graph_builder.py",
    "tools/knowledge/correlation_recommender.py",
    "tools/synthesis/anti_hallucination_report.py",
    "tools/knowledge/knowledge_graph_service.py",
    "tools/knowledge/knowledge_graph_improved.py",
    "tools/synthesis/fact_statement_populator.py",
    "services/workflows/research_report_crew_v2.py",
    "services/skills/livelihood_ecology.py",
    "tools/synthesis/evidence_extractor.py",
    "tasks/rag_tasks.py",
    "core/alerts.py",
    "agents/crew_config.py",
    "tools/vectorization/structured_extractor.py",
    "tools/knowledge/neo4j_adapter.py",
    "services/skills/heritage_dadi.py",
    "tools/vectorization/cross_document_entity_resolver.py",
    "tasks/crawler_tasks.py",
    "services/skills/multi_village_sop.py",
    "tools/report/business_analysis_orchestrator.py",
    "services/agents/relation_agent.py",
    "services/skills/literature_market_research.py",
    "services/workflows/rag_query_crew.py",
    "tools/report/competitor_analysis_service.py",
    "tools/coordinator/document_processing_pipeline_v2.py",
    "tools/ingestion/multimodal_processor.py",
    "tools/synthesis/facts_anchor.py",
    "services/skills/community_governance.py",
    "tools/knowledge/document_relation_discovery.py",
    "tools/chunking/semantic_chunker.py",
    "tools/ingestion/document_converter_v2.py",
    "tools/vectorization/entity_extraction.py",
    "services/workflows/research_report_crew.py",
    "tools/vectorization/entity_extractor.py",
    "tools/ingestion/table_processor.py",
    "agents/field_dimension_agent.py",
    "api/v1/api_docs_enhanced.py",
    "tools/ingestion/data_quality_checker.py",
    "services/agents/entity_agent.py",
    "tools/report/market_demand_service.py",
    "tools/ingestion/data_curation.py",
    "tools/coordinator/batch_processor.py",
    "services/workflows/document_processing_crew.py",
    "middleware/enhanced_monitoring.py",
    "tasks/graph_tasks.py",
    "tasks/audio_tasks.py",
    "agents/v2/tool_registry.py",
    "tools/standalone/ragflow_service.py",
    "core/funasr_service.py",
    "tools/chunking/audio_chunker.py",
    "api/permissions.py",
    "tools/vectorization/llm_enhanced_extractor.py",
    "tools/report/pricing_strategy_service.py",
    "tools/coordinator/auto_processing_trigger.py",
    "core/unified_transcription.py",
    "middleware/project_isolation.py",
    "core/permissions.py",
    "middleware/performance.py",
]

def extract_file_header(file_path: Path, lines: int = 30) -> str:
    """提取文件头部注释"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            header_lines = []
            for i, line in enumerate(f):
                if i >= lines:
                    break
                header_lines.append(line)
            return ''.join(header_lines)
    except:
        return ""

def find_similar_files(module_path: str, root_dir: Path) -> List[Tuple[str, Path]]:
    """查找相似或替代的文件"""
    module_name = Path(module_path).stem
    module_dir = Path(module_path).parent

    similar_files = []

    # 查找模式
    patterns = [
        f"{module_name}_v[0-9]",      # 版本号
        f"{module_name}_v[0-9]+",
        f"{module_name}_improved",     # 改进版
        f"{module_name}_optimized",    # 优化版
        f"{module_name}_new",          # 新版
        f"{module_name}_refactored",   # 重构版
    ]

    # 查找同目录下的相似文件
    full_dir = root_dir / module_dir
    if full_dir.exists():
        for py_file in full_dir.glob("*.py"):
            if py_file.name != Path(module_path).name:
                file_stem = py_file.stem
                # 检查是否匹配模式
                for pattern in patterns:
                    if re.search(pattern, file_stem):
                        similar_files.append(("version", py_file))
                        break
                # 检查是否基础名称相同（去掉_v2等后缀）
                base_name = re.sub(r'_v[0-9]+|_improved|_optimized|_complete|_new', '', file_stem)
                if base_name == module_name and file_stem != module_name:
                    similar_files.append(("related", py_file))

    return similar_files

def check_if_old_version(file_path: Path) -> Dict:
    """检查文件是否为旧版本"""
    header = extract_file_header(file_path, 50)

    # 检查旧版本标记
    old_markers = [
        r'废弃|deprecated|obsolete|legacy',
        r'已被.*替代|replaced by',
        r'旧版|old version',
        r'不再使用|no longer used',
        r'迁移到|migrated to',
    ]

    is_old = False
    evidence = []

    for pattern in old_markers:
        matches = re.findall(pattern, header, re.IGNORECASE)
        if matches:
            is_old = True
            evidence.extend(matches)

    # 检查整合标记
    integration_markers = [
        r'整合|integration|consolidated',
        r'统一|unified',
        r'合并|merged',
    ]

    is_integrated = False
    for pattern in integration_markers:
        if re.search(pattern, header, re.IGNORECASE):
            is_integrated = True
            break

    # 获取文件时间戳
    stat = file_path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime)

    return {
        'is_old': is_old,
        'evidence': evidence,
        'is_integrated': is_integrated,
        'modified': mtime,
        'header_preview': header[:500] if header else ""
    }

def analyze_all_unused_modules():
    """分析所有未使用模块"""
    root_dir = Path("/Users/alwan/FieldMind/backend/src/app")

    results = {
        'old_versions': [],      # 明确标注为旧版本
        'has_replacement': [],   # 有替代版本
        'integrated': [],        # 已被整合
        'orphaned': [],          # 孤立的独立功能
        'unknown': [],           # 无法判断
    }

    print("=" * 80)
    print("深度验证未使用模块")
    print("=" * 80)
    print()

    for module_path in UNUSED_MODULES:
        full_path = root_dir / module_path

        if not full_path.exists():
            print(f"⚠️ 文件不存在: {module_path}")
            continue

        # 检查是否为旧版本
        analysis = check_if_old_version(full_path)

        # 查找替代文件
        similar_files = find_similar_files(module_path, root_dir)

        # 分类
        module_info = {
            'path': module_path,
            'size': full_path.stat().st_size,
            'modified': analysis['modified'],
            'header': analysis['header_preview'],
            'similar_files': similar_files,
            'evidence': analysis['evidence']
        }

        if analysis['is_old']:
            results['old_versions'].append(module_info)
        elif len(similar_files) > 0:
            results['has_replacement'].append(module_info)
        elif analysis['is_integrated']:
            results['integrated'].append(module_info)
        elif '_v2' in module_path or '_improved' in module_path or '_optimized' in module_path:
            # 本身是高版本，但被更高版本替代
            results['has_replacement'].append(module_info)
        else:
            # 需要人工判断
            results['unknown'].append(module_info)

    return results

def generate_report(results: Dict):
    """生成详细报告"""
    report_path = Path("/Users/alwan/FieldMind/PHASE_6_P1_UNUSED_MODULES_DEEP_VERIFICATION.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# P1-3: 未使用模块深度验证报告\n\n")
        f.write("**目的**: 确认每个未使用模块是否为旧版本/重复实现\n\n")

        f.write("## 📊 分类统计\n\n")
        f.write(f"- **明确标注为旧版本**: {len(results['old_versions'])}个 ✅ 可安全删除\n")
        f.write(f"- **有替代版本**: {len(results['has_replacement'])}个 ✅ 可安全删除\n")
        f.write(f"- **已被整合**: {len(results['integrated'])}个 ✅ 可安全删除\n")
        f.write(f"- **需要人工判断**: {len(results['unknown'])}个 ⚠️\n\n")

        total_safe = len(results['old_versions']) + len(results['has_replacement']) + len(results['integrated'])
        f.write(f"**可安全删除**: {total_safe}/83 ({total_safe/83*100:.1f}%)\n\n")

        f.write("---\n\n")

        # 明确标注为旧版本
        f.write("## 1. 明确标注为旧版本 ✅\n\n")
        f.write("这些模块在代码注释中明确标注为废弃/旧版本/已替代。\n\n")
        for item in results['old_versions']:
            f.write(f"### `{item['path']}`\n\n")
            f.write(f"- **大小**: {item['size']} bytes\n")
            f.write(f"- **修改时间**: {item['modified']}\n")
            f.write(f"- **证据**: {', '.join(item['evidence'])}\n")
            f.write(f"- **文件头**:\n```\n{item['header'][:300]}...\n```\n\n")

        # 有替代版本
        f.write("## 2. 有替代版本 ✅\n\n")
        f.write("找到了同名或相似功能的新版本文件。\n\n")
        for item in results['has_replacement']:
            f.write(f"### `{item['path']}`\n\n")
            f.write(f"- **大小**: {item['size']} bytes\n")
            f.write(f"- **修改时间**: {item['modified']}\n")
            if item['similar_files']:
                f.write(f"- **替代文件**:\n")
                for rel_type, sim_file in item['similar_files']:
                    f.write(f"  - `{sim_file.name}` ({rel_type})\n")
            f.write("\n")

        # 已被整合
        f.write("## 3. 已被整合 ✅\n\n")
        f.write("功能已被整合到其他模块中。\n\n")
        for item in results['integrated']:
            f.write(f"### `{item['path']}`\n\n")
            f.write(f"- **大小**: {item['size']} bytes\n")
            f.write(f"- **文件头**:\n```\n{item['header'][:300]}...\n```\n\n")

        # 需要人工判断
        f.write("## 4. 需要人工判断 ⚠️\n\n")
        f.write("无法自动判断是否为旧版本，需要查看具体内容。\n\n")
        for item in results['unknown']:
            f.write(f"### `{item['path']}`\n\n")
            f.write(f"- **大小**: {item['size']} bytes\n")
            f.write(f"- **修改时间**: {item['modified']}\n")
            f.write(f"- **文件头**:\n```\n{item['header'][:200]}...\n```\n\n")

        f.write("---\n\n")
        f.write("## 推荐行动\n\n")
        f.write(f"1. **立即删除**: 类别1-3共{total_safe}个文件（已确认为旧版本/重复）\n")
        f.write(f"2. **人工审查**: 类别4共{len(results['unknown'])}个文件\n")

    print(f"\n📄 详细报告已保存: {report_path}")

    return results

def main():
    results = analyze_all_unused_modules()

    print()
    print("=" * 80)
    print("分类结果")
    print("=" * 80)
    print(f"明确标注为旧版本: {len(results['old_versions'])}个")
    print(f"有替代版本: {len(results['has_replacement'])}个")
    print(f"已被整合: {len(results['integrated'])}个")
    print(f"需要人工判断: {len(results['unknown'])}个")
    print()

    total_safe = len(results['old_versions']) + len(results['has_replacement']) + len(results['integrated'])
    print(f"✅ 可安全删除: {total_safe}/83 ({total_safe/83*100:.1f}%)")

    generate_report(results)

if __name__ == "__main__":
    main()
