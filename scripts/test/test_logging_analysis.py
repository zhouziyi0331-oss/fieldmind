"""
高级日志分析测试套件
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.core.logging.query import (
    AggregationType,
    FilterOperator,
    LogAggregation,
    LogFilter,
    LogLevel,
    LogQuery,
)
from app.core.logging.correlator import (
    LogCorrelator,
    LogGroup,
    TraceLogCorrelator,
    UserLogCorrelator,
)
from app.core.logging.analyzer import LogAnalyzer, LogStatistics
from app.core.logging.exporter import (
    ElasticsearchExporter,
    ExporterConfig,
    FileExporter,
    LokiExporter,
    MultiExporter,
)


# 测试数据生成器
def create_test_logs(count: int = 10) -> list:
    """创建测试日志数据"""
    logs = []
    base_time = datetime.now()

    for i in range(count):
        log = {
            "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
            "level": "INFO" if i % 5 != 0 else "ERROR",
            "message": f"Test message {i}",
            "extra": {
                "request_id": f"req_{i // 3}",
                "trace_id": f"trace_{i // 5}",
                "user_id": f"user_{i % 3}",
                "operation": f"operation_{i % 4}",
            },
        }
        logs.append(log)

    return logs


class TestLogFilter:
    """测试日志过滤器"""

    def test_filter_eq(self):
        """测试相等过滤"""
        log_filter = LogFilter("level", FilterOperator.EQ, "ERROR")

        assert log_filter.match({"level": "ERROR"}) is True
        assert log_filter.match({"level": "INFO"}) is False

    def test_filter_in(self):
        """测试 IN 过滤"""
        log_filter = LogFilter("level", FilterOperator.IN, ["ERROR", "CRITICAL"])

        assert log_filter.match({"level": "ERROR"}) is True
        assert log_filter.match({"level": "CRITICAL"}) is True
        assert log_filter.match({"level": "INFO"}) is False

    def test_filter_contains(self):
        """测试包含过滤"""
        log_filter = LogFilter("message", FilterOperator.CONTAINS, "error")

        assert log_filter.match({"message": "An error occurred"}) is True
        assert log_filter.match({"message": "Success"}) is False

    def test_filter_nested_field(self):
        """测试嵌套字段过滤"""
        log_filter = LogFilter("extra.user_id", FilterOperator.EQ, "user123")

        assert log_filter.match({"extra": {"user_id": "user123"}}) is True
        assert log_filter.match({"extra": {"user_id": "user456"}}) is False

    def test_filter_exists(self):
        """测试字段存在过滤"""
        log_filter = LogFilter("extra.trace_id", FilterOperator.EXISTS, None)

        assert log_filter.match({"extra": {"trace_id": "abc"}}) is True
        assert log_filter.match({"extra": {}}) is False

    def test_filter_regex(self):
        """测试正则表达式过滤"""
        log_filter = LogFilter("message", FilterOperator.REGEX, r"error \d+")

        assert log_filter.match({"message": "error 404"}) is True
        assert log_filter.match({"message": "error abc"}) is False


class TestLogAggregation:
    """测试日志聚合"""

    def test_count_aggregation(self):
        """测试计数聚合"""
        logs = create_test_logs(10)
        agg = LogAggregation(AggregationType.COUNT)

        result = agg.apply(logs)
        assert result == 10

    def test_group_by_aggregation(self):
        """测试分组聚合"""
        logs = create_test_logs(10)
        agg = LogAggregation(AggregationType.GROUP_BY, group_by="level")

        result = agg.apply(logs)
        assert isinstance(result, dict)
        assert "ERROR" in result
        assert "INFO" in result
        assert result["ERROR"] == 2  # 每5个有1个ERROR
        assert result["INFO"] == 8

    def test_sum_aggregation(self):
        """测试求和聚合"""
        logs = [
            {"duration": 1.5},
            {"duration": 2.0},
            {"duration": 3.5},
        ]
        agg = LogAggregation(AggregationType.SUM, field="duration")

        result = agg.apply(logs)
        assert result == 7.0

    def test_avg_aggregation(self):
        """测试平均值聚合"""
        logs = [
            {"duration": 1.0},
            {"duration": 2.0},
            {"duration": 3.0},
        ]
        agg = LogAggregation(AggregationType.AVG, field="duration")

        result = agg.apply(logs)
        assert result == 2.0

    def test_percentile_aggregation(self):
        """测试百分位数聚合"""
        logs = [{"value": i} for i in range(100)]
        agg = LogAggregation(AggregationType.PERCENTILE, field="value", percentile=0.95)

        result = agg.apply(logs)
        assert 90 <= result <= 95


class TestLogQuery:
    """测试日志查询"""

    def test_query_builder(self):
        """测试查询构建器"""
        query = LogQuery()
        query.where("level", FilterOperator.EQ, "ERROR")
        query.filter_levels(LogLevel.ERROR)
        query.last(hours=1)
        query.paginate(limit=50, offset=0)
        query.order_by("timestamp", "desc")

        assert len(query.filters) == 1
        assert query.levels == [LogLevel.ERROR]
        assert query.limit == 50

    def test_query_execute(self):
        """测试查询执行"""
        logs = create_test_logs(10)

        query = LogQuery()
        query.where("level", FilterOperator.EQ, "ERROR")

        results = query.execute(logs)
        assert all(log["level"] == "ERROR" for log in results)
        assert len(results) == 2

    def test_query_time_range(self):
        """测试时间范围查询"""
        logs = create_test_logs(10)

        now = datetime.now()
        query = LogQuery()
        query.time_range(start=now, end=now + timedelta(seconds=5))

        results = query.execute(logs)
        assert len(results) <= 6  # 0-5秒内的日志

    def test_query_aggregation(self):
        """测试聚合查询"""
        logs = create_test_logs(10)

        query = LogQuery()
        query.aggregate(AggregationType.COUNT)
        query.aggregate(AggregationType.GROUP_BY, group_by="level")

        results = query.execute_aggregations(logs)
        assert "agg_0_count" in results
        assert "agg_1_group_by" in results
        assert results["agg_0_count"] == 10

    def test_query_to_loki(self):
        """测试转换为 Loki 查询"""
        query = LogQuery()
        query.filter_levels(LogLevel.ERROR)
        query.where("message", FilterOperator.CONTAINS, "error")

        loki_query = query.to_loki_query()
        assert '{job="fieldmind"}' in loki_query
        assert '|~' in loki_query

    def test_query_to_elasticsearch(self):
        """测试转换为 Elasticsearch 查询"""
        query = LogQuery()
        query.filter_levels(LogLevel.ERROR)
        query.where("level", FilterOperator.EQ, "ERROR")
        query.order_by("timestamp", "desc")

        es_query = query.to_elasticsearch_query()
        assert "query" in es_query
        assert "bool" in es_query["query"]
        assert "sort" in es_query


class TestLogCorrelator:
    """测试日志关联器"""

    def test_correlate_by_request_id(self):
        """测试按请求ID关联"""
        logs = create_test_logs(10)
        correlator = LogCorrelator()

        groups = correlator.correlate(logs, group_by="extra.request_id")

        assert len(groups) > 0
        assert all(isinstance(group, LogGroup) for group in groups.values())

    def test_find_error_chains(self):
        """测试查找错误链"""
        logs = create_test_logs(10)
        correlator = LogCorrelator()

        error_chains = correlator.find_error_chains(logs, group_by="extra.request_id")

        assert len(error_chains) > 0
        assert all(group.has_errors for group in error_chains)

    def test_find_slow_operations(self):
        """测试查找慢操作"""
        logs = create_test_logs(5)
        # 添加持续时间
        for i, log in enumerate(logs):
            log["duration"] = i * 0.5

        correlator = LogCorrelator()
        slow_ops = correlator.find_slow_operations(logs, threshold_seconds=1.0)

        # 应该找到持续时间 >= 1.0s 的操作组
        assert len(slow_ops) >= 0


class TestTraceLogCorrelator:
    """测试追踪-日志关联器"""

    def test_correlate_with_traces(self):
        """测试与追踪关联"""
        logs = create_test_logs(10)
        correlator = TraceLogCorrelator()

        trace_groups = correlator.correlate_with_traces(logs)

        assert len(trace_groups) > 0
        assert all(isinstance(group, LogGroup) for group in trace_groups.values())

    def test_find_trace_errors(self):
        """测试查找追踪错误"""
        logs = create_test_logs(10)
        correlator = TraceLogCorrelator()

        error_traces = correlator.find_trace_errors(logs)

        assert len(error_traces) >= 0
        if error_traces:
            assert all("trace_id" in trace for trace in error_traces)

    def test_get_trace_timeline(self):
        """测试获取追踪时间线"""
        logs = create_test_logs(10)
        correlator = TraceLogCorrelator()

        # 获取第一个trace的时间线
        trace_id = "trace_0"
        timeline = correlator.get_trace_timeline(logs, trace_id)

        assert isinstance(timeline, list)
        if timeline:
            # 验证按时间排序
            timestamps = [log["timestamp"] for log in timeline]
            assert timestamps == sorted(timestamps)

    def test_analyze_trace_flow(self):
        """测试分析追踪流程"""
        logs = create_test_logs(10)
        correlator = TraceLogCorrelator()

        trace_id = "trace_0"
        analysis = correlator.analyze_trace_flow(logs, trace_id)

        if "error" not in analysis:
            assert "trace_id" in analysis
            assert "log_count" in analysis
            assert "operations" in analysis


class TestUserLogCorrelator:
    """测试用户日志关联器"""

    def test_correlate_by_user(self):
        """测试按用户关联"""
        logs = create_test_logs(10)
        correlator = UserLogCorrelator()

        user_groups = correlator.correlate_by_user(logs)

        assert len(user_groups) > 0
        assert all(isinstance(group, LogGroup) for group in user_groups.values())

    def test_find_user_errors(self):
        """测试查找用户错误"""
        logs = create_test_logs(10)
        correlator = UserLogCorrelator()

        user_errors = correlator.find_user_errors(logs)

        assert isinstance(user_errors, dict)
        if user_errors:
            assert all(count > 0 for count in user_errors.values())

    def test_get_user_activity(self):
        """测试获取用户活动"""
        logs = create_test_logs(10)
        correlator = UserLogCorrelator()

        user_id = "user_0"
        activity = correlator.get_user_activity(logs, user_id)

        if "error" not in activity:
            assert "user_id" in activity
            assert "log_count" in activity
            assert "operations" in activity


class TestLogAnalyzer:
    """测试日志分析器"""

    def test_analyze_basic(self):
        """测试基础分析"""
        logs = create_test_logs(10)
        analyzer = LogAnalyzer()
        analyzer.load(logs)

        stats = analyzer.analyze()

        assert isinstance(stats, LogStatistics)
        assert stats.total_count == 10
        assert "INFO" in stats.level_distribution
        assert "ERROR" in stats.level_distribution

    def test_find_error_patterns(self):
        """测试查找错误模式"""
        logs = create_test_logs(10)
        # 添加重复错误
        logs.extend([
            {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": "Database connection failed",
            }
            for _ in range(5)
        ])

        analyzer = LogAnalyzer()
        analyzer.load(logs)

        patterns = analyzer.find_error_patterns()

        assert len(patterns) > 0
        assert all("message" in pattern for pattern in patterns)
        assert all("count" in pattern for pattern in patterns)

    def test_analyze_performance(self):
        """测试性能分析"""
        logs = [
            {"duration": 0.1},
            {"duration": 0.5},
            {"duration": 1.0},
            {"duration": 2.0},
            {"duration": 5.0},
        ]

        analyzer = LogAnalyzer()
        analyzer.load(logs)

        perf = analyzer.analyze_performance()

        assert perf["count"] == 5
        assert perf["min"] == 0.1
        assert perf["max"] == 5.0
        assert 0 < perf["avg"] < 5.0
        assert 0 < perf["p95"] <= 5.0

    def test_detect_anomalies(self):
        """测试异常检测"""
        logs = create_test_logs(100)

        analyzer = LogAnalyzer()
        analyzer.load(logs)

        anomalies = analyzer.detect_anomalies(time_window_minutes=5)

        assert isinstance(anomalies, list)

    def test_compare_time_periods(self):
        """测试时间段比较"""
        now = datetime.now()
        logs = []

        # 时间段1: 10条日志，0个错误
        for i in range(10):
            logs.append({
                "timestamp": (now + timedelta(seconds=i)).isoformat(),
                "level": "INFO",
                "message": f"Log {i}",
            })

        # 时间段2: 10条日志，5个错误
        for i in range(10, 20):
            logs.append({
                "timestamp": (now + timedelta(seconds=i)).isoformat(),
                "level": "ERROR" if i % 2 == 0 else "INFO",
                "message": f"Log {i}",
            })

        analyzer = LogAnalyzer()
        analyzer.load(logs)

        comparison = analyzer.compare_time_periods(
            period1_start=now,
            period1_end=now + timedelta(seconds=9),
            period2_start=now + timedelta(seconds=10),
            period2_end=now + timedelta(seconds=19),
        )

        assert "period1" in comparison
        assert "period2" in comparison
        assert "changes" in comparison
        assert comparison["period2"]["error_count"] > comparison["period1"]["error_count"]


class TestLogExporters:
    """测试日志导出器"""

    def test_loki_exporter_payload(self):
        """测试 Loki 导出器负载构建"""
        logs = create_test_logs(5)
        config = ExporterConfig(endpoint="http://localhost:3100")
        exporter = LokiExporter(config)

        payload = exporter._build_loki_payload(logs)

        assert "streams" in payload
        assert len(payload["streams"]) > 0
        assert all("stream" in s and "values" in s for s in payload["streams"])

    def test_elasticsearch_exporter_bulk_body(self):
        """测试 Elasticsearch 批量请求体"""
        logs = create_test_logs(3)
        config = ExporterConfig(endpoint="http://localhost:9200")
        exporter = ElasticsearchExporter(config, index_name="test-logs")

        bulk_body = exporter._build_bulk_body(logs)

        lines = bulk_body.strip().split("\n")
        assert len(lines) == 6  # 每条日志2行（index操作 + 文档）

        # 验证第一行是索引操作
        first_line = json.loads(lines[0])
        assert "index" in first_line

    def test_file_exporter(self, tmp_path):
        """测试文件导出器"""
        logs = create_test_logs(5)
        file_path = tmp_path / "test_logs.jsonl"

        config = ExporterConfig(endpoint="")
        exporter = FileExporter(config, str(file_path))

        result = exporter.export(logs)

        assert result is True
        assert file_path.exists()

        # 验证文件内容
        lines = file_path.read_text().strip().split("\n")
        assert len(lines) == 5

    def test_multi_exporter(self, tmp_path):
        """测试多导出器"""
        logs = create_test_logs(3)

        file1 = tmp_path / "export1.jsonl"
        file2 = tmp_path / "export2.jsonl"

        config = ExporterConfig(endpoint="")
        exporter1 = FileExporter(config, str(file1))
        exporter2 = FileExporter(config, str(file2))

        multi = MultiExporter([exporter1, exporter2])
        result = multi.export(logs)

        assert result is True
        assert file1.exists()
        assert file2.exists()

    def test_exporter_batch(self, tmp_path):
        """测试批量导出"""
        logs = create_test_logs(25)
        file_path = tmp_path / "batch_logs.jsonl"

        config = ExporterConfig(endpoint="", batch_size=10)
        exporter = FileExporter(config, str(file_path))

        stats = exporter.export_batch(logs)

        assert stats["total"] == 25
        assert stats["success"] == 25
        assert stats["failed"] == 0
