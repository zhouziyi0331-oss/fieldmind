#!/usr/bin/env python3
"""
批量连接前端页面到后端 API
"""
import os
import re
from pathlib import Path

# 页面到 API 的映射
PAGE_API_MAPPING = {
    'Login.tsx': ['authAPI'],
    'Register.tsx': ['authAPI'],
    'Dashboard.tsx': ['dashboardAPI', 'analyticsAPI'],
    'DashboardPage.tsx': ['dashboardAPI', 'analyticsAPI'],
    'Projects.tsx': ['projectAPI'],
    'ProjectDetail.tsx': ['projectAPI', 'documentAPI', 'knowledgeGraphAPI'],
    'Documents.tsx': ['documentAPI'],
    'DocumentDetail.tsx': ['documentAPI'],
    'KnowledgeGraph.tsx': ['knowledgeGraphAPI'],
    'Chat.tsx': ['chatAPI', 'conversationAPI'],
    'Workflows.tsx': ['workflowAPI'],
    'WorkflowDetail.tsx': ['workflowAPI'],
    'Analytics.tsx': ['analyticsAPI', 'dashboardAPI'],
    'Assets.tsx': ['assetAPI'],
    'Memory.tsx': ['memoryAPI'],
    'OCR.tsx': ['ocrAPI'],
    'Monitoring.tsx': ['monitoringAPI'],
    'Profile.tsx': ['userAPI'],
    'ProfilePage.tsx': ['userAPI'],
    'Settings.tsx': ['userAPI', 'teamAPI'],
    'UserManagement.tsx': ['userAPI', 'teamAPI', 'permissionAPI'],
    'Visualization.tsx': ['visualizationAPI', 'analyticsAPI'],
    'Reports.tsx': ['reportAPI', 'analyticsAPI'],
    'Citations.tsx': ['citationAPI'],
    'DataQuality.tsx': ['dataCleaningAPI', 'validationAPI'],
    'BusinessAnalysis.tsx': ['analyticsAPI', 'biAPI'],
    'BatchProcessing.tsx': ['batchAPI'],
    'Timeline.tsx': ['versionAPI', 'auditAPI'],
    'Upload.tsx': ['documentAPI', 'assetAPI'],
}

def analyze_pages():
    """分析所有页面的 API 使用情况"""
    frontend_dir = Path('/Users/alwan/FieldMind/frontend/src/pages')

    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return

    pages = list(frontend_dir.glob('*.tsx'))
    print(f"📊 找到 {len(pages)} 个页面文件\n")

    connected_count = 0
    needs_connection = []

    for page_file in sorted(pages):
        page_name = page_file.name
        content = page_file.read_text()

        # 检查是否导入了 fieldmind-api
        has_api_import = bool(re.search(r"from ['\"]@/services/fieldmind-api['\"]", content))

        # 检查是否有 API 调用
        has_api_calls = bool(re.search(r'(authAPI|userAPI|projectAPI|documentAPI|workflowAPI|dashboardAPI|analyticsAPI)', content))

        if has_api_import or has_api_calls:
            connected_count += 1
            status = "✅"
        else:
            needs_connection.append(page_name)
            status = "❌"

        recommended_apis = PAGE_API_MAPPING.get(page_name, ['未映射'])
        print(f"{status} {page_name:30s} -> {', '.join(recommended_apis)}")

    print(f"\n{'='*70}")
    print(f"✅ 已连接: {connected_count}/{len(pages)}")
    print(f"❌ 需要连接: {len(needs_connection)}/{len(pages)}")
    print(f"{'='*70}\n")

    if needs_connection:
        print("需要连接的页面:")
        for page in needs_connection:
            apis = PAGE_API_MAPPING.get(page, ['未映射'])
            print(f"  - {page:30s} -> {', '.join(apis)}")

    return needs_connection

def generate_import_statement(apis):
    """生成 import 语句"""
    return f"import {{ {', '.join(apis)} }} from '@/services/fieldmind-api';"

def update_page_with_api(page_path, apis):
    """更新页面添加 API 导入"""
    content = page_path.read_text()

    # 检查是否已有导入
    if 'fieldmind-api' in content:
        return False, "已存在 API 导入"

    # 在 import 部分添加
    import_statement = generate_import_statement(apis)

    # 找到最后一个 import 的位置
    import_lines = []
    lines = content.split('\n')
    last_import_idx = -1

    for idx, line in enumerate(lines):
        if line.strip().startswith('import '):
            last_import_idx = idx

    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, import_statement)
        new_content = '\n'.join(lines)
        page_path.write_text(new_content)
        return True, "成功添加 API 导入"

    return False, "未找到合适的导入位置"

if __name__ == '__main__':
    print("🔍 开始分析前端页面 API 连接情况...\n")
    needs_connection = analyze_pages()

    if needs_connection:
        print(f"\n📝 建议: 手动为这些页面添加具体的 API 调用逻辑")
        print(f"    每个页面根据功能使用对应的 API 服务")
