# FieldMind 优先级修复计划

## 当前状态诊断 (2026-08-06)

### ✅ 已验证正常的功能
1. **后台处理器** - 正在运行 (PID 31004, 端口8000)
2. **时间戳映射逻辑** - DocumentChunker._map_timestamps_to_chunks() 测试通过
3. **转录文件生成** - Whisper转录正常保存transcript JSON
4. **数据库表结构** - fact_statements表包含start_sec/end_sec字段

### ❌ 核心问题

**问题1: 时间戳覆盖率低 (34.2%)**
- 现状: 5626条fact_statements中仅1924条有时间戳
- 根本原因: **历史数据在时间戳映射功能完善前处理**
- 影响: 用户无法看到大部分音视频的时间轴

**问题2: 僵尸文档待清理**
- 需要清理状态异常的文档 (processing/failed状态卡住)

**问题3: 实体提取准确率待验证**
- spaCy中文模型是否正确加载
- 知识图谱节点质量

## 修复优先级

### P0 - 立即修复 (阻塞用户体验)

#### 1. 重新处理历史音视频文档 (时间戳回填)
**目标**: 将时间戳覆盖率从34.2%提升到>95%

**方案**:
```sql
-- 筛选需要重新处理的文档
SELECT id, filename, file_type 
FROM project_documents 
WHERE (file_type LIKE '%audio%' OR file_type LIKE '%video%')
  AND status = 'completed'
  AND id IN (
    SELECT DISTINCT document_id 
    FROM fact_statements 
    WHERE start_sec IS NULL
  );
```

**执行步骤**:
1. 查询所有需要重新处理的音视频文档ID
2. 清空这些文档的fact_statements记录
3. 重置文档状态为pending
4. 触发后台处理器重新处理
5. 验证时间戳覆盖率

**预期结果**: 时间戳覆盖率 >95%

#### 2. 僵尸文档清理
**目标**: 清理status异常的文档

**方案**:
```sql
-- 重置超过1小时仍在processing的文档
UPDATE project_documents 
SET status = 'failed', 
    error_message = '处理超时，请重新上传'
WHERE status = 'processing' 
  AND datetime(created_at, '+1 hour') < datetime('now');

-- 删除failed状态超过7天的文档
DELETE FROM project_documents 
WHERE status = 'failed' 
  AND datetime(created_at, '+7 days') < datetime('now');
```

### P1 - 重要优化 (提升质量)

#### 3. 验证spaCy中文模型
**目标**: 确认zh_core_web_sm已安装并正常工作

**验证步骤**:
```python
import spacy
nlp = spacy.load("zh_core_web_sm")
doc = nlp("李明在北京大学学习人类学")
entities = [(ent.text, ent.label_) for ent in doc.ents]
print(entities)  # 期望: [('李明', 'PERSON'), ('北京大学', 'ORG')]
```

#### 4. 知识图谱质量检查
- 检查Neo4j节点数量和关系
- 验证实体提取准确率
- 清理重复/低质量节点

### P2 - 性能优化 (长期改进)

#### 5. 向量化Pipeline优化
- 批量处理优化
- ChromaDB连接池

#### 6. 前端时间戳显示增强
- 添加播放器集成
- 点击时间戳跳转音频位置

## 执行计划

### 阶段1: 数据修复 (今天完成)
- [ ] 统计需要重新处理的文档数量
- [ ] 执行历史文档重新处理脚本
- [ ] 验证时间戳覆盖率提升
- [ ] 清理僵尸文档

### 阶段2: 质量验证 (今天完成)
- [ ] 验证spaCy模型
- [ ] 检查知识图谱质量
- [ ] 运行端到端测试

### 阶段3: 文档记录
- [ ] 更新完成报告
- [ ] 记录遗留问题清单

## 成功标准

1. ✅ 时间戳覆盖率 >95%
2. ✅ 无僵尸文档 (processing状态<5分钟)
3. ✅ spaCy实体提取准确率 >70%
4. ✅ 所有服务运行正常
5. ✅ 零技术债务

---
创建时间: 2026-08-06
最后更新: 2026-08-06
