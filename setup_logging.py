#!/usr/bin/env python3
"""
日志系统配置工具
用于配置和验证日志系统
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging_config import setup_logging, get_logger, audit_logger


def main():
    """主函数"""
    print("=" * 60)
    print("📋 日志系统配置工具")
    print("=" * 60)
    print()

    # 配置日志系统
    print("✅ 正在配置日志系统...")
    setup_logging(
        log_level="INFO",
        log_dir="logs",
        enable_console=True,
        enable_json=True
    )
    print("✅ 日志系统配置完成")
    print()

    # 测试日志记录
    print("🧪 测试日志功能...")
    logger = get_logger("test")

    print("  - 测试INFO日志...")
    logger.info("这是一条INFO日志", extra={"test_id": "001", "component": "setup"})

    print("  - 测试WARNING日志...")
    logger.warning("这是一条WARNING日志", extra={"test_id": "002"})

    print("  - 测试ERROR日志...")
    try:
        raise ValueError("测试异常")
    except Exception as e:
        logger.error("捕获到测试异常", exc_info=e, extra={"test_id": "003"})

    print("  - 测试审计日志...")
    audit_logger.log_action(
        action="test_action",
        user_id="test_user_001",
        resource_type="document",
        resource_id="doc_123",
        ip_address="127.0.0.1",
        details={"operation": "create", "size": 1024},
        status="success"
    )

    print()
    print("✅ 日志功能测试完成")
    print()

    # 检查日志文件
    print("📁 检查日志文件...")
    log_files = [
        "logs/app.log",
        "logs/error.log",
        "logs/audit.log"
    ]

    for log_file in log_files:
        if Path(log_file).exists():
            size = Path(log_file).stat().st_size
            print(f"  ✅ {log_file} - {size} bytes")
        else:
            print(f"  ❌ {log_file} - 不存在")

    print()
    print("=" * 60)
    print("✅ 日志系统配置完成！")
    print("=" * 60)
    print()
    print("📚 日志文件位置:")
    print("  - 应用日志: logs/app.log")
    print("  - 错误日志: logs/error.log")
    print("  - 审计日志: logs/audit.log")
    print()
    print("💡 使用方法:")
    print("  from app.core.logging_config import get_logger")
    print("  logger = get_logger(__name__)")
    print("  logger.info('消息', extra={'key': 'value'})")
    print()


if __name__ == "__main__":
    main()
