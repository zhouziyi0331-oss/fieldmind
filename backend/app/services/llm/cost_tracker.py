"""
成本追踪器

追踪和分析 LLM 使用成本
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """使用记录"""
    timestamp: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency: float
    user_id: Optional[int] = None
    project_id: Optional[int] = None


class CostTracker:
    """
    成本追踪器

    追踪 LLM 使用情况和成本
    """

    def __init__(self, budget_limit: Optional[float] = None):
        """
        初始化成本追踪器

        Args:
            budget_limit: 预算限制（美元）
        """
        self.budget_limit = budget_limit
        self.records: List[UsageRecord] = []
        self._total_cost = 0.0
        self._total_tokens = 0

        # 按提供商统计
        self._provider_stats = defaultdict(lambda: {
            "cost": 0.0,
            "tokens": 0,
            "requests": 0
        })

        # 按用户统计
        self._user_stats = defaultdict(lambda: {
            "cost": 0.0,
            "tokens": 0,
            "requests": 0
        })

        # 按项目统计
        self._project_stats = defaultdict(lambda: {
            "cost": 0.0,
            "tokens": 0,
            "requests": 0
        })

    def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency: float,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None
    ):
        """
        记录使用情况

        Args:
            provider: 提供商名称
            model: 模型名称
            prompt_tokens: prompt tokens
            completion_tokens: completion tokens
            cost: 成本
            latency: 延迟
            user_id: 用户 ID
            project_id: 项目 ID
        """
        total_tokens = prompt_tokens + completion_tokens

        record = UsageRecord(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency=latency,
            user_id=user_id,
            project_id=project_id
        )

        self.records.append(record)

        # 更新总计
        self._total_cost += cost
        self._total_tokens += total_tokens

        # 更新提供商统计
        self._provider_stats[provider]["cost"] += cost
        self._provider_stats[provider]["tokens"] += total_tokens
        self._provider_stats[provider]["requests"] += 1

        # 更新用户统计
        if user_id:
            self._user_stats[user_id]["cost"] += cost
            self._user_stats[user_id]["tokens"] += total_tokens
            self._user_stats[user_id]["requests"] += 1

        # 更新项目统计
        if project_id:
            self._project_stats[project_id]["cost"] += cost
            self._project_stats[project_id]["tokens"] += total_tokens
            self._project_stats[project_id]["requests"] += 1

        # 检查预算
        if self.budget_limit and self._total_cost >= self.budget_limit:
            logger.warning(
                f"Budget limit reached! "
                f"Total cost: ${self._total_cost:.4f}, "
                f"Limit: ${self.budget_limit:.4f}"
            )

    def get_total_cost(self) -> float:
        """获取总成本"""
        return self._total_cost

    def get_total_tokens(self) -> int:
        """获取总 token 数"""
        return self._total_tokens

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取按提供商的统计"""
        return dict(self._provider_stats)

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """获取指定用户的统计"""
        return self._user_stats.get(user_id, {
            "cost": 0.0,
            "tokens": 0,
            "requests": 0
        })

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """获取指定项目的统计"""
        return self._project_stats.get(project_id, {
            "cost": 0.0,
            "tokens": 0,
            "requests": 0
        })

    def get_top_users(self, limit: int = 10, by: str = "cost") -> List[Dict[str, Any]]:
        """
        获取消费最多的用户

        Args:
            limit: 返回数量
            by: 排序依据 (cost/tokens/requests)

        Returns:
            用户列表
        """
        sorted_users = sorted(
            self._user_stats.items(),
            key=lambda x: x[1].get(by, 0),
            reverse=True
        )

        return [
            {
                "user_id": user_id,
                **stats
            }
            for user_id, stats in sorted_users[:limit]
        ]

    def get_top_projects(self, limit: int = 10, by: str = "cost") -> List[Dict[str, Any]]:
        """获取消费最多的项目"""
        sorted_projects = sorted(
            self._project_stats.items(),
            key=lambda x: x[1].get(by, 0),
            reverse=True
        )

        return [
            {
                "project_id": project_id,
                **stats
            }
            for project_id, stats in sorted_projects[:limit]
        ]

    def get_time_series_data(
        self,
        interval: str = "hour",
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取时间序列数据

        Args:
            interval: 时间间隔 (hour/day)
            days: 天数

        Returns:
            时间序列数据
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_records = [r for r in self.records if r.timestamp >= cutoff_time]

        # 按时间分组
        time_groups = defaultdict(lambda: {
            "cost": 0.0,
            "tokens": 0,
            "requests": 0
        })

        for record in recent_records:
            if interval == "hour":
                key = record.timestamp.strftime("%Y-%m-%d %H:00")
            else:  # day
                key = record.timestamp.strftime("%Y-%m-%d")

            time_groups[key]["cost"] += record.cost
            time_groups[key]["tokens"] += record.total_tokens
            time_groups[key]["requests"] += 1

        # 转换为列表并排序
        return sorted(
            [{"time": k, **v} for k, v in time_groups.items()],
            key=lambda x: x["time"]
        )

    def get_budget_status(self) -> Dict[str, Any]:
        """获取预算状态"""
        if not self.budget_limit:
            return {
                "has_limit": False,
                "total_cost": self._total_cost,
            }

        remaining = self.budget_limit - self._total_cost
        usage_percent = (self._total_cost / self.budget_limit) * 100

        return {
            "has_limit": True,
            "budget_limit": self.budget_limit,
            "total_cost": self._total_cost,
            "remaining": remaining,
            "usage_percent": usage_percent,
            "is_exceeded": self._total_cost >= self.budget_limit
        }

    def reset_stats(self):
        """重置所有统计"""
        self.records.clear()
        self._total_cost = 0.0
        self._total_tokens = 0
        self._provider_stats.clear()
        self._user_stats.clear()
        self._project_stats.clear()

    def export_records(self, format: str = "json") -> Any:
        """
        导出使用记录

        Args:
            format: 导出格式 (json/csv)

        Returns:
            导出的数据
        """
        if format == "json":
            return [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "provider": r.provider,
                    "model": r.model,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "cost": r.cost,
                    "latency": r.latency,
                    "user_id": r.user_id,
                    "project_id": r.project_id
                }
                for r in self.records
            ]
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "timestamp", "provider", "model",
                    "prompt_tokens", "completion_tokens", "total_tokens",
                    "cost", "latency", "user_id", "project_id"
                ]
            )
            writer.writeheader()

            for r in self.records:
                writer.writerow({
                    "timestamp": r.timestamp.isoformat(),
                    "provider": r.provider,
                    "model": r.model,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "cost": r.cost,
                    "latency": r.latency,
                    "user_id": r.user_id,
                    "project_id": r.project_id
                })

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
