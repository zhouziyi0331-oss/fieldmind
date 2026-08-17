#!/usr/bin/env python3
"""
FieldMind 部署验证测试
测试所有部署配置是否正确
"""

import requests
import time
import sys
from typing import Dict, List, Tuple

# 颜色输出
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color


class DeploymentValidator:
    """部署验证器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
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

    def test_basic_connectivity(self) -> bool:
        """测试基础连接"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "基础连接",
                    True,
                    f"API版本: {data.get('version', 'unknown')}"
                )
                return True
            else:
                self.print_result(
                    "基础连接",
                    False,
                    f"状态码: {response.status_code}"
                )
                return False
        except Exception as e:
            self.print_result("基础连接", False, f"错误: {str(e)}")
            return False

    def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                services = data.get("services", {})
                response_time = data.get("response_time_ms", 0)

                # 检查服务状态
                all_ok = True
                service_status = []
                for service, state in services.items():
                    if state != "ok" and state != "not_configured":
                        all_ok = False
                    service_status.append(f"{service}: {state}")

                self.print_result(
                    "健康检查",
                    status == "healthy",
                    f"状态: {status}, 响应时间: {response_time}ms\n      " +
                    "\n      ".join(service_status)
                )
                return status == "healthy"
            else:
                self.print_result(
                    "健康检查",
                    False,
                    f"状态码: {response.status_code}"
                )
                return False
        except Exception as e:
            self.print_result("健康检查", False, f"错误: {str(e)}")
            return False

    def test_api_docs(self) -> bool:
        """测试API文档"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            passed = response.status_code == 200
            self.print_result(
                "API文档可访问",
                passed,
                f"状态码: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.print_result("API文档可访问", False, f"错误: {str(e)}")
            return False

    def test_openapi_schema(self) -> bool:
        """测试OpenAPI Schema"""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                endpoints = len(data.get("paths", {}))
                self.print_result(
                    "OpenAPI Schema",
                    True,
                    f"API端点数量: {endpoints}"
                )
                return True
            else:
                self.print_result(
                    "OpenAPI Schema",
                    False,
                    f"状态码: {response.status_code}"
                )
                return False
        except Exception as e:
            self.print_result("OpenAPI Schema", False, f"错误: {str(e)}")
            return False

    def test_cors_headers(self) -> bool:
        """测试CORS配置"""
        try:
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
            response = requests.options(
                f"{self.base_url}/",
                headers=headers,
                timeout=10
            )

            has_cors = "access-control-allow-origin" in response.headers
            self.print_result(
                "CORS配置",
                has_cors,
                f"允许源: {response.headers.get('access-control-allow-origin', 'N/A')}"
            )
            return has_cors
        except Exception as e:
            self.print_result("CORS配置", False, f"错误: {str(e)}")
            return False

    def test_gzip_compression(self) -> bool:
        """测试Gzip压缩"""
        try:
            headers = {"Accept-Encoding": "gzip"}
            response = requests.get(
                f"{self.base_url}/openapi.json",
                headers=headers,
                timeout=10
            )

            has_gzip = response.headers.get("content-encoding") == "gzip"
            self.print_result(
                "Gzip压缩",
                has_gzip,
                f"Content-Encoding: {response.headers.get('content-encoding', 'none')}"
            )
            return has_gzip
        except Exception as e:
            self.print_result("Gzip压缩", False, f"错误: {str(e)}")
            return False

    def test_response_time(self) -> bool:
        """测试响应时间"""
        try:
            times = []
            for _ in range(5):
                start = time.time()
                requests.get(f"{self.base_url}/health", timeout=10)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                time.sleep(0.1)

            avg_time = sum(times) / len(times)
            passed = avg_time < 500  # 小于500ms
            self.print_result(
                "响应时间",
                passed,
                f"平均: {avg_time:.2f}ms (5次请求)"
            )
            return passed
        except Exception as e:
            self.print_result("响应时间", False, f"错误: {str(e)}")
            return False

    def test_database_connection(self) -> bool:
        """测试数据库连接（通过健康检查）"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("services", {}).get("database", "error")
                passed = db_status == "ok"
                self.print_result(
                    "数据库连接",
                    passed,
                    f"状态: {db_status}"
                )
                return passed
            else:
                self.print_result("数据库连接", False, "无法获取状态")
                return False
        except Exception as e:
            self.print_result("数据库连接", False, f"错误: {str(e)}")
            return False

    def test_api_endpoints(self) -> bool:
        """测试关键API端点"""
        endpoints = [
            ("/api/projects", "项目API"),
            ("/api/chat", "对话API"),
            ("/api/documents", "文档API"),
        ]

        all_passed = True
        for path, name in endpoints:
            try:
                # 不提供认证，预期401或200
                response = requests.get(
                    f"{self.base_url}{path}",
                    timeout=10
                )
                # 401表示端点存在但需要认证，200表示公开端点
                passed = response.status_code in [200, 401, 404, 422]
                self.print_result(
                    f"API端点 - {name}",
                    passed,
                    f"状态码: {response.status_code}"
                )
                if not passed:
                    all_passed = False
            except Exception as e:
                self.print_result(f"API端点 - {name}", False, f"错误: {str(e)}")
                all_passed = False

        return all_passed

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
        self.print_header("FieldMind 部署验证测试")

        print(f"测试目标: {self.base_url}\n")

        # 运行所有测试
        tests = [
            ("基础功能", [
                self.test_basic_connectivity,
                self.test_health_check,
                self.test_api_docs,
                self.test_openapi_schema,
            ]),
            ("性能和配置", [
                self.test_cors_headers,
                self.test_gzip_compression,
                self.test_response_time,
            ]),
            ("数据库和API", [
                self.test_database_connection,
                self.test_api_endpoints,
            ])
        ]

        for category, category_tests in tests:
            print(f"\n{YELLOW}=== {category} ==={NC}\n")
            for test_func in category_tests:
                test_func()
                time.sleep(0.1)  # 避免请求过快

        # 打印摘要
        self.print_summary()

        # 判断是否全部通过
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        return passed == total


def main():
    """主函数"""
    # 获取命令行参数
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    # 运行验证
    validator = DeploymentValidator(base_url)

    try:
        all_passed = validator.run_all_tests()

        # 退出码
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}测试中断{NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}测试失败: {str(e)}{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
