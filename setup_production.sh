#!/bin/bash
# FieldMind 生产环境初始化脚本

set -e

echo "========================================="
echo "FieldMind 生产环境初始化"
echo "========================================="
echo ""

# 1. 检查必要的工具
echo "1. 检查必要工具..."
command -v docker >/dev/null 2>&1 || { echo "错误: 需要安装 Docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "错误: 需要安装 Docker Compose"; exit 1; }
echo "✓ Docker 和 Docker Compose 已安装"
echo ""

# 2. 生成生产环境配置
echo "2. 生成生产环境配置..."
if [ ! -f .env.production ]; then
    echo "创建 .env.production 文件..."

    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 24)
    REDIS_PASSWORD=$(openssl rand -base64 24)
    JWT_SECRET=$(openssl rand -hex 32)

    cat > .env.production << EOF
# FieldMind 生产环境配置
# 生成时间: $(date)

# ==================== 应用配置 ====================
ENVIRONMENT=production
DEBUG=false
VERSION=2.0.0
APP_NAME=FieldMind
APP_HOST=0.0.0.0
APP_PORT=8000

# ==================== 数据库配置 ====================
DATABASE_URL=postgresql://fieldmind:${DB_PASSWORD}@postgres:5432/fieldmind
DB_PASSWORD=${DB_PASSWORD}

# ==================== Redis 配置 ====================
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# ==================== 安全配置 ====================
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# ==================== AI API Keys (需要手动填写) ====================
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# ==================== 可选: Sentry 监控 ====================
SENTRY_ENABLED=false
SENTRY_DSN=

# ==================== 可选: S3 存储 ====================
S3_ENABLED=false
S3_BUCKET=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=

# ==================== Neo4j 图数据库 ====================
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=${DB_PASSWORD}

# ==================== CORS 配置 ====================
CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:8080

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
EOF

    echo "✓ .env.production 已创建"
    echo ""
    echo "⚠️  重要: 请编辑 .env.production 文件，填写以下信息:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - 如果使用自定义域名，请更新 CORS_ORIGINS"
    echo ""
else
    echo "✓ .env.production 已存在"
    echo ""
fi

# 3. 创建必要的目录
echo "3. 创建必要的目录..."
mkdir -p backend/data
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p frontend/dist
mkdir -p nginx/ssl
mkdir -p monitoring/prometheus/data
mkdir -p monitoring/grafana/data
echo "✓ 目录创建完成"
echo ""

# 4. 数据库初始化脚本
echo "4. 创建数据库初始化脚本..."
cat > backend/init_db.py << 'PYEOF'
#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有表并插入初始数据
"""
import sys
from pathlib import Path

# 添加 backend/src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.core.database import engine, Base, SessionLocal
from app.models import *
from datetime import datetime
import hashlib

def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")

    # 创建所有表
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建完成")

    # 创建默认用户
    db = SessionLocal()
    try:
        # 检查是否已有用户
        existing_user = db.query(User).filter(User.email == "admin@fieldmind.com").first()
        if not existing_user:
            print("创建默认管理员用户...")
            admin_user = User(
                username="admin",
                email="admin@fieldmind.com",
                hashed_password=hashlib.sha256("admin123".encode()).hexdigest(),
                full_name="系统管理员",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            print("✓ 默认管理员用户创建完成")
            print("  用户名: admin")
            print("  邮箱: admin@fieldmind.com")
            print("  密码: admin123")
            print("  ⚠️  请登录后立即修改密码!")
        else:
            print("✓ 管理员用户已存在")

    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n✓ 数据库初始化完成!")

if __name__ == "__main__":
    init_database()
PYEOF

chmod +x backend/init_db.py
echo "✓ 数据库初始化脚本创建完成"
echo ""

# 5. 创建 SSL 证书配置说明
echo "5. 创建 SSL 证书配置说明..."
cat > nginx/ssl/README.md << 'EOF'
# SSL 证书配置

## 本地开发（自签名证书）

生成自签名证书用于本地 HTTPS 测试:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/C=CN/ST=State/L=City/O=FieldMind/CN=localhost"
```

## 生产环境（Let's Encrypt）

使用 Certbot 获取免费的 SSL 证书:

```bash
# 安装 Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 获取证书（替换 yourdomain.com）
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 证书会自动安装到 /etc/letsencrypt/live/yourdomain.com/
# 需要在 nginx 配置中指向这些证书
```

## 证书文件

生产环境需要以下文件:
- `privkey.pem` - 私钥
- `fullchain.pem` - 完整证书链
EOF

echo "✓ SSL 配置说明创建完成"
echo ""

# 6. 创建前端构建脚本
echo "6. 创建前端构建脚本..."
cat > frontend/build.sh << 'EOF'
#!/bin/bash
# 前端构建脚本

set -e

echo "开始构建前端..."

if [ -d "web" ]; then
    cd web
    echo "安装依赖..."
    npm install
    echo "构建生产版本..."
    npm run build
    echo "✓ 前端构建完成"
    echo "输出目录: frontend/web/dist"
else
    echo "警告: frontend/web 目录不存在"
fi
EOF

chmod +x frontend/build.sh
echo "✓ 前端构建脚本创建完成"
echo ""

# 7. 创建启动脚本
echo "7. 创建启动脚本..."
cat > start.sh << 'EOF'
#!/bin/bash
# FieldMind 启动脚本

set -e

echo "========================================="
echo "启动 FieldMind"
echo "========================================="

# 检查环境配置
if [ ! -f .env.production ]; then
    echo "错误: .env.production 不存在"
    echo "请先运行: ./setup_production.sh"
    exit 1
fi

# 检查是否已初始化数据库
if [ ! -f backend/data/.db_initialized ]; then
    echo "初始化数据库..."
    docker-compose -f docker-compose.prod.yml run --rm backend python init_db.py
    touch backend/data/.db_initialized
    echo "✓ 数据库初始化完成"
fi

# 启动服务
echo "启动 Docker 服务..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "✓ FieldMind 已启动!"
echo ""
echo "访问地址:"
echo "  - 前端: http://localhost"
echo "  - API: http://localhost/api"
echo "  - API 文档: http://localhost/api/docs"
echo "  - Grafana 监控: http://localhost:3000"
echo ""
echo "查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.prod.yml down"
EOF

chmod +x start.sh
echo "✓ 启动脚本创建完成"
echo ""

# 8. 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash
# FieldMind 停止脚本

echo "停止 FieldMind 服务..."
docker-compose -f docker-compose.prod.yml down
echo "✓ 服务已停止"
EOF

chmod +x stop.sh

echo "========================================="
echo "初始化完成!"
echo "========================================="
echo ""
echo "下一步:"
echo "1. 编辑 .env.production 填写 API keys"
echo "2. (可选) 配置 SSL 证书到 nginx/ssl/"
echo "3. 运行 ./start.sh 启动服务"
echo ""
echo "文档位置:"
echo "  - 生产就绪报告: docs/PRODUCTION_READINESS_REPORT.md"
echo "  - SSL 配置说明: nginx/ssl/README.md"
echo ""
