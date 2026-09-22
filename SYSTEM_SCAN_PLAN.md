# FieldMind 全面系统扫描计划

## 扫描目标

### 1. 程序重复与整合
- ✅ 发现重复目录：
  - `/Users/alwan/FieldMind` (主程序，728个服务文件)
  - `/Users/alwan/Downloads/FieldMind-fieldmind` (旧版本，包含部署文档)
  - `/Users/alwan/Desktop/FieldMind_Apps` (打包应用)
  - `/Users/alwan/FieldMind/fieldmind` (内部重复目录)

### 2. 工作流引擎植入检查
- [ ] 检查所有服务是否正确集成WorkflowEngine
- [ ] 确认WorkflowTemplates覆盖所有核心流程
- [ ] 验证API层是否完整支持工作流调用

### 3. Skills封装检查
- [ ] 确认所有Skills实现统一接口
- [ ] 检查Skills是否完全数据驱动（无硬编码）
- [ ] 验证Skills之间的依赖关系清晰

### 4. 数据流断链检查
- [ ] 前端→API层
- [ ] API层→Service层
- [ ] Service层→Database层
- [ ] Skills→LLM调用链

### 5. Bug修复检查
- [ ] 扫描所有TODO/FIXME注释
- [ ] 检查异常处理完整性
- [ ] 验证数据库操作事务安全

### 6. 路径与架构清晰度
- [ ] 确认所有import路径正确
- [ ] 验证模块依赖关系
- [ ] 检查循环依赖

## 扫描执行顺序

1. **程序整合** - 合并重复代码，统一到主目录
2. **工作流引擎全面植入** - 确保所有核心服务支持工作流
3. **数据流全链路测试** - 端到端验证
4. **Bug修复** - 解决所有已知问题
5. **架构优化** - 清理冗余，优化路径

## 开始时间
2026-09-17
