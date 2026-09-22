# FieldMind MVP 部署指南

## 📋 部署前检查清单

### 1. 环境要求

**后端环境：**
- Python 3.11+
- PostgreSQL 14+ 或 SQLite 3.35+
- Redis 6.0+ (可选，用于缓存)
- Neo4j 4.4+ (可选，用于知识图谱)

**前端环境：**
- Node.js 18+
- npm 9+ 或 yarn 1.22+

**系统资源：**
- CPU: 4核心以上
- 内存: 8GB 以上
- 磁盘: 20GB 可用空间

### 2. 依赖服务

- OpenAI API Key (GPT-4 推荐)
- 文件存储 (本地或 S3)
- SMTP 邮件服务 (可选)

---

## 🚀 快速部署 (本地测试环境)

### 步骤 1: 克隆代码并安装依赖

```bash
# 克隆代码 (如果还没有)
cd /path/to/FieldMind

# 安装后端依赖
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend/web
npm install
```

### 步骤 2: 配置环境变量

创建后端环境配置文件：

```bash
cd ../../backend
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./fieldmind_dev.db  # 或使用 PostgreSQL

# AI 服务
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# JWT 密钥
SECRET_KEY=your-secure-random-secret-key-here

# 应用配置
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

创建前端环境配置：

```bash
cd ../frontend/web
cp .env.example .env
```

编辑 `frontend/web/.env`：

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### 步骤 3: 初始化数据库

```bash
cd ../../backend

# 运行数据库迁移
python3 migrations/add_collaboration_tables_v2.py upgrade

# (可选) 使用 Alembic 运行其他迁移
# cd src && alembic upgrade head
```

### 步骤 4: 启动服务

**终端 1 - 启动后端：**

```bash
cd backend
source venv/bin/activate
cd src
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 - 启动前端：**

```bash
cd frontend/web
npm run dev
```

### 步骤 5: 验证部署

1. 访问前端：http://localhost:5173
2. 访问 API 文档：http://localhost:8000/docs
3. 检查健康状态：http://localhost:8000/health

---

## 🏭 生产环境部署

### 方案 1: Docker Compose 部署 (推荐)

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fieldmind
      POSTGRES_USER: fieldmind
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  # FieldMind 后端
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://fieldmind:${DB_PASSWORD}@postgres:5432/fieldmind
      REDIS_HOST: redis
      REDIS_PORT: 6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      DEBUG: false
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # FieldMind 前端
  frontend:
    build:
      context: ./frontend/web
      dockerfile: Dockerfile
    environment:
      VITE_API_BASE_URL: http://backend:8000
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

**后端 Dockerfile：**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 运行迁移和启动
CMD ["sh", "-c", "cd src && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

**前端 Dockerfile：**

```dockerfile
# frontend/web/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Nginx 配置 (frontend/web/nginx.conf)：**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**启动部署：**

```bash
# 创建 .env 文件
cat > .env << EOF
DB_PASSWORD=your-secure-db-password
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secure-secret-key
EOF

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

### 方案 2: 传统部署 (Systemd)

**1. 后端部署为系统服务：**

创建 `/etc/systemd/system/fieldmind-backend.service`：

```ini
[Unit]
Description=FieldMind Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=fieldmind
WorkingDirectory=/opt/fieldmind/backend/src
Environment="PATH=/opt/fieldmind/backend/venv/bin"
ExecStart=/opt/fieldmind/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable fieldmind-backend
sudo systemctl start fieldmind-backend
sudo systemctl status fieldmind-backend
```

**2. 前端部署到 Nginx：**

```bash
# 构建前端
cd frontend/web
npm run build

# 复制到 Nginx 目录
sudo cp -r dist/* /var/www/fieldmind/

# 配置 Nginx
sudo nano /etc/nginx/sites-available/fieldmind
```

Nginx 配置：

```nginx
server {
    listen 80;
    server_name fieldmind.yourdomain.com;

    root /var/www/fieldmind;
    index index.html;

    # 启用 gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/fieldmind /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 SSL/HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书并自动配置 Nginx
sudo certbot --nginx -d fieldmind.yourdomain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 📊 监控与日志

### 1. 应用日志

后端日志位置：`/opt/fieldmind/backend/logs/app.log`

查看实时日志：

```bash
# Systemd 服务日志
sudo journalctl -u fieldmind-backend -f

# Docker 日志
docker-compose logs -f backend
```

### 2. 性能监控

推荐工具：
- Prometheus + Grafana (指标监控)
- Sentry (错误追踪)
- ELK Stack (日志聚合)

---

## 🔧 常见问题排查

### 问题 1: 数据库连接失败

```bash
# 检查数据库是否运行
sudo systemctl status postgresql

# 检查连接字符串
echo $DATABASE_URL

# 测试连接
psql $DATABASE_URL -c "SELECT 1;"
```

### 问题 2: API 响应慢

```bash
# 检查数据库查询性能
# 启用慢查询日志

# 检查 Redis 缓存
redis-cli ping

# 增加 workers 数量
# 修改 uvicorn --workers 参数
```

### 问题 3: 前端无法连接后端

```bash
# 检查 CORS 配置
# backend/src/app/main.py 中的 CORS 设置

# 检查 API 基础 URL
# frontend/web/.env 中的 VITE_API_BASE_URL

# 检查防火墙
sudo ufw status
```

---

## 🧪 运行测试

### MVP 功能测试

```bash
cd backend

# 运行 API 测试 (需要后端服务运行中)
python3 test_mvp_api.py

# 运行单元测试
pytest tests/
```

### 前端测试

```bash
cd frontend/web

# 运行单元测试
npm run test

# 运行 E2E 测试
npm run test:e2e
```

---

## 📈 性能优化建议

1. **数据库优化**
   - 添加适当的索引
   - 启用查询缓存
   - 使用连接池

2. **Redis 缓存**
   - 缓存频繁查询的数据
   - 设置合理的过期时间

3. **CDN 加速**
   - 静态资源使用 CDN
   - 启用浏览器缓存

4. **负载均衡**
   - 使用 Nginx 或 HAProxy
   - 多实例部署后端

---

## 🔄 备份与恢复

### 数据库备份

```bash
# PostgreSQL 备份
pg_dump -U fieldmind fieldmind > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复
psql -U fieldmind fieldmind < backup_20260909_120000.sql
```

### 文件备份

```bash
# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /opt/fieldmind/data/uploads

# 备份配置
tar -czf config_backup_$(date +%Y%m%d).tar.gz /opt/fieldmind/backend/.env
```

---

## 📞 技术支持

- 文档：查看项目 README.md
- 问题追踪：GitHub Issues
- 社区讨论：GitHub Discussions

---

## ✅ 部署验证清单

部署完成后，请验证以下项目：

- [ ] 前端页面可以正常访问
- [ ] 后端 API 文档可以访问 (/docs)
- [ ] 用户可以注册和登录
- [ ] 可以创建项目
- [ ] 可以上传文档
- [ ] 文档自动处理和分块
- [ ] 知识图谱正常显示
- [ ] 数据质量监控面板正常
- [ ] 溯源回溯功能正常
- [ ] 协作权限管理正常
- [ ] 日志正常记录
- [ ] 备份脚本正常运行

---

**恭喜！FieldMind MVP 部署完成！** 🎉

现在您可以开始使用田野调查的核心功能，并根据实际需求进行扩展。
