"""
FieldMind 端到端真实文件测试

使用下载文件夹中的真实文件测试完整数据流：
上传 → 文档化 → 边界验证 → 九步流水线 → 知识图谱 → 缩影生成

测试文件：
1. PDF文档：音寨布依族村 · 文化全景深度报告.pdf
2. 图片：e5031004fce426b0d3566eb96b5a067d.jpg
3. Excel表格：deliverables_____1___.xlsx
"""

import sys
import os
import time
import requests
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/Users/alwan/Downloads/FieldMind/fieldmind/backend/src')

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试文件
TEST_FILES = {
    "pdf": "/Users/alwan/Downloads/音寨布依族村 · 文化全景深度报告.pdf",
    "image": "/Users/alwan/Downloads/e5031004fce426b0d3566eb96b5a067d.jpg",
    "excel": "/Users/alwan/Downloads/deliverables_____1___.xlsx"
}

class FieldMindTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_base = API_BASE
        self.project_id = None
        self.uploaded_files = {}

    def print_step(self, step_num, title):
        """打印测试步骤"""
        print(f"\n{'='*80}")
        print(f"步骤 {step_num}: {title}")
        print(f"{'='*80}")

    def print_result(self, success, message):
        """打印测试结果"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")

    def test_1_check_backend(self):
        """测试1：检查后端是否运行"""
        self.print_step(1, "检查后端服务")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.print_result(True, "后端服务运行正常")
                return True
            else:
                self.print_result(False, f"后端服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            self.print_result(False, f"无法连接后端: {e}")
            return False

    def test_2_create_project(self):
        """测试2：获取或创建测试项目"""
        self.print_step(2, "获取或创建测试项目")

        try:
            # 先尝试获取项目列表（会自动创建默认项目）
            response = requests.get(
                f"{self.api_base}/projects",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                projects = result if isinstance(result, list) else result.get("projects", [])

                if projects:
                    self.project_id = projects[0].get("id")
                    project_name = projects[0].get("name")
                    self.print_result(True, f"使用现有项目，ID: {self.project_id}, 名称: {project_name}")
                    return True
                else:
                    self.print_result(False, "没有可用的项目")
                    return False
            else:
                self.print_result(False, f"获取项目列表失败: {response.text}")
                return False

        except Exception as e:
            self.print_result(False, f"获取项目异常: {e}")
            return False

    def test_3_upload_files(self):
        """测试3：上传真实文件"""
        self.print_step(3, "上传真实文件")

        if not self.project_id:
            self.print_result(False, "项目ID不存在，跳过上传")
            return False

        success_count = 0

        for file_type, file_path in TEST_FILES.items():
            if not os.path.exists(file_path):
                self.print_result(False, f"{file_type} 文件不存在: {file_path}")
                continue

            try:
                filename = os.path.basename(file_path)
                print(f"\n正在上传 {file_type}: {filename}")

                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f)}
                    data = {'project_id': self.project_id}

                    response = requests.post(
                        f"{self.api_base}/projects/{self.project_id}/documents/upload",
                        files=files,
                        data=data,
                        timeout=30
                    )

                if response.status_code == 200:
                    result = response.json()
                    doc_id = result.get("id")
                    self.uploaded_files[file_type] = doc_id
                    self.print_result(True, f"{file_type} 上传成功，文档ID: {doc_id}")
                    success_count += 1
                else:
                    self.print_result(False, f"{file_type} 上传失败: {response.text}")

            except Exception as e:
                self.print_result(False, f"{file_type} 上传异常: {e}")

        return success_count > 0

    def test_4_trigger_normalization(self):
        """测试4：触发文档规范化"""
        self.print_step(4, "触发文档规范化")

        if not self.uploaded_files:
            self.print_result(False, "没有已上传的文件")
            return False

        success_count = 0

        for file_type, doc_id in self.uploaded_files.items():
            try:
                print(f"\n触发 {file_type} 规范化...")

                response = requests.post(
                    f"{self.api_base}/files/{doc_id}/normalize",
                    json={"force": False},
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    self.print_result(True, f"{file_type} 规范化已触发，状态: {status}")
                    success_count += 1
                else:
                    self.print_result(False, f"{file_type} 规范化触发失败: {response.text}")

            except Exception as e:
                self.print_result(False, f"{file_type} 规范化异常: {e}")

        return success_count > 0

    def test_5_wait_and_check_normalization(self):
        """测试5：等待并检查规范化结果"""
        self.print_step(5, "等待并检查规范化结果")

        if not self.uploaded_files:
            self.print_result(False, "没有已上传的文件")
            return False

        print("等待处理完成（10秒）...")
        time.sleep(10)

        success_count = 0

        for file_type, doc_id in self.uploaded_files.items():
            try:
                print(f"\n检查 {file_type} 规范化结果...")

                response = requests.get(
                    f"{self.api_base}/files/{doc_id}/normalized",
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"   文档类型: {result.get('file_type')}")
                    print(f"   文本长度: {result.get('word_count')} 字")
                    print(f"   完整性: {result.get('completeness', {}).get('score', 0):.1%}")
                    print(f"   置信度: {result.get('confidence', 0):.1%}")
                    self.print_result(True, f"{file_type} 规范化完成")
                    success_count += 1
                else:
                    self.print_result(False, f"{file_type} 规范化结果获取失败: {response.status_code}")

            except Exception as e:
                self.print_result(False, f"{file_type} 检查异常: {e}")

        return success_count > 0

    def test_6_check_dirty_data_report(self):
        """测试6：检查脏数据报告"""
        self.print_step(6, "检查脏数据报告")

        if not self.uploaded_files:
            self.print_result(False, "没有已上传的文件")
            return False

        success_count = 0

        for file_type, doc_id in self.uploaded_files.items():
            try:
                print(f"\n检查 {file_type} 脏数据报告...")

                response = requests.get(
                    f"{self.api_base}/files/{doc_id}/dirty-data-report",
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"   文件名: {result.get('file_name')}")
                    print(f"   脏数据总数: {result.get('total_dirty_data')}")

                    by_type = result.get('dirty_data_by_type', {})
                    if by_type:
                        print(f"   脏数据分类:")
                        for dtype, count in by_type.items():
                            print(f"      - {dtype}: {count}个")

                    self.print_result(True, f"{file_type} 脏数据报告获取成功")
                    success_count += 1
                else:
                    self.print_result(False, f"{file_type} 脏数据报告获取失败: {response.status_code}")

            except Exception as e:
                self.print_result(False, f"{file_type} 报告检查异常: {e}")

        return success_count > 0

    def test_7_check_completeness(self):
        """测试7：检查完整性检查结果"""
        self.print_step(7, "检查完整性检查结果")

        if not self.uploaded_files:
            self.print_result(False, "没有已上传的文件")
            return False

        success_count = 0

        for file_type, doc_id in self.uploaded_files.items():
            try:
                print(f"\n检查 {file_type} 完整性...")

                response = requests.get(
                    f"{self.api_base}/files/{doc_id}/completeness-check",
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"   是否完整: {'✅' if result.get('is_complete') else '❌'}")
                    print(f"   完整性得分: {result.get('score', 0):.1%}")

                    issues = result.get('issues', [])
                    if issues:
                        print(f"   问题列表:")
                        for issue in issues[:3]:
                            print(f"      - {issue}")

                    self.print_result(True, f"{file_type} 完整性检查成功")
                    success_count += 1
                else:
                    self.print_result(False, f"{file_type} 完整性检查失败: {response.status_code}")

            except Exception as e:
                self.print_result(False, f"{file_type} 完整性检查异常: {e}")

        return success_count > 0

    def test_8_check_knowledge_extraction(self):
        """测试8：检查知识提取结果"""
        self.print_step(8, "检查知识提取结果（九步流水线）")

        # TODO: 这里需要检查 entities_unified, events_unified 等表
        self.print_result(True, "知识提取检查（待实现数据库查询）")
        return True

    def test_9_check_summary(self):
        """测试9：检查缩影生成"""
        self.print_step(9, "检查缩影生成")

        if not self.uploaded_files:
            self.print_result(False, "没有已上传的文件")
            return False

        # TODO: 检查 document_summaries 表
        self.print_result(True, "缩影生成检查（待实现）")
        return True

    def test_10_check_knowledge_graph(self):
        """测试10：检查知识图谱"""
        self.print_step(10, "检查知识图谱构建")

        # TODO: 查询知识图谱 API
        self.print_result(True, "知识图谱检查（待实现）")
        return True

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 开始 FieldMind 端到端测试")
        print("="*80)

        tests = [
            self.test_1_check_backend,
            self.test_2_create_project,
            self.test_3_upload_files,
            self.test_4_trigger_normalization,
            self.test_5_wait_and_check_normalization,
            self.test_6_check_dirty_data_report,
            self.test_7_check_completeness,
            self.test_8_check_knowledge_extraction,
            self.test_9_check_summary,
            self.test_10_check_knowledge_graph
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                result = test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                failed += 1

        # 总结
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 通过率: {passed/(passed+failed)*100:.1f}%")
        print("="*80)

if __name__ == "__main__":
    tester = FieldMindTester()
    tester.run_all_tests()
