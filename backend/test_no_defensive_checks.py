#!/usr/bin/env python3
"""
测试：验证所有防御性检查已被移除，数据必须真实流通

目标：
1. 当输入为空时，应该抛出异常而不是返回空结果
2. 当处理失败时，应该抛出异常而不是静默跳过
3. 所有数据必须真实流通，不允许快速路径返回
"""
import sys
import os
sys.path.insert(0, 'src')

def test_knowledge_agent_no_documents():
    """测试：KnowledgeAgent.build_knowledge_graph() 在没有文档时应该抛出异常"""
    print("\n=== 测试1: KnowledgeAgent 无文档应抛异常 ===")

    from app.agents.v2.knowledge_agent import KnowledgeAgent
    from unittest.mock import MagicMock

    agent = KnowledgeAgent()
    mock_session = MagicMock()

    # Mock查询返回空列表
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = []
    mock_session.query.return_value = mock_query

    try:
        result = agent.build_knowledge_graph(
            project_id=999,
            db_session=mock_session
        )
        print("❌ 失败：应该抛出异常但返回了结果")
        return False
    except ValueError as e:
        if "没有文档" in str(e):
            print(f"✅ 成功：正确抛出异常 - {e}")
            return True
        else:
            print(f"❌ 失败：异常消息不正确 - {e}")
            return False
    except Exception as e:
        print(f"❌ 失败：抛出了错误的异常类型 - {type(e).__name__}: {e}")
        return False


def test_knowledge_agent_no_chunks_for_skills():
    """测试：KnowledgeAgent._analyze_with_skills() 在没有chunks时应该抛出异常"""
    print("\n=== 测试2: KnowledgeAgent Skills分析无chunks应抛异常 ===")

    from app.agents.v2.knowledge_agent import KnowledgeAgent
    from unittest.mock import MagicMock

    agent = KnowledgeAgent()
    mock_session = MagicMock()

    # Mock查询返回空列表
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = []
    mock_session.query.return_value = mock_query

    try:
        result = agent._analyze_with_skills(
            project_id=999,
            db_session=mock_session
        )
        print("❌ 失败：应该抛出异常但返回了结果")
        return False
    except ValueError as e:
        if "没有chunks" in str(e):
            print(f"✅ 成功：正确抛出异常 - {e}")
            return True
        else:
            print(f"❌ 失败：异常消息不正确 - {e}")
            return False
    except Exception as e:
        print(f"❌ 失败：抛出了错误的异常类型 - {type(e).__name__}: {e}")
        return False


def test_chunking_agent_no_sources():
    """测试：ChunkingAgent._match_sources_to_chunks 在没有溯源数据时应该抛出异常"""
    print("\n=== 测试3: ChunkingAgent 溯源匹配无sources应抛异常 ===")

    from app.agents.v2.chunking_agent import ChunkingAgent

    agent = ChunkingAgent()

    try:
        # 测试溯源匹配没有sources
        chunks = [{"text": "some text"}]
        result = agent._match_sources_to_chunks(chunks=chunks, sources=None)
        print("❌ 失败：应该抛出异常但返回了结果")
        return False
    except ValueError as e:
        if "溯源" in str(e):
            print(f"✅ 成功：正确抛出异常 - {e}")
            return True
        else:
            print(f"❌ 失败：异常消息不正确 - {e}")
            return False
    except Exception as e:
        print(f"❌ 失败：抛出了错误的异常类型 - {type(e).__name__}: {e}")
        return False


def test_chunking_agent_empty_chunk_text():
    """测试：ChunkingAgent._convert_to_standard_chunks 在chunk没有文本时应该抛出异常"""
    print("\n=== 测试4: ChunkingAgent 转换空chunk文本应抛异常 ===")

    from app.agents.v2.chunking_agent import ChunkingAgent

    agent = ChunkingAgent()

    try:
        # 直接测试包含空文本chunk的转换
        raw_chunks = [
            {"text": "valid text", "sources": []},
            {"text": "", "sources": []},  # 空文本
        ]

        result = agent._convert_to_standard_chunks(
            raw_chunks=raw_chunks,
            source_file="test.txt",
            file_type="text",
            language="zh"
        )
        print("❌ 失败：应该抛出异常但返回了结果")
        return False
    except ValueError as e:
        if "没有文本内容" in str(e):
            print(f"✅ 成功：正确抛出异常 - {e}")
            return True
        else:
            print(f"❌ 失败：异常消息不正确 - {e}")
            return False
    except Exception as e:
        print(f"❌ 失败：抛出了错误的异常类型 - {type(e).__name__}: {e}")
        return False


def test_v2_adapter_no_documents():
    """测试：V2Adapter._execute_chunking 在没有文档时应该抛出异常"""
    print("\n=== 测试5: V2Adapter ChunkingAgent 无文档应抛异常 ===")

    from app.services.workflows.v2_adapter import WorkflowV2Adapter
    from app.agents.v2.chunking_agent import ChunkingAgent
    from unittest.mock import MagicMock

    adapter = WorkflowV2Adapter()
    agent = ChunkingAgent()
    mock_session = MagicMock()

    try:
        result = adapter._execute_chunking(
            agent=agent,
            input_data={'documents': [], 'project_id': 999},
            db_session=mock_session
        )
        print("❌ 失败：应该抛出异常但返回了结果")
        return False
    except ValueError as e:
        if "没有文档" in str(e):
            print(f"✅ 成功：正确抛出异常 - {e}")
            return True
        else:
            print(f"❌ 失败：异常消息不正确 - {e}")
            return False
    except Exception as e:
        print(f"❌ 失败：抛出了错误的异常类型 - {type(e).__name__}: {e}")
        return False


def test_v2_adapter_no_chunks():
    """测试：V2Adapter._execute_vectorization 在没有chunks时应该抛出异常"""
    print("\n=== 测试6: V2Adapter VectorizationAgent 无chunks应抛异常 ===")

    from app.services.workflows.v2_adapter import WorkflowV2Adapter
    from app.agents.v2.vectorization_agent import VectorizationAgent
    from unittest.mock import MagicMock

    adapter = WorkflowV2Adapter()
    agent = VectorizationAgent()
    mock_session = MagicMock()

    try:
        result = adapter._execute_vectorization(
            agent=agent,
            input_data={'stored_chunk_ids': [], 'project_id': 999},
            db_session=mock_session
        )
        print("❌ 失败：应该抛出异常但返回了结果")
        return False
    except ValueError as e:
        if "chunk_ids" in str(e):
            print(f"✅ 成功：正确抛出异常 - {e}")
            return True
        else:
            print(f"❌ 失败：异常消息不正确 - {e}")
            return False
    except Exception as e:
        print(f"❌ 失败：抛出了错误的异常类型 - {type(e).__name__}: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("防御性检查清理验证测试")
    print("=" * 60)

    tests = [
        test_knowledge_agent_no_documents,
        test_knowledge_agent_no_chunks_for_skills,
        test_chunking_agent_no_sources,
        test_chunking_agent_empty_chunk_text,
        test_v2_adapter_no_documents,
        test_v2_adapter_no_chunks,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)

    if all(results):
        print("✅ 所有测试通过！数据必须真实流通，无静默失败")
        return 0
    else:
        print("❌ 部分测试失败，仍存在防御性检查")
        return 1


if __name__ == '__main__':
    sys.exit(main())
