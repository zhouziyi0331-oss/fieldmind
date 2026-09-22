#!/usr/bin/env python3
"""
批量为前端页面添加 API 连接
"""
from pathlib import Path
import re

# API 导入模板
API_IMPORTS = {
    'Login.tsx': "import { authAPI } from '@/services/fieldmind-api';",
    'Register.tsx': "import { authAPI } from '@/services/fieldmind-api';",
    'Dashboard.tsx': "import { dashboardAPI, analyticsAPI } from '@/services/fieldmind-api';",
    'DashboardPage.tsx': "import { dashboardAPI, analyticsAPI } from '@/services/fieldmind-api';",
    'Projects.tsx': "import { projectAPI } from '@/services/fieldmind-api';",
    'ProjectDetail.tsx': "import { projectAPI, documentAPI, knowledgeGraphAPI } from '@/services/fieldmind-api';",
    'Documents.tsx': "import { documentAPI } from '@/services/fieldmind-api';",
    'DocumentDetail.tsx': "import { documentAPI } from '@/services/fieldmind-api';",
    'KnowledgeGraph.tsx': "import { knowledgeGraphAPI } from '@/services/fieldmind-api';",
    'Chat.tsx': "import { chatAPI, conversationAPI } from '@/services/fieldmind-api';",
    'Workflows.tsx': "import { workflowAPI } from '@/services/fieldmind-api';",
    'WorkflowDetail.tsx': "import { workflowAPI } from '@/services/fieldmind-api';",
    'Analytics.tsx': "import { analyticsAPI, dashboardAPI } from '@/services/fieldmind-api';",
    'Assets.tsx': "import { assetAPI } from '@/services/fieldmind-api';",
    'Memory.tsx': "import { memoryAPI } from '@/services/fieldmind-api';",
    'OCR.tsx': "import { ocrAPI } from '@/services/fieldmind-api';",
    'Monitoring.tsx': "import { monitoringAPI } from '@/services/fieldmind-api';",
    'Profile.tsx': "import { userAPI } from '@/services/fieldmind-api';",
    'ProfilePage.tsx': "import { userAPI } from '@/services/fieldmind-api';",
    'Settings.tsx': "import { userAPI, teamAPI } from '@/services/fieldmind-api';",
    'UserManagement.tsx': "import { userAPI, teamAPI, permissionAPI } from '@/services/fieldmind-api';",
    'Visualization.tsx': "import { visualizationAPI, analyticsAPI } from '@/services/fieldmind-api';",
    'Reports.tsx': "import { reportAPI, analyticsAPI } from '@/services/fieldmind-api';",
    'Citations.tsx': "import { citationAPI } from '@/services/fieldmind-api';",
    'DataQuality.tsx': "import { dataCleaningAPI, validationAPI } from '@/services/fieldmind-api';",
    'BusinessAnalysis.tsx': "import { analyticsAPI, biAPI } from '@/services/fieldmind-api';",
    'BatchProcessing.tsx': "import { batchAPI } from '@/services/fieldmind-api';",
    'Timeline.tsx': "import { versionAPI, auditAPI } from '@/services/fieldmind-api';",
    'Upload.tsx': "import { documentAPI, assetAPI } from '@/services/fieldmind-api';",
}

def add_api_import(page_path, import_statement):
    """在页面中添加 API 导入"""
    content = page_path.read_text()

    # 检查是否已有 fieldmind-api 导入
    if 'fieldmind-api' in content:
        return False, "已存在 API 导入"

    lines = content.split('\n')

    # 找到第一个 import 语句
    first_import_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith('import '):
            first_import_idx = idx
            break

    if first_import_idx >= 0:
        # 在第一个 import 之后插入
        lines.insert(first_import_idx + 1, import_statement)
        page_path.write_text('\n'.join(lines))
        return True, "成功添加 API 导入"

    return False, "未找到合适的导入位置"

def main():
    frontend_dir = Path('/Users/alwan/FieldMind/frontend/src/pages')

    if not frontend_dir.exists():
        print(f"❌ 目录不存在: {frontend_dir}")
        return

    print("🚀 开始批量添加 API 导入...\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for page_name, import_stmt in API_IMPORTS.items():
        page_path = frontend_dir / page_name

        if not page_path.exists():
            print(f"⚠️  {page_name:30s} - 文件不存在")
            fail_count += 1
            continue

        success, message = add_api_import(page_path, import_stmt)

        if success:
            print(f"✅ {page_name:30s} - {message}")
            success_count += 1
        elif "已存在" in message:
            print(f"⏭️  {page_name:30s} - {message}")
            skip_count += 1
        else:
            print(f"❌ {page_name:30s} - {message}")
            fail_count += 1

    print(f"\n{'='*70}")
    print(f"✅ 成功添加: {success_count}")
    print(f"⏭️  已跳过: {skip_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
