#!/usr/bin/env python3
"""修复统一模块的路由注册"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到batch_processing路由注册的位置
insert_pos = None
for i, line in enumerate(lines):
    if 'batch_processing.router' in line:
        insert_pos = i + 2  # 在batch_processing后面插入
        break

if insert_pos:
    # 删除所有现有的统一模块注册（从850行开始到900行）
    # 找到第一个统一模块注册的位置
    start_remove = None
    end_remove = None
    
    for i, line in enumerate(lines):
        if '阶段2: 统一知识图谱模块' in line and start_remove is None:
            start_remove = i
        if '阶段4: 统一工具模块' in line:
            # 找到统一工具模块的结束
            for j in range(i, min(i+10, len(lines))):
                if 'logger.info' in lines[j] and '统一工具' in lines[j]:
                    end_remove = j + 2
                    break
            if end_remove:
                break
    
    if start_remove and end_remove:
        # 删除旧的统一模块注册
        del lines[start_remove:end_remove]
        print(f"删除了第{start_remove+1}到{end_remove}行的旧注册")
        
        # 重新计算插入位置
        insert_pos = start_remove
    
    # 插入新的统一模块注册
    unified_registration = """
# ============================================================================
# 统一模块注册区域
# ============================================================================

# 阶段2: 统一知识图谱模块
app.include_router(unified_knowledge_graph.router, tags=["统一知识图谱"])
logger.info("✅ 统一知识图谱API已注册 (合并7个旧模块)")

# 阶段2: 统一文档处理模块
app.include_router(unified_documents.router, tags=["统一文档处理"])
logger.info("✅ 统一文档处理API已注册 (合并4个旧模块)")

# 阶段2: 统一RAG检索模块
app.include_router(unified_rag.router, tags=["统一RAG检索"])
logger.info("✅ 统一RAG检索API已注册 (合并5个旧模块)")

# 阶段3: 统一聊天对话模块
app.include_router(unified_chat.router, tags=["统一聊天对话"])
logger.info("✅ 统一聊天对话API已注册 (合并5个旧模块)")

# 阶段3: 统一分析模块
app.include_router(unified_analysis.router, tags=["统一分析"])
logger.info("✅ 统一分析API已注册 (合并3个旧模块)")

# 阶段3: 统一项目管理模块
app.include_router(unified_projects.router, tags=["统一项目管理"])
logger.info("✅ 统一项目管理API已注册 (合并2个旧模块)")

# 阶段4: 统一技能管理模块
app.include_router(unified_skills.router, tags=["统一技能管理"])
logger.info("✅ 统一技能管理API已注册 (合并3个旧模块)")

# 阶段4: 统一报告生成模块
app.include_router(unified_reports.router, tags=["统一报告生成"])
logger.info("✅ 统一报告生成API已注册 (合并2个旧模块)")

# 阶段4: 统一工具模块
app.include_router(unified_tools.router, tags=["统一工具"])
logger.info("✅ 统一工具API已注册 (合并OCR等工具)")

# ============================================================================
# 其他API模块
# ============================================================================

"""
    
    lines.insert(insert_pos, unified_registration)
    print(f"在第{insert_pos+1}行插入统一模块注册")
    
    # 写回文件
    with open(main_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n✅ 修复完成！")
else:
    print("❌ 未找到batch_processing路由")
