# 配置系统迁移指南

## 📋 迁移策略

**原则**: 逐步迁移，保证每一步都可用，不破坏现有功能。

---

## 🎯 迁移阶段

### 阶段1: 建立新配置系统（✅ 已完成）
- [x] 创建配置模块
- [x] 定义常量
- [x] 建立日志系统
- [x] 创建环境配置文件

### 阶段2: 迁移现有服务（下一步）
1. 迁移multimodal_processor.py
2. 迁移cross_document_entity_resolver.py
3. 迁移document_relation_discovery.py
4. 迁移document_network_builder.py
5. 迁移workflow_chain.py

### 阶段3: 迁移数据库层
1. 更新database.py使用新配置
2. 更新连接池配置
3. 添加健康检查

### 阶段4: 迁移API层
1. 更新路由使用新错误码
2. 统一错误响应格式
3. 添加请求日志

### 阶段5: 清理旧配置
1. 删除旧的config.py
2. 更新所有导入
3. 验证完整性

---

## 📖 迁移示例

### 示例1: 迁移硬编码常量

**旧代码** (multimodal_processor.py):
```python
logger = logging.getLogger(__name__)

class MultiModalProcessor:
    def process_any_format(self, file_path: str, file_type: str):
        # 硬编码的超时
        timeout = 600
        
        # 硬编码的错误信息
        raise Exception("处理失败")
```

**新代码**:
```python
from app.core.config import get_logger
from app.core.config.constants import ErrorCode, Limits

logger = get_logger(__name__)

class MultiModalProcessor:
    def process_any_format(self, file_path: str, file_type: str):
        # 使用配置的超时
        timeout = Limits.FILE_PROCESSING_TIMEOUT
        
        # 使用统一错误码
        raise FileProcessingError(
            code=ErrorCode.FILE_PROCESSING_FAILED,
            message="文件处理失败"
        )
```

### 示例2: 迁移日志

**旧代码**:
```python
logger.info(f"处理文档: {doc_id}")
logger.error(f"处理失败: {str(e)}")
```

**新代码**:
```python
from app.core.config.logging_config import LogContext, log_error

# 带上下文的日志
with LogContext(document_id=doc_id, user_id=user_id):
    logger.info("开始处理文档")
    
    try:
        # 处理逻辑
        pass
    except Exception as e:
        log_error(logger, "文档处理失败", error=e, doc_id=doc_id)
```

### 示例3: 迁移配置值

**旧代码**:
```python
similarity_threshold = 0.85
redis_ttl = 3600
```

**新代码**:
```python
from app.core.config import settings

similarity_threshold = settings.processing.similarity_threshold
redis_ttl = settings.cache.ttl_medium  # 或 Limits.CACHE_TTL_MEDIUM
```

### 示例4: 迁移错误处理

**旧代码**:
```python
try:
    process_file(file_path)
except Exception as e:
    return {"error": "处理失败"}
```

**新代码**:
```python
from app.core.config.constants import ErrorCode
from app.core.exceptions import FileProcessingError

try:
    process_file(file_path)
except FileNotFoundError:
    raise FileProcessingError(
        code=ErrorCode.FILE_NOT_FOUND,
        message=f"文件不存在: {file_path}"
    )
except Exception as e:
    log_error(logger, "文件处理失败", error=e)
    raise FileProcessingError(
        code=ErrorCode.FILE_PROCESSING_FAILED,
        message=str(e)
    )
```

---

## 🔧 迁移检查清单

### 服务文件迁移检查
- [ ] 替换 `logging.getLogger` → `get_logger`
- [ ] 替换硬编码常量 → `Limits.*` 或 `Defaults.*`
- [ ] 添加错误码 → `ErrorCode.*`
- [ ] 添加日志上下文 → `LogContext`
- [ ] 使用配置值 → `settings.*`
- [ ] 添加类型提示
- [ ] 添加文档字符串

### API路由迁移检查
- [ ] 统一错误响应格式
- [ ] 添加请求ID追踪
- [ ] 使用ErrorCode枚举
- [ ] 添加性能日志
- [ ] 验证输入参数

### 数据库层迁移检查
- [ ] 使用连接池配置
- [ ] 添加查询超时
- [ ] 添加健康检查
- [ ] 添加重试机制
- [ ] 记录慢查询

---

## 🚀 快速迁移脚本

创建一个辅助脚本来查找需要迁移的代码：

```bash
#!/bin/bash
# find_hardcoded.sh - 查找硬编码常量

echo "🔍 查找硬编码的相似度阈值..."
grep -rn "0.85\|0.70\|0.95" app/services/ --include="*.py"

echo "\n🔍 查找硬编码的超时值..."
grep -rn "timeout.*=.*[0-9]" app/services/ --include="*.py"

echo "\n🔍 查找旧的日志导入..."
grep -rn "logging.getLogger" app/services/ --include="*.py"

echo "\n🔍 查找硬编码的错误信息..."
grep -rn 'raise Exception\|raise ValueError' app/services/ --include="*.py"
```

---

## 📊 迁移优先级

### 高优先级（影响稳定性）
1. **database.py** - 连接池配置
2. **workflow_chain.py** - 处理链核心逻辑
3. **multimodal_processor.py** - 文件处理入口

### 中优先级（改善可维护性）
4. **document_network_builder.py** - 网络构建
5. **cross_document_entity_resolver.py** - 实体消歧
6. **knowledge_graph_service.py** - 知识图谱

### 低优先级（渐进式改善）
7. API路由层
8. 工具函数
9. 测试代码

---

## ⚠️ 迁移注意事项

### 1. 向后兼容
```python
# 保留旧的导入路径（临时）
# 在app/config.py添加：
from app.core.config import settings
__all__ = ['settings']
```

### 2. 测试每一步
```bash
# 迁移一个文件后立即测试
python3 -c "from app.services.multimodal_processor import MultiModalProcessor; print('✅ 导入成功')"
```

### 3. 渐进式迁移
- 不要一次性改所有文件
- 每次迁移1-2个服务
- 测试通过后再继续

### 4. 保留旧配置
- 不要立即删除旧的config.py
- 让新旧配置共存一段时间
- 确保所有功能正常后再清理

---

## 🎯 下一步行动

**立即开始**: 迁移 `multimodal_processor.py`

这是文件处理的核心服务，迁移后可以验证：
1. 新日志系统是否正常
2. 配置值是否正确读取
3. 错误处理是否完善
4. 超时配置是否生效

准备好开始迁移第一个服务吗？
