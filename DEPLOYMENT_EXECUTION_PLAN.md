# FieldMind 部署与测试执行计划

**创建时间**: 2026-09-09  
**状态**: 准备执行

---

## 🔍 当前问题诊断

### 发现的问题
1. **模块导入错误**: `app.config.business_database` 模块不存在
2. **后端服务无法启动**: 依赖问题导致启动失败

### 根本原因
- 某些 API 路由引用了不存在的配置模块
- 可能是开发过程中的临时导入未清理

---

## 🛠️ 解决方案

### 方案 A: 快速修复（推荐）

**步骤 1: 检查并修复导入问题**

```bash
# 查找所有问题导入
cd /Users/alwan/FieldMind/backend/src
grep -r "from app.config.business_database" app/

# 选项 1: 注释掉问题导入
# 选项 2: 创建缺失的模块
# 选项 3: 修改为正确的导入路径
```

**步骤 2: 创建最小启动配置**

创建 `backend/minimal_start.py`:
```python
"""
最小化启动脚本 - 仅加载核心功能
跳过有问题的模块
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FieldMind API - Minimal")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": "minimal"}

# 仅加载核心 API
from app.api.v1 import (
    projects,
    documents,
    chunks,
    # 跳过有问题的模块
)

app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 方案 B: Docker 隔离部署（更稳定）

使用 Docker Compose 完全隔离环境，避免本地依赖问题。

---

## 📋 执行步骤

### 阶段 1: 问题修复（30分钟）

**步骤 1.1: 定位问题文件**
```bash
cd /Users/alwan/FieldMind/backend/src
find app/api/v1 -name "*.py" -exec grep -l "business_database" {} \;
```

**步骤 1.2: 修复导入**
- 选项A: 注释掉 `business_analysis.py` 中的问题导入
- 选项B: 创建空的 `app/config/business_database.py` 模块
- 选项C: 在 `app/api/v1/__init__.py` 中排除 `business_analysis`

**步骤 1.3: 验证修复**
```bash
cd backend/src
python3 -c "from app.main import app; print('Import successful')"
```

### 阶段 2: 启动服务（10分钟）

**步骤 2.1: 启动后端**
```bash
cd backend/src
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**步骤 2.2: 验证健康检查**
```bash
curl http://localhost:8000/health
# 预期输出: {"status": "healthy"}
```

**步骤 2.3: 查看 API 文档**
```bash
# 浏览器访问
open http://localhost:8000/docs
```

### 阶段 3: 运行测试（20分钟）

**步骤 3.1: API 测试**
```bash
cd backend
python3 test_mvp_api.py
```

**步骤 3.2: 功能测试**
```bash
# 测试数据质量 API
curl -X GET "http://localhost:8000/api/v1/data-quality/overview/1"

# 测试溯源 API
curl -X POST "http://localhost:8000/api/v1/traceability/trace" \
  -H "Content-Type: application/json" \
  -d '{"conclusion_text":"测试溯源","project_id":1,"top_k":5}'

# 测试协作 API
curl -X GET "http://localhost:8000/api/v1/collaboration/projects/1/members"
```

**步骤 3.3: 前端集成测试**
```bash
# 终端 1: 后端已运行
# 终端 2: 启动前端
cd frontend/web
npm run dev

# 终端 3: 手动测试
# 浏览器访问 http://localhost:5173
# 测试所有新功能标签页
```

### 阶段 4: P2 优化准备（今天规划，明天执行）

**P2-1: 性能优化任务清单**
- [ ] 数据库索引优化
- [ ] Redis 缓存集成
- [ ] 查询优化
- [ ] 前端懒加载

**P2-2: 代码质量任务清单**
- [ ] 单元测试（目标 70%）
- [ ] 集成测试
- [ ] 代码审查
- [ ] 文档完善

**P2-3: 监控告警任务清单**
- [ ] Sentry 集成
- [ ] Prometheus 指标
- [ ] 日志聚合
- [ ] 告警配置

---

## 🚀 立即执行

### 快速修复脚本

创建 `backend/quick_fix.sh`:
```bash
#!/bin/bash
# FieldMind 快速修复脚本

echo "🔧 开始修复..."

cd /Users/alwan/FieldMind/backend/src

# 1. 备份原文件
echo "📦 备份文件..."
cp app/api/v1/__init__.py app/api/v1/__init__.py.backup

# 2. 检查问题文件
echo "🔍 检查问题导入..."
grep -n "business_database" app/api/v1/*.py

# 3. 临时排除问题模块
echo "⚠️  临时排除 business_analysis 模块..."
cat > app/api/v1/__init__.py << 'EOF'
from . import (
    projects,
    documents,
    chunks,
    analysis,
    chat,
    dashboard,
    # business_analysis,  # 临时禁用
)
EOF

# 4. 测试导入
echo "✅ 测试导入..."
python3 -c "from app.main import app; print('✅ Import successful!')" || {
    echo "❌ Import failed, restoring backup..."
    cp app/api/v1/__init__.py.backup app/api/v1/__init__.py
    exit 1
}

echo "🎉 修复完成！现在可以启动服务："
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
```

### 使用方法

```bash
# 给脚本执行权限
chmod +x backend/quick_fix.sh

# 执行修复
./backend/quick_fix.sh

# 启动服务
cd backend/src
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 测试验收标准

### 核心功能验证

**数据质量监控**
- [ ] API 返回质量评分
- [ ] 4个维度都有数值
- [ ] 数据缺口列表正常

**溯源回溯**
- [ ] 输入结论返回 chunks
- [ ] 匹配度 > 0
- [ ] 上下文加载正常

**协作权限**
- [ ] 成员列表可获取
- [ ] 邀请链接可生成
- [ ] 活动日志可查看

**知识图谱**
- [ ] 节点数据正确
- [ ] 边数据正确
- [ ] 前端可视化正常

**报告生成**
- [ ] Level 1 报告可生成
- [ ] Level 3 报告可生成
- [ ] 导出功能正常

---

## 🔄 回滚计划

如果修复失败，使用备份文件回滚：

```bash
# 回滚 API 路由
cp app/api/v1/__init__.py.backup app/api/v1/__init__.py

# 回滚其他修改（如果有）
git checkout app/api/v1/business_analysis.py

# 清理测试数据
rm -f fieldmind_test.db
```

---

## 📝 执行日志模板

```
[2026-09-09 21:30] 开始执行快速修复
[2026-09-09 21:32] ✅ 问题定位完成
[2026-09-09 21:35] ✅ 导入问题已修复
[2026-09-09 21:36] ✅ 服务启动成功
[2026-09-09 21:40] ✅ API 测试通过
[2026-09-09 21:45] ✅ 前端集成测试通过
[2026-09-09 21:50] ✅ 完整流程验证通过

状态: 所有测试通过，准备部署
```

---

## 🎯 明天的计划

### 上午 (2小时)
- P2-1 性能优化
  - 添加数据库索引
  - 集成 Redis 缓存
  - 优化慢查询

### 下午 (3小时)
- P2-2 代码质量
  - 编写单元测试
  - 代码审查和重构
  - 完善文档

### 晚上 (1小时)
- P2-3 监控告警
  - Sentry 集成
  - 基础监控配置

---

**准备好了吗？让我们开始执行！**

如果您同意这个计划，我将：
1. 创建快速修复脚本
2. 执行修复
3. 启动服务
4. 运行测试
