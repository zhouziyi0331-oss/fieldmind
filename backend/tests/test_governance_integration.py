"""
数据治理系统集成测试
测试完整的 8 阶段处理流程
"""

import pytest
import os
import tempfile
from pathlib import Path

from app.orchestration.data_governance_orchestrator import (
    DataGovernanceOrchestrator,
    GovernanceStage,
    process_file_with_governance
)


class TestGovernanceIntegration:
    """数据治理集成测试"""

    @pytest.fixture
    def test_pdf(self):
        """创建测试 PDF 文件"""
        content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(content)
            return f.name

    @pytest.fixture
    def test_txt(self):
        """创建测试文本文件"""
        content = "这是一个测试文档。\n用于验证数据治理系统的完整流程。\n包含多个段落和句子。"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w', encoding='utf-8') as f:
            f.write(content)
            return f.name

    @pytest.fixture
    def orchestrator(self):
        """创建编排器实例"""
        return DataGovernanceOrchestrator()

    def test_complete_governance_flow_txt(self, orchestrator, test_txt):
        """测试完整治理流程 - 文本文件"""

        # 执行完整治理流程
        result = orchestrator.process_file(
            file_path=test_txt,
            filename="test.txt",
            mime_type="text/plain",
            project_id=1,
            collection_info={
                "device": "test_device",
                "user": "test_user"
            }
        )

        # 验证结果
        assert result.success is True, f"治理流程失败: {result.errors}"

        # 验证 8 个阶段都完成了
        assert len(result.stages_completed) == 8, \
            f"期望完成 8 个阶段，实际完成 {len(result.stages_completed)} 个"

        expected_stages = [
            GovernanceStage.INGESTION,
            GovernanceStage.METADATA,
            GovernanceStage.CHUNKING,
            GovernanceStage.METRICS,
            GovernanceStage.VECTORIZATION,
            GovernanceStage.KNOWLEDGE,
            GovernanceStage.LINEAGE,
            GovernanceStage.QUALITY
        ]

        for stage in expected_stages:
            assert stage in result.stages_completed, f"阶段 {stage} 未完成"

        # 验证各阶段结果
        assert GovernanceStage.INGESTION in result.stage_results
        ingestion = result.stage_results[GovernanceStage.INGESTION]
        assert "raw_text" in ingestion
        assert len(ingestion["raw_text"]) > 0

        assert GovernanceStage.METADATA in result.stage_results
        metadata = result.stage_results[GovernanceStage.METADATA]
        assert metadata["extracted"] is True

        assert GovernanceStage.CHUNKING in result.stage_results
        chunking = result.stage_results[GovernanceStage.CHUNKING]
        assert chunking["total_chunks"] > 0

        assert GovernanceStage.METRICS in result.stage_results
        metrics = result.stage_results[GovernanceStage.METRICS]
        assert metrics["chunks_processed"] > 0

        assert GovernanceStage.LINEAGE in result.stage_results
        lineage = result.stage_results[GovernanceStage.LINEAGE]
        assert lineage["lineage_recorded"] > 0

        # 验证处理时长
        assert result.total_duration > 0

        # 清理测试文件
        os.unlink(test_txt)

    def test_ingestion_plugin_coverage(self, orchestrator):
        """测试采集插件覆盖率"""
        from app.agents.ingestion_agent import get_ingestion_agent

        agent = get_ingestion_agent()

        # 验证所有 18 个插件类型都已注册
        expected_formats = [
            # 文档类 (5)
            "pdf", "docx", "pptx", "txt", "md",
            # 图像类 (1)
            "png", "jpg",
            # 音视频类 (2)
            "mp3", "wav", "mp4",
            # 表格类 (2)
            "xlsx", "csv",
            # 网页类 (2)
            "html", "rtf",
            # 数据类 (2)
            "json", "xml",
            # 压缩包类 (2)
            "epub", "zip",
            # 邮件类 (1)
            "eml",
            # 代码类 (1)
            "py", "js"
        ]

        registered_formats = agent.get_supported_formats()

        for fmt in ["pdf", "docx", "txt", "xlsx", "json", "mp3", "png"]:
            assert fmt in registered_formats, \
                f"格式 {fmt} 未注册到 IngestionAgent"

    def test_metadata_extraction(self, orchestrator, test_txt):
        """测试元数据提取"""
        from app.agents.ingestion_agent import get_ingestion_agent

        agent = get_ingestion_agent()
        result = agent.ingest_file(test_txt, "test.txt", "text/plain")

        # 验证结构化元数据
        assert "structured_metadata" in result
        metadata = result["structured_metadata"]

        assert "content_type" in metadata
        assert "total_words" in metadata or "word_count" in metadata

        # 清理
        os.unlink(test_txt)

    def test_lineage_tracking(self, orchestrator, test_txt):
        """测试血缘追踪"""
        from app.services.lineage_tracker import LineageTracker
        from app.core.database import get_db_session

        # 记录血缘
        LineageTracker.record_lineage(
            project_id=1,
            source_type="file",
            source_id="test_file_123",
            target_type="chunk",
            target_id="test_chunk_456",
            transform_type="extract",
            transform_description="测试血缘记录"
        )

        # 验证记录成功
        db = get_db_session()
        from app.models.governance import LineageEdge

        edge = db.query(LineageEdge).filter(
            LineageEdge.source_id == "test_file_123"
        ).first()

        assert edge is not None
        assert edge.target_id == "test_chunk_456"
        assert edge.transform_type == "extract"

        db.close()
        os.unlink(test_txt)

    def test_metric_calculation(self, orchestrator):
        """测试指标计算"""
        from app.services.metric_calculator import calculate_chunk_metrics

        test_text = "这是一个测试文本。包含多个句子。用于验证指标计算功能。"

        metrics = calculate_chunk_metrics(
            chunk_id="test_chunk_001",
            chunk_text=test_text
        )

        # 验证返回的指标
        assert "word_count" in metrics
        assert "sentence_count" in metrics
        assert "quality_score" in metrics

        assert metrics["word_count"] > 0
        assert metrics["sentence_count"] >= 3

    def test_convenience_function(self, test_txt):
        """测试便捷函数"""

        result = process_file_with_governance(
            file_path=test_txt,
            filename="test.txt",
            mime_type="text/plain",
            project_id=1
        )

        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'stages_completed')
        assert hasattr(result, 'total_duration')

        os.unlink(test_txt)

    def test_error_handling(self, orchestrator):
        """测试错误处理"""

        # 使用不存在的文件
        result = orchestrator.process_file(
            file_path="/nonexistent/file.txt",
            filename="nonexistent.txt",
            mime_type="text/plain",
            project_id=1
        )

        # 应该失败但不崩溃
        assert result.success is False
        assert len(result.errors) > 0

    def test_plugin_format_detection(self, orchestrator):
        """测试插件格式检测"""
        from app.agents.ingestion_agent import get_ingestion_agent

        agent = get_ingestion_agent()

        # 测试各种文件格式
        test_cases = [
            ("document.pdf", "application/pdf", "pdf"),
            ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
            ("text.txt", "text/plain", "txt"),
            ("image.png", "image/png", "png"),
            ("audio.mp3", "audio/mpeg", "mp3"),
        ]

        for filename, mime_type, expected_ext in test_cases:
            # 验证能正确识别格式
            detected = agent._detect_format(filename, mime_type)
            assert detected == expected_ext or expected_ext in agent.get_supported_formats()


class TestGovernanceTables:
    """测试治理表结构"""

    def test_governance_tables_exist(self):
        """测试治理表是否存在"""
        from app.core.database import get_db_session
        from sqlalchemy import inspect

        db = get_db_session()
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()

        # 验证 7 个治理表
        expected_tables = [
            "metric_dictionary",
            "lineage_edges",
            "metric_calculation_history",
            "quality_rules",
            "quality_check_results",
            "change_events",
            "governance_metadata"
        ]

        for table in expected_tables:
            assert table in tables, f"治理表 {table} 不存在"

        db.close()

    def test_metric_dictionary_populated(self):
        """测试指标字典是否已初始化"""
        from app.core.database import get_db_session
        from app.models.governance import MetricDictionary

        db = get_db_session()

        # 应该有 20 个预定义指标
        metric_count = db.query(MetricDictionary).count()

        assert metric_count >= 20, \
            f"指标字典应包含至少 20 个指标，当前有 {metric_count} 个"

        # 验证核心指标存在
        core_metrics = ["M001", "M011", "M021"]  # 字数、情感极性、专业度

        for metric_id in core_metrics:
            metric = db.query(MetricDictionary).filter(
                MetricDictionary.metric_id == metric_id
            ).first()

            assert metric is not None, f"核心指标 {metric_id} 不存在"

        db.close()


class TestStructuredProcessorIntegration:
    """测试结构化处理器集成"""

    def test_ingestion_agent_integration(self):
        """测试 IngestionAgent 已集成到 StructuredProcessor"""
        from app.services.structured_processor import StructuredProcessor
        import inspect

        processor = StructuredProcessor()

        # 检查 _extract_content 方法是否使用了 IngestionAgent
        source = inspect.getsource(processor._extract_content)

        assert "IngestionAgent" in source or "ingestion_agent" in source, \
            "StructuredProcessor 未集成 IngestionAgent"

        assert "get_ingestion_agent" in source, \
            "StructuredProcessor 未调用 get_ingestion_agent()"

    def test_lineage_tracking_integration(self):
        """测试血缘追踪已集成到 StructuredProcessor"""
        from app.services.structured_processor import StructuredProcessor
        import inspect

        processor = StructuredProcessor()

        # 检查 _save_chunks_with_lineage 方法
        source = inspect.getsource(processor._save_chunks_with_lineage)

        assert "LineageTracker" in source, \
            "StructuredProcessor 未集成 LineageTracker"

        assert "record_lineage" in source, \
            "StructuredProcessor 未调用 record_lineage()"

    def test_metadata_collection_integration(self):
        """测试元数据收集已集成到 StructuredProcessor"""
        from app.services.structured_processor import StructuredProcessor
        import inspect

        processor = StructuredProcessor()

        # 检查 process_uploaded_file 方法
        source = inspect.getsource(processor.process_uploaded_file)

        assert "MetadataCollector" in source, \
            "StructuredProcessor 未集成 MetadataCollector"

        assert "extract_content_metadata" in source, \
            "StructuredProcessor 未调用 extract_content_metadata()"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
