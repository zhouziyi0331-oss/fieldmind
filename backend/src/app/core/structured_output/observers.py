"""
验证观察者

用于监控和记录验证过程
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from pydantic import BaseModel, ValidationError
from app.core.logging import logger


class ValidationObserver(ABC):
    """验证观察者接口"""

    @abstractmethod
    def on_validation_start(self, model: type[BaseModel], messages: List[Dict]):
        """验证开始时调用"""
        pass

    @abstractmethod
    def on_validation_success(self, result: BaseModel):
        """验证成功时调用"""
        pass

    @abstractmethod
    def on_validation_error(self, error: ValidationError, attempt: int):
        """验证失败时调用"""
        pass


class LoggingObserver(ValidationObserver):
    """日志观察者"""

    def on_validation_start(self, model: type[BaseModel], messages: List[Dict]):
        logger.info(f"开始验证 {model.__name__}")

    def on_validation_success(self, result: BaseModel):
        logger.info(f"✅ 验证成功: {result.__class__.__name__}")

    def on_validation_error(self, error: ValidationError, attempt: int):
        error_count = len(error.errors())
        logger.warning(f"⚠️ 验证失败 (尝试 {attempt}): {error_count} 个错误")


class MetricsObserver(ValidationObserver):
    """指标观察者"""

    def __init__(self):
        self.total_attempts = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.retry_counts = []
        self.error_types = {}

    def on_validation_start(self, model: type[BaseModel], messages: List[Dict]):
        self.total_attempts += 1

    def on_validation_success(self, result: BaseModel):
        self.successful_validations += 1

    def on_validation_error(self, error: ValidationError, attempt: int):
        if attempt == 1:
            self.failed_validations += 1

        # 记录错误类型
        for err in error.errors():
            err_type = err['type']
            self.error_types[err_type] = self.error_types.get(err_type, 0) + 1

    def get_report(self) -> Dict:
        """获取统计报告"""
        success_rate = (
            self.successful_validations / self.total_attempts * 100
            if self.total_attempts > 0 else 0
        )

        return {
            "total_attempts": self.total_attempts,
            "successful_validations": self.successful_validations,
            "failed_validations": self.failed_validations,
            "success_rate": f"{success_rate:.2f}%",
            "error_types": self.error_types
        }


class DebugObserver(ValidationObserver):
    """调试观察者 - 记录详细信息"""

    def __init__(self):
        self.history = []

    def on_validation_start(self, model: type[BaseModel], messages: List[Dict]):
        self.history.append({
            "event": "start",
            "model": model.__name__,
            "message_count": len(messages)
        })

    def on_validation_success(self, result: BaseModel):
        self.history.append({
            "event": "success",
            "model": result.__class__.__name__,
            "data": result.model_dump()
        })

    def on_validation_error(self, error: ValidationError, attempt: int):
        self.history.append({
            "event": "error",
            "attempt": attempt,
            "errors": [
                {
                    "field": " -> ".join(str(x) for x in err['loc']),
                    "message": err['msg'],
                    "type": err['type']
                }
                for err in error.errors()
            ]
        })

    def get_history(self) -> List[Dict]:
        """获取完整历史"""
        return self.history
