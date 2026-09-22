# FieldMind 系统诊断报告
生成时间: 2026-09-15

## 🎯 执行摘要

检测到 **3 个关键问题**，其中 **1 个已修复**，**2 个待处理**。

---

## ✅ 已修复问题

### 1. 知识图谱核心表缺失 ✓
**状态**: 已完全修复  
**问题**: 数据库中完全缺失 6 个知识图谱核心表  
**影响**: 知识图谱功能完全不可用  
**修复方式**: 使用 SQLAlchemy `Base.metadata.create_all()` 自动创建  

**创建的表**:
- ✓ `dirty_channel_documents` - 9 字段
- ✓ `clean_channel_entities` - 10 字段 (含 is_manual, pipeline_step)
- ✓ `clean_channel_events` - 9 字段 (含 is_manual, pipeline_step)
- ✓ `clean_channel_relations` - 10 字段 (含 is_manual, pipeline_step)
- ✓ `nine_step_pipeline_status` - 14 字段
- ✓ `unified_processing_routes` - 11 字段

**验证结果**: 所有表已创建，字段完整，包含手动添加所需的 `is_manual` 和 `pipeline_step` 字段

---

## ⚠️ 待修复问题

### 2. 后端端口配置不匹配 ❌
**严重程度**: 高 - 导致前端无法连接后端  

**问题详情**:
- 后端实际运行: `127.0.0.1:8000`
- 前端配置期望: `127.0.0.1:8013`
- 前端代码默认: `localhost:8000` ([api.ts:4](../frontend/src/services/api.ts#L4))

**测试结果**:
```bash
# 8000 端口 - 后端实际运行
curl http://127.0.0.1:8000/api/monitoring/health
✓ 返回正常

# 8013 端口 - 前端期望
curl http://127.0.0.1:8013/api/monitoring/health
✓ 返回正常 (可能有反向代理)
```

**发现**: 两个端口都能访问，说明可能存在 Nginx 反向代理从 8013 → 8000

**建议修复**:
1. 检查 Nginx/代理配置
2. 统一使用一个端口 (建议 8000)
3. 或在前端环境变量中明确指定 8013

---

### 3. 前端服务健康检查路径错误（已修复但需验证）⚠️
**严重程度**: 中 - 已修复代码，需重启前端验证

**修复的文件**:
- [fieldmind.ts:313](../frontend/src/services/fieldmind.ts#L313) - 已改为 `/api/monitoring/health`

**待验证**: 前端是否已重启加载新代码

---

## 📊 系统当前状态

### 数据库
- **类型**: SQLite
- **路径**: `/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db`
- **总表数**: 109 (103 原有 + 6 新增)
- **知识图谱表**: ✓ 完整

### 后端服务
- **进程**: uvicorn (PID 95515)
- **监听**: 127.0.0.1:8000
- **健康状态**: ✓ Healthy
- **API**: ✓ 正常响应

### 前端服务
- **API 基础地址**: `localhost:8000` (默认) 或 环境变量配置
- **期望后端**: `127.0.0.1:8013`
- **状态**: 需要检查环境变量配置

---

## 🔧 建议的后续操作

### 立即操作
1. **检查前端环境变量配置**
   ```bash
   cd frontend
   cat .env .env.local .env.development
   ```

2. **统一端口配置** (二选一)
   - 方案 A: 修改前端环境变量指向 8000
   - 方案 B: 检查 Nginx 配置，确认 8013 → 8000 代理正常

3. **重启前端服务**
   ```bash
   cd frontend
   npm run dev
   ```

4. **验证系统检验页面**
   - 打开浏览器访问系统检验页面
   - 确认健康检查显示正常

### 功能测试
5. **测试知识图谱手动添加**
   - 尝试手动添加实体
   - 尝试手动添加关系
   - 检查数据库中 `is_manual=true` 和 `pipeline_step=0`

---

## 📝 错误日志分析

从 `logs/error.log` 发现的历史问题:

1. **SQLite NOW() 函数错误** (8月22日)
   - 血缘追踪使用了 MySQL 特有的 `NOW()` 函数
   - SQLite 应使用 `CURRENT_TIMESTAMP`
   - 位置: [lineage_tracker.py:313](../backend/src/app/services/lineage_tracker.py#L313)

2. **结构化输出重试失败** (8月30日)
   - AI 结构化输出验证失败
   - 达到最大重试次数
   - 位置: [client.py:119](../backend/src/app/core/structured_output/client.py#L119)

---

## 📈 数据完整性检查

### ✓ 模型与数据库同步状态
- 模型定义: 6 个知识图谱表
- 数据库实际: 6 个知识图谱表
- 字段完整性: ✓ 所有必需字段已创建

### ✓ 迁移脚本状态
- `001_initial_schema.sql` - 初始化脚本 (已被 SQLAlchemy 替代)
- `002_add_manual_fields.sql` - 字段添加脚本 (已被 SQLAlchemy 包含)

---

## 🎯 总结

**已完成**:
- ✓ 知识图谱数据库表创建
- ✓ 手动添加字段 (is_manual, pipeline_step) 已包含
- ✓ 前端服务代码健康检查路径已修复

**待处理**:
- ⚠️ 确认前端端口配置和环境变量
- ⚠️ 重启前端服务验证修复
- ⚠️ 端到端功能测试

**建议优先级**:
1. **P0**: 检查并统一端口配置
2. **P0**: 重启前端验证健康检查
3. **P1**: 测试知识图谱手动添加功能
4. **P2**: 修复历史遗留的 SQLite NOW() 问题
