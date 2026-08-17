# FieldMind 全面审计和修复计划

## 目标
检查并修复整个程序的：
1. 编程错误和逻辑问题
2. 前后端连接问题
3. 多个系统冲突和打架
4. 影响正常使用的问题

## 审计范围

### 1. 后端问题排查
- **重复路由冲突** - main.py 注册了多个版本的相同功能
- **数据库连接和初始化**
- **API 响应格式一致性**
- **错误处理和日志**
- **服务依赖完整性** (Neo4j, Redis, ChromaDB, PostgreSQL)
- **导入错误和循环依赖**

### 2. 前端问题排查
- **API 调用端点正确性**
- **路由配置**
- **状态管理和上下文**
- **组件通信**
- **错误边界处理**

### 3. 前后端连接问题
- **CORS 配置**
- **API 端点匹配** (前端调用的端点是否存在)
- **请求/响应数据结构一致性**
- **认证流程完整性**

### 4. 系统冲突检查
- **重复功能模块** (v1 vs 新版本)
- **数据库模型冲突**
- **配置文件冲突**
- **端口占用**

## 执行步骤

### Phase 1: 后端代码审计 (高优先级)
1. 检查 main.py 路由注册冲突
2. 检查配置文件完整性
3. 测试数据库连接
4. 检查 API 端点实现
5. 查找 Python 语法/逻辑错误

### Phase 2: 前端代码审计
1. 检查 API 服务配置
2. 检查路由配置
3. 检查组件导入
4. 查找 TypeScript 错误

### Phase 3: 集成测试
1. 启动后端服务
2. 测试关键 API 端点
3. 前后端联调
4. 修复连接问题

### Phase 4: 修复和验证
1. 修复发现的问题
2. 重新测试
3. 文档更新

## 需要检查的文件

### 后端关键文件
- `fieldmind-backend/app/main.py` - 路由注册
- `fieldmind-backend/app/config.py` - 配置
- `fieldmind-backend/app/core/database.py` - 数据库
- `fieldmind-backend/app/api/**/*.py` - API 端点
- `fieldmind-backend/requirements.txt` - 依赖

### 前端关键文件
- `fieldmind-web/src/main.tsx` - 入口
- `fieldmind-web/src/App.tsx` - 路由
- `fieldmind-web/src/contexts/AppContext.tsx` - 状态
- `fieldmind-web/src/pages/**/*.tsx` - 页面组件
- `fieldmind-web/package.json` - 依赖

## 预期问题清单

### 已发现的潜在问题
1. **路由重复注册** - auth.router 注册了两次
2. **多版本 API 共存** - v1 和新版本可能冲突
3. **项目管理系统重复** - projects vs new_projects
4. **知识图谱多版本** - kg, kg_new, v2, v3 四个版本
5. **文档处理重复** - documents, new_documents, document_processing, document_processing_v2

### 需要验证的服务
- PostgreSQL 数据库
- Neo4j 图数据库
- Redis 缓存
- ChromaDB 向量数据库
- Celery 任务队列

## 修复策略

1. **保守修复** - 不删除现有代码，只修复错误
2. **标记弃用** - 对重复功能添加注释说明哪个是主版本
3. **统一接口** - 确保同一功能的不同版本返回格式一致
4. **渐进式清理** - 先修复致命错误，再优化架构
