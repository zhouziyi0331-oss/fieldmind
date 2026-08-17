# FieldMind 部署指南

本文档提供FieldMind系统的完整部署指南，包括开发、测试和生产环境。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Kubernetes部署](#kubernetes部署)
- [配置说明](#配置说明)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)

---

## 系统要求

### 硬件要求

**最低配置（开发环境）：**
- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB

**推荐配置（生产环境）：**
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 100GB+ (SSD推荐)

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (本地开发)
- Kubernetes 1.25+ (K8s部署)

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-org/FieldMind-Rebuild.git
cd FieldMind-Rebuild
```

### 2. 配置环境变量

```bash
cp fieldmind-backend/.env.example fieldmind-backend/.env
```

编辑 `.env` 文件，修改必要的配置。

### 3. 启动服务

```bash
# 使用部署脚本（推荐）
./deploy.sh development

# 或手动启动
docker-compose -f docker-compose.full.yml up -d
```

### 4. 访问服务

- **API文档**: http://localhost:8000/docs
- **API端点**: http://localhost:8000/api
- **Neo4j浏览器**: http://localhost:7474

---

## 开发环境部署

### 方式1: 本地开发（无Docker）

#### 安装依赖

```bash
cd fieldmind-backend
pip install -r requirements.txt
```

#### 启动数据库服务

```bash
# 只启动数据库服务
docker-compose up -d postgres redis neo4j
```

#### 运行数据库迁移

```bash
alembic upgrade head
```

#### 启动Backend

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用启动脚本
./start.sh
```

### 方式2: Docker开发环境

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.full.yml up --build

# 后台运行
docker-compose -f docker-compose.full.yml up -d

# 查看日志
docker-compose -f docker-compose.full.yml logs -f backend
```

### 开发工具

#### 运行测试

```bash
cd fieldmind-backend
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=app --cov-report=html
```

#### 代码格式化

```bash
# 格式化代码
black app/

# 检查类型
mypy app/
```

---

## 生产环境部署

### 前置准备

1. **准备服务器**
   - Ubuntu 20.04+ / CentOS 8+ 或其他Linux发行版
   - 安装Docker和Docker Compose
   - 配置防火墙规则

2. **域名和SSL证书**
   - 准备域名（如：api.fieldmind.example.com）
   - 获取SSL证书（Let's Encrypt推荐）

3. **配置生产环境变量**

```bash
cp fieldmind-backend/.env.example fieldmind-backend/.env.production
```

编辑 `.env.production`，**必须修改**以下配置：

```bash
# 安全密钥（生成随机32字符以上）
SECRET_KEY=your-super-secret-key-change-in-production

# JWT密钥
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# 数据库密码
NEO4J_PASSWORD=strong-password-here

# 生产环境设置
ENVIRONMENT=production
DEBUG=false

# CORS设置（改为实际域名）
CORS_ORIGINS=["https://fieldmind.example.com"]
```

### 部署步骤

#### 1. 使用自动化部署脚本（推荐）

```bash
# 部署到生产环境
./deploy.sh production

# 脚本会自动：
# - 检查环境
# - 备份数据库
# - 构建镜像
# - 启动服务
# - 运行迁移
# - 健康检查
```

#### 2. 手动部署

```bash
# 1. 备份现有数据（如果有）
cp fieldmind-backend/data/fieldmind.db backups/fieldmind_$(date +%Y%m%d).db

# 2. 构建生产镜像
docker build -t fieldmind/backend:latest \
    -f fieldmind-backend/Dockerfile.prod \
    fieldmind-backend/

# 3. 启动服务
docker-compose -f docker-compose.full.yml up -d

# 4. 运行数据库迁移
docker-compose -f docker-compose.full.yml exec backend \
    alembic upgrade head

# 5. 检查服务状态
docker-compose -f docker-compose.full.yml ps
curl http://localhost:8000/health
```

### 配置Nginx反向代理

#### 安装SSL证书

```bash
# 将SSL证书放到nginx目录
mkdir -p nginx/ssl
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/
```

#### 启动Nginx

```bash
docker-compose -f docker-compose.full.yml up -d nginx
```

### 生产环境优化

#### 1. 数据库优化

**切换到PostgreSQL**（推荐用于生产）：

修改 `.env.production`：

```bash
DATABASE_URL=postgresql://fieldmind:password@postgres:5432/fieldmind
```

#### 2. 启用Redis缓存

```bash
CACHE_BACKEND=redis
REDIS_HOST=redis
REDIS_PORT=6379
```

#### 3. 配置日志收集

```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=your-sentry-dsn  # 错误追踪
```

---

## Kubernetes部署

### 前置条件

- Kubernetes集群（1.25+）
- kubectl已配置
- Helm 3.x（可选）
- 容器镜像仓库（如Docker Hub, Harbor）

### 部署步骤

#### 1. 构建并推送镜像

```bash
# 构建镜像
docker build -t your-registry/fieldmind-backend:v1.0.0 \
    -f fieldmind-backend/Dockerfile.prod \
    fieldmind-backend/

# 推送到镜像仓库
docker push your-registry/fieldmind-backend:v1.0.0
```

#### 2. 修改K8s配置

编辑 `k8s/configmap.yaml`，更新配置：

```yaml
data:
  CORS_ORIGINS: '["https://your-domain.com"]'
```

编辑 `k8s/backend-deployment.yaml`，更新镜像：

```yaml
image: your-registry/fieldmind-backend:v1.0.0
```

#### 3. 使用自动化脚本部署

```bash
./deploy-k8s.sh v1.0.0
```

#### 4. 手动部署

```bash
# 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 创建配置
kubectl apply -f k8s/configmap.yaml

# 创建持久卷
kubectl apply -f k8s/pvc.yaml

# 部署数据库服务
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/neo4j-statefulset.yaml

# 部署Backend
kubectl apply -f k8s/backend-deployment.yaml

# 配置自动扩缩容
kubectl apply -f k8s/hpa.yaml

# 配置Ingress
kubectl apply -f k8s/ingress.yaml
```

#### 5. 验证部署

```bash
# 查看所有资源
kubectl get all -n fieldmind

# 查看Pod状态
kubectl get pods -n fieldmind

# 查看日志
kubectl logs -f deployment/fieldmind-backend -n fieldmind

# 端口转发测试
kubectl port-forward svc/fieldmind-backend-service 8000:8000 -n fieldmind
```

### K8s生产优化

#### 1. 资源限制

根据实际负载调整 `k8s/backend-deployment.yaml`：

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

#### 2. 持久化存储

使用云存储（AWS EBS, GCP PD, Azure Disk）：

```yaml
storageClassName: gp3  # AWS
# storageClassName: pd-ssd  # GCP
# storageClassName: managed-premium  # Azure
```

#### 3. 配置Ingress Controller

```bash
# 安装Nginx Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace

# 安装Cert Manager（自动SSL）
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

---

## 配置说明

### 核心配置项

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `SECRET_KEY` | 应用密钥 | - | ✅ |
| `DATABASE_URL` | 数据库连接 | sqlite:///... | ✅ |
| `REDIS_HOST` | Redis地址 | redis | ❌ |
| `NEO4J_URI` | Neo4j连接 | bolt://neo4j:7687 | ❌ |
| `CORS_ORIGINS` | 允许的跨域源 | [] | ✅ |

### 环境变量优先级

1. 系统环境变量
2. `.env` 文件
3. 代码默认值

---

## 监控和日志

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 响应示例
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "response_time_ms": 15.2,
  "services": {
    "api": "ok",
    "database": "ok",
    "redis": "ok",
    "neo4j": "not_configured"
  }
}
```

### 查看日志

```bash
# Docker环境
docker-compose -f docker-compose.full.yml logs -f backend

# Kubernetes环境
kubectl logs -f deployment/fieldmind-backend -n fieldmind

# 查看特定时间范围
kubectl logs --since=1h deployment/fieldmind-backend -n fieldmind
```

### Prometheus监控（可选）

集成Prometheus指标：

```python
# app/main.py
from prometheus_client import make_asgi_app

# 添加metrics端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.full.yml logs backend

# 检查端口占用
lsof -i :8000

# 检查配置文件
docker-compose -f docker-compose.full.yml config
```

#### 2. 数据库连接失败

```bash
# 检查数据库服务状态
docker-compose -f docker-compose.full.yml ps postgres

# 测试数据库连接
docker-compose -f docker-compose.full.yml exec postgres \
    psql -U fieldmind -d fieldmind -c "SELECT 1"
```

#### 3. Redis连接失败

```bash
# 检查Redis状态
docker-compose -f docker-compose.full.yml exec redis redis-cli ping

# 应该返回: PONG
```

#### 4. Neo4j连接失败

```bash
# 检查Neo4j状态
docker-compose -f docker-compose.full.yml exec neo4j \
    cypher-shell -u neo4j -p fieldmind_password "RETURN 1"
```

#### 5. 健康检查失败

```bash
# 详细健康检查
curl -v http://localhost:8000/health

# 检查所有容器状态
docker-compose -f docker-compose.full.yml ps
```

### 性能问题

#### 数据库慢查询

```bash
# 启用PostgreSQL慢查询日志
# 在postgresql.conf中添加：
log_min_duration_statement = 1000  # 记录超过1秒的查询
```

#### 内存不足

```bash
# 查看容器内存使用
docker stats

# 调整容器内存限制（docker-compose.yml）
deploy:
  resources:
    limits:
      memory: 2G
```

### 回滚部署

```bash
# Docker环境
docker-compose -f docker-compose.full.yml down
docker-compose -f docker-compose.full.yml up -d

# Kubernetes环境
kubectl rollout undo deployment/fieldmind-backend -n fieldmind

# 回滚到特定版本
kubectl rollout undo deployment/fieldmind-backend --to-revision=2 -n fieldmind
```

---

## 备份和恢复

### 数据库备份

```bash
# SQLite备份
cp fieldmind-backend/data/fieldmind.db backups/fieldmind_$(date +%Y%m%d).db

# PostgreSQL备份
docker-compose -f docker-compose.full.yml exec postgres \
    pg_dump -U fieldmind fieldmind > backups/fieldmind_$(date +%Y%m%d).sql
```

### 数据恢复

```bash
# SQLite恢复
cp backups/fieldmind_20261201.db fieldmind-backend/data/fieldmind.db

# PostgreSQL恢复
docker-compose -f docker-compose.full.yml exec -T postgres \
    psql -U fieldmind fieldmind < backups/fieldmind_20261201.sql
```

---

## 安全建议

### 生产环境安全清单

- [ ] 修改所有默认密码
- [ ] 使用HTTPS/TLS加密
- [ ] 配置防火墙规则
- [ ] 启用API限流
- [ ] 定期更新依赖
- [ ] 配置日志审计
- [ ] 实施数据库定期备份
- [ ] 使用非root用户运行服务
- [ ] 配置Secret管理（如Vault）
- [ ] 启用网络隔离

### 最佳实践

1. **使用环境变量管理敏感信息**，不要硬编码
2. **定期更新依赖**，修复安全漏洞
3. **实施最小权限原则**
4. **启用审计日志**
5. **配置自动化备份**

---

## 更新和维护

### 滚动更新

```bash
# Docker环境
./deploy.sh production

# Kubernetes环境
kubectl set image deployment/fieldmind-backend \
    backend=your-registry/fieldmind-backend:v1.1.0 \
    -n fieldmind
```

### 数据库迁移

```bash
# 生成新迁移
alembic revision --autogenerate -m "add new table"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## 联系支持

如有问题，请联系：
- Email: support@fieldmind.example.com
- GitHub Issues: https://github.com/your-org/FieldMind-Rebuild/issues

---

**最后更新**: 2026-08-02
**文档版本**: 1.0.0
