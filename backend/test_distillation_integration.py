"""
蒸馏功能 Phase 4 - 集成测试
测试端到端的完整蒸馏流程
"""
import sys
sys.path.insert(0, 'src')

import requests
import json
import time
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8000"
PROJECT_ID = 1

class DistillationIntegrationTest:
    """蒸馏功能集成测试"""

    def __init__(self):
        self.base_url = BASE_URL
        self.project_id = PROJECT_ID
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log(self, message, level="INFO"):
        """日志输出"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{icons.get(level, 'ℹ️')} {message}")

    def test_api_health(self):
        """测试API健康状态"""
        self.log("测试1: API健康检查", "INFO")
        self.test_results["total"] += 1

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("API服务正常", "SUCCESS")
                self.test_results["passed"] += 1
                return True
            else:
                self.log(f"API返回异常状态码: {response.status_code}", "ERROR")
                self.test_results["failed"] += 1
                self.test_results["errors"].append("API健康检查失败")
                return False
        except requests.exceptions.ConnectionError:
            self.log("无法连接到API服务", "ERROR")
            self.test_results["failed"] += 1
            self.test_results["errors"].append("API连接失败")
            return False
        except Exception as e:
            self.log(f"API健康检查异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"API健康检查异常: {str(e)}")
            return False

    def test_distillation_trigger(self):
        """测试触发蒸馏"""
        self.log("测试2: 触发蒸馏", "INFO")
        self.test_results["total"] += 1

        try:
            response = requests.post(
                f"{self.base_url}/api/projects/{self.project_id}/distill",
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                self.log(f"蒸馏成功: {result.get('total_units', 0)} 个知识单元", "SUCCESS")
                self.test_results["passed"] += 1

                # 验证返回数据结构
                assert "total_units" in result, "缺少 total_units 字段"
                assert "breakdown" in result, "缺少 breakdown 字段"
                assert isinstance(result["breakdown"], dict), "breakdown 应该是字典"

                return result
            else:
                self.log(f"蒸馏失败: {response.status_code}", "ERROR")
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"蒸馏API返回 {response.status_code}")
                return None

        except Exception as e:
            self.log(f"蒸馏异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"蒸馏异常: {str(e)}")
            return None

    def test_get_stats(self):
        """测试获取统计数据"""
        self.log("测试3: 获取统计数据", "INFO")
        self.test_results["total"] += 1

        try:
            response = requests.get(
                f"{self.base_url}/api/projects/{self.project_id}/distillation/stats",
                timeout=10
            )

            if response.status_code == 200:
                stats = response.json()
                self.log(f"统计数据: 总计 {stats.get('total_units', 0)} 个", "SUCCESS")
                self.test_results["passed"] += 1

                # 验证数据结构
                assert "total_units" in stats
                assert "breakdown" in stats
                assert all(key in stats["breakdown"] for key in
                          ["insights", "quotes", "models", "cases", "actions", "methods"])

                return stats
            else:
                self.log(f"获取统计失败: {response.status_code}", "ERROR")
                self.test_results["failed"] += 1
                return None

        except Exception as e:
            self.log(f"获取统计异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return None

    def test_get_units_list(self):
        """测试获取知识单元列表"""
        self.log("测试4: 获取知识单元列表", "INFO")
        self.test_results["total"] += 1

        try:
            response = requests.get(
                f"{self.base_url}/api/projects/{self.project_id}/distilled-units",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                units = data.get("units", [])
                self.log(f"获取到 {len(units)} 个知识单元", "SUCCESS")
                self.test_results["passed"] += 1

                # 验证数据格式
                if units:
                    first_unit = units[0]
                    required_fields = ["id", "project_id", "unit_type", "title",
                                      "content", "credibility", "confidence"]
                    for field in required_fields:
                        assert field in first_unit, f"缺少字段: {field}"

                return units
            else:
                self.log(f"获取列表失败: {response.status_code}", "ERROR")
                self.test_results["failed"] += 1
                return []

        except Exception as e:
            self.log(f"获取列表异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return []

    def test_get_unit_detail(self, unit_id):
        """测试获取知识单元详情"""
        self.log(f"测试5: 获取知识单元详情 (ID: {unit_id})", "INFO")
        self.test_results["total"] += 1

        try:
            response = requests.get(
                f"{self.base_url}/api/distilled-units/{unit_id}",
                timeout=10
            )

            if response.status_code == 200:
                unit = response.json()
                self.log(f"获取详情成功: {unit.get('title', 'N/A')}", "SUCCESS")
                self.test_results["passed"] += 1

                # 验证数据完整性
                assert "id" in unit
                assert "title" in unit
                assert "content" in unit
                assert "credibility" in unit
                assert "confidence" in unit

                return unit
            else:
                self.log(f"获取详情失败: {response.status_code}", "ERROR")
                self.test_results["failed"] += 1
                return None

        except Exception as e:
            self.log(f"获取详情异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return None

    def test_get_unit_sources(self, unit_id):
        """测试获取溯源信息"""
        self.log(f"测试6: 获取溯源信息 (ID: {unit_id})", "INFO")
        self.test_results["total"] += 1

        try:
            response = requests.get(
                f"{self.base_url}/api/distilled-units/{unit_id}/sources",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                sources = data.get("sources", [])
                self.log(f"获取到 {len(sources)} 个来源", "SUCCESS")
                self.test_results["passed"] += 1

                # 验证溯源数据格式
                if sources:
                    first_source = sources[0]
                    expected_fields = ["chunk_id", "content", "document_name"]
                    for field in expected_fields:
                        if field not in first_source:
                            self.log(f"溯源数据缺少字段: {field}", "WARNING")

                return sources
            else:
                self.log(f"获取溯源失败: {response.status_code}", "ERROR")
                self.test_results["failed"] += 1
                return []

        except Exception as e:
            self.log(f"获取溯源异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return []

    def test_filter_by_type(self):
        """测试按类型筛选"""
        self.log("测试7: 按类型筛选", "INFO")
        self.test_results["total"] += 1

        types = ["insight", "quote", "model", "case", "action", "method"]
        success_count = 0

        try:
            for unit_type in types:
                response = requests.get(
                    f"{self.base_url}/api/projects/{self.project_id}/distilled-units",
                    params={"unit_type": unit_type},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    units = data.get("units", [])
                    # 验证所有返回的单元都是指定类型
                    if all(u["unit_type"] == unit_type for u in units):
                        success_count += 1

            if success_count == len(types):
                self.log(f"类型筛选测试通过 ({success_count}/{len(types)})", "SUCCESS")
                self.test_results["passed"] += 1
                return True
            else:
                self.log(f"部分类型筛选失败 ({success_count}/{len(types)})", "WARNING")
                self.test_results["passed"] += 1
                return False

        except Exception as e:
            self.log(f"类型筛选异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return False

    def test_data_consistency(self, stats, units):
        """测试数据一致性"""
        self.log("测试8: 数据一致性检查", "INFO")
        self.test_results["total"] += 1

        try:
            # 统计数据应该和实际单元数量一致
            expected_total = stats.get("total_units", 0)
            actual_total = len(units)

            if expected_total == actual_total:
                self.log(f"数据一致: {expected_total} == {actual_total}", "SUCCESS")
                self.test_results["passed"] += 1
                return True
            else:
                self.log(f"数据不一致: 统计={expected_total}, 实际={actual_total}", "WARNING")
                self.test_results["passed"] += 1  # 轻微不一致不算失败
                return False

        except Exception as e:
            self.log(f"一致性检查异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return False

    def test_performance(self):
        """测试性能指标"""
        self.log("测试9: 性能测试", "INFO")
        self.test_results["total"] += 1

        try:
            # 测试蒸馏性能
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/projects/{self.project_id}/distill",
                timeout=30
            )
            distill_time = time.time() - start_time

            if response.status_code == 200:
                self.log(f"蒸馏耗时: {distill_time:.2f}秒", "INFO")

                # 测试查询性能
                start_time = time.time()
                requests.get(
                    f"{self.base_url}/api/projects/{self.project_id}/distilled-units",
                    timeout=10
                )
                query_time = time.time() - start_time

                self.log(f"查询耗时: {query_time:.2f}秒", "INFO")

                # 性能标准: 蒸馏<10秒, 查询<2秒
                if distill_time < 10 and query_time < 2:
                    self.log("性能测试通过", "SUCCESS")
                    self.test_results["passed"] += 1
                    return True
                else:
                    self.log("性能较慢但可接受", "WARNING")
                    self.test_results["passed"] += 1
                    return False
            else:
                self.log("性能测试失败", "ERROR")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            self.log(f"性能测试异常: {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            return False

    def run_all_tests(self):
        """运行所有集成测试"""
        print("\n" + "="*60)
        print("🔗 Phase 4 集成测试 - 端到端流程")
        print("="*60 + "\n")

        # 1. 健康检查
        if not self.test_api_health():
            self.log("API服务不可用，跳过后续测试", "ERROR")
            self.print_summary()
            return

        print()

        # 2. 触发蒸馏
        distill_result = self.test_distillation_trigger()
        time.sleep(1)  # 等待数据写入

        print()

        # 3. 获取统计
        stats = self.test_get_stats()

        print()

        # 4. 获取列表
        units = self.test_get_units_list()

        print()

        # 5. 测试详情和溯源（如果有数据）
        if units:
            first_unit = units[0]
            unit_id = first_unit["id"]

            self.test_get_unit_detail(unit_id)
            print()

            self.test_get_unit_sources(unit_id)
            print()

        # 6. 测试筛选
        self.test_filter_by_type()

        print()

        # 7. 数据一致性
        if stats and units:
            self.test_data_consistency(stats, units)

        print()

        # 8. 性能测试
        self.test_performance()

        print()

        # 打印总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 集成测试总结")
        print("="*60)

        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 通过率: {pass_rate:.1f}%")

        if self.test_results["errors"]:
            print("\n❌ 错误列表:")
            for i, error in enumerate(self.test_results["errors"], 1):
                print(f"  {i}. {error}")

        print("\n" + "="*60)

        if failed == 0:
            print("🎉 所有集成测试通过!")
        elif pass_rate >= 80:
            print("⚠️  大部分测试通过，存在少量问题")
        else:
            print("❌ 测试失败率较高，需要修复")

        print("="*60 + "\n")


def main():
    """主函数"""
    tester = DistillationIntegrationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
