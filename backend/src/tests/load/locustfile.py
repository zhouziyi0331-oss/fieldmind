"""
Locust 压力测试 - FieldMind 系统
测试后端 API 在高并发下的性能表现
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import json
import time


class FieldMindUser(HttpUser):
    """FieldMind 用户行为模拟"""

    # 请求间隔时间（秒）
    wait_time = between(1, 3)

    def on_start(self):
        """用户启动时执行：登录"""
        # 尝试登录
        try:
            response = self.client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "test123"
            }, catch_response=True)

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
            else:
                # 登录失败，使用空 token 继续测试其他端点
                self.token = None
                self.headers = {}
                response.failure("Login failed")
        except Exception as e:
            self.token = None
            self.headers = {}

    @task(5)
    def health_check(self):
        """健康检查端点（最频繁）"""
        self.client.get("/health/live", name="/health/live")

    @task(3)
    def metrics(self):
        """获取 Prometheus 指标"""
        self.client.get("/metrics", name="/metrics")

    @task(2)
    def full_health_check(self):
        """完整健康检查"""
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') in ['healthy', 'degraded']:
                        response.success()
                    else:
                        response.failure(f"Unhealthy: {data.get('status')}")
                except Exception as e:
                    response.failure(f"Parse error: {e}")

    @task(1)
    def readiness_check(self):
        """就绪检查"""
        self.client.get("/health/ready", name="/health/ready")


class FieldMindAuthUser(HttpUser):
    """需要认证的 FieldMind 用户"""

    wait_time = between(2, 5)

    def on_start(self):
        """登录并获取 token"""
        try:
            response = self.client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "test123"
            })

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                self.token = None
                self.headers = {}
        except:
            self.token = None
            self.headers = {}

    @task(3)
    def list_projects(self):
        """查询项目列表"""
        if not self.token:
            return

        self.client.get(
            "/api/v1/projects",
            headers=self.headers,
            name="/api/v1/projects"
        )

    @task(2)
    def get_documents(self):
        """查询文档列表"""
        if not self.token:
            return

        project_id = random.randint(1, 10)
        self.client.get(
            f"/api/v1/projects/{project_id}/documents",
            headers=self.headers,
            name="/api/v1/projects/[id]/documents"
        )

    @task(1)
    def search(self):
        """搜索功能"""
        if not self.token:
            return

        keywords = ["测试", "田野调查", "数据", "分析"]
        keyword = random.choice(keywords)

        self.client.post(
            "/api/v1/search/semantic",
            headers=self.headers,
            json={"query": keyword, "limit": 10},
            name="/api/v1/search/semantic"
        )


# 测试事件监听
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时"""
    print("\n" + "=" * 80)
    print("🚀 FieldMind 压力测试开始")
    print("=" * 80)
    print(f"目标主机: {environment.host}")
    print(f"测试模式: {'分布式' if isinstance(environment.runner, MasterRunner) else '单机'}")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时"""
    print("\n" + "=" * 80)
    print("✅ FieldMind 压力测试完成")
    print("=" * 80)

    # 打印统计
    stats = environment.stats
    print(f"\n📊 测试统计:")
    print(f"  总请求数: {stats.total.num_requests}")
    print(f"  失败数: {stats.total.num_failures}")
    print(f"  失败率: {stats.total.fail_ratio:.2%}")
    print(f"  平均响应时间: {stats.total.avg_response_time:.2f}ms")
    print(f"  最大响应时间: {stats.total.max_response_time:.2f}ms")
    print(f"  RPS: {stats.total.total_rps:.2f}")

    print("\n" + "=" * 80 + "\n")
