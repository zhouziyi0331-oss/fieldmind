#!/usr/bin/env python3
"""
监控系统测试
验证所有监控组件是否正常工作
"""

import requests
import time
import sys
from typing import Dict, List, Tuple

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'


class MonitoringSystemTest:
    """监控系统测试器"""

    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        prometheus_url: str = "http://localhost:9090",
        grafana_url: str = "http://localhost:3000",
        alertmanager_url: str = "http://localhost:9093"
    ):
        self.backend_url = backend_url
        self.prometheus_url = prometheus_url
        self.grafana_url = grafana_url
        self.alertmanager_url = alertmanager_url
        self.results: List[Tuple[str, bool, str]] = []

    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{GREEN}{'=' * 60}{NC}")
        print(f"{GREEN}{text}{NC}")
        print(f"{GREEN}{'=' * 60}{NC}\n")

    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """打印测试结果"""
        status = f"{GREEN}✓ PASS{NC}" if passed else f"{RED}✗ FAIL{NC}"
        print(f"{status} - {test_name}")
        if message:
            print(f"      {message}")
        self.results.append((test_name, passed, message))

    def test_backend_health(self) -> bool:
        """测试Backend健康状态"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Backend健康检查",
                    True,
                    f"状态: {data.get('status')}"
                )
                return True
            else:
                self.print_result("Backend健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Backend健康检查", False, f"错误: {str(e)}")
            return False

    def test_metrics_endpoint(self) -> bool:
        """测试Prometheus指标端点"""
        try:
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            if response.status_code == 200:
                content = response.text
                # 检查是否包含关键指标
                has_metrics = all([
                    'http_requests_total' in content,
                    'http_request_duration_seconds' in content,
                    'system_cpu_usage_percent' in content
                ])
                self.print_result(
                    "Prometheus指标端点",
                    has_metrics,
                    f"指标行数: {len(content.splitlines())}"
                )
                return has_metrics
            else:
                self.print_result("Prometheus指标端点", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Prometheus指标端点", False, f"错误: {str(e)}")
            return False

    def test_prometheus_server(self) -> bool:
        """测试Prometheus服务器"""
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            passed = response.status_code == 200
            self.print_result(
                "Prometheus服务器",
                passed,
                f"状态码: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.print_result("Prometheus服务器", False, f"错误: {str(e)}")
            return False

    def test_prometheus_targets(self) -> bool:
        """测试Prometheus抓取目标"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])
                up_targets = sum(1 for t in targets if t.get('health') == 'up')
                total_targets = len(targets)
                self.print_result(
                    "Prometheus抓取目标",
                    up_targets > 0,
                    f"活跃目标: {up_targets}/{total_targets}"
                )
                return up_targets > 0
            else:
                self.print_result("Prometheus抓取目标", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Prometheus抓取目标", False, f"错误: {str(e)}")
            return False

    def test_prometheus_rules(self) -> bool:
        """测试Prometheus告警规则"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules", timeout=5)
            if response.status_code == 200:
                data = response.json()
                groups = data.get('data', {}).get('groups', [])
                total_rules = sum(len(g.get('rules', [])) for g in groups)
                self.print_result(
                    "Prometheus告警规则",
                    total_rules > 0,
                    f"规则组: {len(groups)}, 总规则: {total_rules}"
                )
                return total_rules > 0
            else:
                self.print_result("Prometheus告警规则", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Prometheus告警规则", False, f"错误: {str(e)}")
            return False

    def test_grafana_server(self) -> bool:
        """测试Grafana服务器"""
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Grafana服务器",
                    True,
                    f"状态: {data.get('database', 'unknown')}"
                )
                return True
            else:
                self.print_result("Grafana服务器", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Grafana服务器", False, f"错误: {str(e)}")
            return False

    def test_alertmanager_server(self) -> bool:
        """测试AlertManager服务器"""
        try:
            response = requests.get(f"{self.alertmanager_url}/-/healthy", timeout=5)
            passed = response.status_code == 200
            self.print_result(
                "AlertManager服务器",
                passed,
                f"状态码: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.print_result("AlertManager服务器", False, f"错误: {str(e)}")
            return False

    def test_monitoring_api(self) -> bool:
        """测试监控API端点"""
        try:
            response = requests.get(f"{self.backend_url}/monitoring/metrics", timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_metrics = all([
                    'system' in data,
                    'process' in data
                ])
                self.print_result(
                    "监控API端点",
                    has_metrics,
                    f"CPU: {data.get('system', {}).get('cpu_percent', 0)}%"
                )
                return has_metrics
            else:
                self.print_result("监控API端点", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("监控API端点", False, f"错误: {str(e)}")
            return False

    def test_logs_api(self) -> bool:
        """测试日志API"""
        try:
            response = requests.get(
                f"{self.backend_url}/monitoring/logs/recent?lines=10",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                self.print_result(
                    "日志API",
                    len(logs) >= 0,
                    f"日志行数: {len(logs)}"
                )
                return True
            else:
                self.print_result("日志API", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("日志API", False, f"错误: {str(e)}")
            return False

    def print_summary(self):
        """打印测试摘要"""
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed

        print(f"\n{GREEN}{'=' * 60}{NC}")
        print(f"{GREEN}测试摘要{NC}")
        print(f"{GREEN}{'=' * 60}{NC}")
        print(f"总测试数: {total}")
        print(f"{GREEN}通过: {passed}{NC}")
        print(f"{RED}失败: {failed}{NC}")
        print(f"成功率: {(passed/total*100):.1f}%\n")

        if failed > 0:
            print(f"{YELLOW}失败的测试:{NC}")
            for name, passed, message in self.results:
                if not passed:
                    print(f"  - {name}: {message}")
            print()

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        self.print_header("监控系统测试")

        # 测试Backend
        print(f"\n{YELLOW}=== Backend 测试 ==={NC}\n")
        self.test_backend_health()
        self.test_metrics_endpoint()
        self.test_monitoring_api()
        self.test_logs_api()

        # 测试Prometheus
        print(f"\n{YELLOW}=== Prometheus 测试 ==={NC}\n")
        self.test_prometheus_server()
        self.test_prometheus_targets()
        self.test_prometheus_rules()

        # 测试Grafana
        print(f"\n{YELLOW}=== Grafana 测试 ==={NC}\n")
        self.test_grafana_server()

        # 测试AlertManager
        print(f"\n{YELLOW}=== AlertManager 测试 ==={NC}\n")
        self.test_alertmanager_server()

        # 打印摘要
        self.print_summary()

        # 判断是否全部通过
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        return passed == total


def main():
    """主函数"""
    # 获取命令行参数
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    # 运行测试
    tester = MonitoringSystemTest(backend_url=backend_url)

    try:
        all_passed = tester.run_all_tests()
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}测试中断{NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}测试失败: {str(e)}{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
