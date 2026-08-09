# CI/CD Pipeline 集成指南

> **版本**: 1.0  
> **更新时间**: 2026-08-01  
> **适用项目**: FieldMind 知识脉络分析系统

---

## 📖 目录

1. [系统概述](#系统概述)
2. [GitHub Actions工作流](#github-actions工作流)
3. [Docker集成](#docker集成)
4. [本地测试](#本地测试)
5. [部署策略](#部署策略)
6. [监控和告警](#监控和告警)
7. [故障排除](#故障排除)

---

## 系统概述

### CI/CD Pipeline架构

```
开发者推送代码
    ↓
GitHub Actions触发
    ↓
┌─────────────────────────────────────┐
│  Stage 1: 代码质量检查              │
│  • Black (代码格式)                 │
│  • Flake8 (代码规范)                │
│  • MyPy (类型检查)                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Stage 2: 单元测试                  │
│  • PostgreSQL服务                   │
│  • Redis服务                        │
│  • PyTest测试套件                   │
│  • 代码覆盖率报告                   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Stage 3: 安全扫描                  │
│  • Safety (依赖漏洞)                │
│  • Bandit (代码安全)                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Stage 4: Docker构建                │
│  • 构建后端镜像                     │
│  • 推送到GHCR                       │
│  • 多架构支持                       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Stage 5: 自动部署                  │
│  • develop → Staging环境            │
│  • main → Production环境            │
└─────────────────────────────────────┘
```

### 文件结构

```
.github/
└── workflows/
    ├── ci-cd.yml           # 主CI/CD流程
    ├── release.yml         # 版本发布流程
    └── nightly-tests.yml   # 夜间全量测试

docker-compose.prod.yml     # 生产环境Docker配置
Dockerfile.backend          # 后端多阶段构建
.gitignore                  # Git忽略配置
test_ci_cd.sh              # 本地CI/CD测试脚本
```

---

## GitHub Actions工作流

### 1. 主CI/CD流程 (ci-cd.yml)

**触发条件**:
- `push` 到 `main` 或 `develop` 分支
- 向 `main` 或 `develop` 提交 Pull Request
- 手动触发 (`workflow_dispatch`)

**5个主要任务**:

#### Job 1: 代码质量检查 (lint)

```yaml
- Black格式检查 (--line-length 100)
- Flake8代码规范 (E203, W503忽略)
- MyPy类型检查 (忽略缺失导入)
```

**本地运行**:
```bash
black --check app/ tests/ --line-length 100
flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
mypy app/ --ignore-missing-imports
```

#### Job 2: 单元测试 (test)

**服务依赖**:
- PostgreSQL 15
- Redis 7

**执行步骤**:
1. 安装FFmpeg系统依赖
2. 安装Python依赖
3. 创建测试环境配置
4. 运行pytest + 代码覆盖率
5. 上传覆盖率到Codecov

**本地运行**:
```bash
TESTING=true pytest tests/ -v --cov=app --cov-report=xml
```

#### Job 3: 安全扫描 (security)

```bash
# 依赖漏洞扫描
safety check --json

# 代码安全扫描
bandit -r app/ -f json
```

#### Job 4: Docker构建 (build-docker)

**条件**: 仅在 `push` 事件触发

**执行步骤**:
1. 设置Docker Buildx
2. 登录GitHub Container Registry
3. 提取镜像元数据（标签）
4. 构建并推送镜像
5. 使用GitHub Actions缓存加速

**镜像标签策略**:
```
ghcr.io/<org>/<repo>:main         # main分支
ghcr.io/<org>/<repo>:develop      # develop分支
ghcr.io/<org>/<repo>:pr-123       # PR编号
ghcr.io/<org>/<repo>:sha-abc123   # Git SHA
```

#### Job 5: 自动部署

**Staging部署** (develop分支):
```yaml
environment: staging
url: https://staging.fieldmind.example.com
```

**Production部署** (main分支):
```yaml
environment: production
url: https://fieldmind.example.com
```

---

### 2. 版本发布流程 (release.yml)

**触发条件**: 推送版本标签 `v*.*.*`

**执行步骤**:
1. 从Git历史生成Changelog
2. 创建GitHub Release
3. 构建并推送带版本号的Docker镜像
4. 同时更新 `latest` 标签

**使用示例**:
```bash
# 创建发布标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# GitHub Actions自动执行:
# 1. 创建Release页面
# 2. 生成Changelog
# 3. 构建Docker镜像: ghcr.io/org/repo:v1.0.0
```

---

### 3. 夜间测试流程 (nightly-tests.yml)

**触发时间**: 每天UTC时间02:00 (北京时间10:00)

**测试矩阵**:
```yaml
python-version: ['3.9', '3.10', '3.11']
```

**服务依赖**:
- PostgreSQL 15
- Redis 7
- Neo4j 5 Community

**特点**:
- 全量测试覆盖
- 多Python版本兼容性
- 完整服务栈测试
- 30分钟超时保护

---

## Docker集成

### 多阶段构建 (Dockerfile.backend)

**Stage 1: Builder**
```dockerfile
FROM python:3.11-slim AS builder

# 安装编译依赖
RUN apt-get install gcc g++ make libpq-dev

# 安装Python包到用户目录
RUN pip install --user -r requirements.txt
```

**Stage 2: Runtime**
```dockerfile
FROM python:3.11-slim

# 只安装运行时依赖
RUN apt-get install ffmpeg libpq5 curl

# 复制已编译的Python包
COPY --from=builder /root/.local /home/fieldmind/.local

# 非root用户运行
USER fieldmind

# 健康检查
HEALTHCHECK CMD curl -f http://localhost:8000/health
```

**优势**:
- ✅ 镜像体积减少50%+
- ✅ 构建缓存优化
- ✅ 安全性提升（非root）
- ✅ 健康检查自动化

### 生产环境部署 (docker-compose.prod.yml)

**5个服务**:

1. **postgres**: PostgreSQL 15数据库
2. **redis**: Redis 7缓存
3. **neo4j**: Neo4j 5图数据库
4. **backend**: FastAPI应用
5. **celery-worker**: 异步任务处理

**启动命令**:
```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 停止服务
docker-compose -f docker-compose.prod.yml down
```

**健康检查**:
```bash
# 所有服务的健康状态
docker-compose -f docker-compose.prod.yml ps

# 预期输出:
# fieldmind-postgres   healthy
# fieldmind-redis      healthy
# fieldmind-neo4j      healthy
# fieldmind-backend    healthy
```

---

## 本地测试

### 使用test_ci_cd.sh脚本

**功能**: 在本地模拟CI/CD流程

```bash
# 执行本地CI/CD测试
./test_ci_cd.sh
```

**测试步骤**:

1. **代码质量检查**
   - Black格式验证
   - Flake8规范检查
   - MyPy类型检查

2. **单元测试**
   - PyTest测试套件
   - 代码覆盖率报告

3. **安全扫描**
   - Safety依赖检查
   - Bandit安全扫描

4. **Docker构建测试**
   - 构建后端镜像
   - 验证构建成功

5. **配置文件验证**
   - 检查必需文件存在
   - 验证配置完整性

**输出示例**:
```
============================================================
FieldMind CI/CD Local Testing
============================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Code Quality Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TEST] Black (code formatting)
✓ PASSED

[TEST] Flake8 (linting)
✓ PASSED

[TEST] MyPy (type checking)
✓ PASSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total tests: 8
Passed: 8
Failed: 0

✓ All tests passed!
Ready for CI/CD pipeline
```

### 手动测试命令

```bash
# 1. 格式化代码
black app/ tests/ --line-length 100

# 2. 检查代码质量
flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503

# 3. 运行测试
TESTING=true pytest tests/ -v --cov=app

# 4. 安全扫描
safety check
bandit -r app/

# 5. 构建Docker镜像
docker build -f Dockerfile.backend -t fieldmind:test .

# 6. 测试Docker镜像
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./test.db \
  fieldmind:test
```

---

## 部署策略

### 分支策略

```
main (生产分支)
  ↑
  └─ develop (开发分支)
       ↑
       └─ feature/* (功能分支)
```

**工作流程**:

1. **功能开发**
   ```bash
   git checkout -b feature/new-feature develop
   # 开发功能...
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **创建PR到develop**
   - CI/CD自动运行测试
   - 代码审查
   - 合并到develop

3. **自动部署到Staging**
   ```bash
   # develop分支合并后自动触发
   # → Staging环境部署
   # URL: https://staging.fieldmind.example.com
   ```

4. **发布到生产**
   ```bash
   # 创建PR: develop → main
   # 审查通过后合并
   
   # 创建版本标签
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   
   # 自动触发:
   # → Production环境部署
   # → GitHub Release创建
   ```

### 环境配置

#### Staging环境

```yaml
# .env.staging
ENVIRONMENT=staging
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-staging-key
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Production环境

```yaml
# .env.production
ENVIRONMENT=production
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-production-key
DEBUG=false
LOG_LEVEL=INFO
```

### GitHub Secrets配置

在GitHub仓库设置中配置以下Secrets:

```
# 必需的Secrets
ANTHROPIC_API_KEY          # Claude API密钥
SECRET_KEY                 # 应用密钥
JWT_SECRET_KEY             # JWT密钥
POSTGRES_PASSWORD          # 数据库密码
NEO4J_PASSWORD             # Neo4j密码

# 可选的Secrets
CODECOV_TOKEN              # Codecov上传令牌
SLACK_WEBHOOK_URL          # Slack通知
```

**配置步骤**:
1. 访问: `https://github.com/<org>/<repo>/settings/secrets/actions`
2. 点击 "New repository secret"
3. 添加Name和Value
4. 保存

---

## 监控和告警

### 健康检查端点

```bash
# 应用健康检查
curl http://localhost:8000/health

# 预期响应:
{
  "status": "healthy",
  "database": "connected",
  "vector_db": "connected",
  "graph_db": "connected"
}
```

### Docker健康检查

```bash
# 检查容器健康状态
docker ps --filter health=healthy

# 查看健康检查日志
docker inspect fieldmind-backend | jq '.[0].State.Health'
```

### 日志监控

```bash
# 查看应用日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 查看Celery日志
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# 查看数据库日志
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### GitHub Actions监控

**查看工作流运行状态**:
```
https://github.com/<org>/<repo>/actions
```

**徽章显示**:
```markdown
![CI/CD](https://github.com/<org>/<repo>/actions/workflows/ci-cd.yml/badge.svg)
```

---

## 故障排除

### 问题1: 测试失败

**症状**: 单元测试在CI中失败，本地正常

**解决方案**:
```bash
# 1. 检查环境差异
cat .github/workflows/ci-cd.yml | grep TESTING

# 2. 使用相同环境变量本地测试
TESTING=true DATABASE_URL=postgresql://... pytest tests/

# 3. 检查服务依赖
docker-compose up postgres redis -d
pytest tests/
```

### 问题2: Docker构建超时

**症状**: Docker构建超过10分钟

**解决方案**:
```bash
# 1. 优化Dockerfile缓存
# 将不变的层（依赖安装）放在前面

# 2. 使用.dockerignore
cat > .dockerignore << EOF
.git
__pycache__
*.pyc
tests/
.env
data/
logs/
EOF

# 3. 启用BuildKit
export DOCKER_BUILDKIT=1
docker build -f Dockerfile.backend .
```

### 问题3: 部署失败

**症状**: 部署任务显示成功，但服务无法访问

**排查步骤**:
```bash
# 1. 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 2. 查看容器日志
docker-compose -f docker-compose.prod.yml logs backend

# 3. 测试健康检查
curl http://localhost:8000/health

# 4. 检查环境变量
docker exec fieldmind-backend env | grep DATABASE_URL

# 5. 进入容器调试
docker exec -it fieldmind-backend bash
```

### 问题4: 权限错误

**症状**: 容器内无法写入文件

**解决方案**:
```bash
# 1. 检查目录权限
docker exec fieldmind-backend ls -la /app/logs

# 2. 修复权限
docker-compose -f docker-compose.prod.yml down
chown -R 1000:1000 ./logs ./uploads ./data
docker-compose -f docker-compose.prod.yml up -d

# 3. 验证非root用户
docker exec fieldmind-backend whoami
# 输出: fieldmind
```

### 问题5: GitHub Actions配额不足

**症状**: 工作流无法启动

**解决方案**:
```bash
# 1. 检查配额使用
# 访问: https://github.com/settings/billing

# 2. 优化工作流
# - 减少矩阵维度
# - 合并相似任务
# - 使用条件执行

# 3. 使用自托管Runner
# 在自己的服务器上运行Actions
```

---

## 最佳实践

### 1. 提交前检查

```bash
# 使用pre-commit钩子
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
./test_ci_cd.sh || exit 1
EOF

chmod +x .git/hooks/pre-commit
```

### 2. 分支保护规则

在GitHub设置中配置:
- ✅ Require pull request reviews (至少1个审批)
- ✅ Require status checks to pass (CI必须通过)
- ✅ Require branches to be up to date
- ✅ Include administrators

### 3. 代码覆盖率要求

```yaml
# .github/workflows/ci-cd.yml
- name: Check coverage threshold
  run: |
    coverage report --fail-under=80
```

### 4. 安全扫描强制

```yaml
# 安全扫描失败则阻止部署
security:
  steps:
    - name: Run safety check
      run: safety check --json
      # 移除 continue-on-error: true
```

### 5. 自动回滚

```bash
# 部署脚本中添加健康检查
deploy_and_verify() {
    docker-compose up -d
    sleep 10
    
    if ! curl -f http://localhost:8000/health; then
        echo "Health check failed, rolling back..."
        docker-compose down
        docker-compose up -d --force-recreate
        exit 1
    fi
}
```

---

## 总结

### 交付成果

✅ **5个工作流文件**:
- `.github/workflows/ci-cd.yml` (主流程)
- `.github/workflows/release.yml` (发布)
- `.github/workflows/nightly-tests.yml` (夜间测试)

✅ **Docker配置**:
- `Dockerfile.backend` (多阶段构建)
- `docker-compose.prod.yml` (生产环境)
- `.dockerignore` (构建优化)

✅ **测试工具**:
- `test_ci_cd.sh` (本地CI/CD测试)

✅ **配置文件**:
- `.gitignore` (Git忽略规则)

✅ **完整文档**:
- 架构说明
- 使用指南
- 故障排除
- 最佳实践

### 系统特性

- 🚀 **自动化**: Push即触发完整CI/CD流程
- 🔒 **安全**: 多层安全扫描 + 非root运行
- 📊 **监控**: 健康检查 + 日志收集
- 🎯 **高效**: 多阶段构建 + 缓存优化
- 🔄 **灵活**: 多环境部署 + 自动回滚

### 下一步建议

1. **配置GitHub Secrets**
2. **设置分支保护规则**
3. **运行test_ci_cd.sh验证**
4. **推送代码触发首次CI/CD**
5. **配置通知集成（Slack/Email）**

---

**文档版本**: 1.0  
**最后更新**: 2026-08-01  
**维护者**: FieldMind开发团队
