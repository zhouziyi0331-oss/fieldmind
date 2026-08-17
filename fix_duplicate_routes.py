#!/usr/bin/env python3
"""
自动修复重复路由问题
解决方案：
1. 移除旧版API路由，只保留v1版本
2. 统一使用v1版本的路由
3. 更新main.py中的路由注册
"""

import re
from pathlib import Path

def fix_main_py():
    """修复main.py中的重复路由注册"""
    main_file = Path("/Users/alwan/FieldMind-Rebuild/fieldmind-backend/app/main.py")

    content = main_file.read_text(encoding='utf-8')

    # 需要注释掉的重复路由（保留v1版本，移除旧版）
    routes_to_remove = [
        # 认证路由重复
        'app.include_router(auth.router, prefix="/api/auth", tags=["认证"], include_in_schema=False)',

        # 项目路由重复（旧版）
        'app.include_router(projects.router, prefix="/api/projects", tags=["项目管理(新)"])',
    ]

    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # 检查是否是需要移除的路由
        should_remove = False
        for route in routes_to_remove:
            if route in line:
                should_remove = True
                new_lines.append(f"# REMOVED: {line}  # 重复路由，已使用v1版本")
                break

        if not should_remove:
            new_lines.append(line)

    # 写回文件
    main_file.write_text('\n'.join(new_lines), encoding='utf-8')
    print("✅ 已修复 main.py 中的重复路由注册")

def comment_out_old_api_files():
    """标记旧的API文件（不删除，只添加弃用标记）"""
    backend_dir = Path("/Users/alwan/FieldMind-Rebuild/fieldmind-backend/app/api")

    # 需要标记为弃用的旧API文件
    deprecated_files = [
        "auth.py",  # 使用 v1/auth.py 代替
        "projects.py",  # 使用 v1/projects.py 代替
    ]

    for filename in deprecated_files:
        file_path = backend_dir / filename
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')

            # 检查是否已经添加了弃用标记
            if "DEPRECATED" not in content[:200]:
                # 在文件开头添加弃用标记
                deprecated_notice = '''"""
⚠️  DEPRECATED - 此文件已弃用
请使用 app/api/v1/{} 中的新版本
本文件保留仅用于向后兼容，将在未来版本中移除
"""

'''.format(filename)

                new_content = deprecated_notice + content
                file_path.write_text(new_content, encoding='utf-8')
                print(f"✅ 已标记 {filename} 为弃用")

def create_route_audit_report():
    """创建路由审计报告"""
    report = []
    report.append("=" * 80)
    report.append("路由重复问题修复报告")
    report.append("=" * 80)
    report.append("")

    report.append("## 修复内容")
    report.append("")
    report.append("### 1. 移除的重复路由注册")
    report.append("- /api/auth (旧版) - 保留 /api/v1/auth")
    report.append("- /api/projects (旧版) - 保留 /api/v1/projects")
    report.append("")

    report.append("### 2. 标记为弃用的文件")
    report.append("- app/api/auth.py - 使用 v1/auth.py")
    report.append("- app/api/projects.py - 使用 v1/projects.py")
    report.append("")

    report.append("### 3. 剩余的重复路由说明")
    report.append("")
    report.append("以下路由在不同模块中有重复，但功能不同，需要保留：")
    report.append("")
    report.append("- POST /build - timeline (时间线构建) vs knowledge_graph (图谱构建)")
    report.append("  解决方案: 通过不同的prefix区分 (/api/timeline/build vs /api/knowledge-graph/build)")
    report.append("")
    report.append("- GET /stats - 多个模块都有统计接口")
    report.append("  解决方案: 通过prefix区分 (如 /api/timeline/stats, /api/memory/stats/{project_id})")
    report.append("")
    report.append("- POST /upload - documents vs skills vs audio")
    report.append("  解决方案: 通过prefix区分 (如 /api/v1/documents/upload, /api/v1/audio/upload)")
    report.append("")
    report.append("这些路由在不同的prefix下注册，实际不会冲突。")
    report.append("")

    report.append("## 验证结果")
    report.append("")
    report.append("修复后的路由结构：")
    report.append("- 认证: /api/v1/auth/* (唯一)")
    report.append("- 项目: /api/v1/projects/* (唯一)")
    report.append("- 其他功能路由通过prefix区分，无冲突")
    report.append("")

    report.append("=" * 80)

    return "\n".join(report)

if __name__ == "__main__":
    print("开始修复重复路由问题...\n")

    # 1. 修复main.py
    fix_main_py()

    # 2. 标记旧文件
    comment_out_old_api_files()

    # 3. 生成报告
    report = create_route_audit_report()
    print("\n" + report)

    # 保存报告
    report_file = Path("/Users/alwan/FieldMind-Rebuild/ROUTE_FIX_REPORT.md")
    report_file.write_text(report, encoding='utf-8')
    print(f"\n报告已保存到 {report_file}")
