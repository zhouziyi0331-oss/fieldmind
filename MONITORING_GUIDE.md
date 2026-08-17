# FieldMind 监控和日志系统指南

本文档提供FieldMind监控和日志系统的完整配置和使用指南。

## 目录

- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [Prometheus监控](#prometheus监控)
- [Grafana仪表板](#grafana仪表板)
- [日志聚合](#日志聚合)
- [告警系统](#告警系统)
- [分布式追踪](#分布式追踪)
- [故障排查](#故障排查)

---

## 系统架构

### 组件概览

```
┌─────────────────────────────────────────────────────────┐
│                    FieldMind Backend                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Metrics  │  │  Logs    │  │  Traces  │              │
│  │ /metrics │  │  loguru  │  │ (future) │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
└───────┼─────────────┼─────────────┼─────────────────────┘
        │             │             │
        ↓             ↓             ↓
┌───────────┐  ┌───────────┐  ┌───────────┐
│Prometheus │  │ Promtail  │  │  Jaeger   │
│           │  │           │  │           │
│ 抓取指标  │  │ 收集日志  │  │  追踪     │
└─────┬─────┘  └─────┬─────┘  └───────────┘
      │              │
      ↓              ↓
┌───────────┐  ┌───────────┐
│AlertMgr   │  │   Loki    │
│           │  │           │
│ 告警管理  │  │ 日志存储  │
└─────┬─────┘  └─────┬─────┘
      │              │
      └──────┬───────┘
             ↓
      ┌───────────┐
      │  Grafana  │
      │           │
      │ 可视化    │
      └───────────┘
```

### 核心组件

1. **Prometheus** - 指标收集和存储
2. **Grafana** - 可视化仪表板
3. **AlertManager** - 告警管理和路由
4. **Loki** - 日志聚合
5. **Promtail** - 日志收集器
6. **Jaeger** - 分布式追踪（可选）

---

## 快速开始

### 1. 启动监控栈

```bash
# 启动所有监控组件
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. 验证服务

```bash
# 测试监控系统
python test_monitoring_system.py
```

### 3. 访问界面

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Jaeger**: http://localhost:16686

---

## Prometheus监控

### 指标类型

#### 1. HTTP请求指标

```promql
# 总请求数
http_requests_total

# 请求速率
rate(http_requests_total[5m])

# 按端点分组的请求速率
sum(rate(http_requests_total[5m])) by (endpoint)

# 错误率
sum(rate(http_requests_total{status=~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m]))
```

#### 2. 响应时间指标

```promql
# P50响应时间
histogram_quantile(0.50, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)

# P95响应时间
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)

# P99响应时间
histogram_quantile(0.99, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

#### 3. 系统资源指标

```promql
# CPU使用率
system_cpu_usage_percent

# 内存使用率
system_memory_usage_percent

# 磁盘使用率
system_disk_usage_percent

# 进程内存
process_memory_bytes / 1024 / 1024  # MB
```

#### 4. 业务指标

```promql
# 项目总数
projects_total

# 文档总数
documents_total

# 分析任务总数
sum(analysis_tasks_total)

# 对话总数
sum(conversations_total)
```

#### 5. 数据库指标

```promql
# 数据库查询延迟（P95）
histogram_quantile(0.95,
  sum(rate(db_query_duration_seconds_bucket[5m])) by (le, operation)
)

# 活跃连接数
db_connections_active

# 数据库错误率
rate(db_errors_total[5m])
```

#### 6. 缓存指标

```promql
# 缓存命中率
sum(rate(cache_hits_total[5m])) by (cache_name)
/
(sum(rate(cache_hits_total[5m])) by (cache_name) 
 + sum(rate(cache_misses_total[5m])) by (cache_name))
```

### 常用查询

#### 当前QPS

```promql
sum(rate(http_requests_total[1m]))
```

#### 过去1小时的平均响应时间

```promql
avg_over_time(
  histogram_quantile(0.95, 
    sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
  )[1h:]
)
```

#### TOP 5 慢端点

```promql
topk(5,
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
  )
)
```

---

## Grafana仪表板

### 导入仪表板

1. 登录Grafana (http://localhost:3000)
2. 点击左侧 "+" → "Import"
3. 上传 `monitoring/grafana/fieldmind-dashboard.json`
4. 选择Prometheus数据源
5. 点击 "Import"

### 仪表板面板

#### 1. 系统健康状态
- Backend服务状态 (Up/Down)
- 实时健康检查

#### 2. 请求速率 (QPS)
- 总请求速率
- 按状态码分组 (2xx/4xx/5xx)
- 时间序列图

#### 3. 错误率
- 5xx错误率百分比
- 仪表盘显示
- 告警阈值标记

#### 4. 响应时间
- P50/P95/P99分位数
- 时间序列图
- 慢请求标记

#### 5. 系统资源
- CPU使用率
- 内存使用率
- 磁盘使用率
- 进程内存

#### 6. API端点分布
- 各端点请求量
- 堆叠面积图

#### 7. 数据库性能
- 查询延迟
- 连接池状态
- 错误统计

#### 8. 缓存性能
- 命中率
- 命中/未命中趋势

#### 9. 业务指标
- 项目数
- 文档数
- 分析任务数

### 自定义仪表板

```json
{
  "title": "我的自定义面板",
  "targets": [
    {
      "expr": "your_promql_query",
      "legendFormat": "标签名"
    }
  ]
}
```

---

## 日志聚合

### Loki日志查询

#### 基础查询

```logql
# 所有FieldMind日志
{job="fieldmind-backend"}

# 错误日志
{job="fieldmind-errors"}

# API调用日志
{job="fieldmind-api"}

# 按级别筛选
{job="fieldmind-backend"} |= "ERROR"

# 正则匹配
{job="fieldmind-backend"} |~ "database.*error"
```

#### 聚合查询

```logql
# 错误日志速率
rate({job="fieldmind-errors"}[5m])

# 按状态码统计API调用
sum(rate({job="fieldmind-api"}[5m])) by (status)

# 慢请求计数
count_over_time({job="fieldmind-api"} |~ "duration.*[5-9][0-9]{3}ms"[5m])
```

### 日志级别

- **DEBUG** - 详细调试信息
- **INFO** - 一般信息日志
- **WARNING** - 警告信息
- **ERROR** - 错误信息
- **CRITICAL** - 严重错误

### 日志文件

```
/tmp/fieldmind_logs/
├── fieldmind_2024-08-02.log      # 所有日志
├── api_2024-08-02.log             # API调用日志
├── errors_2024-08-02.log          # 错误日志
└── performance_2024-08-02.log     # 性能日志
```

### 日志保留策略

- **所有日志**: 30天
- **错误日志**: 90天
- **性能日志**: 7天
- **自动压缩**: 旧日志自动zip压缩

---

## 告警系统

### 告警级别

1. **CRITICAL** - 严重告警，立即处理
2. **ERROR** - 错误告警，尽快处理
3. **WARNING** - 警告告警，关注即可
4. **INFO** - 信息告警，仅记录

### 预定义告警

#### 1. 服务可用性

```yaml
- alert: ServiceDown
  expr: up{job="fieldmind-backend"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Backend服务不可用"
```

#### 2. 高错误率

```yaml
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total[5m]))
    > 0.05
  for: 5m
  labels:
    severity: critical
```

#### 3. 高响应时间

```yaml
- alert: HighResponseTime
  expr: |
    histogram_quantile(0.95,
      sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
    ) > 2
  for: 10m
  labels:
    severity: warning
```

#### 4. 资源告警

```yaml
# CPU使用率过高
- alert: HighCPUUsage
  expr: system_cpu_usage_percent > 80
  for: 5m

# 内存使用率过高
- alert: HighMemoryUsage
  expr: system_memory_usage_percent > 85
  for: 5m

# 磁盘空间不足
- alert: HighDiskUsage
  expr: system_disk_usage_percent > 85
  for: 10m
```

### 告警通道

#### 1. Email

配置 `monitoring/alertmanager/config.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@fieldmind.example.com'
  smtp_auth_username: 'alerts@fieldmind.example.com'
  smtp_auth_password: 'your-password'
```

#### 2. Webhook

```yaml
receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'https://your-webhook-url.com/alerts'
        send_resolved: true
```

#### 3. 钉钉

```yaml
receivers:
  - name: 'dingtalk'
    webhook_configs:
      - url: 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN'
```

#### 4. 企业微信

```yaml
receivers:
  - name: 'wechat'
    wechat_configs:
      - corp_id: 'YOUR_CORP_ID'
        agent_id: 'YOUR_AGENT_ID'
        api_secret: 'YOUR_API_SECRET'
```

### 使用应用内告警API

```python
from app.core.alerts import send_critical_alert

# 发送Critical告警
await send_critical_alert(
    title="数据库连接失败",
    message="无法连接到PostgreSQL数据库",
    tags=["database", "postgresql"],
    metadata={"host": "postgres:5432"}
)
```

---

## 分布式追踪

### Jaeger配置（可选）

1. 访问 http://localhost:16686
2. 选择服务 "fieldmind-backend"
3. 查看追踪链路

### 追踪ID

每个请求都会自动生成追踪ID:

```
X-Trace-ID: 550e8400-e29b-41d4-a716-446655440000
X-Span-ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
```

---

## 故障排查

### 问题1: Prometheus无法抓取指标

**检查**:
```bash
# 测试metrics端点
curl http://localhost:8000/metrics

# 检查Prometheus targets
curl http://localhost:9090/api/v1/targets
```

**解决**:
- 确保Backend服务正常运行
- 检查网络连通性
- 验证Prometheus配置文件

### 问题2: Grafana无数据

**检查**:
```bash
# 测试Prometheus查询
curl 'http://localhost:9090/api/v1/query?query=up'
```

**解决**:
- 验证Prometheus数据源配置
- 检查PromQL查询语法
- 确认时间范围设置

### 问题3: 日志不显示

**检查**:
```bash
# 检查日志文件
ls -lh /tmp/fieldmind_logs/

# 检查Promtail状态
docker logs fieldmind-promtail
```

**解决**:
- 确认日志文件路径正确
- 检查Promtail配置
- 验证Loki服务状态

### 问题4: 告警不发送

**检查**:
```bash
# 查看AlertManager日志
docker logs fieldmind-alertmanager

# 测试告警规则
curl http://localhost:9090/api/v1/rules
```

**解决**:
- 验证告警规则语法
- 检查AlertManager配置
- 测试通知渠道连通性

---

## 性能优化

### Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s       # 降低抓取频率
  evaluation_interval: 15s

# 添加retention
storage:
  tsdb:
    retention.time: 30d      # 保留30天数据
```

### Loki

```yaml
# loki-config.yml
limits_config:
  retention_period: 744h     # 31天
  max_query_series: 1000     # 限制查询范围
```

---

## 最佳实践

### 1. 指标命名

- 使用下划线分隔: `http_requests_total`
- 添加单位后缀: `_bytes`, `_seconds`, `_total`
- 保持一致性

### 2. 标签使用

- 控制标签基数（cardinality）
- 避免使用高基数标签（如user_id）
- 使用有意义的标签名

### 3. 告警设置

- 设置合理的阈值
- 避免告警疲劳
- 使用告警分组
- 设置静默规则

### 4. 日志管理

- 结构化日志
- 合理的日志级别
- 避免记录敏感信息
- 定期清理旧日志

---

## 监控检查清单

- [ ] Prometheus正常抓取指标
- [ ] Grafana仪表板显示数据
- [ ] AlertManager接收告警
- [ ] 告警通道配置正确
- [ ] 日志正常收集
- [ ] Loki查询正常
- [ ] 关键告警规则已配置
- [ ] 监控数据定期备份

---

**最后更新**: 2026-08-02  
**文档版本**: 1.0.0
