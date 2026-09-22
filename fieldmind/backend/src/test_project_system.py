#!/usr/bin/env python3
"""
项目隔离系统测试脚本
测试核心功能：项目创建、文档管理、对话、记忆系统
"""

import sys
sys.path.insert(0, '.')

from app.models.project import (
    Project, ProjectDocument, ProjectContext,
    ProjectChatSession, ProjectChatMessage, ProjectMemory
)
from app.core.database import SessionLocal, init_db

def test_models():
    """测试数据模型"""
    print("=" * 60)
    print("🧪 测试 1: 数据模型导入")
    print("=" * 60)
    
    models = [
        ("Project", Project),
        ("ProjectDocument", ProjectDocument),
        ("ProjectContext", ProjectContext),
        ("ProjectChatSession", ProjectChatSession),
        ("ProjectChatMessage", ProjectChatMessage),
        ("ProjectMemory", ProjectMemory)
    ]
    
    for name, model in models:
        print(f"  ✅ {name}: {model.__tablename__}")
    
    print("\n✨ 所有模型导入成功\n")


def test_database():
    """测试数据库初始化"""
    print("=" * 60)
    print("🧪 测试 2: 数据库初始化")
    print("=" * 60)
    
    try:
        init_db()
        print("  ✅ 数据库表创建成功")
    except Exception as e:
        print(f"  ❌ 数据库初始化失败: {e}")
        return False
    
    print("\n✨ 数据库初始化成功\n")
    return True


def test_project_creation():
    """测试项目创建"""
    print("=" * 60)
    print("🧪 测试 3: 项目创建")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建测试项目
        project = Project(
            name="测试项目",
            description="这是一个测试项目",
            owner_id=1,  # 假设用户ID为1
            settings={"test": True}
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        print(f"  ✅ 项目创建成功")
        print(f"     ID: {project.id}")
        print(f"     名称: {project.name}")
        print(f"     状态: {project.status}")
        
        return project.id
        
    except Exception as e:
        print(f"  ❌ 项目创建失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()
    
    print("\n✨ 项目创建测试完成\n")


def test_document_upload(project_id):
    """测试文档上传"""
    print("=" * 60)
    print("🧪 测试 4: 文档上传")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建测试文档
        document = ProjectDocument(
            project_id=project_id,
            filename="test_doc.txt",
            original_filename="测试文档.txt",
            file_type="txt",
            file_path="/tmp/test_doc.txt",
            file_size=1024,
            status="completed",
            summary="这是一个测试文档的摘要",
            keywords=["测试", "文档", "关键词"]
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        print(f"  ✅ 文档上传成功")
        print(f"     ID: {document.id}")
        print(f"     文件名: {document.original_filename}")
        print(f"     状态: {document.status}")
        
        return document.id
        
    except Exception as e:
        print(f"  ❌ 文档上传失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()
    
    print("\n✨ 文档上传测试完成\n")


def test_memory_system(project_id):
    """测试记忆系统"""
    print("=" * 60)
    print("🧪 测试 5: 三层记忆系统")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建不同层级的记忆
        memories = [
            ProjectMemory(
                project_id=project_id,
                memory_type="short_term",
                content="这是一条短期记忆",
                summary="短期记忆摘要",
                relevance_score=70
            ),
            ProjectMemory(
                project_id=project_id,
                memory_type="mid_term",
                content="这是一条中期记忆",
                summary="中期记忆摘要",
                relevance_score=80
            ),
            ProjectMemory(
                project_id=project_id,
                memory_type="long_term",
                content="这是一条长期记忆",
                summary="长期记忆摘要",
                relevance_score=90
            )
        ]
        
        for memory in memories:
            db.add(memory)
        
        db.commit()
        
        print(f"  ✅ 创建了 {len(memories)} 条记忆")
        for memory in memories:
            print(f"     - {memory.memory_type}: {memory.summary}")
        
    except Exception as e:
        print(f"  ❌ 记忆系统测试失败: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✨ 记忆系统测试完成\n")


def test_chat_session(project_id):
    """测试对话会话"""
    print("=" * 60)
    print("🧪 测试 6: 对话会话")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建对话会话
        session = ProjectChatSession(
            project_id=project_id,
            name="测试对话",
            config={
                "use_long_memory": True,
                "use_deep_thinking": True,
                "skill_name": "fxt-differential"
            }
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # 创建对话消息
        messages = [
            ProjectChatMessage(
                session_id=session.id,
                role="user",
                content="这是一条用户消息"
            ),
            ProjectChatMessage(
                session_id=session.id,
                role="assistant",
                content="这是AI的回复",
                thinking_process="深度思考过程...",
                sources=[{"document_id": 1, "relevance": 0.95}]
            )
        ]
        
        for msg in messages:
            db.add(msg)
        
        db.commit()
        
        print(f"  ✅ 对话会话创建成功")
        print(f"     会话ID: {session.id}")
        print(f"     会话名称: {session.name}")
        print(f"     消息数: {len(messages)}")
        
    except Exception as e:
        print(f"  ❌ 对话会话测试失败: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✨ 对话会话测试完成\n")


def test_context_hierarchy(project_id):
    """测试知识脉络层级"""
    print("=" * 60)
    print("🧪 测试 7: 知识脉络层级")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建三级知识脉络
        level1 = ProjectContext(
            project_id=project_id,
            name="社会关系",
            level=1,
            keywords=["社会", "关系", "结构"]
        )
        db.add(level1)
        db.commit()
        db.refresh(level1)
        
        level2 = ProjectContext(
            project_id=project_id,
            name="家庭关系",
            level=2,
            parent_id=level1.id,
            keywords=["家庭", "亲属"]
        )
        db.add(level2)
        db.commit()
        db.refresh(level2)
        
        level3 = ProjectContext(
            project_id=project_id,
            name="代际关系",
            level=3,
            parent_id=level2.id,
            keywords=["代际", "传承"]
        )
        db.add(level3)
        db.commit()
        
        print(f"  ✅ 知识脉络创建成功")
        print(f"     Level 1: {level1.name}")
        print(f"     Level 2: {level2.name} (parent: {level1.id})")
        print(f"     Level 3: {level3.name} (parent: {level2.id})")
        
    except Exception as e:
        print(f"  ❌ 知识脉络测试失败: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✨ 知识脉络测试完成\n")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🎯 FieldMind 项目隔离系统测试")
    print("=" * 60 + "\n")
    
    # 测试1: 模型导入
    test_models()
    
    # 测试2: 数据库初始化
    if not test_database():
        print("❌ 数据库初始化失败，测试终止")
        return
    
    # 测试3: 项目创建
    project_id = test_project_creation()
    if not project_id:
        print("❌ 项目创建失败，测试终止")
        return
    
    # 测试4: 文档上传
    test_document_upload(project_id)
    
    # 测试5: 记忆系统
    test_memory_system(project_id)
    
    # 测试6: 对话会话
    test_chat_session(project_id)
    
    # 测试7: 知识脉络
    test_context_hierarchy(project_id)
    
    print("=" * 60)
    print("✨ 所有测试完成！")
    print("=" * 60)
    print(f"\n📊 测试项目ID: {project_id}")
    print("   可以在数据库中查看创建的数据\n")


if __name__ == "__main__":
    main()
