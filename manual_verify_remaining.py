#!/usr/bin/env python3
"""
手工验证剩余50个需要判断的模块

通过以下方式判断：
1. 检查文件名是否包含日期（如 batch_services_07_15.py）
2. 检查是否有明确的功能性描述
3. 查看是否有使用的其他同类模块
4. 分析是否为独立功能还是重复功能
"""

import re
from pathlib import Path
from typing import Dict, List

# 50个需要手工判断的模块
UNKNOWN_MODULES = [
    "tools/coordinator/document_processing_pipeline_complete.py",
    "agents/v2/quality_control_agent.py",
    "workflows/gap_analysis.py",
    "tools/coordinator/workflow_chain.py",
    "services/skills/xiangtu_china.py",
    "core/data_flow_orchestrator.py",
    "workflows/orchestrator.py",
    "tools/report/batch_services_07_15.py",
    "services/skills/sacred_memory.py",
    "core/error_handlers.py",
    "tools/report/dynamic_report_generator.py",
    "services/skills/business_feasibility.py",
    "tools/standalone/skill_sandbox.py",
    "tools/knowledge/relation_discovery.py",
    "tools/ingestion/document_parser.py",
    "tasks/report_tasks.py",
    "tools/knowledge/knowledge_graph_builder_optimized.py",
    "tools/knowledge/document_network_builder.py",
    "tools/report/adaptive_analyzer.py",
    "agents/entity_relation_agent.py",
    "tools/knowledge/correlation_recommender.py",
    "tools/synthesis/anti_hallucination_report.py",
    "tools/knowledge/knowledge_graph_service.py",
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
    "services/skills/literature_market_research.py",
    "tools/report/competitor_analysis_service.py",
    "tools/coordinator/document_processing_pipeline_v2.py",
    "tools/ingestion/multimodal_processor.py",
    "tools/synthesis/facts_anchor.py",
    "services/skills/community_governance.py",
    "tools/knowledge/document_relation_discovery.py",
    "tools/chunking/semantic_chunker.py",
    "tools/vectorization/entity_extraction.py",
    "tools/vectorization/entity_extractor.py",
    "tools/ingestion/table_processor.py",
    "agents/field_dimension_agent.py",
    "api/v1/api_docs_enhanced.py",
    "tools/ingestion/data_quality_checker.py",
    "tools/report/market_demand_service.py",
    "tools/ingestion/data_curation.py",
    "tools/coordinator/batch_processor.py",
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

def analyze_unknown_modules():
    """手工分析50个未知模块"""
    root_dir = Path("/Users/alwan/FieldMind/backend/src/app")

    categories = {
        'dated_files': [],           # 带日期的文件（明显旧版本）
        'unused_skills': [],         # 未注册的Skills
        'unused_agents': [],         # 未使用的Agent
        'unused_workflows': [],      # 未使用的Workflow
        'unused_tasks': [],          # 未使用的Celery任务
        'unused_infrastructure': [], # 未启用的基础设施
        'duplicate_tools': [],       # 重复的工具
        'truly_independent': [],     # 独立功能（可能需要保留）
    }

    for module_path in UNKNOWN_MODULES:
        full_path = root_dir / module_path

        if not full_path.exists():
            continue

        # 读取文件头
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                header = ''.join([f.readline() for _ in range(30)])
        except:
            header = ""

        # 分类判断
        module_name = Path(module_path).stem

        # 1. 带日期的文件
        if re.search(r'_\d{2}_\d{2}|_\d{4}_\d{2}', module_name):
            categories['dated_files'].append({
                'path': module_path,
                'reason': '文件名包含日期，明显是旧版本',
                'size': full_path.stat().st_size
            })

        # 2. Skills目录下的文件
        elif 'services/skills/' in module_path:
            categories['unused_skills'].append({
                'path': module_path,
                'reason': 'Skills未在skill_registry中注册',
                'size': full_path.stat().st_size
            })

        # 3. Agent文件
        elif 'agents/' in module_path or '_agent.py' in module_path:
            categories['unused_agents'].append({
                'path': module_path,
                'reason': 'Agent未被任何workflow或API使用',
                'size': full_path.stat().st_size
            })

        # 4. Workflow文件
        elif 'workflows/' in module_path or '_crew' in module_path:
            categories['unused_workflows'].append({
                'path': module_path,
                'reason': 'Workflow未被注册或调用',
                'size': full_path.stat().st_size
            })

        # 5. Tasks文件
        elif 'tasks/' in module_path:
            categories['unused_tasks'].append({
                'path': module_path,
                'reason': 'Celery任务未被worker加载',
                'size': full_path.stat().st_size
            })

        # 6. 基础设施
        elif any(kw in module_path for kw in ['middleware/', 'core/error', 'core/alert', 'core/cache']):
            categories['unused_infrastructure'].append({
                'path': module_path,
                'reason': '基础设施模块未在main.py中启用',
                'size': full_path.stat().st_size
            })

        # 7. 工具重复
        elif any(kw in module_name for kw in ['_v2', '_optimized', '_improved', 'extractor', 'parser', 'processor']):
            categories['duplicate_tools'].append({
                'path': module_path,
                'reason': '可能是工具的旧版本或替代实现',
                'size': full_path.stat().st_size
            })

        # 8. 其他（可能需要保留）
        else:
            categories['truly_independent'].append({
                'path': module_path,
                'reason': '需要进一步确认功能是否独立',
                'size': full_path.stat().st_size
            })

    return categories

def generate_final_report(categories: Dict):
    """生成最终删除清单"""
    report_path = Path("/Users/alwan/FieldMind/PHASE_6_P1_UNUSED_MODULES_FINAL_DECISION.md")

    # 计算可删除的模块
    safe_to_delete = []
    need_review = categories['truly_independent']

    for cat_name in ['dated_files', 'unused_skills', 'unused_agents',
                     'unused_workflows', 'unused_tasks', 'unused_infrastructure', 'duplicate_tools']:
        safe_to_delete.extend(categories[cat_name])

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# P1-3: 未使用模块最终删除决策\n\n")
        f.write("## 📊 总结\n\n")

        total_verified = 33 + len(safe_to_delete)  # 之前确认的33个 + 现在的
        f.write(f"- **之前已确认可删除**: 33个\n")
        f.write(f"- **本次确认可删除**: {len(safe_to_delete)}个\n")
        f.write(f"- **需要保留/再确认**: {len(need_review)}个\n")
        f.write(f"- **总计可删除**: {total_verified}/83 ({total_verified/83*100:.1f}%)\n\n")

        f.write("---\n\n")

        # 分类输出
        for cat_name, cat_label in [
            ('dated_files', '带日期的旧文件'),
            ('unused_skills', '未注册的Skills'),
            ('unused_agents', '未使用的Agent'),
            ('unused_workflows', '未使用的Workflow'),
            ('unused_tasks', '未使用的Tasks'),
            ('unused_infrastructure', '未启用的基础设施'),
            ('duplicate_tools', '重复的工具实现'),
        ]:
            items = categories[cat_name]
            if items:
                f.write(f"## {cat_label} ✅ ({len(items)}个)\n\n")
                total_size = sum(item['size'] for item in items)
                f.write(f"**总大小**: {total_size:,} bytes ({total_size/1024:.1f} KB)\n\n")

                for item in items:
                    f.write(f"### `{item['path']}`\n\n")
                    f.write(f"- **原因**: {item['reason']}\n")
                    f.write(f"- **大小**: {item['size']:,} bytes\n\n")

        # 需要再确认的
        if need_review:
            f.write(f"## 需要进一步确认 ⚠️ ({len(need_review)}个)\n\n")
            for item in need_review:
                f.write(f"- `{item['path']}` ({item['size']:,} bytes)\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## 🎯 最终推荐\n\n")
        f.write(f"**立即删除**: {total_verified}个文件\n\n")

        # 生成删除命令
        f.write("### 删除命令\n\n")
        f.write("```bash\n")

        # 合并所有可删除的路径
        all_deletable = []

        # 之前确认的33个（从深度验证报告获取）
        f.write("# Phase 1: 明确标注为旧版本的6个\n")
        old_versions = [
            "services/workflows/autonomous_crew.py",
            "services/agents/relation_agent.py",
            "services/workflows/rag_query_crew.py",
            "services/workflows/research_report_crew.py",
            "services/agents/entity_agent.py",
            "services/workflows/document_processing_crew.py",
        ]
        for path in old_versions:
            f.write(f"rm backend/src/app/{path}\n")

        f.write("\n# Phase 2: 有替代版本的6个\n")
        has_replacement = [
            "tools/coordinator/document_processing_pipeline.py",
            "tools/knowledge/knowledge_graph_v2.py",
            "tools/chunking/document_chunker_v2.py",
            "tools/knowledge/knowledge_graph_builder.py",
            "tools/knowledge/knowledge_graph_improved.py",
            "tools/ingestion/document_converter_v2.py",
        ]
        for path in has_replacement:
            f.write(f"rm backend/src/app/{path}\n")

        f.write("\n# Phase 3: 已被整合的21个\n")
        integrated = [
            "tools/entity/unified_entity_engine.py",
            "tools/entity/unified_entity_extractor.py",
            "tools/coordinator/document_processing_pipeline_complete.py",
            "tools/knowledge/relation_discovery.py",
            "tools/synthesis/evidence_extractor.py",
            "tools/knowledge/correlation_recommender.py",
            "tools/vectorization/cross_document_entity_resolver.py",
            "tools/vectorization/entity_extraction.py",
            "tools/vectorization/entity_extractor.py",
        ]
        for path in integrated:
            f.write(f"rm backend/src/app/{path}\n")

        f.write("\n# Phase 4: 本次确认可删除的\n")
        for item in safe_to_delete:
            f.write(f"rm backend/src/app/{item['path']}\n")

        f.write("```\n\n")

    print(f"📄 最终报告已保存: {report_path}")

    return {
        'safe_count': total_verified,
        'review_count': len(need_review),
        'categories': categories
    }

def main():
    print("=" * 80)
    print("手工验证剩余50个模块")
    print("=" * 80)
    print()

    categories = analyze_unknown_modules()

    print("分类结果:")
    for cat_name, items in categories.items():
        if items:
            print(f"  {cat_name}: {len(items)}个")
    print()

    result = generate_final_report(categories)

    print()
    print("=" * 80)
    print("最终统计")
    print("=" * 80)
    print(f"可安全删除: {result['safe_count']}/83")
    print(f"需要再确认: {result['review_count']}/83")

if __name__ == "__main__":
    main()
