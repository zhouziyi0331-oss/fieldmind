#!/usr/bin/env python3
"""
安全清理计划 - 分步骤执行，确保不丢失任何功能
"""

print("""
╔══════════════════════════════════════════════════════════════════╗
║              FieldMind 安全清理计划                               ║
╚══════════════════════════════════════════════════════════════════╝

根据审计结果，制定以下安全清理计划：

阶段1: 修复核心问题（必须先做）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 执行数据库迁移
   命令: cd /Users/alwan/FieldMind/backend
        sqlite3 fieldmind.db < app/models/migrations/create_rag_evaluation_tables.sql

   验证: python3 -c "import sqlite3; conn=sqlite3.connect('fieldmind.db');
         print(len([t for t in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]))"

2. 修复2个Python语法错误
   文件: src/app/services/rag_retrieval_service.py:48
        src/app/services/agents/agent_mesh.py:24

阶段2: 确认主程序完整性（验证后才能删除）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 启动主程序测试
   命令: cd /Users/alwan/FieldMind/backend
        python3 -m uvicorn app.main:app --reload

   验证: curl http://localhost:8000/health

2. 测试核心功能
   - 文档上传
   - RAG查询
   - Agent对话
   - 知识图谱

阶段3: 备份清理（主程序确认正常后才执行）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
可以删除的目录（这些是.app应用包或纯备份）:
✅ /Users/alwan/Desktop/FieldMind_Apps/*.app (3个备份app)
✅ /Applications/FieldMind.app (如果主程序在/Users/alwan/FieldMind)

需要检查后才能决定的目录:
⚠️  /Users/alwan/.fieldmind (可能有用户数据)
⚠️  /Users/alwan/Library/Application Support/FieldMind (可能有数据库)

阶段4: API优化（功能稳定后优化）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 合并重复的API端点
- 删除未使用的路由
- 统一API命名规范

当前状态检查命令:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 检查主程序文件数
find /Users/alwan/FieldMind -type f -name "*.py" | wc -l

# 检查数据库是否存在
ls -lh /Users/alwan/FieldMind/backend/*.db

# 检查是否有语法错误
python3 -m py_compile /Users/alwan/FieldMind/backend/src/app/services/rag_retrieval_service.py
python3 -m py_compile /Users/alwan/FieldMind/backend/src/app/services/agents/agent_mesh.py

建议执行顺序:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 先执行阶段1（修复核心问题）
2. 再执行阶段2（验证主程序）
3. 主程序确认无误后，再执行阶段3（删除备份）
4. 最后执行阶段4（API优化）

⚠️  警告: 在主程序验证完全正常之前，不要删除任何备份！

╚══════════════════════════════════════════════════════════════════╝
""")
