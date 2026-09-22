"""
Tests for Custom Metrics and Dashboard System

Tests business metrics, dashboard builder, alert rules, and performance profiler.
"""

import pytest
import time
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry

from app.core.metrics.custom_metrics import (
    MetricType,
    CustomCounter,
    CustomGauge,
    CustomHistogram,
    CustomSummary,
    MetricRegistry,
    BusinessMetrics,
    record_business_event,
    track_user_action,
    measure_operation,
)

from app.core.metrics.dashboard import (
    VisualizationType,
    DataSource,
    Query,
    Panel,
    Dashboard,
    DashboardBuilder,
    GrafanaDashboard,
    export_grafana_dashboard,
)

from app.core.metrics.alerts import (
    AlertSeverity,
    ConditionOperator,
    AlertCondition,
    Alert,
    AlertRule,
    AlertManager,
    SlackNotifier,
    WebhookNotifier,
    create_default_alert_rules,
)

from app.core.metrics.profiler import (
    ProfileResult,
    PerformanceProfiler,
    profile_function,
    profile_block,
    analyze_performance,
    BottleneckDetector,
    PerformanceBudget,
)


class TestCustomMetrics:
    """Test custom metrics"""

    def test_custom_counter(self):
        """Test custom counter"""
        registry = CollectorRegistry()
        counter = CustomCounter(
            "test_counter",
            "Test counter",
            labels=["status"],
            registry=registry
        )

        counter.inc(status="success")
        counter.inc(amount=5.0, status="success")
        counter.inc(status="error")

        assert counter.count(status="success") == 6.0
        assert counter.count(status="error") == 1.0

    def test_custom_gauge(self):
        """Test custom gauge"""
        registry = CollectorRegistry()
        gauge = CustomGauge(
            "test_gauge",
            "Test gauge",
            labels=["type"],
            registry=registry
        )

        gauge.set(100.0, type="cpu")
        assert gauge.get(type="cpu") == 100.0

        gauge.inc(10.0, type="cpu")
        assert gauge.get(type="cpu") == 110.0

        gauge.dec(5.0, type="cpu")
        assert gauge.get(type="cpu") == 105.0

    def test_custom_histogram(self):
        """Test custom histogram"""
        registry = CollectorRegistry()
        histogram = CustomHistogram(
            "test_histogram",
            "Test histogram",
            labels=["method"],
            registry=registry
        )

        histogram.observe(0.5, method="GET")
        histogram.observe(1.5, method="GET")
        histogram.observe(2.5, method="POST")

        # Histogram doesn't expose counts directly in prometheus_client
        # but we can test the time context manager
        with histogram.time(method="GET"):
            time.sleep(0.01)

    def test_custom_summary(self):
        """Test custom summary"""
        registry = CollectorRegistry()
        summary = CustomSummary(
            "test_summary",
            "Test summary",
            labels=["operation"],
            registry=registry
        )

        summary.observe(0.5, operation="read")
        summary.observe(1.5, operation="write")

        with summary.time(operation="read"):
            time.sleep(0.01)

    def test_metric_registry(self):
        """Test metric registry"""
        registry = MetricRegistry()

        # Register counter
        counter = registry.register(
            "test_counter_registry",
            "Test counter",
            MetricType.COUNTER,
            labels=["status"]
        )
        assert counter is not None

        # Get metric
        same_counter = registry.get("test_counter_registry")
        assert same_counter is counter

        # List metrics
        metrics = registry.list_metrics()
        assert len(metrics) > 0

    def test_business_metrics(self):
        """Test business metrics initialization"""
        metrics = BusinessMetrics()

        # Test that all metrics are initialized
        assert metrics.user_registrations is not None
        assert metrics.documents_uploaded is not None
        assert metrics.queries_total is not None
        assert metrics.rag_retrievals is not None
        assert metrics.ai_requests is not None
        assert metrics.kg_nodes is not None

    def test_record_business_event(self):
        """Test recording business events"""
        metrics = BusinessMetrics()

        # Record user registration
        metrics.user_registrations.inc(source="direct")
        assert metrics.user_registrations.count(source="direct") >= 1.0

        # Record document upload
        metrics.documents_uploaded.inc(file_type="pdf", status="success")
        assert metrics.documents_uploaded.count(file_type="pdf", status="success") >= 1.0

    def test_track_user_action(self):
        """Test tracking user actions"""
        metrics = BusinessMetrics()

        # Track registration
        track_user_action("register", source="direct")

        # Track login
        track_user_action("login", status="success")

        # Track upload with size
        track_user_action("upload", file_type="pdf", status="success", size=1024000)

        # Track query with metrics
        track_user_action(
            "query",
            query_type="semantic",
            status="success",
            latency=0.5,
            result_count=10
        )

    def test_measure_operation(self):
        """Test operation measurement"""
        registry = MetricRegistry()
        histogram = registry.register(
            "test_operation_duration",
            "Test operation duration",
            MetricType.HISTOGRAM
        )

        with measure_operation("test_operation_duration"):
            time.sleep(0.01)


class TestDashboard:
    """Test dashboard builder"""

    def test_query_creation(self):
        """Test query creation"""
        query = Query(
            expr='rate(http_requests_total[5m])',
            legend="{{method}}",
            ref_id="A",
            datasource=DataSource.PROMETHEUS
        )

        assert query.expr == 'rate(http_requests_total[5m])'
        assert query.legend == "{{method}}"
        assert query.datasource == DataSource.PROMETHEUS

    def test_panel_creation(self):
        """Test panel creation"""
        query = Query(expr='up', legend="Status")
        panel = Panel(
            title="Service Status",
            queries=[query],
            visualization=VisualizationType.GAUGE,
            unit="short",
            min_value=0,
            max_value=1
        )

        assert panel.title == "Service Status"
        assert len(panel.queries) == 1
        assert panel.visualization == VisualizationType.GAUGE

    def test_panel_to_grafana_json(self):
        """Test panel conversion to Grafana JSON"""
        query = Query(expr='up', legend="Status")
        panel = Panel(
            title="Test Panel",
            queries=[query],
            visualization=VisualizationType.STAT
        )

        panel_json = panel.to_grafana_panel(1)

        assert panel_json["id"] == 1
        assert panel_json["title"] == "Test Panel"
        assert panel_json["type"] == "stat"
        assert len(panel_json["targets"]) == 1

    def test_dashboard_builder(self):
        """Test dashboard builder"""
        builder = DashboardBuilder("Test Dashboard", "Test description")

        builder.add_time_series_panel(
            "Request Rate",
            'rate(http_requests_total[5m])',
            legend="{{method}}",
            unit="reqps"
        )

        builder.add_stat_panel(
            "Total Requests",
            'sum(http_requests_total)',
            unit="short"
        )

        builder.add_gauge_panel(
            "CPU Usage",
            'cpu_usage_percent',
            unit="percent",
            max_value=100
        )

        dashboard = builder.build()

        assert dashboard.title == "Test Dashboard"
        assert len(dashboard.panels) == 3

    def test_dashboard_to_grafana_json(self):
        """Test dashboard conversion to Grafana JSON"""
        builder = DashboardBuilder("Test Dashboard")
        builder.add_stat_panel("Test", 'up')
        dashboard = builder.build()

        dashboard_json = dashboard.to_grafana_json()

        assert "dashboard" in dashboard_json
        assert dashboard_json["dashboard"]["title"] == "Test Dashboard"
        assert len(dashboard_json["dashboard"]["panels"]) == 1

    def test_grafana_overview_dashboard(self):
        """Test pre-built overview dashboard"""
        dashboard = GrafanaDashboard.create_overview_dashboard()

        assert dashboard.title == "FieldMind - System Overview"
        assert len(dashboard.panels) > 0
        assert "overview" in dashboard.tags

    def test_grafana_business_dashboard(self):
        """Test pre-built business dashboard"""
        dashboard = GrafanaDashboard.create_business_dashboard()

        assert dashboard.title == "FieldMind - Business Metrics"
        assert len(dashboard.panels) > 0
        assert "business" in dashboard.tags

    def test_grafana_ai_dashboard(self):
        """Test pre-built AI dashboard"""
        dashboard = GrafanaDashboard.create_ai_dashboard()

        assert dashboard.title == "FieldMind - AI Services"
        assert len(dashboard.panels) > 0
        assert "ai" in dashboard.tags

    def test_export_dashboard(self, tmp_path):
        """Test dashboard export"""
        builder = DashboardBuilder("Test")
        builder.add_stat_panel("Test", 'up')
        dashboard = builder.build()

        output_file = tmp_path / "dashboard.json"
        exported = export_grafana_dashboard(dashboard, str(output_file))

        assert output_file.exists()
        assert exported == str(output_file)


class TestAlerts:
    """Test alert system"""

    def test_alert_condition_evaluation(self):
        """Test alert condition evaluation"""
        condition = AlertCondition(
            metric="test_metric",
            operator=ConditionOperator.GT,
            threshold=100.0
        )

        assert condition.evaluate(150.0) is True
        assert condition.evaluate(100.0) is False
        assert condition.evaluate(50.0) is False

    def test_alert_condition_operators(self):
        """Test all condition operators"""
        tests = [
            (ConditionOperator.GT, 150, 100, True),
            (ConditionOperator.GTE, 100, 100, True),
            (ConditionOperator.LT, 50, 100, True),
            (ConditionOperator.LTE, 100, 100, True),
            (ConditionOperator.EQ, 100, 100, True),
            (ConditionOperator.NE, 99, 100, True),
        ]

        for operator, value, threshold, expected in tests:
            condition = AlertCondition(
                metric="test",
                operator=operator,
                threshold=threshold
            )
            assert condition.evaluate(value) == expected

    def test_alert_creation(self):
        """Test alert instance creation"""
        condition = AlertCondition(
            metric="error_rate",
            operator=ConditionOperator.GT,
            threshold=0.05
        )

        alert = Alert(
            rule_name="high_error_rate",
            severity=AlertSeverity.ERROR,
            message="Error rate too high",
            condition=condition,
            current_value=0.15
        )

        assert alert.rule_name == "high_error_rate"
        assert alert.severity == AlertSeverity.ERROR
        assert alert.current_value == 0.15

        alert_dict = alert.to_dict()
        assert alert_dict["severity"] == "error"

    def test_alert_rule(self):
        """Test alert rule"""
        condition = AlertCondition(
            metric="test_metric",
            operator=ConditionOperator.GT,
            threshold=100.0
        )

        rule = AlertRule(
            name="test_rule",
            condition=condition,
            severity=AlertSeverity.WARNING,
            message_template="Value is {value}, threshold is {threshold}",
            cooldown=timedelta(minutes=5)
        )

        # Should alert on first violation
        current_time = datetime.now()
        assert rule.should_alert(150.0, current_time) is True

        # Trigger the alert to set last_alert_time
        alert = rule.create_alert(150.0)
        assert alert is not None

        # Should not alert during cooldown
        assert rule.should_alert(150.0, current_time + timedelta(minutes=2)) is False

        # Should alert after cooldown
        assert rule.should_alert(150.0, current_time + timedelta(minutes=10)) is True

    def test_alert_manager(self):
        """Test alert manager"""
        manager = AlertManager()

        # Add rule
        condition = AlertCondition(
            metric="test_metric",
            operator=ConditionOperator.GT,
            threshold=100.0
        )

        rule = AlertRule(
            name="test_alert",
            condition=condition,
            severity=AlertSeverity.WARNING,
            message_template="Test alert: {value}"
        )

        manager.add_rule(rule)

        # Set metric provider
        def metric_provider(metric: str, labels: dict) -> float:
            return 150.0  # Above threshold

        manager.set_metric_provider(metric_provider)

        # Evaluate rules
        manager.evaluate_rules()

        # Check alert history
        alerts = manager.get_alert_history()
        assert len(alerts) > 0
        assert alerts[0].rule_name == "test_alert"

    def test_slack_notifier(self):
        """Test Slack notifier creation"""
        notifier = SlackNotifier(
            webhook_url="https://hooks.slack.com/services/TEST",
            channel="#alerts"
        )

        assert notifier.webhook_url == "https://hooks.slack.com/services/TEST"
        assert notifier.channel == "#alerts"

    def test_webhook_notifier(self):
        """Test webhook notifier creation"""
        notifier = WebhookNotifier(
            url="https://example.com/webhook",
            method="POST",
            headers={"Authorization": "Bearer token"}
        )

        assert notifier.url == "https://example.com/webhook"
        assert notifier.method == "POST"

    def test_default_alert_rules(self):
        """Test default alert rules creation"""
        rules = create_default_alert_rules()

        assert len(rules) > 0

        # Check for expected rules
        rule_names = [r.name for r in rules]
        assert "high_error_rate" in rule_names
        assert "high_latency_p95" in rule_names
        assert "db_pool_exhausted" in rule_names


class TestProfiler:
    """Test performance profiler"""

    def test_profile_result(self):
        """Test profile result"""
        result = ProfileResult(
            name="test_operation",
            duration=0.5,
            cpu_time=0.45,
            memory_delta=1024000,
            peak_memory=2048000,
            call_count=100
        )

        assert result.name == "test_operation"
        assert result.duration == 0.5

        result_dict = result.to_dict()
        assert result_dict["duration_ms"] == 500.0
        assert result_dict["memory_delta_mb"] == pytest.approx(0.976, rel=0.1)

    def test_performance_profiler_basic(self):
        """Test basic profiling"""
        profiler = PerformanceProfiler()

        with profiler.profile("test_operation"):
            time.sleep(0.01)
            result = sum(range(1000))

        profiles = profiler.get_profiles()
        assert len(profiles) == 1
        assert profiles[0].name == "test_operation"
        assert profiles[0].duration >= 0.01

    def test_performance_profiler_memory_tracking(self):
        """Test memory tracking"""
        profiler = PerformanceProfiler()
        profiler.enable_memory_tracking()

        with profiler.profile("memory_test"):
            # Allocate some memory
            data = [0] * 10000

        profiler.disable_memory_tracking()

        profiles = profiler.get_profiles(name="memory_test")
        assert len(profiles) == 1
        # Memory tracking should show some allocation
        assert profiles[0].peak_memory > 0

    def test_profile_function_decorator(self):
        """Test profile function decorator"""

        @profile_function("decorated_function")
        def test_func():
            time.sleep(0.01)
            return 42

        result = test_func()
        assert result == 42

        # Use the global profiler instance
        from app.core.metrics.profiler import get_profiler
        profiler = get_profiler()
        profiles = profiler.get_profiles(name="decorated_function")
        assert len(profiles) >= 1

    def test_profile_block_context_manager(self):
        """Test profile block context manager"""
        with profile_block("test_block"):
            time.sleep(0.01)

        analysis = analyze_performance("test_block")
        assert analysis["total_samples"] >= 1

    def test_analyze_performance(self):
        """Test performance analysis"""
        profiler = PerformanceProfiler()
        profiler.clear_profiles()

        # Create multiple profiles
        for i in range(5):
            with profiler.profile("analysis_test"):
                time.sleep(0.01)

        analysis = profiler.analyze_performance("analysis_test")

        assert analysis["total_samples"] == 5
        assert "duration" in analysis
        assert "p50" in analysis["duration"]
        assert "p95" in analysis["duration"]
        assert analysis["duration"]["avg"] >= 10.0  # At least 10ms average

    def test_bottleneck_detector(self):
        """Test bottleneck detection"""
        profiler = PerformanceProfiler()
        profiler.clear_profiles()

        # Create slow operation
        with profiler.profile("slow_op"):
            time.sleep(0.1)

        # Create fast operation
        with profiler.profile("fast_op"):
            time.sleep(0.001)

        detector = BottleneckDetector(profiler)

        # Find slow operations (>50ms)
        slow_ops = detector.find_slow_operations(threshold_ms=50.0)
        assert len(slow_ops) == 1
        assert slow_ops[0].name == "slow_op"

    def test_top_operations(self):
        """Test top operations retrieval"""
        profiler = PerformanceProfiler()
        profiler.clear_profiles()

        # Create operations with different durations
        for i in range(3):
            with profiler.profile(f"op_{i}"):
                time.sleep(0.01 * (i + 1))

        detector = BottleneckDetector(profiler)
        top_ops = detector.get_top_operations(by="duration", limit=2)

        assert len(top_ops) == 2
        # Top operation should be the slowest
        assert top_ops[0].name == "op_2"

    def test_performance_budget(self):
        """Test performance budget"""
        budget = PerformanceBudget()

        # Set budget
        budget.set_budget("critical_operation", max_duration_ms=100.0, max_memory_mb=10.0)

        # Check budget - under budget
        result_ok = ProfileResult(
            name="critical_operation",
            duration=0.05,  # 50ms
            cpu_time=0.05,
            memory_delta=5 * 1024 * 1024,  # 5MB
            peak_memory=5 * 1024 * 1024,
            call_count=10
        )

        check_ok = budget.check_budget(result_ok)
        assert check_ok["status"] == "ok"

        # Check budget - over budget
        result_bad = ProfileResult(
            name="critical_operation",
            duration=0.15,  # 150ms
            cpu_time=0.15,
            memory_delta=15 * 1024 * 1024,  # 15MB
            peak_memory=15 * 1024 * 1024,
            call_count=10
        )

        check_bad = budget.check_budget(result_bad)
        assert check_bad["status"] == "violated"
        assert len(check_bad["violations"]) == 2  # Both duration and memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
