# FieldMind 实际可用性问题清单

## 🔴 严重问题

### 1. 数据库连接问题
**错误**: `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`
**影响**: 数据库健康检查失败
**位置**: `app/main.py`, `app/api/monitoring.py`
**修复**: 使用 `text()` 包装SQL语句

### 2. AI功能依赖问题
**错误**: 
- `ANTHROPIC_API_KEY` 未配置
- HuggingFace模型下载失败
**影响**: AI对话、记忆功能无法使用
**修复**: 
- 添加降级方案（无AI key时禁用功能）
- 提供本地模型配置

### 3. FastAPI废弃警告
**错误**: `on_event` 已废弃
**影响**: 代码将在未来版本失效
**位置**: `app/main.py`
**修复**: 使用 `lifespan` 事件处理器

## 🟡 中等问题

### 4. ChromaDB telemetry错误
**错误**: `capture() takes 1 positional argument but 3 were given`
**影响**: 日志污染，但不影响功能
**修复**: 禁用telemetry或升级ChromaDB

### 5. 向量搜索降级
**警告**: ChromaDB不支持关键词搜索
**影响**: 只能语义搜索，无混合搜索
**修复**: 实现独立的TF-IDF搜索

### 6. 依赖版本问题
**错误**: LangChain组件已废弃
**影响**: 未来版本不兼容
**修复**: 迁移到新的langchain-huggingface包

## 🟢 轻微问题

### 7. 未实现的核心功能
**问题**: 
- 文档上传后是否真正处理？
- 分析是否真正生成结果？
- 数据是否真正持久化？
**修复**: 需要端到端测试验证

### 8. 配置缺失
**问题**:
- `.env` 文件不完整
- API keys未配置
- 数据库路径可能不存在
**修复**: 提供完整的默认配置

---

## 📋 修复计划

### 优先级1（立即修复）
1. ✅ 修复数据库SQL语法问题
2. ✅ 修复FastAPI废弃警告
3. ✅ 添加配置检查和友好提示
4. ✅ 确保基础功能可用（无AI key）

### 优先级2（重要）
5. ✅ 实现真实的TF-IDF搜索（不依赖向量数据库）
6. ✅ 文档处理流程验证
7. ✅ 数据持久化验证
8. ✅ 端到端功能测试

### 优先级3（改进）
9. ⏭️ 升级依赖包
10. ⏭️ 禁用telemetry
11. ⏭️ 性能优化

---

## 🔧 立即开始修复

让我开始修复这些问题...
