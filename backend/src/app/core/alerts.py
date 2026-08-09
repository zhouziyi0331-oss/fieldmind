"""
告警系统
支持多种告警通道：Email、Webhook、钉钉、企业微信
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json

from app.core.logging import logger
from app.config import settings


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """告警通道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    SLACK = "slack"


class Alert:
    """告警对象"""

    def __init__(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.message = message
        self.level = level
        self.tags = tags or []
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.channels: Dict[AlertChannel, bool] = {
            AlertChannel.EMAIL: self._check_email_config(),
            AlertChannel.WEBHOOK: self._check_webhook_config(),
            AlertChannel.DINGTALK: self._check_dingtalk_config(),
            AlertChannel.WECHAT: self._check_wechat_config(),
        }

    def _check_email_config(self) -> bool:
        """检查Email配置"""
        return all([
            getattr(settings, 'SMTP_HOST', None),
            getattr(settings, 'SMTP_PORT', None),
            getattr(settings, 'SMTP_USER', None),
        ])

    def _check_webhook_config(self) -> bool:
        """检查Webhook配置"""
        return bool(getattr(settings, 'ALERT_WEBHOOK_URL', None))

    def _check_dingtalk_config(self) -> bool:
        """检查钉钉配置"""
        return bool(getattr(settings, 'DINGTALK_WEBHOOK_URL', None))

    def _check_wechat_config(self) -> bool:
        """检查企业微信配置"""
        return bool(getattr(settings, 'WECHAT_WEBHOOK_URL', None))

    async def send_alert(
        self,
        alert: Alert,
        channels: Optional[List[AlertChannel]] = None
    ):
        """
        发送告警

        Args:
            alert: 告警对象
            channels: 要发送的通道列表，None表示发送到所有可用通道
        """
        # 确定要发送的通道
        target_channels = channels or [
            ch for ch, enabled in self.channels.items() if enabled
        ]

        if not target_channels:
            logger.warning("没有可用的告警通道")
            return

        # 并发发送到所有通道
        tasks = []
        for channel in target_channels:
            if channel == AlertChannel.EMAIL:
                tasks.append(self._send_email(alert))
            elif channel == AlertChannel.WEBHOOK:
                tasks.append(self._send_webhook(alert))
            elif channel == AlertChannel.DINGTALK:
                tasks.append(self._send_dingtalk(alert))
            elif channel == AlertChannel.WECHAT:
                tasks.append(self._send_wechat(alert))

        # 执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 记录结果
        for channel, result in zip(target_channels, results):
            if isinstance(result, Exception):
                logger.error(f"发送告警到 {channel.value} 失败: {result}")
            else:
                logger.info(f"告警已发送到 {channel.value}")

    async def _send_email(self, alert: Alert):
        """发送Email告警"""
        smtp_host = getattr(settings, 'SMTP_HOST', '')
        smtp_port = getattr(settings, 'SMTP_PORT', 587)
        smtp_user = getattr(settings, 'SMTP_USER', '')
        smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        smtp_from = getattr(settings, 'SMTP_FROM', smtp_user)
        alert_emails = getattr(settings, 'ALERT_EMAILS', [])

        if not alert_emails:
            logger.warning("未配置告警邮箱")
            return

        # 构建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
        msg['From'] = smtp_from
        msg['To'] = ', '.join(alert_emails)

        # 邮件内容
        html = f"""
        <html>
          <head></head>
          <body>
            <h2 style="color: {'#d32f2f' if alert.level == AlertLevel.CRITICAL else '#ff9800' if alert.level == AlertLevel.ERROR else '#2196f3'};">
              {alert.title}
            </h2>
            <p><strong>级别:</strong> {alert.level.value.upper()}</p>
            <p><strong>时间:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>消息:</strong></p>
            <pre>{alert.message}</pre>
            {f"<p><strong>标签:</strong> {', '.join(alert.tags)}</p>" if alert.tags else ""}
            {f"<p><strong>元数据:</strong><pre>{json.dumps(alert.metadata, indent=2)}</pre></p>" if alert.metadata else ""}
          </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        # 发送邮件
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if getattr(settings, 'SMTP_TLS', True):
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            raise

    async def _send_webhook(self, alert: Alert):
        """发送Webhook告警"""
        webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', '')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=alert.to_dict(),
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Webhook返回状态码: {response.status}")

    async def _send_dingtalk(self, alert: Alert):
        """发送钉钉告警"""
        webhook_url = getattr(settings, 'DINGTALK_WEBHOOK_URL', '')

        # 钉钉消息格式
        color_map = {
            AlertLevel.INFO: "#2196f3",
            AlertLevel.WARNING: "#ff9800",
            AlertLevel.ERROR: "#f44336",
            AlertLevel.CRITICAL: "#d32f2f",
        }

        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": alert.title,
                "text": f"## {alert.title}\n\n"
                        f"**级别:** <font color='{color_map[alert.level]}'>{alert.level.value.upper()}</font>\n\n"
                        f"**时间:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"**消息:**\n\n{alert.message}\n\n"
                        f"{f'**标签:** {', '.join(alert.tags)}' if alert.tags else ''}"
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise Exception(f"钉钉返回状态码: {response.status}")

    async def _send_wechat(self, alert: Alert):
        """发送企业微信告警"""
        webhook_url = getattr(settings, 'WECHAT_WEBHOOK_URL', '')

        # 企业微信消息格式
        color_map = {
            AlertLevel.INFO: "info",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "warning",
            AlertLevel.CRITICAL: "warning",
        }

        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## {alert.title}\n"
                          f"> 级别: <font color='{color_map[alert.level]}'>{alert.level.value.upper()}</font>\n"
                          f"> 时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                          f"\n{alert.message}"
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise Exception(f"企业微信返回状态码: {response.status}")


# 全局告警管理器实例
alert_manager = AlertManager()


# 便捷函数
async def send_info_alert(title: str, message: str, **kwargs):
    """发送INFO级别告警"""
    alert = Alert(title, message, AlertLevel.INFO, **kwargs)
    await alert_manager.send_alert(alert)


async def send_warning_alert(title: str, message: str, **kwargs):
    """发送WARNING级别告警"""
    alert = Alert(title, message, AlertLevel.WARNING, **kwargs)
    await alert_manager.send_alert(alert)


async def send_error_alert(title: str, message: str, **kwargs):
    """发送ERROR级别告警"""
    alert = Alert(title, message, AlertLevel.ERROR, **kwargs)
    await alert_manager.send_alert(alert)


async def send_critical_alert(title: str, message: str, **kwargs):
    """发送CRITICAL级别告警"""
    alert = Alert(title, message, AlertLevel.CRITICAL, **kwargs)
    await alert_manager.send_alert(alert)


# 导出
__all__ = [
    'AlertLevel',
    'AlertChannel',
    'Alert',
    'AlertManager',
    'alert_manager',
    'send_info_alert',
    'send_warning_alert',
    'send_error_alert',
    'send_critical_alert',
]
