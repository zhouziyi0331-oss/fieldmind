# 编排器事务管理完整修复计划

## 问题诊断

### 当前问题
1. **编排器主流程无事务管理**
   - `process_file()` 方法没有创建和管理数据库会话
   - 8个阶段的处理缺乏统一的事务边界
   - 异常处理块缺少rollback

2. **子服务独立事务**
   - `LineageTracker.record_lineage()` 自己创建会话并commit
   - `MetricCalculator._save_calculation_history()` 自己创建会话并commit
   - `_stage_quality()` 自己创建会话并commit
   - **后果**：如果阶段6失败，阶段1-5的数据已经提交无法回滚

3. **事务隔离问题**
   - 每个子服务独立commit，破坏了ACID特性
   - 无法保证8个阶段的原子性

## 修复策略

### 策略选择：会话传递模式

**方案A：编排器统一会话**（推荐）
- 编排器创建一个会话，传递给所有子服务
- 所有阶段共享同一会话
- 编排器负责最终的commit/rollback
- **优点**：完整的事务原子性，所有阶段要么全成功要么全失败
- **缺点**：需要修改所有子服务的接口

**方案B：嵌套事务**
- 使用savepoint实现子事务
- **缺点**：SQLite对savepoint支持有限，复杂度高

**决定**：采用方案A

## 修复步骤

### 第1步：修改编排器主流程
文件：`data_governance_orchestrator.py`

修改 `process_file()` 方法：
```python
def process_file(...) -> GovernanceResult:
    start_time = time.time()
    result = GovernanceResult(...)
    
    # 创建数据库会话
    db = get_db_session()
    
    try:
        # 阶段1-8: 传递db会话
        ingestion_result = self._stage_ingestion(...)
        metadata_result = self._stage_metadata(...)
        chunking_result = self._stage_chunking(..., db=db)
        metrics_result = self._stage_metrics(..., db=db)
        vectorization_result = self._stage_vectorization(...)
        knowledge_result = self._stage_knowledge(...)
        lineage_result = self._stage_lineage(..., db=db)
        quality_result = self._stage_quality(..., db=db)
        
        # 所有阶段成功，提交事务
        db.commit()
        result.success = True
        
    except Exception as e:
        # 任何阶段失败，回滚所有数据库操作
        db.rollback()
        logger.error(f"[数据治理] 文件处理失败，已回滚: {e}")
        result.errors.append(str(e))
        
    finally:
        # 无论成功失败，关闭会话
        db.close()
        result.total_duration = time.time() - start_time
    
    return result
```

### 第2步：修改子服务接口

#### 2.1 LineageTracker.record_lineage()
修改为接受可选的db参数：
```python
@staticmethod
def record_lineage(..., db=None) -> bool:
    should_close = False
    if db is None:
        db = get_db_session()
        should_close = True
    
    try:
        # 执行SQL
        db.execute(...)
        
        # 只有自己创建的会话才commit
        if should_close:
            db.commit()
        
        return True
    except Exception as e:
        if should_close:
            db.rollback()
        raise
    finally:
        if should_close:
            db.close()
```

#### 2.2 MetricCalculator._save_calculation_history()
修改为接受可选的db参数：
```python
def _save_calculation_history(..., db=None):
    should_close = False
    if db is None:
        db = get_db_session()
        should_close = True
    
    try:
        # 保存指标
        for metric_name, metric_value in results.items():
            db.execute(...)
        
        if should_close:
            db.commit()
    except Exception as e:
        if should_close:
            db.rollback()
        logger.error(f"保存计算历史失败: {e}")
    finally:
        if should_close:
            db.close()
```

#### 2.3 _stage_quality()
已经有db参数，但需要修改为不自动commit：
```python
def _stage_quality(..., db) -> Dict[str, Any]:
    # 移除内部的 db = get_db_session()
    # 使用传入的db
    # 移除 db.commit()
    # 移除 db.rollback()
    # 移除 finally: db.close()
```

### 第3步：修改stage方法

#### 3.1 _stage_metrics()
```python
def _stage_metrics(self, chunks: List[Any], db=None) -> Dict[str, Any]:
    for chunk in chunks:
        # 传递db给calculator
        calculator = MetricCalculator()
        calculator.calculate_all_metrics(..., db=db)
```

#### 3.2 _stage_lineage()
```python
def _stage_lineage(..., db=None) -> Dict[str, Any]:
    for chunk_id in chunk_ids:
        LineageTracker.record_lineage(..., db=db)
```

### 第4步：修改MetricCalculator.calculate_all_metrics()
添加db参数并传递给_save_calculation_history：
```python
def calculate_all_metrics(self, ..., db=None) -> Dict[str, Any]:
    # 计算所有指标
    results = {...}
    
    # 传递db
    self._save_calculation_history(..., db=db)
    
    return results
```

## 测试计划

### 单元测试
1. 测试正常流程：所有阶段成功，数据正确提交
2. 测试回滚：阶段3失败，阶段1-2的数据被回滚
3. 测试会话传递：验证所有子服务使用同一个会话
4. 测试独立调用：验证子服务仍可独立使用（不传db参数）

### 集成测试
1. 处理多个文件，验证事务隔离
2. 模拟各种失败场景，验证回滚机制
3. 检查数据库完整性

## 预期结果

修复后：
- ✓ 编排器有完整的事务管理（try/commit/rollback/finally/close）
- ✓ 8个阶段共享同一事务
- ✓ 任何阶段失败，所有数据库操作回滚
- ✓ 子服务保持向后兼容（支持独立调用）
- ✓ 数据库操作具有ACID保证
- ✓ 系统健康检查问题#3和#4修复

## 风险评估

### 低风险
- 向后兼容性：子服务仍可独立使用
- 增量修改：逐个修改每个组件

### 中等风险
- 需要修改多个文件的接口
- 需要全面的测试覆盖

### 缓解措施
- 先修改编排器，验证基本流程
- 逐个修改子服务，每次修改后测试
- 保留原有的独立调用能力

## 实施顺序

1. ✓ 编写修复计划（本文档）
2. 修改 `data_governance_orchestrator.py` 的 `process_file()` 方法
3. 修改 `_stage_quality()` 方法（移除内部事务管理）
4. 修改 `lineage_tracker.py` 的 `record_lineage()` 方法
5. 修改 `metric_calculator.py` 的相关方法
6. 修改 `_stage_lineage()` 和 `_stage_metrics()` 方法
7. 运行测试验证
8. 重新运行系统健康检查
