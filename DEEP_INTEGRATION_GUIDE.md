# 深度融合执行指南

## 步骤1: 准备
1. 备份当前代码: git branch backup-before-integration
2. 确保测试通过: pytest tests/
3. 记录当前API列表

## 步骤2: 融合SBPACK到distillation
- 将sbpack.py的端点迁移到distillation.py
- 保持向后兼容（重定向旧端点）
- 更新文档

## 步骤3: 融合RAG到unified_rag
- 在unified_rag.py中添加"enhanced"模式
- 使用新RAG引擎作为可选后端
- A/B测试两种模式

## 步骤4: 其他模块类似处理

## 步骤5: 测试验证
- 端到端测试
- 性能对比
- 逐步切换
