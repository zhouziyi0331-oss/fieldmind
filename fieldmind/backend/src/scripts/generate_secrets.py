#!/usr/bin/env python3
"""
安全密钥生成脚本
用于生成生产环境所需的密码学安全的随机密钥和密码
"""
import secrets
import string
import sys


def generate_secret_key(length_bytes: int = 48) -> str:
    """
    生成密码学安全的 SECRET_KEY

    Args:
        length_bytes: 字节长度（默认48字节 = 64字符 base64）

    Returns:
        URL-safe base64 编码的随机字符串
    """
    return secrets.token_urlsafe(length_bytes)


def generate_password(length: int = 20, use_symbols: bool = True) -> str:
    """
    生成强随机密码

    Args:
        length: 密码长度
        use_symbols: 是否包含特殊字符

    Returns:
        随机密码字符串
    """
    alphabet = string.ascii_letters + string.digits
    if use_symbols:
        # 使用安全的特殊字符（避免shell转义问题）
        alphabet += '!@#$%^&*'

    # 确保至少包含一个大写、小写、数字
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]

    if use_symbols:
        password.append(secrets.choice('!@#$%^&*'))

    # 填充剩余字符
    password.extend(secrets.choice(alphabet) for _ in range(length - len(password)))

    # 打乱顺序
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def generate_api_key(prefix: str = "sk", length: int = 32) -> str:
    """
    生成API密钥格式的字符串

    Args:
        prefix: 前缀（如 sk, pk）
        length: 随机部分长度

    Returns:
        API密钥格式字符串
    """
    random_part = secrets.token_hex(length)
    return f"{prefix}-{random_part}"


def print_section(title: str):
    """打印分隔标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main():
    """主函数"""
    print_section("FieldMind 安全密钥生成器")
    print("\n⚠️  安全提示:")
    print("  1. 这些密钥仅显示一次，请妥善保存")
    print("  2. 将密钥添加到 .env 文件中")
    print("  3. 永远不要将 .env 文件提交到 Git")
    print("  4. 定期轮换生产环境密钥")

    # 1. JWT Secret Key
    print_section("JWT Secret Key (用于 token 签名)")
    secret_key = generate_secret_key(48)
    print(f"SECRET_KEY={secret_key}")
    print(f"长度: {len(secret_key)} 字符 ✅")

    # 2. 数据库密码
    print_section("数据库密码")
    postgres_password = generate_password(24)
    neo4j_password = generate_password(24)
    redis_password = generate_password(20)

    print(f"POSTGRES_PASSWORD={postgres_password}")
    print(f"NEO4J_PASSWORD={neo4j_password}")
    print(f"REDIS_PASSWORD={redis_password}")

    # 3. 其他密钥
    print_section("其他安全密钥")
    encryption_key = generate_secret_key(32)
    webhook_secret = generate_secret_key(24)

    print(f"ENCRYPTION_KEY={encryption_key}  # 可用于加密敏感数据")
    print(f"WEBHOOK_SECRET={webhook_secret}  # 可用于验证 Webhook 请求")

    # 4. 完整 .env 配置示例
    print_section("完整 .env 配置（复制到你的 .env 文件）")
    print(f"""
# ============================================
# 安全配置 (生成时间: {secrets.token_hex(4)})
# ============================================
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# 数据库密码
# ============================================
POSTGRES_PASSWORD={postgres_password}
NEO4J_PASSWORD={neo4j_password}
REDIS_PASSWORD={redis_password}

# ============================================
# API 密钥（需要从服务商获取）
# ============================================
# OPENAI_API_KEY=sk-...  # 从 https://platform.openai.com/api-keys 获取
# ANTHROPIC_API_KEY=sk-ant-...  # 从 https://console.anthropic.com/ 获取
""")

    # 5. 安全检查清单
    print_section("部署前安全检查清单")
    print("""
□ SECRET_KEY 已设置且长度 >= 64 字符
□ 数据库密码已更改（不含 'your', 'password', '123'）
□ 生产环境 DEBUG=false
□ CORS_ORIGINS 仅包含实际域名
□ OpenAI/Anthropic API 密钥已配置
□ .env 文件已加入 .gitignore
□ 敏感日志已过滤
□ HTTPS 已启用（生产环境）
    """)

    print_section("完成")
    print("\n密钥已生成！请复制上述配置到你的 .env 文件。\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消。")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
