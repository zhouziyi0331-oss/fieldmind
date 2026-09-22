#!/usr/bin/env python3
"""
安全配置检查脚本
用于部署前验证配置的安全性
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple


class SecurityChecker:
    """安全配置检查器"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.issues: List[Tuple[str, str, str]] = []  # (level, category, message)

    def check_all(self) -> bool:
        """执行所有检查"""
        if not self.env_file.exists():
            print(f"❌ 错误: {self.env_file} 文件不存在")
            return False

        print(f"🔍 检查配置文件: {self.env_file}")
        print("=" * 60)

        self.check_secret_key()
        self.check_database_passwords()
        self.check_debug_mode()
        self.check_api_keys()
        self.check_cors_origins()

        return self.print_results()

    def check_secret_key(self):
        """检查 SECRET_KEY"""
        secret_key = self._get_env_value('SECRET_KEY')

        if not secret_key:
            self.add_error("SECRET_KEY", "SECRET_KEY 未设置")
            return

        # 检查弱密钥
        weak_patterns = [
            'your-secret',
            'change-this',
            'changeme',
            'dev-only',
            'test-key',
            'example',
            '12345',
            'change-in-production'
        ]

        for pattern in weak_patterns:
            if pattern in secret_key.lower():
                self.add_error("SECRET_KEY", f"使用了弱密钥模式 '{pattern}'")
                return

        # 检查长度
        if len(secret_key) < 32:
            self.add_error("SECRET_KEY", f"SECRET_KEY 长度不足 (当前: {len(secret_key)}, 最小: 32)")
        elif len(secret_key) < 64:
            self.add_warning("SECRET_KEY", f"SECRET_KEY 长度建议至少64字符 (当前: {len(secret_key)})")
        else:
            self.add_success("SECRET_KEY", f"长度: {len(secret_key)} 字符")

    def check_database_passwords(self):
        """检查数据库密码"""
        passwords = {
            'POSTGRES_PASSWORD': self._get_env_value('POSTGRES_PASSWORD'),
            'NEO4J_PASSWORD': self._get_env_value('NEO4J_PASSWORD'),
            'REDIS_PASSWORD': self._get_env_value('REDIS_PASSWORD'),
        }

        weak_passwords = [
            'password', 'your_password', 'your-password',
            '123456', 'admin', 'root', 'postgres', 'neo4j', 'redis'
        ]

        for name, password in passwords.items():
            if not password:
                self.add_warning(name, f"{name} 未设置")
                continue

            if password.lower() in weak_passwords:
                self.add_error(name, f"使用了弱密码")
            elif len(password) < 12:
                self.add_warning(name, f"密码长度过短 (当前: {len(password)}, 建议: ≥16)")
            else:
                self.add_success(name, f"已设置 (长度: {len(password)})")

    def check_debug_mode(self):
        """检查调试模式"""
        debug = self._get_env_value('DEBUG')
        environment = self._get_env_value('ENVIRONMENT', 'development')

        if debug and debug.lower() in ['true', '1', 'yes']:
            if environment.lower() == 'production':
                self.add_error("DEBUG", "生产环境不能开启 DEBUG 模式")
            else:
                self.add_info("DEBUG", "开发环境已开启 DEBUG 模式")
        else:
            self.add_success("DEBUG", "DEBUG 模式已关闭")

    def check_api_keys(self):
        """检查 API 密钥"""
        api_keys = {
            'OPENAI_API_KEY': self._get_env_value('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': self._get_env_value('ANTHROPIC_API_KEY'),
        }

        placeholder_patterns = ['your-', 'sk-your', 'sk-ant-your']

        for name, key in api_keys.items():
            if not key:
                self.add_warning(name, f"{name} 未设置")
                continue

            is_placeholder = any(pattern in key.lower() for pattern in placeholder_patterns)
            if is_placeholder:
                self.add_warning(name, "使用了占位符，需要配置真实 API 密钥")
            else:
                # 简单验证格式
                if name == 'OPENAI_API_KEY' and key.startswith('sk-'):
                    self.add_success(name, "已配置")
                elif name == 'ANTHROPIC_API_KEY' and key.startswith('sk-ant-'):
                    self.add_success(name, "已配置")
                else:
                    self.add_warning(name, "格式可能不正确")

    def check_cors_origins(self):
        """检查 CORS 配置"""
        cors_origins = self._get_env_value('CORS_ORIGINS')

        if not cors_origins:
            self.add_info("CORS_ORIGINS", "未设置，将使用默认值")
            return

        environment = self._get_env_value('ENVIRONMENT', 'development')

        # 检查是否允许所有域名
        if '*' in cors_origins or 'http://*' in cors_origins:
            if environment.lower() == 'production':
                self.add_error("CORS_ORIGINS", "生产环境不应允许所有域名")
            else:
                self.add_warning("CORS_ORIGINS", "允许所有域名，仅限开发环境使用")
        else:
            self.add_success("CORS_ORIGINS", "已配置特定域名")

    def _get_env_value(self, key: str, default: str = None) -> str:
        """从 .env 文件读取配置值"""
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() == key:
                            # 移除引号
                            v = v.strip().strip('"').strip("'")
                            return v
        except Exception:
            pass
        return default

    def add_error(self, category: str, message: str):
        """添加错误"""
        self.issues.append(("ERROR", category, message))

    def add_warning(self, category: str, message: str):
        """添加警告"""
        self.issues.append(("WARNING", category, message))

    def add_info(self, category: str, message: str):
        """添加信息"""
        self.issues.append(("INFO", category, message))

    def add_success(self, category: str, message: str):
        """添加成功"""
        self.issues.append(("SUCCESS", category, message))

    def print_results(self) -> bool:
        """打印检查结果"""
        errors = [i for i in self.issues if i[0] == "ERROR"]
        warnings = [i for i in self.issues if i[0] == "WARNING"]
        infos = [i for i in self.issues if i[0] == "INFO"]
        successes = [i for i in self.issues if i[0] == "SUCCESS"]

        print("\n" + "=" * 60)
        print("检查结果")
        print("=" * 60)

        # 打印错误
        if errors:
            print(f"\n❌ 错误 ({len(errors)}):")
            for _, category, message in errors:
                print(f"   [{category}] {message}")

        # 打印警告
        if warnings:
            print(f"\n⚠️  警告 ({len(warnings)}):")
            for _, category, message in warnings:
                print(f"   [{category}] {message}")

        # 打印成功
        if successes:
            print(f"\n✅ 通过 ({len(successes)}):")
            for _, category, message in successes:
                print(f"   [{category}] {message}")

        # 打印信息
        if infos:
            print(f"\nℹ️  信息 ({len(infos)}):")
            for _, category, message in infos:
                print(f"   [{category}] {message}")

        # 总结
        print("\n" + "=" * 60)
        if errors:
            print("❌ 检查失败: 发现安全问题，必须修复后才能部署！")
            return False
        elif warnings:
            print("⚠️  检查通过但有警告: 建议修复警告项后再部署")
            return True
        else:
            print("✅ 所有检查通过: 配置符合安全要求")
            return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="FieldMind 安全配置检查")
    parser.add_argument(
        '--env-file',
        default='.env',
        help='环境配置文件路径 (默认: .env)'
    )
    args = parser.parse_args()

    checker = SecurityChecker(args.env_file)
    success = checker.check_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消。")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
