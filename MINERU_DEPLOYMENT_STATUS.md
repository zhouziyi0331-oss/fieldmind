# MinerU 集成部署状态

## 📊 当前进度

### ✅ 已完成
1. **仓库准备**
   - ✅ 克隆 mineru-tianshu 到 `/Users/alwan/FieldMind-Rebuild/mineru-tianshu`
   - ✅ 克隆原始 MinerU 数据（mineru.zip）
   - ✅ 创建 mineru-service 目录和客户端代码

2. **集成代码**
   - ✅ MinerU API 客户端 ([mineru-service/mineru_client.py](mineru-service/mineru_client.py))
   - ✅ 增强的文档解析器 ([fieldmind-backend/app/services/document_parser.py](fieldmind-backend/app/services/document_parser.py))
   - ✅ 自动降级机制（MinerU 不可用时使用基础解析器）
   - ✅ 集成测试脚本 ([mineru-service/test_integration.py](mineru-service/test_integration.py))

3. **文档**
   - ✅ [MINERU_INTEGRATION_REPORT.md](MINERU_INTEGRATION_REPORT.md) - 原始集成报告
   - ✅ [MINERU_TIANSHU_INTEGRATION.md](MINERU_TIANSHU_INTEGRATION.md) - Tianshu 集成指南
   - ✅ [mineru-service/QUICK_START.md](mineru-service/QUICK_START.md) - 快速入门
   - ✅ 更新主 README.md

### 🔄 进行中
4. **Docker 部署**
   - 🔄 正在拉取 `quincyqiang/mineru:0.3-models` 镜像
   - ⏳ 预计完成时间：5-10 分钟（取决于网络速度）

### ⏸️ 待完成
5. **服务启动**
   - ⏸️ 启动 MinerU Docker 服务
   - ⏸️ 健康检查和功能验证
   - ⏸️ 端到端集成测试

## 🎯 部署方案对比

### 方案 A：简化版 MinerU（推荐，正在部署）
**镜像**: `quincyqiang/mineru:0.3-models`
**优点**:
- ✅ 现成的镜像，无需构建
- ✅ 包含所有模型，开箱即用
- ✅ 单容器部署，配置简单
- ✅ 8GB+ 模型已预装
- ✅ 适合快速验证功能

**缺点**:
- ⚠️ 功能相对基础
- ⚠️ 没有 Web 界面
- ⚠️ 没有任务队列

**部署命令**:
```bash
cd /Users/alwan/FieldMind-Rebuild/mineru-service
./start-simple.sh
```

### 方案 B：完整版 Tianshu（企业级）
**镜像**: 需要自行构建
**优点**:
- ✅ 完整的 Web 管理界面
- ✅ 任务队列和进度追踪
- ✅ 对象存储集成（RustFS）
- ✅ 大文件自动拆分
- ✅ JWT 认证系统
- ✅ 多服务架构（Backend + Worker + Frontend）

**缺点**:
- ❌ 需要构建镜像（遇到网络问题）
- ❌ 配置复杂
- ❌ 资源消耗较大

**部署命令**:
```bash
cd /Users/alwan/FieldMind-Rebuild/mineru-tianshu
bash scripts/build-local-cpu.sh  # 需要解决网络问题
bash scripts/start-local-cpu.sh
```

## 🚀 下一步操作

### 等待镜像下载完成
```bash
# 检查下载进度
docker images | grep mineru

# 当看到以下输出时，表示下载完成：
# quincyqiang/mineru   0.3-models   ...   8.5GB   ...
```

### 启动服务
```bash
cd /Users/alwan/FieldMind-Rebuild/mineru-service
./start-simple.sh
```

### 验证服务
```bash
# 健康检查
curl http://localhost:8765/health

# 测试解析（如果 API 支持）
curl -X POST http://localhost:8765/parse \
  -F "file=@test.pdf"
```

### 更新 FieldMind 配置
```bash
# 1. 确认 MinerU URL 正确
# 文件: fieldmind-backend/app/services/document_parser.py
# 当前配置: http://localhost:8765 ✅ 正确

# 2. 运行集成测试
cd /Users/alwan/FieldMind-Rebuild/mineru-service
python3 test_integration.py
```

## 📝 配置文件

### 当前 docker-compose.yml
```yaml
services:
  mineru:
    image: quincyqiang/mineru:0.3-models
    container_name: fieldmind-mineru
    ports:
      - "8765:8080"
    volumes:
      - ./data:/app/data
      - ./models:/root/.cache
      - ./output:/app/output
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      - fieldmind-network
```

### MinerU Client 配置
```python
# mineru-service/mineru_client.py
class MinerUClient:
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
```

### FieldMind Parser 配置
```python
# fieldmind-backend/app/services/document_parser.py
def __init__(self, use_mineru: bool = True, mineru_url: str = "http://localhost:8765"):
    if use_mineru and MINERU_AVAILABLE:
        self.mineru_client = MinerUClient(mineru_url)
```

## 🔍 故障排查

### 镜像下载慢
- **原因**: Docker Hub 连接超时
- **解决**: 配置国内镜像加速
  ```
  Docker Desktop → Settings → Docker Engine
  添加 registry-mirrors
  ```

### 服务无法启动
```bash
# 查看详细日志
docker-compose logs -f

# 检查端口占用
lsof -i :8765

# 重启 Docker
Docker Desktop → Restart
```

### API 调用失败
```bash
# 检查容器状态
docker ps | grep mineru

# 检查容器日志
docker logs fieldmind-mineru

# 进入容器调试
docker exec -it fieldmind-mineru bash
```

## 📚 相关资源

- [quincyqiang/mineru Docker Hub](https://hub.docker.com/r/quincyqiang/mineru)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [Tianshu GitHub](https://github.com/magicyuan876/mineru-tianshu)
- [FieldMind 集成报告](MINERU_INTEGRATION_REPORT.md)
- [Tianshu 集成指南](MINERU_TIANSHU_INTEGRATION.md)

## ⏱️ 时间线

| 时间 | 事件 | 状态 |
|------|------|------|
| 13:35 | 首次尝试启动（镜像不存在） | ❌ |
| 13:36 | 启动 Docker Desktop | ✅ |
| 13:36 | 尝试使用 opendatalab/mineru | ❌ |
| 13:40 | 克隆 mineru-tianshu 仓库 | ✅ |
| 13:41 | 开始构建 Tianshu CPU 镜像 | ❌ 网络超时 |
| 13:45 | 切换到 quincyqiang/mineru:0.3-models | 🔄 |
| 13:45+ | 正在下载镜像... | 🔄 |

---

**当前任务**: 等待 `quincyqiang/mineru:0.3-models` 镜像下载完成

**预计完成**: 5-10 分钟

**下一步**: 启动服务 → 健康检查 → 集成测试
