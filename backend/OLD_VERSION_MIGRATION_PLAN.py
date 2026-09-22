#!/usr/bin/env python3
"""
旧版本迁移检查和方案
/Users/alwan/FieldMind/fieldmind → /Users/alwan/FieldMind
"""

print("""
╔══════════════════════════════════════════════════════════════════╗
║     旧版本迁移方案 - /Users/alwan/FieldMind/fieldmind            ║
╚══════════════════════════════════════════════════════════════════╝

⚠️ 警告：此目录不能直接删除！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
发现的问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 数据库文件（需要迁移）
   ❌ fieldmind.db (47.14MB) - 有大量数据
   ❌ reuse_tracking.db (3.25MB) - 复用追踪数据
   ❌ build.db (0.17MB) - 构建数据

2. 独有功能模块（35个文件）
   - unified_pipeline_coordinator.py
   - boundary2_validator.py
   - summary_generator.py
   - kg_analysis_service.py
   - vision_service.py
   等等...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
安全迁移步骤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

步骤1: 备份旧版本数据库
   mkdir -p /Users/alwan/FieldMind/backend/db_backup
   cp /Users/alwan/FieldMind/fieldmind/backend/fieldmind.db \\
      /Users/alwan/FieldMind/backend/db_backup/fieldmind_old_47mb.db
   cp /Users/alwan/FieldMind/fieldmind/reuse_tracking.db \\
      /Users/alwan/FieldMind/backend/db_backup/reuse_tracking_old.db

步骤2: 检查数据库内容
   sqlite3 /Users/alwan/FieldMind/backend/db_backup/fieldmind_old_47mb.db \\
      "SELECT name FROM sqlite_master WHERE type='table'"

   sqlite3 /Users/alwan/FieldMind/backend/db_backup/fieldmind_old_47mb.db \\
      "SELECT COUNT(*) FROM projects"

步骤3: 迁移独有功能模块（需要逐个检查）
   对比列表：
   1. unified_pipeline_coordinator.py - 需要检查主程序是否有等效功能
   2. boundary2_validator.py - 检查验证器是否已迁移
   3. summary_generator.py - 检查摘要生成功能
   4. kg_analysis_service.py - 检查知识图谱分析
   5. vision_service.py - 检查视觉处理功能
   ... 等等35个文件

步骤4: 确认功能完整后再删除
   只有在确认以下条件后才能删除：
   ✅ 数据库已备份
   ✅ 重要数据已迁移到主程序数据库
   ✅ 35个独有模块确认主程序有等效功能
   ✅ 主程序测试通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

暂时不要删除 /Users/alwan/FieldMind/fieldmind 目录！

需要先：
1. 检查47MB数据库中有什么数据
2. 逐个检查35个独有模块的功能
3. 确认主程序是否有等效实现

你想让我：
A. 检查数据库内容
B. 检查独有模块功能
C. 创建完整的迁移脚本

请回复 A、B 或 C
""")
