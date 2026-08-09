# FieldMind 监控和告警系统集成指南

> **版本**: 1.0  
> **完成日期**: 2026-08-01  
> **系统**: FieldMind知识脉络分析系统

---

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [快速开始](#快速开始)
4. [Prometheus配置](#prometheus配置)
5. [Grafana仪表板](#grafana仪表板)
6. [告警规则](#告警规则)
7. [指标说明](#指标说明)
8. [故障排除](#故障排除)
9. [最佳实践](#最佳实践)

---

## 系统概述

FieldMind监控和告警系统提供全方位的性能监控、健康检查和自动告警功能。

### 核心特性

- ✅ **实时指标收集** - Prometheus自动抓取应用和基础设施指标
- ✅ **可视化仪表板** - Grafana提供3个预配置仪表板
- ✅ **智能告警** - 40+条告警规则覆盖应用、数据库、基础设施
- ✅ **多渠道通知** - Slack、Email、PagerDuty集成
- ✅ **历史数据** - 30天指标保留期
- ✅ **自动发现** - 服务自动注册和健康检查

### 技术栈

| 组件 | 版本 | 用途 |
|-----|------|------|
| Prometheus | 2.45.0 | 指标收集和存储 |
| Grafana | 10.0.3 | 数据可视化 |
| Alertmanager | 0.26.0 | 告警路由和通知 |
| Node Exporter | 1.6.1 | 系统指标 |
| Postgres Exporter | 0.13.2 | PostgreSQL指标 |
| Redis Exporter | 1.52.0 | Redis指标 |
| Celery Exporter | latest | Celery任务指标 |

---

## 架构设计

### 监控架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Metrics Middleware (自动收集HTTP指标)                │   │
│  │  • 请求计数、延迟、状态码                              │   │
│  │  • 业务指标 (文档、报告、对话)                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓ /metrics                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Prometheus (指标收集)                       │
│  • 抓取应用指标 (15s间隔)                                     │
│  • 抓取数据库指标                                             │
│  • 抓取系统指标                                               │
│  • 评估告警规则                                               │
└─────────────────────────────────────────────────────────────┘
         ↓                           ↓                  ↓
┌──────────────┐         ┌──────────────────┐   ┌─────────────┐
│  Grafana     │         │  Alertmanager    │   │  存储层     │
│  (可视化)    │         │  (告警路由)      │   │  (30天)     │
│  • 仪表板    │         │  • Slack通知     │   │             │
│  • 图表      │         │  • Email通知     │   │             │
│  • 监控      │         │  • 告警分组      │   │             │
└──────────────┘         └──────────────────┘   └─────────────┘
```

### 数据流

```
应用指标 → /metrics端点 → Prometheus抓取 → 存储 → Grafana展示
                                      ↓
                               评估告警规则
                                      ↓
                              Alertmanager路由
                                      ↓
                          Slack/Email/PagerDuty
```

---

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 10GB+ 磁盘空间

### 一键启动

```bash
# 1. 启动监控栈
./start_monitoring.sh

# 2. 访问服务
# Prometheus:   http://localhost:9090
# Grafana:      http://localhost:3000 (admin/admin)
# Alertmanager: http://localhost:9093
```

### 验证安装

```bash
# 运行测试套件
./test_monitoring.sh

# 检查服务健康
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health # Grafana
curl http://localhost:9093/-/healthy  # Alertmanager

# 查看应用指标
curl http://localhost:8000/metrics
```

### 配置Grafana

```bash
# 1. 登录Grafana (admin/admin)
open http://localhost:3000

# 2. 首次登录会提示修改密码

# 3. 仪表板自动加载
# - Infrastructure Metrics (基础设施)
# - Application Metrics (应用性能)
# - Database Metrics (数据库)
```

---

## Prometheus配置

### 主配置文件

**文件**: `prometheus.yml`

```yaml
global:
  scrape_interval: 15s      # 抓取间隔
  evaluation_interval: 15s  # 告警评估间隔

# 抓取目标
scrape_configs:
  # FieldMind后端
  - job_name: 'fieldmind-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Neo4j
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']

  # Celery
  - job_name: 'celery'
    static_configs:
      - targets: ['celery-exporter:9540']

  # 系统指标
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### 查询示例

```promql
# HTTP请求率 (按状态码)
sum(rate(http_requests_total[5m])) by (status)

# P95请求延迟
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# 错误率
sum(rate(http_requests_total{status=~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m]))

# 文档处理成功率
sum(rate(documents_processed_total{status="success"}[10m])) 
/ 
sum(rate(documents_processed_total[10m]))

# LLM API调用延迟
histogram_quantile(0.90, 
  sum(rate(llm_api_duration_seconds_bucket[10m])) by (le, provider, model)
)

# 缓存命中率
sum(rate(cache_hits_total[5m])) 
/ 
(sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))

# CPU使用率
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# PostgreSQL连接数
pg_stat_activity_count

# Redis内存使用
redis_memory_used_bytes / redis_memory_max_bytes
```

---

## Grafana仪表板

### 1. Infrastructure Metrics (基础设施监控)

**路径**: `grafana/dashboards/infrastructure.json`

**面板**:
- CPU使用率 (按实例)
- 内存使用率 (按实例)
- 磁盘使用率 (按挂载点)
- 网络流量 (RX/TX)
- 系统负载 (1m/5m/15m)
- 服务状态 (Up/Down)

**使用场景**:
- 监控服务器资源使用
- 容量规划
- 性能瓶颈识别

---

### 2. Application Metrics (应用性能监控)

**路径**: `grafana/dashboards/application.json`

**面板**:
- HTTP请求率 (按状态码)
- HTTP请求延迟 (P95, 按端点)
- 文档处理率 (按状态)
- 对话响应时间 (P95)
- LLM API调用 (按provider/model)
- Token使用率 (input/output)
- 缓存命中率
- 活跃请求数

**使用场景**:
- API性能监控
- 用户体验优化
- LLM成本控制

---

### 3. Database Metrics (数据库监控)

**路径**: `grafana/dashboards/database.json`

**面板**:
- PostgreSQL连接数 (活跃/最大)
- PostgreSQL查询延迟 (P95)
- Redis内存使用 (used/max)
- Redis缓存命中率
- Neo4j活跃事务数
- 数据库查询率 (按操作)

**使用场景**:
- 数据库性能优化
- 连接池调优
- 查询优化

---

### 自定义仪表板

```bash
# 1. 在Grafana UI中创建仪表板
# 2. 导出JSON
# 3. 保存到grafana/dashboards/

# 4. 重启Grafana自动加载
docker-compose -f docker-compose.monitoring.yml restart grafana
```

---

## 告警规则

### 告警分类

| 文件 | 分类 | 规则数 | 说明 |
|-----|------|-------|------|
| `alerts/application.yml` | 应用层 | 15条 | HTTP错误、性能、LLM |
| `alerts/database.yml` | 数据库层 | 12条 | PostgreSQL、Redis、Neo4j |
| `alerts/infrastructure.yml` | 基础设施层 | 18条 | CPU、内存、磁盘、网络 |

### 告警级别

- **Critical** (严重) - 立即处理，影响服务可用性
- **Warning** (警告) - 需要关注，可能影响性能
- **Info** (信息) - 仅记录，供参考

### 关键告警规则

#### 1. 高错误率 (Critical)

```yaml
- alert: HighErrorRate
  expr: |
    (sum(rate(http_requests_total{status=~"5.."}[5m])) / 
     sum(rate(http_requests_total[5m]))) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High HTTP error rate"
    description: "Error rate is {{ $value | humanizePercentage }}"
```

**触发条件**: 5分钟内5xx错误率 > 5%  
**处理**: 检查应用日志、数据库连接、外部依赖

---

#### 2. 高延迟 (Warning)

```yaml
- alert: HighLatency
  expr: |
    histogram_quantile(0.95, 
      sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
    ) > 2.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High HTTP latency on {{ $labels.endpoint }}"
```

**触发条件**: 10分钟内P95延迟 > 2秒  
**处理**: 优化慢查询、增加缓存、扩容资源

---

#### 3. 服务宕机 (Critical)

```yaml
- alert: ServiceDown
  expr: up == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.job }} is down"
```

**触发条件**: 服务2分钟内无法访问  
**处理**: 检查服务状态、重启服务、查看日志

---

#### 4. LLM API高错误率 (Critical)

```yaml
- alert: LLMAPIHighErrorRate
  expr: |
    (sum(rate(llm_api_calls_total{status!="success"}[10m])) / 
     sum(rate(llm_api_calls_total[10m]))) > 0.10
  for: 10m
  labels:
    severity: critical
```

**触发条件**: 10分钟内LLM API错误率 > 10%  
**处理**: 检查API密钥、配额、网络连接

---

#### 5. 高Token使用 (Warning)

```yaml
- alert: HighTokenUsage
  expr: sum(rate(llm_tokens_used_total[1h])) > 1000000
  for: 30m
  labels:
    severity: warning
```

**触发条件**: 1小时内使用 > 100万tokens  
**处理**: 检查是否有异常调用、优化prompt长度

---

### 告警通知

**Alertmanager配置**: `alertmanager.yml`

#### 通知渠道

```yaml
receivers:
  # Critical告警 → 多渠道
  - name: 'critical-alerts'
    slack_configs:
      - channel: '#critical-alerts'
        color: 'danger'
    email_configs:
      - to: 'oncall@fieldmind.com'
    # pagerduty_configs:
    #   - service_key: '${PAGERDUTY_SERVICE_KEY}'

  # 数据库团队
  - name: 'database-team'
    slack_configs:
      - channel: '#database-alerts'
    email_configs:
      - to: 'dba@fieldmind.com'

  # 开发团队
  - name: 'dev-team'
    slack_configs:
      - channel: '#dev-alerts'
```

#### 配置Slack

```bash
# 1. 创建Slack Incoming Webhook
# https://api.slack.com/messaging/webhooks

# 2. 设置环境变量
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 3. 重启Alertmanager
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

#### 配置Email

```bash
# 编辑 .env
SMTP_PASSWORD=your_smtp_password

# 或编辑 alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@fieldmind.com'
  smtp_auth_username: 'alerts@fieldmind.com'
  smtp_auth_password: 'your_password'
```

---

## 指标说明

### HTTP指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `http_requests_total` | Counter | method, endpoint, status | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | method, endpoint | HTTP请求延迟 |
| `http_requests_in_progress` | Gauge | method, endpoint | 进行中的HTTP请求 |

### 业务指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `documents_processed_total` | Counter | doc_type, status | 文档处理总数 |
| `document_processing_duration_seconds` | Histogram | doc_type | 文档处理时长 |
| `reports_generated_total` | Counter | tier, status | 报告生成总数 |
| `report_generation_duration_seconds` | Histogram | tier | 报告生成时长 |
| `chat_messages_total` | Counter | status | 对话消息总数 |
| `chat_response_duration_seconds` | Histogram | - | 对话响应时长 |
| `vector_searches_total` | Counter | collection | 向量检索总数 |
| `vector_search_duration_seconds` | Histogram | collection | 向量检索时长 |

### LLM指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `llm_api_calls_total` | Counter | provider, model, status | LLM API调用总数 |
| `llm_api_duration_seconds` | Histogram | provider, model | LLM API调用时长 |
| `llm_tokens_used_total` | Counter | provider, model, type | Token使用量 |

### 数据库指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `db_queries_total` | Counter | operation, table | 数据库查询总数 |
| `db_query_duration_seconds` | Histogram | operation, table | 数据库查询时长 |
| `cache_hits_total` | Counter | cache_type | 缓存命中总数 |
| `cache_misses_total` | Counter | cache_type | 缓存未命中总数 |

### Celery指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `celery_tasks_total` | Counter | task_name, status | Celery任务总数 |
| `celery_task_duration_seconds` | Histogram | task_name | Celery任务时长 |
| `celery_tasks_pending` | Gauge | task_name | 待处理任务数 |

---

## 故障排除

### 问题1: Prometheus无法抓取指标

**症状**: Prometheus UI显示目标为DOWN

**排查步骤**:

```bash
# 1. 检查应用是否运行
docker ps | grep fieldmind-backend

# 2. 检查/metrics端点
curl http://localhost:8000/metrics

# 3. 检查网络连接
docker network inspect fieldmind-network

# 4. 查看Prometheus日志
docker logs fieldmind-prometheus
```

**解决方案**:
- 确保应用已启动且健康
- 确认`prometheus.yml`中的target配置正确
- 确保所有服务在同一Docker网络

---

### 问题2: Grafana仪表板无数据

**症状**: 仪表板显示"No Data"

**排查步骤**:

```bash
# 1. 检查数据源连接
# Grafana UI → Configuration → Data Sources → Prometheus

# 2. 测试PromQL查询
# Grafana UI → Explore → 输入查询

# 3. 检查Prometheus是否有数据
curl 'http://localhost:9090/api/v1/query?query=up'
```

**解决方案**:
- 检查Prometheus数据源URL: `http://prometheus:9090`
- 确认时间范围选择正确
- 检查PromQL查询语法

---

### 问题3: 告警未触发

**症状**: 满足告警条件但未收到通知

**排查步骤**:

```bash
# 1. 检查Alertmanager状态
curl http://localhost:9093/api/v2/status

# 2. 查看活跃告警
curl http://localhost:9093/api/v2/alerts

# 3. 检查Alertmanager日志
docker logs fieldmind-alertmanager

# 4. 验证告警规则
curl http://localhost:9090/api/v1/rules
```

**解决方案**:
- 检查`alertmanager.yml`配置
- 验证Slack Webhook URL或Email配置
- 检查告警抑制规则

---

### 问题4: 指标未记录

**症状**: 某些自定义指标不显示

**排查步骤**:

```python
# 1. 检查指标是否已定义
from app.core.metrics import http_requests_total
print(http_requests_total)

# 2. 验证指标是否被调用
# 在代码中添加日志

# 3. 检查/metrics输出
curl http://localhost:8000/metrics | grep http_requests_total
```

**解决方案**:
- 确认指标已在`app/core/metrics.py`中定义
- 检查中间件是否正确集成
- 验证标签值是否合法

---

## 最佳实践

### 1. 指标命名

```python
# ✅ 好的命名
http_requests_total          # 清晰的名词
http_request_duration_seconds  # 带单位
document_processing_errors_total

# ❌ 避免
requests                     # 太模糊
time_taken                   # 缺少单位
processDocumentError         # 驼峰命名
```

### 2. 标签使用

```python
# ✅ 好的标签
http_requests_total{method="GET", endpoint="/api/documents", status="200"}

# ❌ 避免高基数标签
http_requests_total{user_id="123456"}  # 用户ID会导致大量时间序列
http_requests_total{request_id="..."}  # 请求ID唯一
```

### 3. 告警设置

```yaml
# ✅ 合理的告警
- alert: HighErrorRate
  expr: error_rate > 0.05  # 5%阈值合理
  for: 5m                  # 持续5分钟才触发
  
# ❌ 避免
- alert: AnyError
  expr: errors > 0         # 太敏感
  for: 10s                 # 太快触发
```

### 4. 仪表板设计

- 按层级组织 (基础设施 → 应用 → 业务)
- 使用合适的图表类型 (Graph、Gauge、Stat)
- 设置合理的刷新间隔 (30s)
- 添加说明和文档链接

### 5. 性能优化

```yaml
# Prometheus配置
global:
  scrape_interval: 15s      # 默认15秒合理
  evaluation_interval: 15s

# 对高频端点使用更短间隔
scrape_configs:
  - job_name: 'critical-service'
    scrape_interval: 10s    # 关键服务10秒
```

### 6. 数据保留

```bash
# Prometheus启动参数
--storage.tsdb.retention.time=30d  # 保留30天
--storage.tsdb.retention.size=50GB # 或限制大小
```

---

## 监控检查清单

### 日常检查

- [ ] 所有服务状态为UP
- [ ] 无Critical告警
- [ ] CPU/内存使用 < 80%
- [ ] 磁盘空间充足
- [ ] 错误率 < 1%
- [ ] P95延迟 < 2秒

### 每周检查

- [ ] 回顾告警历史
- [ ] 检查慢查询
- [ ] 分析Token使用趋势
- [ ] 审查缓存命中率
- [ ] 容量规划

### 每月检查

- [ ] 更新仪表板
- [ ] 优化告警规则
- [ ] 清理过期数据
- [ ] 性能基准测试
- [ ] 文档更新

---

## 附录

### A. 环境变量

```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

# Alertmanager
SMTP_PASSWORD=your_smtp_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Exporters
POSTGRES_USER=fieldmind
POSTGRES_PASSWORD=fieldmind123
POSTGRES_DB=fieldmind
REDIS_PASSWORD=
```

### B. 端口列表

| 服务 | 端口 | 说明 |
|-----|------|------|
| Prometheus | 9090 | Web UI |
| Grafana | 3000 | 仪表板 |
| Alertmanager | 9093 | 告警管理 |
| Node Exporter | 9100 | 系统指标 |
| Postgres Exporter | 9187 | PostgreSQL指标 |
| Redis Exporter | 9121 | Redis指标 |
| Celery Exporter | 9540 | Celery指标 |
| Backend /metrics | 8000 | 应用指标 |

### C. 参考资源

- [Prometheus文档](https://prometheus.io/docs/)
- [Grafana文档](https://grafana.com/docs/)
- [Alertmanager文档](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [PromQL查询语言](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

**文档版本**: 1.0  
**最后更新**: 2026-08-01  
**维护者**: FieldMind DevOps Team
