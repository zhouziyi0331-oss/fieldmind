#!/usr/bin/env python3
"""
完整分析前端和后端的实际数量和缺失情况
"""
import os
from pathlib import Path
import re

def analyze_backend():
    """分析后端 API 模块"""
    backend_dir = Path('/Users/alwan/FieldMind/backend/src/app/api/v1')

    if not backend_dir.exists():
        print(f"❌ 后端目录不存在: {backend_dir}")
        return []

    api_files = sorted([f for f in backend_dir.glob('*.py') if f.name != '__init__.py'])

    print("=" * 80)
    print("📊 后端 API 模块分析")
    print("=" * 80)
    print(f"总数: {len(api_files)} 个 API 模块\n")

    modules = []
    for idx, file in enumerate(api_files, 1):
        module_name = file.stem

        # 读取文件内容，统计端点数量
        content = file.read_text()

        # 统计路由装饰器
        post_count = len(re.findall(r'@router\.post\(', content))
        get_count = len(re.findall(r'@router\.get\(', content))
        put_count = len(re.findall(r'@router\.put\(', content))
        delete_count = len(re.findall(r'@router\.delete\(', content))
        patch_count = len(re.findall(r'@router\.patch\(', content))

        total_endpoints = post_count + get_count + put_count + delete_count + patch_count

        modules.append({
            'name': module_name,
            'file': file.name,
            'endpoints': total_endpoints
        })

        print(f"{idx:2d}. {module_name:30s} - {total_endpoints:3d} 端点")

    total_endpoints = sum(m['endpoints'] for m in modules)
    print(f"\n{'='*80}")
    print(f"后端总计: {len(modules)} 模块, {total_endpoints} 个 API 端点")
    print(f"{'='*80}\n")

    return modules

def analyze_frontend():
    """分析前端页面"""
    frontend_dir = Path('/Users/alwan/FieldMind/frontend/src/pages')

    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return []

    # 获取所有 tsx 和 vue 文件
    all_pages = sorted(frontend_dir.rglob('*.tsx')) + sorted(frontend_dir.rglob('*.vue'))

    # 排除备份文件
    pages = [p for p in all_pages if '_backup' not in str(p)]

    print("=" * 80)
    print("📊 前端页面分析")
    print("=" * 80)
    print(f"总数: {len(pages)} 个页面文件\n")

    page_info = []
    connected_count = 0

    for idx, page_path in enumerate(pages, 1):
        relative_path = page_path.relative_to(frontend_dir)
        content = page_path.read_text()

        # 检查是否导入了 fieldmind-api
        has_api_import = 'fieldmind-api' in content

        status = "✅" if has_api_import else "❌"
        if has_api_import:
            connected_count += 1

        page_info.append({
            'path': str(relative_path),
            'connected': has_api_import
        })

        print(f"{idx:2d}. {status} {str(relative_path):50s}")

    print(f"\n{'='*80}")
    print(f"前端总计: {len(pages)} 页面, {connected_count} 已连接, {len(pages) - connected_count} 未连接")
    print(f"连接率: {connected_count/len(pages)*100:.1f}%")
    print(f"{'='*80}\n")

    return page_info

def find_missing_pages(backend_modules):
    """根据后端模块找出缺失的前端页面"""
    frontend_dir = Path('/Users/alwan/FieldMind/frontend/src/pages')

    print("=" * 80)
    print("🔍 缺失前端页面分析")
    print("=" * 80)

    # 后端模块到前端页面的映射
    module_to_page = {
        'annotation': 'Annotation.tsx',
        'audio': 'Audio.tsx',
        'audit': 'Audit.tsx',
        'background_learning': 'BackgroundLearning.tsx',
        'business_analysis': 'BusinessAnalysis.tsx',
        'chunks_quantification': 'ChunksQuantification.tsx',
        'collaboration': 'Collaboration.tsx',
        'crawler': 'Crawler.tsx',
        'data_enrichment': 'DataEnrichment.tsx',
        'data_quality': 'DataQuality.tsx',
        'enhanced_chat': 'EnhancedChat.tsx',
        'execution_tracking': 'ExecutionTracking.tsx',
        'experience_graph': 'ExperienceGraph.tsx',
        'feedback_loops': 'FeedbackLoops.tsx',
        'feeding': 'Feeding.tsx',
        'governance_validation': 'GovernanceValidation.tsx',
        'industry': 'Industry.tsx',
        'knowledge_network': 'KnowledgeNetwork.tsx',
        'learning': 'Learning.tsx',
        'lineage': 'Lineage.tsx',
        'pattern_recognition': 'PatternRecognition.tsx',
        'skills': 'Skills.tsx',
        'skill_generation': 'SkillGeneration.tsx',
        'skill_optimization': 'SkillOptimization.tsx',
        'sop': 'SOP.tsx',
        'super_agents': 'SuperAgents.tsx',
        'tagging': 'Tagging.tsx',
        'tasks': 'Tasks.tsx',
        'topic_analysis': 'TopicAnalysis.tsx',
        'traceability': 'Traceability.tsx',
        'unified_plugins': 'UnifiedPlugins.tsx',
        'user_analysis': 'UserAnalysis.tsx',
        'workbench': 'Workbench.tsx',
    }

    missing_pages = []

    for module in backend_modules:
        module_name = module['name']

        # 跳过一些特殊模块
        if module_name in ['__init__', 'api_docs_enhanced', 'api_management',
                           'dashboard_optimized', 'knowledge_graph_api',
                           'knowledge_graph_enhanced', 'learning_old',
                           'query_api', 'workflows_old', 'project_documents',
                           'project_workflow', 'project_chat']:
            continue

        # 检查对应的前端页面是否存在
        page_name = module_to_page.get(module_name)

        if page_name:
            page_path = frontend_dir / page_name
            if not page_path.exists():
                missing_pages.append({
                    'module': module_name,
                    'page': page_name,
                    'endpoints': module['endpoints']
                })

    if missing_pages:
        print(f"找到 {len(missing_pages)} 个缺失的前端页面:\n")
        for idx, missing in enumerate(missing_pages, 1):
            print(f"{idx:2d}. {missing['page']:40s} <- {missing['module']:30s} ({missing['endpoints']} 端点)")
    else:
        print("✅ 没有发现明显缺失的页面")

    print(f"\n{'='*80}\n")

    return missing_pages

def analyze_api_coverage():
    """分析 fieldmind-api.ts 的覆盖率"""
    api_file = Path('/Users/alwan/FieldMind/frontend/src/services/fieldmind-api.ts')

    if not api_file.exists():
        print("❌ fieldmind-api.ts 不存在")
        return

    content = api_file.read_text()

    # 统计导出的 API 对象
    api_exports = re.findall(r'export const (\w+API) = {', content)

    print("=" * 80)
    print("📊 API 服务封装分析")
    print("=" * 80)
    print(f"fieldmind-api.ts 中定义的 API 服务: {len(api_exports)} 个\n")

    for idx, api_name in enumerate(api_exports, 1):
        print(f"{idx:2d}. {api_name}")

    print(f"\n{'='*80}\n")

def main():
    print("\n" + "🚀 FieldMind 完整系统分析" + "\n")

    # 分析后端
    backend_modules = analyze_backend()

    # 分析前端
    frontend_pages = analyze_frontend()

    # 分析缺失页面
    missing_pages = find_missing_pages(backend_modules)

    # 分析 API 覆盖
    analyze_api_coverage()

    # 总结
    print("=" * 80)
    print("📋 总结")
    print("=" * 80)
    print(f"✅ 后端 API 模块: {len(backend_modules)} 个")
    print(f"✅ 前端页面: {len(frontend_pages)} 个")
    print(f"⚠️  缺失前端页面: {len(missing_pages)} 个")
    print(f"📝 需要补充的工作量: ~{len(missing_pages)} 个页面需要创建")
    print("=" * 80)

if __name__ == '__main__':
    main()
