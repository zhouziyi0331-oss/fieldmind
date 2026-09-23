# FieldMind Skills系统快速开始指南

## 使用现有Skills

### 1. 触发蒸馏
```python
from app.services.distillation_engine import DistillationEngine
from app.database import get_db

db = get_db()
engine = DistillationEngine(db)

# 对项目进行完整蒸馏
result = engine.distill_project(project_id=1)

print(result)
# {
#   "project_id": 1,
#   "total_units": 45,
#   "breakdown": {
#     "insights": 8,
#     "quotes": 12,
#     "models": 5,
#     "cases": 7,
#     "actions": 9,
#     "methods": 4
#   }
# }
```

### 2. API调用
```bash
# 触发蒸馏
curl -X POST http://localhost:8000/api/distillation/distill/1

# 获取知识单元列表
curl http://localhost:8000/api/distillation/units?project_id=1&type=洞察

# 获取单元详情
curl http://localhost:8000/api/distillation/units/123

# 获取来源追溯
curl http://localhost:8000/api/distillation/units/123/sources
```

---

## 开发新Skill

### Step 1: 创建Skill文件
在 `backend/src/app/skills/` 创建新文件 `extract_my_type.py`:

```python
"""
提取XXX类型 Skill
"""
from typing import Dict, Any, List


class ExtractMyTypeSkill:
    """
    XXX提取Skill
    
    方法论: 描述你的方法论
    """
    
    METADATA = {
        "name": "extract_my_type",
        "version": "1.0.0",
        "type": "your_extraction_type",
        "output_type": "XXX类型"
    }
    
    def __init__(self, db_session):
        self.db = db_session
    
    def extract(self, chunks: List[Dict[str, Any]],
                entities: List[Dict[str, Any]],
                relations: List[Dict[str, Any]],
                events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行提取
        
        参数:
            chunks: 文本块列表
            entities: 实体列表
            relations: 关系列表
            events: 事件列表
            
        返回:
            提取结果列表，每个包含：
            - content: 核心内容（必须）
            - credibility: 可信度 0-1（必须）
            - confidence: 置信度 0-1（必须）
            - source_chunks: 来源chunk ID列表（必须）
            - 其他自定义字段（可选）
        """
        results = []
        
        # 你的提取逻辑
        for chunk in chunks:
            # 分析chunk
            result = {
                "content": "提取的内容",
                "credibility": 0.8,
                "confidence": 0.75,
                "source_chunks": [chunk["id"]],
                # 自定义字段
                "custom_field": "..."
            }
            results.append(result)
        
        return results
```

### Step 2: 注册Skill
在 `skill_registry.py` 的 `initialize_distillation_skills()` 中添加：

```python
from .extract_my_type import ExtractMyTypeSkill

def initialize_distillation_skills():
    # ... 现有代码 ...
    
    registry.register_skill("extract_my_type", ExtractMyTypeSkill, {
        "type": "your_extraction_type",
        "output_type": "XXX类型",
        "methodology": "你的方法论"
    })
    
    return registry
```

### Step 3: 在引擎中使用
在 `distillation_engine.py` 的 `distill_project()` 中添加：

```python
results = {
    # ... 现有类型 ...
    "my_type": self._extract_with_skill(project_id, "extract_my_type", structured_data, "XXX类型"),
}
```

### Step 4: 测试Skill
创建测试文件 `test_extract_my_type.py`:

```python
import pytest
from app.skills.extract_my_type import ExtractMyTypeSkill

def test_extract_my_type():
    skill = ExtractMyTypeSkill(db=None)
    
    chunks = [{"id": 1, "content": "测试内容"}]
    entities = []
    relations = []
    events = []
    
    results = skill.extract(chunks, entities, relations, events)
    
    assert len(results) > 0
    assert "content" in results[0]
    assert "credibility" in results[0]
    assert "confidence" in results[0]
    assert "source_chunks" in results[0]
```

运行测试：
```bash
pytest backend/tests/test_extract_my_type.py -v
```

---

## Skill开发最佳实践

### 1. 必须字段
每个提取结果必须包含：
- `content` (str): 核心内容
- `credibility` (float): 可信度 0-1
- `confidence` (float): 置信度 0-1
- `source_chunks` (list): 来源chunk ID列表

### 2. 可信度评分指南
- 0.9-1.0: 直接引用、精确匹配
- 0.7-0.9: 高频模式、多重验证
- 0.5-0.7: 推断、单一来源
- <0.5: 不建议返回

### 3. 置信度评分指南
- 0.8-1.0: 算法确定性高
- 0.6-0.8: 中等确定性
- <0.6: 不确定，需人工审核

### 4. 性能优化
- 使用Counter进行批量计数
- 避免嵌套循环（O(n²)）
- 优先使用列表推导式
- 大量数据时使用批处理

```python
# ❌ 低效
for chunk in chunks:
    for entity in entities:
        if entity.chunk_id == chunk.id:
            # 处理
            pass

# ✅ 高效
chunk_entities = {}
for entity in entities:
    if entity.chunk_id not in chunk_entities:
        chunk_entities[entity.chunk_id] = []
    chunk_entities[entity.chunk_id].append(entity)

for chunk in chunks:
    entities_in_chunk = chunk_entities.get(chunk.id, [])
    # 处理
```

### 5. 错误处理
```python
def extract(self, chunks, entities, relations, events):
    results = []
    
    try:
        for chunk in chunks:
            try:
                # 提取逻辑
                result = self._process_chunk(chunk)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"处理chunk {chunk['id']} 失败: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Skill提取失败: {str(e)}", exc_info=True)
    
    return results
```

---

## 调试技巧

### 1. 单独测试Skill
```python
from app.skills.extract_insights import ExtractInsightsSkill

# 准备测试数据
chunks = [
    {"id": 1, "content": "这是一段测试文本"},
    {"id": 2, "content": "另一段测试文本"}
]
entities = [
    {"entity_name": "测试实体", "entity_type": "PERSON", "chunk_id": 1}
]

# 实例化并测试
skill = ExtractInsightsSkill(db=None)
results = skill.extract(chunks, entities, [], [])

# 检查结果
for r in results:
    print(f"内容: {r['content']}")
    print(f"可信度: {r['credibility']}")
    print(f"置信度: {r['confidence']}")
    print(f"来源: {r['source_chunks']}")
    print("---")
```

### 2. 日志输出
```python
import logging
logger = logging.getLogger(__name__)

class ExtractMyTypeSkill:
    def extract(self, chunks, entities, relations, events):
        logger.info(f"开始提取，输入数据: {len(chunks)} chunks, {len(entities)} entities")
        
        results = []
        # ... 提取逻辑 ...
        
        logger.info(f"提取完成，返回 {len(results)} 个结果")
        return results
```

### 3. 查看中间结果
```python
def extract(self, chunks, entities, relations, events):
    # 打印输入统计
    print(f"Chunks: {len(chunks)}")
    print(f"Entities: {len(entities)}")
    
    # 打印第一个chunk示例
    if chunks:
        print(f"示例chunk: {chunks[0]}")
    
    # 提取并打印统计
    results = self._do_extraction(chunks, entities, relations, events)
    print(f"提取结果数: {len(results)}")
    
    return results
```

---

## 常见问题

### Q1: Skill没有被调用？
检查是否在 `skill_registry.py` 中正确注册了Skill

### Q2: 提取结果为空？
- 检查输入数据是否有效
- 添加日志查看中间步骤
- 降低过滤阈值（如频率要求）

### Q3: 性能慢？
- 使用性能分析工具：`python -m cProfile your_script.py`
- 检查是否有O(n²)循环
- 考虑添加缓存

### Q4: 如何添加LLM支持？
```python
from app.services.llm_service import LLMService

class ExtractMyTypeSkill:
    def __init__(self, db_session):
        self.db = db_session
        self.llm = LLMService()
    
    def extract(self, chunks, entities, relations, events):
        # 先用规则提取候选
        candidates = self._rule_based_extraction(chunks)
        
        # 用LLM增强质量
        enhanced = []
        for candidate in candidates:
            prompt = f"分析以下内容: {candidate['content']}"
            llm_result = self.llm.analyze(prompt)
            candidate['llm_analysis'] = llm_result
            enhanced.append(candidate)
        
        return enhanced
```

---

## 资源链接

- **完整文档**: `DISTILLATION_SKILLS_SYSTEM.md`
- **SBPACK 2.0标准**: `/Users/alwan/Downloads/直接给WorkBuddy-开始蒸馏-中文表达1.4.4-交付/01-给WorkBuddy的最终提示词.md`
- **示例Skills**: `backend/src/app/skills/`
- **测试示例**: `backend/tests/test_distillation_*.py`

---

## 下一步

1. ✅ Skills系统已完成
2. ⏭️ 创建Skills管理API（查看、启用/禁用、配置）
3. ⏭️ 前端Skills配置界面
4. ⏭️ Skills性能监控和统计
5. ⏭️ Skills市场（分享和下载社区Skills）
