# FieldMind Kubernetes 部署清单

本文档列出了Kubernetes部署所需的所有资源清单。

## 📦 部署资源概览

### 核心配置文件

| 文件 | 用途 | 资源类型 |
|------|------|----------|
| `k8s/namespace.yaml` | 命名空间定义 | Namespace |
| `k8s/configmap.yaml` | 配置和密钥 | ConfigMap, Secret |
| `k8s/pvc.yaml` | 持久化存储 | PersistentVolumeClaim |

### 应用部署

| 文件 | 用途 | 资源类型 |
|------|------|----------|
| `k8s/backend-deployment.yaml` | Backend应用 | Deployment, Service |
| `k8s/redis-statefulset.yaml` | Redis缓存 | StatefulSet, Service |
| `k8s/neo4j-statefulset.yaml` | Neo4j图数据库 | StatefulSet, Service |

### 网络和扩展

| 文件 | 用途 | 资源类型 |
|------|------|----------|
| `k8s/ingress.yaml` | 入口控制器 | Ingress |
| `k8s/hpa.yaml` | 自动扩缩容 | HorizontalPodAutoscaler |

## 🚀 快速部署

### 方式1：使用自动化脚本（推荐）

```bash
./deploy-k8s.sh latest
```

### 方式2：手动部署

```bash
# 1. 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 2. 创建配置
kubectl apply -f k8s/configmap.yaml

# 3. 创建持久卷
kubectl apply -f k8s/pvc.yaml

# 4. 部署数据服务
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/neo4j-statefulset.yaml

# 5. 部署应用
kubectl apply -f k8s/backend-deployment.yaml

# 6. 配置扩展
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

## 📊 资源规格

### Backend Deployment

- **副本数**: 3个Pod（可通过HPA自动扩展到10个）
- **CPU请求/限制**: 250m / 1000m
- **内存请求/限制**: 512Mi / 2Gi
- **存储**: 
  - 数据卷: 10Gi
  - 上传卷: 50Gi

### Redis StatefulSet

- **副本数**: 1个Pod
- **CPU请求/限制**: 100m / 500m
- **内存请求/限制**: 256Mi / 512Mi
- **存储**: 5Gi
- **配置**: maxmemory 512mb, LRU淘汰策略

### Neo4j StatefulSet

- **副本数**: 1个Pod
- **CPU请求/限制**: 500m / 2000m
- **内存请求/限制**: 1Gi / 2Gi
- **存储**: 20Gi
- **配置**: pagecache 512M, heap 1G

## 🔍 监控命令

### 查看所有资源

```bash
kubectl get all -n fieldmind
```

### 查看Pod状态

```bash
kubectl get pods -n fieldmind -w
```

### 查看服务

```bash
kubectl get svc -n fieldmind
```

### 查看Ingress

```bash
kubectl get ingress -n fieldmind
```

### 查看HPA状态

```bash
kubectl get hpa -n fieldmind
```

## 📝 日志查看

### Backend日志

```bash
kubectl logs -f deployment/fieldmind-backend -n fieldmind
```

### Redis日志

```bash
kubectl logs -f statefulset/redis -n fieldmind
```

### Neo4j日志

```bash
kubectl logs -f statefulset/neo4j -n fieldmind
```

## 🔧 故障排查

### 查看Pod详情

```bash
kubectl describe pod <pod-name> -n fieldmind
```

### 进入容器

```bash
kubectl exec -it <pod-name> -n fieldmind -- /bin/bash
```

### 查看事件

```bash
kubectl get events -n fieldmind --sort-by='.lastTimestamp'
```

### 端口转发（本地测试）

```bash
# Backend
kubectl port-forward svc/fieldmind-backend-service 8000:8000 -n fieldmind

# Neo4j浏览器
kubectl port-forward svc/neo4j-service 7474:7474 -n fieldmind

# Redis
kubectl port-forward svc/redis-service 6379:6379 -n fieldmind
```

## 🔄 更新和回滚

### 更新镜像

```bash
kubectl set image deployment/fieldmind-backend \
    backend=your-registry/fieldmind-backend:v1.1.0 \
    -n fieldmind
```

### 查看更新状态

```bash
kubectl rollout status deployment/fieldmind-backend -n fieldmind
```

### 回滚

```bash
# 回滚到上一版本
kubectl rollout undo deployment/fieldmind-backend -n fieldmind

# 回滚到指定版本
kubectl rollout undo deployment/fieldmind-backend --to-revision=2 -n fieldmind
```

### 查看历史版本

```bash
kubectl rollout history deployment/fieldmind-backend -n fieldmind
```

## 🗑️ 清理资源

### 删除所有资源

```bash
kubectl delete namespace fieldmind
```

### 删除特定资源

```bash
kubectl delete -f k8s/backend-deployment.yaml
kubectl delete -f k8s/ingress.yaml
```

## 🔐 安全配置

### 更新Secret

```bash
# 编辑Secret
kubectl edit secret fieldmind-backend-secret -n fieldmind

# 或者重新应用
kubectl apply -f k8s/configmap.yaml
```

### 重启Pod以应用新配置

```bash
kubectl rollout restart deployment/fieldmind-backend -n fieldmind
```

## 📈 扩展配置

### 手动扩展

```bash
kubectl scale deployment/fieldmind-backend --replicas=5 -n fieldmind
```

### HPA自动扩展

HPA已配置：
- 最小副本数: 2
- 最大副本数: 10
- CPU目标: 70%
- 内存目标: 80%

## 🌐 Ingress配置

### 查看Ingress地址

```bash
kubectl get ingress fieldmind-ingress -n fieldmind
```

### 配置域名

在Ingress配置中修改 `host` 字段，然后应用：

```bash
kubectl apply -f k8s/ingress.yaml
```

### SSL证书（Cert Manager）

如果使用Cert Manager自动获取SSL：

```bash
# 查看证书状态
kubectl get certificate -n fieldmind

# 查看证书详情
kubectl describe certificate fieldmind-tls-secret -n fieldmind
```

## 💾 备份和恢复

### 备份PVC数据

```bash
# 创建备份Pod
kubectl run backup --image=busybox -n fieldmind -- sleep 3600

# 挂载PVC并复制数据
kubectl cp fieldmind/<pod-name>:/app/data ./backup/
```

### 恢复数据

```bash
# 复制数据到PVC
kubectl cp ./backup/ fieldmind/<pod-name>:/app/data/
```

## 📊 资源使用监控

### 查看资源使用

```bash
kubectl top pods -n fieldmind
kubectl top nodes
```

### Prometheus监控（如果安装）

```bash
# 端口转发Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

## 🔗 相关文档

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 完整部署指南
- [README.md](README.md) - 项目说明
- [FEATURE_COMPLETION_REPORT.md](FEATURE_COMPLETION_REPORT.md) - 功能完成报告

---

**最后更新**: 2026-08-02
**K8s版本**: 1.25+
