# FieldMind 知识蒸馏系统完整集成文档

## 概述

本文档记录了 WorkBuddy 第二大脑系统 v1.4.4 到 FieldMind Backend 的完整深度集成。

## 系统架构

### 核心模块

```
app/distillation/
├── __init__.py                # 模块入口
├── types.py                   # 数据类型定义（60+ 个类）
├── normalizer.py              # 源规范化器
├── knowledge.py               # 知识蒸馏器
├── method.py                  # 方法蒸馏器（含阶段 0-4）
├── pipeline.py                # 完整流水线
├── adapter.py                 # Adapter 编译器（TODO）
├── packager.py                # SBPACK 封装器（TODO）
└── validator.py               # 验收器（TODO）

app/models/distillation.py     # 数据库模型
app/services/distillation_service.py  # 业务服务
app/api/distillation.py        # API 端点
app/config/distillation.py     # 配置文件
```

### 数据库模型

```sql
-- 6 张表
distillation_jobs              -- 蒸馏任务
extracted_knowledge            -- 知识单元
extracted_methods              -- 方法单元
knowledge_method_relations     -- 知识-方法关系
method_method_relations        -- 方法-方法关系
production_snapshots           -- 生产快照
```

## 完整特性清单

### ✅ 已实现核心功能

1. **输入规范化层**
   - 支持文件（EPUB/PDF/DOCX/TXT/Markdown）
   - 支持 URL（网页/视频）
   - 支持音频（Whisper 转写）
   - 章节切分与字节偏移计算
   - 质量检查（缺页/乱码/OCR）

2. **知识轨生产线**
   - 8 种知识类型（概念/主张/原则/机制/论证/边界/反例）
   - 证据锚点 UTF-8 字节精确绑定
   - 双独立证据或连续论证
   - 知识单元冻结清单

3. **方法轨生产线**
   - 阶段 0：Adler 四步分析（结构/解释/批判/应用）
   - 阶段 1：五类并行提取（框架/原则/案例/反例/术语）
   - 阶段 1.5：三重验证（V1 跨域/V2 预测力/V3 独特性）
   - 阶段 2：RIA++ 六段构造（R/I/A1/A2/E/B）
   - 阶段 4：压力测试（5-10 个测试用例）
   - 方法单元冻结清单

4. **审计系统**
   - 候选覆盖与去向追踪
   - 生产者快照（输入/输出/配置/运行记录）
   - 生产审计 JSON（章节基线/候选去向/正式方法）
   - SHA-256 身份绑定

5. **数据库集成**
   - 完整的 SQLAlchemy 模型
   - 级联删除和索引优化
   - 任务状态追踪（11 个状态）
   - 进度报告

6. **API 端点**
   - POST /api/v1/distillation/upload - 上传文件蒸馏
   - POST /api/v1/distillation/url - URL 蒸馏
   - GET /api/v1/distillation/jobs - 列出任务
   - GET /api/v1/distillation/jobs/{id} - 任务状态
   - GET /api/v1/distillation/jobs/{id}/knowledge - 知识单元
   - GET /api/v1/distillation/jobs/{id}/methods - 方法单元
   - GET /api/v1/distillation/jobs/{id}/package - 下载 SBPACK
   - DELETE /api/v1/distillation/jobs/{id} - 删除任务
   - GET /api/v1/distillation/stats - 统计信息

### 🚧 待完成功能

1. **Adapter 编译器**
   - 确定性运行投影
   - 引用校验
   - ID 分配

2. **SBPACK 2.0 封装器**
   - Hashing and Sealing
   - Manifest Projection
   - 控制文件生成

3. **独立验收器**
   - 61 项跨文件检查
   - 语义验证
   - 预检报告

4. **关系建立器**
   - 方法-方法关系（前置/替代/互补/冲突）
   - 知识-方法关系（支撑/解释/矛盾）
   - Zettelkasten 链接

5. **真实的 Sub-agent 盲测**
   - 当前是模拟实现
   - 需要集成 FieldMind 的 Agent 工具

6. **用户确认机制**
   - WebSocket 实时推送
   - 前端确认界面
   - 当前是自动确认

## 使用指南

### 1. 环境配置

在 `.env` 文件中添加：

```bash
# 蒸馏系统配置
DISTILLATION_OUTPUT_DIR=/var/fieldmind/distillation/output
DISTILLATION_TEMP_DIR=/var/fieldmind/distillation/temp
DISTILLATION_MAX_FILE_SIZE=500MB

# Whisper 配置
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# 模型配置
DISTILLATION_MODEL=claude-opus-5
DISTILLATION_MAX_TOKENS=200000

# Jina Reader API
JINA_READER_API_KEY=your-api-key

# 质量门配置
DISTILLATION_MIN_PASS_RATE=0.8
```

### 2. 数据库迁移

```bash
# 运行迁移脚本
alembic upgrade head

# 或手动创建表
python -c "
from app.database import engine
from app.models.distillation import Base
Base.metadata.create_all(engine)
"
```

### 3. API 调用示例

#### 上传文件蒸馏

```bash
curl -X POST "http://localhost:8000/api/v1/distillation/upload" \
  -F "file=@book.pdf" \
  -F 'metadata={
    "title": "穷查理宝典",
    "author": "查理·芒格",
    "source_kind": "book",
    "language": "zh-CN"
  }'
```

#### 从 URL 蒸馏

```bash
curl -X POST "http://localhost:8000/api/v1/distillation/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1234567890",
    "source_kind": "video",
    "title": "课程视频"
  }'
```

#### 查询任务状态

```bash
curl "http://localhost:8000/api/v1/distillation/jobs/job-abc123"
```

响应：

```json
{
  "id": "job-abc123",
  "generation_id": "gen-550e8400-e29b-41d4-a716-446655440000",
  "status": "stage2_building",
  "current_stage": "阶段 2: RIA++ 构造",
  "progress": {
    "stage": "stage2",
    "completed": 5,
    "total": 12
  },
  "knowledge_count": 45,
  "method_count": 8,
  "created_at": "2024-09-19T10:00:00Z",
  "started_at": "2024-09-19T10:00:05Z"
}
```

#### 获取提取结果

```bash
# 知识单元
curl "http://localhost:8000/api/v1/distillation/jobs/job-abc123/knowledge"

# 方法单元
curl "http://localhost:8000/api/v1/distillation/jobs/job-abc123/methods"
```

### 4. Python SDK 使用

```python
from app.distillation import DistillationPipeline
from app.distillation.types import SourceMetadata, InputMode, SourceKind, SourceMode

# 创建元数据
metadata = SourceMetadata(
    input_mode=InputMode.FILE,
    source_kind=SourceKind.BOOK,
    source_mode=SourceMode.EMBEDDED,
    title="穷查理宝典",
    author="查理·芒格",
    file_path="/path/to/book.pdf",
)

# 创建流水线
pipeline = DistillationPipeline(
    llm_service=your_llm_service,
    output_dir="/tmp/distillation_output"
)

# 执行蒸馏
result = await pipeline.execute(metadata)

# 访问结果
print(f"知识单元数: {len(result.knowledge_units)}")
print(f"方法单元数: {len(result.methods)}")

for ku in result.knowledge_units:
    print(f"- {ku.title}: {ku.statement}")

for method in result.methods:
    print(f"- {method.display_name}: {method.description}")
```

## 质量标准

### 知识轨质量门

- ✅ 每个知识点有 ≥1 个可验证的证据锚点
- ✅ 证据 quote 与 byte 区间完全相等
- ✅ 原则/机制有双独立证据或连续论证
- ✅ 边界和反例明确
- ✅ 归属清晰（作者主张 vs 蒸馏器推断）
- ✅ 不从技能反向造知识

### 方法轨质量门

- ✅ 通过三重验证（V1 跨域 + V2 预测力 + V3 独特性）
- ✅ RIA++ 六段完整（R/I/A1/A2/E/B）
- ✅ A2 trigger 有可识别的语言信号
- ✅ E 段每步有可判断的完成标准
- ✅ B 段必须有边界
- ✅ description ≤300 字符
- ✅ 压力测试通过率 ≥80%（诱饵测试 100%）
- ✅ 5-10 个测试用例（应触发/不应触发/边界/兄弟混淆）

### 审计质量门

- ✅ 逐章五类扫描记录完整
- ✅ 候选去向逐项登记（kept/merged/rejected + reason）
- ✅ 生产者快照非零且真实
- ✅ 测试原件存在且哈希匹配
- ✅ 三重身份锁验证通过
- ✅ 来源基线在蒸馏前建立

## 性能指标

### 预期处理时间

| 来源类型 | 规模 | 预计时间 |
|---------|------|---------|
| 短文档 | < 1 万字 | 5-10 分钟 |
| 中等书籍 | 10-30 万字 | 30-60 分钟 |
| 大部头 | > 30 万字 | 1-3 小时 |
| 视频（含转写） | 1 小时 | 20-40 分钟 |

### 资源消耗

- **内存**: 2-8 GB（取决于文档大小）
- **存储**: 原文档大小的 5-10 倍（包含所有中间产物）
- **API 调用**: 约 100-500 次 LLM 调用/书（取决于复杂度）

## 监控与日志

### 任务状态

```python
from app.models.distillation import DistillationStatus

# 11 个状态
PENDING           # 等待中
NORMALIZING       # 规范化中
STAGE0_ANALYZING  # 阶段 0：整书理解
STAGE1_EXTRACTING # 阶段 1：五类提取
STAGE1_5_VERIFYING # 阶段 1.5：三重验证
STAGE2_BUILDING   # 阶段 2：RIA++ 构造
KNOWLEDGE_EXTRACTING # 知识轨提取
TESTING           # 压力测试
FREEZING          # 冻结
RELATING          # 关系建立
SEALING           # 封装
COMPLETED         # 完成
FAILED            # 失败
```

### 日志级别

```python
import logging

logger = logging.getLogger("app.distillation")
logger.setLevel(logging.INFO)

# 关键节点日志
logger.info("📄 阶段 1/11: 来源规范化...")
logger.info("📚 阶段 2/11: 整书理解（Adler 分析阅读）...")
logger.info("🔀 阶段 3/11: 双轨并行提取...")
logger.info("✅ 蒸馏流程完成！")
logger.error("❌ 蒸馏流程失败: {error}")
```

## 故障排查

### 常见问题

#### 1. 文件上传失败

```bash
# 检查文件大小限制
echo $DISTILLATION_MAX_FILE_SIZE

# 检查临时目录权限
ls -la $DISTILLATION_TEMP_DIR
```

#### 2. Whisper 转写失败

```bash
# 检查 Whisper 模型
python -c "import whisper; print(whisper.available_models())"

# 检查 CUDA 可用性
python -c "import torch; print(torch.cuda.is_available())"
```

#### 3. LLM 调用超时

```python
# 增加超时时间
DISTILLATION_MAX_TOKENS = 200000
LLM_TIMEOUT = 300  # 秒
```

#### 4. 数据库连接失败

```bash
# 检查数据库连接
python -c "
from app.database import engine
print(engine.url)
"
```

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 保存中间产物
pipeline = DistillationPipeline(
    llm_service=llm_service,
    output_dir="/tmp/debug_output"
)
```

## 扩展开发

### 添加新的知识类型

```python
# 1. 在 types.py 添加枚举
class KnowledgeType(str, Enum):
    # ...
    NEW_TYPE = "new_type"

# 2. 在 knowledge.py 添加提取器
async def _extract_new_type(self, chapter, normalized_source):
    # 实现提取逻辑
    pass
```

### 添加新的提取器类型

```python
# 1. 在 types.py 添加枚举
class ExtractorType(str, Enum):
    # ...
    NEW_EXTRACTOR = "new-extractor"

# 2. 在 method.py 添加提取方法
async def _extract_new_type(self, book_overview, normalized_source):
    # 实现提取逻辑
    pass
```

### 自定义验证规则

```python
# 在 method.py 的 Stage1_5TripleVerifier 中
async def _verify_custom(self, cand: MethodCandidate):
    # 实现自定义验证逻辑
    return {"passed": True, "reason": "..."}
```

## 与现有 FieldMind 功能集成

### 1. 文档处理集成

```python
from app.services import DocumentProcessor

# 使用现有文档处理器
processor = DocumentProcessor()
processed_doc = await processor.process(file_path)

# 传递给蒸馏系统
metadata = SourceMetadata(
    input_mode=InputMode.FILE,
    source_kind=SourceKind.DOCUMENT,
    source_mode=SourceMode.EMBEDDED,
    title=processed_doc.title,
    file_path=file_path,
)
```

### 2. 音频转写集成

```python
from app.audio import AudioTranscriber

# 使用现有 Whisper 集成
transcriber = AudioTranscriber()
result = await transcriber.transcribe(audio_path)

# 蒸馏系统会自动调用
```

### 3. 数据库事务集成

```python
from app.core.data import TransactionManager

# 使用现有事务管理
async with TransactionManager() as tm:
    job = await distillation_service.create_job(...)
    await tm.commit()
```

### 4. 监控集成

```python
from app.core.monitoring import track_distillation_metrics

# 记录指标
track_distillation_metrics(
    job_id=job.id,
    stage="stage2_building",
    duration=elapsed_time
)
```

## 未来规划

### Phase 1: 完善核心功能（1-2 周）

- [ ] 实现 Adapter 编译器
- [ ] 实现 SBPACK 2.0 封装器
- [ ] 实现独立验收器
- [ ] 实现关系建立器

### Phase 2: 增强用户体验（2-3 周）

- [ ] WebSocket 实时进度推送
- [ ] 前端用户确认界面
- [ ] 可视化蒸馏流程
- [ ] 交互式结果浏览器

### Phase 3: 性能优化（1-2 周）

- [ ] 并行处理优化
- [ ] 缓存机制
- [ ] 增量蒸馏
- [ ] 分布式任务队列

### Phase 4: 高级功能（3-4 周）

- [ ] 多语言支持
- [ ] 自定义蒸馏模板
- [ ] 批量蒸馏
- [ ] 蒸馏结果对比

## 贡献指南

欢迎贡献代码！请遵循以下原则：

1. **代码风格**: 遵循 PEP 8
2. **类型注解**: 所有函数必须有类型注解
3. **文档字符串**: 所有公共 API 必须有文档
4. **测试**: 新功能必须有单元测试
5. **质量门**: 不能降低现有质量标准

## 许可证

本蒸馏系统基于 WorkBuddy 第二大脑系统 v1.4.4，遵循 AGPL-3.0 许可证。

仓颉方法论基于：
- 仓颉 v2.0.0 (AGPL-3.0)
- commit: 149cb39f559cafcb82910f8662b3f4e3b9ee5574
- https://github.com/kangarooking/cangjie-skill

## 联系方式

如有问题或建议，请联系 FieldMind 开发团队。

---

**完整集成完成日期**: 2024-09-19  
**文档版本**: 1.0.0  
**集成状态**: ✅ 核心功能已完成，待完善扩展功能
