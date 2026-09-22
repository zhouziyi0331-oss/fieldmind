# FieldMind 当前架构分析报告

## 一、现有架构层次

### 1. 前端架构（Swift/SwiftUI）

#### Pages（页面层）- 42个页面
- **项目管理**: ProjectsPage, ProjectDetailPage, NewProjectPage, OverviewPage
- **文档管理**: FileManagerPage, UploadPage, ImportPage
- **多模态数据**: PhotosPage, TablesPage
- **知识处理**: 
  - KeywordPage（关键词）
  - CitationsPage（引用）
  - VeinPage（上下文/Vein）
  - GraphExplorerPage（知识图谱）
  - MemoryPage（记忆）
- **AI对话**: ChatPage, ConversationsPage
- **工作流**: WorkflowPage, SkillPage
- **分析报告**: ReportPage, Report3Page, BusiPage（商业分析）
- **SOP**: SOPPage, SOPAnalysisPage
- **时间轴**: TimelinePage, ChroniclePage（编年史）
- **系统**: DashboardPage, SettingsPage, ModelPage, QualityMonitorPage, AdvancedSearchPage

#### ViewModels（视图模型层）- 24个
每个主要页面都有对应的ViewModel，负责业务逻辑和状态管理

#### Services（服务层）- 22个
- 数据服务: DocumentService, PhotoService, TableService, ProjectService
- AI服务: ChatService, WorkflowService, SkillService
- 知识服务: KnowledgeGraphService, KeywordSearchService, CitationService, VeinService, MemoryService
- 分析服务: ReportService, BusinessAnalysisService, SOPAnalysisService
- 系统服务: MonitoringService, ModelConfigService, FileAccessManager

#### Core层
- Models.swift（数据模型）
- MenuBarManager.swift（菜单栏管理）
- APIClient（网络请求）

### 2. 后端架构（Python/FastAPI）

需要进一步分析后端结构...

## 二、对照报告的差距分析

### ✅ 已有能力

1. **知识管理基础**
   - 文档、照片、表格的存储和检索
   - 知识图谱、关键词提取
   - 引用追溯、上下文管理

2. **AI能力**
   - 对话交互
   - 工作流（Workflow）
   - 技能（Skill）

3. **项目协作**
   - 项目管理
   - 时间轴/编年史
   - 仪表板

### ❌ 缺失能力（按报告要求）

#### 1. 工作流链路（报告第二章）
- [ ] **任务链路**: 任务的输入、处理、输出、复核机制
- [ ] **数据链路**: 数据来源、口径、更新、追溯
- [ ] **系统链路**: 与外部业务系统的连接（CRM/ERP/OA）
- [ ] **责任链路**: 人工复核、异常处理、结果归属

#### 2. 工作舱概念（报告第六章）
- [ ] 统一任务入口（当前是分散的页面）
- [ ] 知识+任务+系统+AI的聚合
- [ ] 降低信息/系统/协同/知识摩擦

#### 3. 生产化条件（报告第五章）
- [ ] **数据可信**: 来源追溯、版本管理、口径统一
- [ ] **权限清晰**: 角色权限、操作分级、审计日志
- [ ] **责任明确**: 低/中/高风险任务的不同复核机制
- [ ] **指标完整**: 效率/质量/成本/风险/复制指标

#### 4. 资产沉淀（报告第八章）
- [ ] 场景资产库
- [ ] 流程资产库
- [ ] 知识资产库
- [ ] 规则资产库
- [ ] 复盘资产库

## 三、架构升级路径设计

### 路径A：渐进式升级（推荐）

#### 阶段1：补全基础能力（1-2个月）
1. **权限系统**
   - 用户角色管理
   - 数据权限分级
   - 操作审计日志

2. **数据追溯**
   - 数据来源标记
   - 版本管理
   - 变更历史

3. **指标体系**
   - 监控服务升级
   - 效率/质量/成本指标
   - 可视化Dashboard

#### 阶段2：工作流引擎（2-3个月）
1. **任务流转**
   - 任务状态机
   - 流程定义DSL
   - 节点编排

2. **人工复核**
   - 复核点定义
   - 审批流程
   - 异常处理

3. **系统连接**
   - Webhook支持
   - API集成框架
   - 第三方系统适配器

#### 阶段3：工作舱重构（3-4个月）
1. **场景工作舱**
   - 客服工作舱
   - 营销工作舱
   - 销售工作舱

2. **资产库**
   - 场景模板
   - 流程模板
   - 知识模板

### 路径B：激进式重构（不推荐）
直接推倒重来，按报告思路从零开始设计...

## 四、具体改造建议

### 1. 不改动的部分
- 现有的Service层（底层能力）
- 数据模型（Models.swift）
- 基础组件

### 2. 需要新增的模块

#### 新增Core模块
```
Sources/Core/
  ├── Workflow/           # 工作流引擎
  │   ├── TaskNode.swift
  │   ├── FlowDefinition.swift
  │   └── FlowExecutor.swift
  ├── Permission/         # 权限系统
  │   ├── Role.swift
  │   ├── Permission.swift
  │   └── AccessControl.swift
  ├── Audit/             # 审计日志
  │   ├── AuditLog.swift
  │   └── AuditService.swift
  └── Asset/             # 资产库
      ├── SceneAsset.swift
      ├── FlowAsset.swift
      └── KnowledgeAsset.swift
```

#### 新增Workbench模块（工作舱）
```
Sources/Workbench/
  ├── CustomerServiceWorkbench.swift  # 客服工作舱
  ├── MarketingWorkbench.swift        # 营销工作舱
  └── SalesWorkbench.swift            # 销售工作舱
```

### 3. 需要改造的部分

#### Pages层改造
- 从"功能页面"转向"场景工作舱"
- 保留底层能力页面（设置、监控等）
- 主导航改为场景导航

#### Services层增强
- 增加权限检查
- 增加审计日志
- 增加数据追溯

## 五、下一步行动

### 立即行动（本周）
1. [ ] 先解决当前的照片/表格显示问题
2. [ ] 创建架构升级详细设计文档
3. [ ] 评估现有代码的可复用性

### 短期目标（1个月）
1. [ ] 设计并实现权限系统
2. [ ] 设计并实现审计日志
3. [ ] 升级监控服务，增加指标体系

### 中期目标（3个月）
1. [ ] 实现工作流引擎核心
2. [ ] 开发第一个场景工作舱（客服）
3. [ ] 构建资产库框架

### 长期目标（6个月）
1. [ ] 完成3-5个场景工作舱
2. [ ] 形成可复制的资产库
3. [ ] 完成组织级复制能力
