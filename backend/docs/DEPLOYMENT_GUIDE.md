# FieldMind Backend 部署运维手册

## 目录
- [系统架构](#系统架构)
- [部署前准备](#部署前准备)
- [Docker部署](#docker部署)
- [Kubernetes部署](#kubernetes部署)
- [监控配置](#监控配置)
- [日志管理](#日志管理)
- [性能调优](#性能调优)
- [故障排查](#故障排查)

---

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                     │
│                  (Nginx/Traefik)                    │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼────────┐
│  FieldMind API │   │  FieldMind API  │
│   (Container)  │   │   (Container)   │
└────────┬───────┘   └────────┬────────┘
         │                    │
    ┌────┴────────────────────┴────┐
    │                               │
┌───▼──────────┐          ┌────────▼────────┐
│  PostgreSQL  │          │  Redis Cluster  │
│   (Primary)  │          │   (Cache/Queue) │
└──────────────┘          └─────────────────┘
         │
    ┌────▼─────┐
    │PostgreSQL│
    │(Replica) │
    └──────────┘
```

### 技术栈
- **Web框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 14+ (带连接池)
- **缓存**: Redis 7+ (带连接池)
- **向量数据库**: Milvus 2.3+
- **监控**: Prometheus + Grafana
- **日志**: Loguru (JSON格式)
- **容器**: Docker + Kubernetes

---

## 部署前准备

### 1. 硬件要求

**最低配置** (开发/测试):
- CPU: 4核
- 内存: 8GB
- 磁盘: 50GB SSD
- 网络: 100Mbps

**推荐配置** (生产):
- CPU: 8核+
- 内存: 16GB+
- 磁盘: 200GB+ SSD (NVMe)
- 网络: 1Gbps+

### 2. 软件依赖

```bash
# 必需
Python 3.11+
PostgreSQL 14+
Redis 7+
Docker 24+
Docker Compose 2.20+

# 可选
Kubernetes 1.28+
Helm 3.12+
```

### 3. 环境变量配置

创建 `.env` 文件:

```bash
# 应用配置
APP_ENV=production
APP_VERSION=1.0.0
LOG_LEVEL=INFO
JSON_LOGS=true
LOG_FILE=/var/log/fieldmind/app.log

# 数据库配置
DATABASE_URL=postgresql://user:password@postgres:5432/fieldmind
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_POOL_SIZE=50
REDIS_MAX_CONNECTIONS=100
REDIS_SOCKET_TIMEOUT=5

# Milvus配置
MILVUS_HOST=milvus
MILVUS_PORT=19530

# AI模型配置
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4

# 安全配置
SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_PER_MINUTE=60

# 监控配置
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# CORS配置
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## Docker部署

### 1. Docker Compose (快速部署)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
      - "9090:9090"  # Metrics
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://fieldmind:password@postgres:5432/fieldmind
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/var/log/fieldmind
      - ./uploads:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=fieldmind
      - POSTGRES_USER=fieldmind
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./config/prometheus/alerts.yml:/etc/prometheus/alerts.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

**部署命令**:
```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f backend

# 4. 数据库迁移
docker-compose exec backend alembic upgrade head

# 5. 健康检查
curl http://localhost:8000/health
```

### 2. Dockerfile 优化

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# 非root用户
RUN useradd -m -u 1000 fieldmind

WORKDIR /app

# 复制依赖
COPY --from=builder /root/.local /home/fieldmind/.local
COPY --chown=fieldmind:fieldmind . .

# 环境变量
ENV PATH=/home/fieldmind/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER fieldmind

EXPOSE 8000 9090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Kubernetes部署

### 1. Deployment配置

**k8s/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fieldmind-backend
  namespace: fieldmind
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: fieldmind-backend
  template:
    metadata:
      labels:
        app: fieldmind-backend
        version: v1.0.0
    spec:
      containers:
      - name: backend
        image: fieldmind/backend:1.0.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: APP_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fieldmind-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: fieldmind-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: logs
          mountPath: /var/log/fieldmind
      volumes:
      - name: logs
        emptyDir: {}
```

### 2. Service配置

**k8s/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fieldmind-backend
  namespace: fieldmind
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  selector:
    app: fieldmind-backend
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
```

### 3. HPA自动伸缩

**k8s/hpa.yaml**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fieldmind-backend-hpa
  namespace: fieldmind
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fieldmind-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
```

**部署命令**:
```bash
# 1. 创建命名空间
kubectl create namespace fieldmind

# 2. 创建secrets
kubectl create secret generic fieldmind-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=redis-url='redis://...' \
  -n fieldmind

# 3. 应用配置
kubectl apply -f k8s/

# 4. 查看状态
kubectl get pods -n fieldmind
kubectl logs -f deployment/fieldmind-backend -n fieldmind

# 5. 滚动更新
kubectl set image deployment/fieldmind-backend \
  backend=fieldmind/backend:1.0.1 -n fieldmind

# 6. 回滚
kubectl rollout undo deployment/fieldmind-backend -n fieldmind
```

---

## 监控配置

### 1. Prometheus配置

**config/prometheus/prometheus.yml**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

rule_files:
  - '/etc/prometheus/alerts.yml'

scrape_configs:
  - job_name: 'fieldmind-backend'
    static_configs:
    - targets: ['backend:9090']
    metrics_path: '/metrics'
```

### 2. Grafana仪表盘

**关键指标面板**:

1. **API性能监控**
   - QPS (每秒请求数)
   - P50/P95/P99延迟
   - 错误率趋势
   - 请求方法/端点分布

2. **数据库监控**
   - 连接池使用率
   - 查询延迟分布
   - 慢查询统计
   - 事务吞吐量

3. **缓存监控**
   - 命中率曲线
   - 缓存大小
   - 驱逐率
   - 连接数

4. **系统资源监控**
   - CPU使用率
   - 内存使用率
   - 磁盘I/O
   - 网络流量

**导入仪表盘JSON** (在Grafana UI中):
```
Dashboard ID: [待创建自定义Dashboard]
```

---

## 日志管理

### 1. 日志格式

所有日志以JSON格式输出:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123",
  "method": "GET",
  "path": "/api/v1/documents",
  "status_code": 200,
  "duration_ms": 45.23
}
```

### 2. 日志级别

- **DEBUG**: 详细调试信息 (仅开发环境)
- **INFO**: 常规操作日志
- **WARNING**: 警告但不影响功能
- **ERROR**: 错误需要关注
- **CRITICAL**: 严重错误需立即处理

### 3. 日志聚合 (ELK/Loki)

**使用Loki + Promtail**:
```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: fieldmind
    static_configs:
    - targets:
        - localhost
      labels:
        job: fieldmind-backend
        __path__: /var/log/fieldmind/*.log
```

### 4. 日志查询示例

**查找特定用户的请求**:
```
{job="fieldmind-backend"} | json | user_id="123"
```

**查找错误日志**:
```
{job="fieldmind-backend"} | json | level="ERROR"
```

**查找慢请求**:
```
{job="fieldmind-backend"} | json | duration_ms > 1000
```

---

## 性能调优

### 1. 数据库优化

**连接池配置**:
```python
# 推荐配置
DB_POOL_SIZE = 20  # 每个进程的连接数
DB_MAX_OVERFLOW = 10  # 超出pool_size的额外连接
DB_POOL_TIMEOUT = 30  # 获取连接超时(秒)
DB_POOL_RECYCLE = 3600  # 连接回收时间(秒)
```

**索引优化**:
```sql
-- 已创建的性能索引
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

### 2. Redis优化

**缓存策略**:
```python
# TTL配置
USER_CACHE_TTL = 300  # 5分钟
DOCUMENT_CACHE_TTL = 600  # 10分钟
SEARCH_RESULT_CACHE_TTL = 1800  # 30分钟

# 淘汰策略
maxmemory-policy: allkeys-lru
```

**连接池配置**:
```python
REDIS_POOL_SIZE = 50
REDIS_MAX_CONNECTIONS = 100
REDIS_SOCKET_TIMEOUT = 5
```

### 3. API性能优化

**Uvicorn工作进程**:
```bash
# 计算公式: (2 × CPU核心数) + 1
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 17  # 假设8核CPU
  --worker-class uvicorn.workers.UvicornWorker
```

**异步优化**:
- 所有I/O操作使用async/await
- 数据库查询批量化
- 关系预加载避免N+1问题
- 使用后台任务处理耗时操作

### 4. 缓存预热

**启动时预加载热数据**:
```python
async def warmup_cache():
    # 加载热门文档
    popular_docs = await db.query(Document).limit(100).all()
    for doc in popular_docs:
        await cache.set(f"doc:{doc.id}", doc)
    
    # 加载活跃用户
    active_users = await db.query(User).filter(User.is_active).all()
    for user in active_users:
        await cache.set(f"user:{user.id}", user)
```

---

## 故障排查

### 1. 常见问题

#### 问题: API响应慢
**排查步骤**:
```bash
# 1. 检查Prometheus metrics
curl http://localhost:9090/metrics | grep http_request_duration

# 2. 查看慢查询日志
docker-compose logs backend | grep "duration_ms" | awk '$NF > 1000'

# 3. 检查数据库连接池
curl http://localhost:8000/health | jq '.checks.database'

# 4. 检查Redis连接
redis-cli info stats
```

#### 问题: 数据库连接池耗尽
**解决方案**:
```bash
# 1. 查看当前连接数
SELECT count(*) FROM pg_stat_activity;

# 2. 找出慢查询
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
ORDER BY duration DESC;

# 3. 增加连接池大小
# 修改 .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20

# 4. 重启服务
docker-compose restart backend
```

#### 问题: 缓存命中率低
**排查步骤**:
```bash
# 1. 查看命中率
curl http://localhost:9090/metrics | grep cache_hit_rate

# 2. 检查Redis内存
redis-cli info memory

# 3. 查看淘汰策略
redis-cli config get maxmemory-policy

# 4. 调整TTL和内存
redis-cli config set maxmemory 4gb
```

#### 问题: 内存泄漏
**排查步骤**:
```bash
# 1. 查看内存趋势
curl http://localhost:9090/metrics | grep system_memory

# 2. Python内存分析
pip install memory_profiler
python -m memory_profiler app/main.py

# 3. 检查连接是否正确关闭
# 确保所有数据库session使用 with 语句或 finally 块关闭
```

### 2. 紧急恢复流程

#### 服务完全宕机
```bash
# 1. 快速重启
docker-compose restart backend

# 2. 回滚到上一版本
kubectl rollout undo deployment/fieldmind-backend -n fieldmind

# 3. 检查依赖服务
docker-compose ps
kubectl get pods -n fieldmind

# 4. 查看错误日志
docker-compose logs --tail=100 backend
```

#### 数据库故障
```bash
# 1. 切换到只读模式
# 修改环境变量
READONLY_MODE=true

# 2. 启用备库
# 修改 DATABASE_URL 指向replica

# 3. 数据恢复
pg_restore -d fieldmind backup.sql
```

### 3. 性能基准测试

**使用Locust进行压测**:
```python
# locustfile.py
from locust import HttpUser, task, between

class FieldMindUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def list_documents(self):
        self.client.get("/api/v1/documents", headers={
            "Authorization": f"Bearer {self.token}"
        })
    
    @task(1)
    def chat(self):
        self.client.post("/api/v1/chat", json={
            "message": "Hello",
            "session_id": "test"
        })
```

**运行压测**:
```bash
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

---

## 安全检查清单

- [ ] 所有敏感信息已从日志中脱敏
- [ ] 使用HTTPS加密传输
- [ ] JWT token设置合理过期时间
- [ ] SQL注入防护已启用 (ORM参数化查询)
- [ ] CORS配置正确
- [ ] Rate limiting已启用
- [ ] 数据库密码使用强密码
- [ ] Redis需要密码认证
- [ ] Docker容器以非root用户运行
- [ ] Secrets存储在Kubernetes Secrets中

---

## 维护计划

### 日常检查
- 每天查看Grafana仪表盘
- 检查告警通知
- 查看错误日志

### 每周检查
- 数据库备份验证
- 磁盘空间清理
- 性能趋势分析

### 每月检查
- 依赖包更新
- 安全漏洞扫描
- 容量规划评估

---

## 联系支持

- **技术文档**: [BACKEND_FULL_ARCHITECTURE.md](BACKEND_FULL_ARCHITECTURE.md)
- **API文档**: http://localhost:8000/docs
- **监控面板**: http://localhost:3000 (Grafana)
- **问题反馈**: GitHub Issues
