# FieldMind 电脑端缺失功能清单

## 当前状态分析

### 已有的Swift页面（电脑端）
1. LoginView - 登录页面
2. MainAppView - 主应用框架（侧边栏+顶栏）
3. DashboardView - 概览页面
4. ProjectsView - 项目管理
5. DocumentsView - 材料导入
6. ContextsView - 知识脉络
7. ChatView - 智能对话
8. TimelineView - 编年史
9. GraphView - 关系图谱
10. SkillsView - 思维模型
11. FrameworksView - 二度分析

### 后端已有但前端缺失的功能
- audio.py - 音视频转写
- crawler.py - 网络爬虫（新闻、政府文件采集）
- industry.py - 行业分析
- reports.py - 三层报告生成
- workflows.py - 工作流整合引擎
- search.py - 向量搜索

---

## 一、核心功能页面缺失

### 1. 新建项目完整流程（优先级：极高）
**当前问题**：ProjectsView只有简单的名称和描述输入

**需要补充**：
- **项目创建表单页面**（CreateProjectFormView.swift）
  - 基本信息：项目名称、项目描述
  - 地区信息：地理位置、区域范围
  - 项目类型：田野调查、文献研究、产业分析等
  - 时间范围：开始日期、结束日期
  - 标签分类：自定义标签
  - Agent角色设定：选择长期记忆角色（人类学家、历史学者等）
  - 工作模式：是否启用自动处理、是否启用知识图谱等

- **文件拖拽上传区域**（作为CreateProjectFormView的第二步）
  - 大型拖拽区域（支持拖拽和点击选择）
  - 支持批量上传
  - 上传进度显示
  - 文件预览列表
  - 文件类型校验和提示

- **项目初始化确认页面**
  - 显示所有设置的汇总
  - 确认后台处理任务清单
  - 提交按钮和返回修改按钮

### 2. 网络爬虫功能页面（优先级：高）
**后端支持**：crawler.py已实现

**需要新建**：CrawlerView.swift
- 爬虫任务配置区域
  - URL输入框（支持批量输入）
  - 来源类型选择：新闻网站、政府官网、学术网站等
  - 关键词筛选
  - 时间范围设置
  - 深度设置（爬取层级）
  
- 爬虫任务列表
  - 显示正在运行的任务
  - 任务状态：队列中、进行中、已完成、失败
  - 进度条显示
  - 已采集数量统计
  
- 采集结果展示
  - 采集到的文章/文件列表
  - 预览功能
  - 批量导入到项目功能
  - 内容去重提示

### 3. 三层报告生成页面（优先级：高）
**后端支持**：reports.py已实现

**需要新建**：ReportsView.swift
- 报告配置区域
  - 选择文档范围（当前项目、指定文档、时间段）
  - 报告层次选择
    - 第一层：信息整理（事实梳理、时间线、关键人物地点）
    - 第二层：学术分析（理论框架、学术观点、研究价值）
    - 第三层：商业价值（产业机会、市场潜力、开发建议）
  - 报告风格：学术型、商业型、综合型
  - 导出格式：PDF、Markdown、Word
  
- 报告生成历史
  - 已生成报告列表
  - 报告预览
  - 重新生成功能
  - 导出和分享功能

### 4. 音视频处理页面（优先级：中）
**后端支持**：audio.py已实现

**需要新建**：AudioVideoView.swift
- 文件上传区域
  - 支持音频：MP3, WAV, M4A等
  - 支持视频：MP4, MOV, AVI等
  - 拖拽上传
  
- 转写任务列表
  - 任务状态显示
  - 进度条
  - 转写结果预览
  
- 转写结果编辑
  - 文本编辑器
  - 时间轴对照
  - 说话人标注
  - 保存和导出

### 5. 行业分析页面（优先级：中）
**后端支持**：industry.py已实现

**需要新建**：IndustryAnalysisView.swift
- 行业选择和配置
  - 行业类别选择
  - 分析维度配置
  - 数据来源选择
  
- 分析结果展示
  - 行业概况
  - 市场规模
  - 竞争格局
  - 发展趋势
  - 机会识别

### 6. 工作流整合引擎页面（优先级：中）
**后端支持**：workflows.py已实现

**需要新建**：WorkflowsView.swift
- 工作流模板库
  - 预设工作流：田野调查流程、文献研究流程、产业分析流程
  - 自定义工作流
  
- 工作流设计器
  - 拖拽式节点编辑
  - 步骤配置
  - 条件分支
  - 自动触发规则
  
- 工作流执行监控
  - 当前运行的工作流
  - 步骤进度
  - 结果输出

---

## 二、子页面和交互流程缺失

### 1. 项目详情页面
**需要新建**：ProjectDetailView.swift
- 项目概览信息
- 项目统计数据
- 快速操作按钮
- 最近活动时间线
- 项目成员（如果有协作功能）
- 项目设置入口

### 2. 文档详情页面
**需要新建**：DocumentDetailView.swift
- 文档元数据展示
- 文档内容预览
- 处理状态和日志
- 提取的实体和关键词
- 向量化状态
- 关联的知识脉络

### 3. 对话会话管理
**需要完善**：ChatView需要添加
- 会话列表侧边栏
- 新建会话按钮
- 会话重命名功能
- 会话历史搜索
- 多会话切换

### 4. 知识脉络详情页面
**需要新建**：ContextDetailView.swift
- 脉络完整信息
- 关联文档列表
- 实体关系图
- 编辑和标注功能

### 5. 编年史时间线详细视图
**需要完善**：TimelineView需要添加
- 事件详情弹窗
- 事件添加/编辑表单
- 时间轴筛选器
- 导出时间线功能

### 6. 关系图谱交互功能
**需要完善**：GraphView需要添加
- 节点详情面板
- 节点筛选和搜索
- 关系类型筛选
- 图谱布局切换
- 导出图谱图片

### 7. 思维模型配置页面
**需要完善**：SkillsView需要添加
- 模型详情页面
- 模型参数配置
- 测试运行功能
- 模型效果评估

### 8. Agent记忆管理页面
**需要新建**：AgentMemoryView.swift
- 长期记忆配置
  - Agent角色定义
  - 基础人设
  - 专业领域
  - 思维方式
  
- 项目记忆查看
  - 每个项目的独立记忆
  - 记忆边界设置
  - 记忆清理功能
  
- 用户状态记忆
  - 自动总结的用户偏好
  - 常用操作记录
  - 交互风格学习

### 9. SOP和Framework设置页面
**需要新建**：SOPSettingsView.swift
- SOP模板库
  - 预设SOP流程
  - 自定义SOP创建
  - SOP步骤编辑
  
- Framework配置
  - 分析框架选择
  - 框架参数调整
  - 框架测试和预览

---

## 三、隐藏但关键的页面

### 1. 用户设置页面（SettingsView需要完善）
**当前**：只有一个空的Text
**需要添加**：
- 账户信息管理
- API密钥配置（OpenAI、其他LLM）
- 数据库连接设置
- 向量数据库配置（Qdrant）
- 知识图谱配置（Neo4j）
- 默认工作模式设置
- 界面主题切换
- 快捷键设置
- 数据备份和恢复

### 2. 任务队列监控页面
**需要新建**：TaskQueueView.swift
- 后台任务列表
- Celery任务状态
- 任务优先级管理
- 任务取消和重试
- 任务日志查看

### 3. 系统状态监控页面
**需要新建**：SystemStatusView.swift
- 后端服务状态
- 数据库连接状态
- 向量数据库状态
- 知识图谱状态
- 爬虫服务状态
- Celery工作进程状态
- 存储空间使用情况

### 4. 错误日志和调试页面
**需要新建**：LogsView.swift
- 应用日志查看
- 后端错误日志
- API调用日志
- 性能监控
- 错误统计

### 5. 帮助和文档页面
**需要新建**：HelpView.swift
- 快速入门指南
- 功能说明文档
- 视频教程入口
- 常见问题FAQ
- 反馈和建议入口

### 6. 数据导入导出页面
**需要新建**：DataImportExportView.swift
- 批量导入功能
  - 从文件夹导入
  - 从ZIP包导入
  - 从其他系统导入
  
- 数据导出功能
  - 项目完整导出
  - 选择性导出
  - 导出格式选择
  - 导出任务管理

---

## 四、交互逻辑和工作流程需要完善

### 1. 首页（Dashboard）应该有的内容
**当前问题**：显示统计数据，但没有快速入口

**需要添加**：
- 最近打开的项目（点击直接进入）
- 快速新建项目按钮（跳转到完整表单）
- 今日任务提醒
- 处理进度通知
- 最近生成的报告
- 系统通知和提示

### 2. 项目之间的边界隔离
**需要实现**：
- 项目切换时清空相关状态
- 确保文档、脉络、对话都关联到正确的项目
- 项目内存边界提示
- 跨项目对比功能（高级功能）

### 3. 自动化工作流触发
**需要实现**：
- 上传文档后自动触发处理
- 处理完成后自动生成脉络
- 生成脉络后自动更新知识图谱
- 定时爬虫任务
- 定时报告生成

### 4. 通知和进度提示系统
**需要新建**：NotificationManager.swift
- 顶部通知栏
- 进度提示Toast
- 任务完成通知
- 错误警告
- 操作确认对话框

---

## 五、设计要求

### 视觉风格（参考HTML文档）
1. **颜色方案**
   - 主色：#667eea（紫色）
   - 辅助色：#764ba2（深紫）
   - 成功：#48bb78（绿色）
   - 警告：#ed8936（橙色）
   - 错误：#f56565（红色）
   - 背景渐变：从#667eea到#764ba2

2. **设计原则**
   - 圆角：8-12px
   - 卡片阴影：柔和
   - 间距：统一使用12/16/20/24px
   - 字体大小：12-32px梯度
   - 过渡动画：0.3s
   - 悬停效果：轻微上移和阴影加深

3. **严格禁止**
   - 不使用任何emoji
   - 不使用花哨图标
   - 保持专业和简洁
   - 避免过度装饰

### 交互规范
1. 按钮悬停有反馈
2. 加载状态清晰显示
3. 表单验证实时提示
4. 操作确认对话框
5. 键盘快捷键支持

---

## 六、优先级排序

### 第一优先级（立即做）
1. 修复首页空白/蓝屏问题
2. 完善新建项目流程（表单+拖拽上传）
3. 新建网络爬虫页面（CrawlerView）
4. 新建三层报告生成页面（ReportsView）
5. 完善用户设置页面（SettingsView）

### 第二优先级（本周完成）
6. 新建音视频处理页面（AudioVideoView）
7. 新建Agent记忆管理页面（AgentMemoryView）
8. 新建SOP设置页面（SOPSettingsView）
9. 新建工作流引擎页面（WorkflowsView）
10. 完善文档详情页面（DocumentDetailView）

### 第三优先级（后续完善）
11. 新建行业分析页面（IndustryAnalysisView）
12. 新建项目详情页面（ProjectDetailView）
13. 新建任务队列监控页面（TaskQueueView）
14. 新建系统状态页面（SystemStatusView）
15. 新建数据导入导出页面（DataImportExportView）

---

## 七、后端整合检查清单

### 需要确认的后端API端点
- [x] /api/v1/auth/* - 认证
- [x] /api/v1/documents/* - 文档管理
- [ ] /api/v1/audio/* - 音视频转写
- [ ] /api/v1/crawler/* - 网络爬虫
- [x] /api/v1/reports/* - 报告生成
- [x] /api/v1/rag/* - RAG对话
- [x] /api/v1/knowledge_graph/* - 知识图谱
- [x] /api/v1/skills/* - 思维模型
- [x] /api/v1/timeline/* - 编年史
- [ ] /api/v1/workflows/* - 工作流
- [ ] /api/v1/industry/* - 行业分析
- [ ] /api/v1/search/* - 向量搜索

### APIService.swift需要添加的方法
```swift
// 爬虫相关
func startCrawlerTask(...) async throws
func getCrawlerTasks(...) async throws
func getCrawlerResults(...) async throws

// 音视频相关
func uploadAudio(...) async throws
func getTranscription(...) async throws

// 工作流相关
func getWorkflows(...) async throws
func executeWorkflow(...) async throws

// 行业分析相关
func analyzeIndustry(...) async throws

// Agent记忆相关
func getAgentMemory(...) async throws
func updateAgentMemory(...) async throws

// SOP相关
func getSOPTemplates(...) async throws
func createSOP(...) async throws
```

---

## 八、文件结构规划

```
Sources/FieldMind/
├── Views/
│   ├── Core/（核心页面）
│   │   ├── LoginView.swift ✓
│   │   ├── MainAppView.swift ✓
│   │   └── DashboardView.swift ✓
│   ├── Projects/（项目相关）
│   │   ├── ProjectsView.swift ✓
│   │   ├── ProjectDetailView.swift ⚠️ 需要新建
│   │   └── CreateProjectFormView.swift ⚠️ 需要新建
│   ├── Documents/（文档相关）
│   │   ├── DocumentsView.swift ✓
│   │   └── DocumentDetailView.swift ⚠️ 需要新建
│   ├── Analysis/（分析功能）
│   │   ├── ContextsView.swift ✓
│   │   ├── ContextDetailView.swift ⚠️ 需要新建
│   │   ├── GraphView.swift ✓
│   │   ├── TimelineView.swift ✓
│   │   └── IndustryAnalysisView.swift ⚠️ 需要新建
│   ├── Intelligence/（智能功能）
│   │   ├── ChatView.swift ✓
│   │   ├── SkillsView.swift ✓
│   │   ├── FrameworksView.swift ✓
│   │   └── AgentMemoryView.swift ⚠️ 需要新建
│   ├── Tools/（工具功能）
│   │   ├── CrawlerView.swift ⚠️ 需要新建
│   │   ├── AudioVideoView.swift ⚠️ 需要新建
│   │   ├── ReportsView.swift ⚠️ 需要新建
│   │   └── WorkflowsView.swift ⚠️ 需要新建
│   ├── Settings/（设置相关）
│   │   ├── SettingsView.swift ⚠️ 需要完善
│   │   ├── SOPSettingsView.swift ⚠️ 需要新建
│   │   ├── TaskQueueView.swift ⚠️ 需要新建
│   │   ├── SystemStatusView.swift ⚠️ 需要新建
│   │   └── LogsView.swift ⚠️ 需要新建
│   └── Common/（通用组件）
│       ├── EmptyStateView.swift ✓
│       ├── StatusBadge.swift ✓
│       └── NotificationView.swift ⚠️ 需要新建
├── Models/ ✓
├── Services/ ✓
└── Utils/ ✓
```

✓ = 已完成
⚠️ = 需要新建或完善

---

## 总结

### 统计
- **已有页面**：11个
- **需要新建的核心功能页面**：12个
- **需要新建的子页面/详情页**：15个
- **需要完善的现有页面**：6个
- **总计缺失/需要完善**：33个页面

### 关键问题
1. 首页空白/蓝屏需要立即修复
2. 新建项目流程不完整，缺少表单和拖拽上传
3. 大量后端功能（爬虫、报告、音视频、工作流、行业分析）在前端完全缺失
4. Agent记忆管理、SOP设置等核心功能页面未实现
5. 缺少系统监控、任务管理、日志查看等运维页面
6. 项目边界隔离逻辑需要加强
