"""
Phase 3: 数据流打通验证测试

测试目标：
1. 验证ChunkingAgent的输出正确存储到DocumentChunk表
2. 验证VectorizationAgent从数据库读取chunks
3. 验证断点恢复机制
4. 验证跨阶段数据传递
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.agents.v2.coordinator import AgentCoordinator, PipelineStage, PipelineMode
from app.models.pipeline_state import PipelineExecution, PipelineStageResult, DocumentChunk


class TestPhase3DataFlow:
    """Phase 3 数据流测试套件"""

    def test_chunk_stage_stores_to_database(self, db_session: Session, test_project, test_document):
        """测试：ChunkingAgent的输出正确存储到DocumentChunk表"""
        coordinator = AgentCoordinator()

        # 模拟文档加载结果
        previous_results = {
            PipelineStage.DOCUMENT_LOAD: Mock(
                success=True,
                output={'documents': [test_document], 'document_count': 1}
            )
        }

        # 执行chunking阶段
        result = coordinator._stage_chunk(
            project_id=test_project.id,
            db_session=db_session,
            previous_results=previous_results
        )

        # 验证返回结果
        assert 'stored_chunk_ids' in result
        assert 'chunk_count' in result
        assert result['chunk_count'] > 0
        assert len(result['stored_chunk_ids']) == result['chunk_count']

        # 🔥 验证数据库中确实存储了chunks
        db_chunks = db_session.query(DocumentChunk).filter(
            DocumentChunk.id.in_(result['stored_chunk_ids'])
        ).all()

        assert len(db_chunks) == result['chunk_count']

        # 验证每个chunk的字段完整性
        for chunk in db_chunks:
            assert chunk.id is not None
            assert chunk.project_id == test_project.id
            assert chunk.document_id == test_document.id
            assert chunk.chunk_text is not None
            assert len(chunk.chunk_text) > 0
            assert chunk.chunk_size > 0

        print(f"✅ Test 1 通过：{len(db_chunks)} 个chunks已存储到数据库")

    def test_vectorization_stage_reads_from_database(self, db_session: Session, test_project):
        """测试：VectorizationAgent从数据库读取chunks（而非从内存）"""
        coordinator = AgentCoordinator()

        # 1. 先创建一些测试chunks到数据库
        test_chunks = []
        for i in range(3):
            chunk = DocumentChunk(
                project_id=test_project.id,
                document_id=1,
                chunk_index=i,
                chunk_text=f"这是测试chunk {i}的内容",
                chunk_size=20,
                chunking_method='test'
            )
            db_session.add(chunk)
            db_session.flush()
            test_chunks.append(chunk)

        db_session.commit()

        chunk_ids = [c.id for c in test_chunks]

        # 2. 模拟chunking阶段的结果（只传递IDs）
        previous_results = {
            PipelineStage.CHUNK: Mock(
                success=True,
                output={
                    'stored_chunk_ids': chunk_ids,
                    'chunk_count': len(chunk_ids)
                }
            )
        }

        # 3. Mock VectorizationAgent.vectorize_chunks
        mock_result = Mock(
            success_count=len(chunk_ids),
            failed_count=0,
            embedding_model='text-embedding-3-small',
            embedding_dim=1536
        )

        with patch.object(coordinator, '_get_analysis_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.vectorize_chunks.return_value = mock_result
            mock_get_agent.return_value = mock_agent

            # 4. 执行vectorization阶段
            result = coordinator._stage_analysis(
                project_id=test_project.id,
                db_session=db_session,
                previous_results=previous_results
            )

            # 5. 验证Agent被正确调用（传递了从数据库读取的chunks）
            mock_agent.vectorize_chunks.assert_called_once()
            call_args = mock_agent.vectorize_chunks.call_args

            # 验证传递的chunks参数
            chunks_param = call_args.kwargs['chunks']
            assert len(chunks_param) == len(chunk_ids)

            # 验证chunks是从数据库读取的（包含正确的文本）
            for i, chunk_dict in enumerate(chunks_param):
                assert chunk_dict['text'] == f"这是测试chunk {i}的内容"
                assert chunk_dict['chunk_id'] in chunk_ids

            # 验证store_to_db=True被传递
            assert call_args.kwargs['store_to_db'] == True

        print(f"✅ Test 2 通过：VectorizationAgent从数据库读取了 {len(chunk_ids)} 个chunks")

    def test_checkpoint_recovery_mechanism(self, db_session: Session, test_project):
        """测试：断点恢复机制能正确恢复已完成的阶段"""
        coordinator = AgentCoordinator(enable_checkpoint=True)

        # 1. 创建一个已完成部分阶段的执行记录
        execution_id = "test-exec-001"

        pipeline_exec = PipelineExecution(
            execution_id=execution_id,
            project_id=test_project.id,
            pipeline_mode='full',
            status='failed',
            current_stage='analysis',
            started_at=None,
            completed_at=None
        )
        db_session.add(pipeline_exec)

        # 2. 创建已完成的阶段结果（stage 1, 2已完成）
        stage1_result = PipelineStageResult(
            execution_id=execution_id,
            stage_name='document_load',
            stage_order=1,
            status='completed',
            duration_seconds=10,
            stage_data={
                'document_count': 2,
                'documents': []
            }
        )
        db_session.add(stage1_result)

        stage2_result = PipelineStageResult(
            execution_id=execution_id,
            stage_name='chunk',
            stage_order=2,
            status='completed',
            duration_seconds=20,
            stage_data={
                'chunk_count': 10,
                'stored_chunk_ids': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        )
        db_session.add(stage2_result)

        db_session.commit()

        # 3. 使用_resume_execution恢复
        with patch.object(coordinator, '_execute_stage') as mock_execute:
            # Mock后续阶段的执行
            mock_execute.return_value = Mock(
                stage=PipelineStage.ANALYSIS,
                success=True,
                duration_seconds=30,
                output={'vectorized_count': 10},
                errors=[],
                warnings=[]
            )

            # 调用恢复方法
            result = coordinator._resume_execution(
                execution_id=execution_id,
                db_session=db_session
            )

            # 验证：stage 1, 2未被重新执行（从数据库恢复）
            # 只有stage 3, 4, 5, 6被执行
            assert mock_execute.call_count == 4  # analysis, knowledge, synthesis, report

        print(f"✅ Test 3 通过：断点恢复正确跳过了已完成的 2 个阶段")

    def test_cross_stage_data_passing(self, db_session: Session, test_project):
        """测试：验证跨阶段数据传递使用数据库而非内存"""
        coordinator = AgentCoordinator()

        # 场景：Stage 2 → Stage 3 的数据传递

        # 1. Stage 2输出：stored_chunk_ids
        chunk_ids = [101, 102, 103]
        stage2_output = {
            'stored_chunk_ids': chunk_ids,
            'chunk_count': len(chunk_ids)
        }

        # 2. 在数据库中创建对应的chunks
        for chunk_id in chunk_ids:
            chunk = DocumentChunk(
                id=chunk_id,
                project_id=test_project.id,
                document_id=1,
                chunk_index=chunk_id - 100,
                chunk_text=f"Chunk {chunk_id} content",
                chunk_size=20,
                chunking_method='test'
            )
            db_session.add(chunk)

        db_session.commit()

        # 3. Stage 3读取：应该从数据库读取，而非从stage2_output中读取对象
        previous_results = {
            PipelineStage.CHUNK: Mock(
                success=True,
                output=stage2_output  # 注意：这里只有IDs，没有chunk对象
            )
        }

        with patch.object(coordinator, '_get_analysis_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.vectorize_chunks.return_value = Mock(
                success_count=3,
                failed_count=0,
                embedding_model='test-model',
                embedding_dim=768
            )
            mock_get_agent.return_value = mock_agent

            # 执行stage 3
            coordinator._stage_analysis(
                project_id=test_project.id,
                db_session=db_session,
                previous_results=previous_results
            )

            # 验证：Agent接收到的chunks是从数据库读取的
            call_args = mock_agent.vectorize_chunks.call_args
            chunks_param = call_args.kwargs['chunks']

            assert len(chunks_param) == 3
            for chunk_dict in chunks_param:
                assert 'text' in chunk_dict
                assert 'Chunk' in chunk_dict['text']  # 从数据库读取的文本

        print(f"✅ Test 4 通过：Stage 3从数据库读取了 {len(chunk_ids)} 个chunks")

    def test_pipeline_state_result_stores_output(self, db_session: Session, test_project):
        """测试：PipelineStageResult.stage_data正确存储每个阶段的输出"""
        coordinator = AgentCoordinator()
        execution_id = "test-exec-002"

        # 创建执行记录
        pipeline_exec = PipelineExecution(
            execution_id=execution_id,
            project_id=test_project.id,
            pipeline_mode='full',
            status='running'
        )
        db_session.add(pipeline_exec)
        db_session.commit()

        # 模拟一个阶段结果
        from app.agents.v2.coordinator import StageResult

        stage_result = StageResult(
            stage=PipelineStage.CHUNK,
            success=True,
            duration_seconds=15.5,
            output={
                'chunk_count': 25,
                'stored_chunk_ids': list(range(1, 26)),
                'document_count': 3
            },
            errors=[],
            warnings=[]
        )

        # 保存到数据库
        coordinator._save_stage_result(
            execution_id=execution_id,
            stage=PipelineStage.CHUNK,
            result=stage_result,
            db_session=db_session
        )

        # 从数据库读取验证
        saved_stage = db_session.query(PipelineStageResult).filter(
            PipelineStageResult.execution_id == execution_id,
            PipelineStageResult.stage_name == 'chunk'
        ).first()

        assert saved_stage is not None
        assert saved_stage.status == 'completed'
        assert saved_stage.duration_seconds == 15.5

        # 🔥 验证stage_data字段正确存储了JSON
        stage_data = saved_stage.stage_data
        assert stage_data['chunk_count'] == 25
        assert len(stage_data['stored_chunk_ids']) == 25
        assert stage_data['document_count'] == 3

        print(f"✅ Test 5 通过：PipelineStageResult正确存储了阶段输出数据")


# ==================== Fixtures ====================

@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    from app.models.project import Project

    project = Project(
        id=999,
        name="Phase3测试项目",
        description="用于测试数据流打通"
    )
    db_session.add(project)
    db_session.commit()

    yield project

    # Cleanup
    db_session.delete(project)
    db_session.commit()


@pytest.fixture
def test_document(db_session: Session, test_project):
    """创建测试文档"""
    from app.models.project import ProjectDocument

    doc = ProjectDocument(
        id=888,
        project_id=test_project.id,
        file_path="/test/doc.txt",
        file_type="text",
        text_content="这是一个测试文档的内容。" * 50  # 足够生成多个chunks
    )
    db_session.add(doc)
    db_session.commit()

    yield doc

    # Cleanup
    db_session.delete(doc)
    db_session.commit()


if __name__ == "__main__":
    print("Phase 3 数据流测试套件")
    print("运行方式: pytest tests/test_phase3_data_flow.py -v")
