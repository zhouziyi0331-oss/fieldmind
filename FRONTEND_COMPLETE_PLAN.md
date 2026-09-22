# FieldMind 前端完整开发计划

## 📋 项目背景

根据后端 106 个 API 文件和约 300 个端点，前端系统需要完整覆盖所有功能，提供专业、美观、交互流畅的用户体验。

---

## 🎨 设计理念和审美标准

### 参考设计系统
- **Notion** - 简洁、流畅的文档管理体验
- **Linear** - 现代化、高性能的项目管理界面
- **Vercel Dashboard** - 清爽的数据可视化
- **Stripe Dashboard** - 专业的商业应用界面

### 核心设计原则
1. **简洁优先** - 去除冗余，突出核心功能
2. **交互流畅** - 即时反馈，动画自然
3. **信息层次** - 清晰的视觉层级
4. **响应式** - 完美适配所有设备
5. **无障碍** - WCAG 2.1 AA 标准

### 视觉风格
- **色彩系统**: 蓝色主色调（专业、可信）
- **排版**: Inter/SF Pro 字体，清晰易读
- **间距**: 8px 网格系统
- **圆角**: 8px 标准，12px 卡片
- **阴影**: 柔和层次感

---

## 📱 页面架构规划

### 第一层：认证和入口 (3 页)
```
1. 登录页 (/login)
2. 注册页 (/register)
3. 忘记密码页 (/forgot-password)
```

### 第二层：主应用布局
```
侧边栏导航 + 顶部栏 + 主内容区
```

### 第三层：核心功能模块

#### A. Dashboard 模块 (5 页)
```
1. 总览仪表盘 (/dashboard)
   - 项目统计卡片
   - 最近活动时间线
   - 快速操作入口
   - 数据趋势图表

2. 我的工作台 (/dashboard/workspace)
   - 待办事项
   - 收藏的项目
   - 最近访问

3. 数据概览 (/dashboard/overview)
   - 全局统计
   - 资源使用情况
   - 性能指标

4. 活动动态 (/dashboard/activity)
   - 操作日志
   - 系统通知
   - 协作动态

5. 快速搜索 (/dashboard/search)
   - 全局搜索
   - 过滤和筛选
   - 搜索历史
```

#### B. 项目管理模块 (10+ 页)
```
1. 项目列表 (/projects)
   - 卡片/列表视图切换
   - 排序和筛选
   - 批量操作
   - 创建项目向导

2. 项目详情 (/projects/:id)
   - 概览 Tab
   - 文档 Tab
   - 成员 Tab
   - 设置 Tab

3. 项目设置 (/projects/:id/settings)
   - 基本信息
   - 成员管理
   - 权限设置
   - 危险操作

4. 项目分析 (/projects/:id/analytics)
   - 数据统计
   - 趋势分析
   - 自定义报表

5. 项目协作 (/projects/:id/collaboration)
   - 团队成员
   - 邀请链接
   - 协作日志

6. 项目导出 (/projects/:id/export)
   - 导出配置
   - 格式选择
   - 历史记录

7. 项目模板 (/projects/templates)
   - 模板库
   - 创建模板
   - 模板市场

8. 项目归档 (/projects/archived)
   - 已归档项目
   - 恢复操作

9. 项目导入 (/projects/import)
   - 上传文件
   - 映射配置
   - 预览确认

10. 批量管理 (/projects/batch)
    - 批量编辑
    - 批量删除
    - 批量导出
```

#### C. 文档管理模块 (15+ 页)
```
1. 文档列表 (/projects/:id/documents)
   - 表格视图
   - 卡片视图
   - 列表视图
   - 上传区域（拖拽）

2. 文档上传 (/projects/:id/documents/upload)
   - 单文件上传（带进度条）
   - 批量上传（带队列管理）
   - 实时进度动画
   - 上传成功/失败提示
   - 断点续传支持

3. 文档详情 (/projects/:id/documents/:docId)
   - 文档预览
   - 元数据展示
   - 处理状态
   - 相关文档

4. 文档预览 (/projects/:id/documents/:docId/preview)
   - PDF 预览
   - Word 预览
   - 文本预览
   - 图片预览

5. 文档编辑 (/projects/:id/documents/:docId/edit)
   - 在线编辑器
   - 版本历史
   - 协同编辑

6. 文档处理状态 (/projects/:id/documents/:docId/processing)
   - 实时处理进度
   - 处理日志
   - 错误详情

7. 文档分块查看 (/projects/:id/documents/:docId/chunks)
   - 分块列表
   - 分块详情
   - 分块搜索

8. 文档标注 (/projects/:id/documents/:docId/annotations)
   - 添加标注
   - 标注管理
   - 标注导出

9. 文档版本 (/projects/:id/documents/:docId/versions)
   - 版本列表
   - 版本对比
   - 版本回滚

10. 文档分享 (/projects/:id/documents/:docId/share)
    - 生成分享链接
    - 权限设置
    - 访问记录

11. 文档标签 (/projects/:id/documents/:docId/tags)
    - 添加标签
    - 标签管理
    - 标签搜索

12. 文档关联 (/projects/:id/documents/:docId/relations)
    - 相关文档
    - 引用关系
    - 关系图谱

13. 文档统计 (/projects/:id/documents/:docId/stats)
    - 阅读统计
    - 使用统计
    - 热力图

14. 文档转换 (/projects/:id/documents/:docId/convert)
    - 格式转换
    - 转换历史

15. 批量文档操作 (/projects/:id/documents/batch)
    - 批量下载
    - 批量删除
    - 批量标签
```

#### D. 知识图谱模块 (8+ 页)
```
1. 知识图谱总览 (/projects/:id/knowledge-graph)
   - 图谱可视化（D3.js/Cytoscape.js）
   - 节点搜索
   - 关系筛选
   - 布局切换

2. 实体管理 (/projects/:id/knowledge-graph/entities)
   - 实体列表
   - 实体详情
   - 实体编辑
   - 实体合并

3. 关系管理 (/projects/:id/knowledge-graph/relations)
   - 关系列表
   - 关系类型
   - 关系编辑

4. 图谱分析 (/projects/:id/knowledge-graph/analysis)
   - 中心度分析
   - 社区发现
   - 路径查询

5. 图谱导出 (/projects/:id/knowledge-graph/export)
   - 导出格式选择
   - 导出配置
   - 下载管理

6. 图谱搜索 (/projects/:id/knowledge-graph/search)
   - 高级搜索
   - 图谱查询语言
   - 搜索结果可视化

7. 图谱版本 (/projects/:id/knowledge-graph/versions)
   - 版本管理
   - 版本对比
   - 版本回滚

8. 图谱配置 (/projects/:id/knowledge-graph/settings)
   - 显示设置
   - 算法配置
   - 性能优化
```

#### E. 数据质量模块 (6+ 页)
```
1. 质量总览 (/projects/:id/data-quality)
   - 质量评分
   - 问题统计
   - 趋势图表

2. 质量报告 (/projects/:id/data-quality/reports)
   - 报告列表
   - 生成报告
   - 报告详情

3. 数据验证 (/projects/:id/data-quality/validation)
   - 验证规则
   - 验证结果
   - 问题修复

4. 数据清洗 (/projects/:id/data-quality/cleaning)
   - 清洗任务
   - 清洗日志
   - 清洗规则

5. 质量监控 (/projects/:id/data-quality/monitoring)
   - 实时监控
   - 告警设置
   - 监控历史

6. 改进建议 (/projects/:id/data-quality/suggestions)
   - 自动建议
   - 人工审核
   - 应用改进
```

#### F. AI 对话模块 (5+ 页)
```
1. 对话界面 (/projects/:id/chat)
   - 聊天窗口
   - 上下文管理
   - 引用文档

2. 对话历史 (/projects/:id/chat/history)
   - 会话列表
   - 会话详情
   - 会话导出

3. AI 设置 (/projects/:id/chat/settings)
   - 模型选择
   - 参数配置
   - 提示词管理

4. 知识问答 (/projects/:id/chat/qa)
   - 问答界面
   - 问答历史
   - 问答评价

5. Deep RAG (/projects/:id/chat/deep-rag)
   - 深度检索
   - 多跳推理
   - 结果追溯
```

#### G. 报告和分析模块 (8+ 页)
```
1. 报告中心 (/projects/:id/reports)
   - 报告列表
   - 报告类型
   - 报告状态

2. 创建报告 (/projects/:id/reports/create)
   - 报告模板
   - 自定义配置
   - 预览生成

3. 报告详情 (/projects/:id/reports/:reportId)
   - 报告内容
   - 数据可视化
   - 导出选项

4. 业务分析 (/projects/:id/analysis/business)
   - 业务指标
   - 趋势分析
   - 对比分析

5. 时间线分析 (/projects/:id/analysis/timeline)
   - 事件时间线
   - 时间分布
   - 时序分析

6. 引用分析 (/projects/:id/analysis/citations)
   - 引用网络
   - 引用统计
   - 引用追溯

7. 自定义分析 (/projects/:id/analysis/custom)
   - 自定义维度
   - 自定义图表
   - 保存分析

8. 数据可视化 (/projects/:id/visualize)
   - 可视化配置
   - 图表库
   - 交互式图表
```

#### H. 团队协作模块 (7+ 页)
```
1. 团队管理 (/teams)
   - 团队列表
   - 创建团队
   - 团队设置

2. 成员管理 (/teams/:teamId/members)
   - 成员列表
   - 邀请成员
   - 角色权限

3. 协作空间 (/teams/:teamId/workspace)
   - 共享项目
   - 共享文档
   - 协作动态

4. 权限管理 (/teams/:teamId/permissions)
   - 权限配置
   - 角色定义
   - 权限审计

5. 邀请管理 (/teams/:teamId/invites)
   - 邀请列表
   - 邀请链接
   - 邀请统计

6. 团队分析 (/teams/:teamId/analytics)
   - 使用统计
   - 活跃度分析
   - 贡献排名

7. 团队设置 (/teams/:teamId/settings)
   - 基本信息
   - 集成配置
   - 计费管理
```

#### I. 系统设置模块 (10+ 页)
```
1. 个人设置 (/settings/profile)
   - 基本信息
   - 头像上传
   - 偏好设置

2. 账户安全 (/settings/security)
   - 密码修改
   - 两步验证
   - 登录设备

3. 通知设置 (/settings/notifications)
   - 通知偏好
   - 邮件提醒
   - 推送设置

4. API 密钥 (/settings/api-keys)
   - 密钥列表
   - 创建密钥
   - 权限配置

5. 集成管理 (/settings/integrations)
   - 第三方集成
   - Webhook 配置
   - OAuth 应用

6. 计费管理 (/settings/billing)
   - 订阅计划
   - 使用量统计
   - 账单历史

7. 使用统计 (/settings/usage)
   - API 使用量
   - 存储使用量
   - 配额管理

8. 审计日志 (/settings/audit-log)
   - 操作记录
   - 安全事件
   - 导出日志

9. 开发者设置 (/settings/developer)
   - API 文档
   - SDK 下载
   - 沙箱环境

10. 系统偏好 (/settings/preferences)
    - 主题切换
    - 语言设置
    - 快捷键配置
```

#### J. 搜索和发现模块 (4+ 页)
```
1. 全局搜索 (/search)
   - 全文搜索
   - 高级筛选
   - 搜索建议

2. 关键词搜索 (/search/keywords)
   - 关键词提取
   - 相关推荐
   - 趋势分析

3. 语义搜索 (/search/semantic)
   - 向量检索
   - 相似度排序
   - 关联发现

4. 搜索管理 (/search/manage)
   - 搜索历史
   - 保存搜索
   - 搜索分析
```

#### K. 工作流和自动化模块 (6+ 页)
```
1. 工作流列表 (/workflows)
   - 工作流管理
   - 状态监控
   - 执行历史

2. 工作流编辑器 (/workflows/:id/edit)
   - 可视化编辑
   - 节点配置
   - 测试运行

3. 工作流执行 (/workflows/:id/executions)
   - 执行记录
   - 执行详情
   - 错误追踪

4. 自动化规则 (/automation/rules)
   - 规则列表
   - 创建规则
   - 规则测试

5. 定时任务 (/automation/scheduled)
   - 任务列表
   - Cron 配置
   - 执行日志

6. 触发器管理 (/automation/triggers)
   - 触发器列表
   - Webhook 触发
   - 事件触发
```

#### L. 监控和运维模块 (5+ 页)
```
1. 系统监控 (/admin/monitoring)
   - 性能指标
   - 资源使用
   - 实时监控

2. 健康检查 (/admin/health)
   - 服务状态
   - 依赖检查
   - 诊断工具

3. 日志查看 (/admin/logs)
   - 日志流
   - 日志搜索
   - 日志下载

4. 缓存管理 (/admin/cache)
   - 缓存统计
   - 缓存清理
   - 缓存配置

5. 系统配置 (/admin/config)
   - 系统参数
   - 功能开关
   - 维护模式
```

---

## 🎬 交互动画和反馈设计

### 上传进度系统（重点）
```typescript
// 多种进度状态
interface UploadProgress {
  // 准备阶段
  preparing: {
    status: 'validating' | 'ready'
    animation: '旋转加载器'
  }
  
  // 上传阶段
  uploading: {
    status: 'uploading'
    progress: 0-100  // 实时进度
    speed: string    // 上传速度
    remaining: string // 剩余时间
    animation: '进度条 + 百分比数字'
  }
  
  // 处理阶段
  processing: {
    status: 'processing'
    stage: '文件解析' | '内容提取' | '索引构建'
    animation: '脉动加载器'
  }
  
  // 完成阶段
  completed: {
    status: 'success'
    animation: '✓ 勾选动画'
    duration: 500ms
  }
  
  // 错误处理
  error: {
    status: 'error'
    message: string
    retry: boolean
    animation: '抖动 + 红色提示'
  }
}
```

### 动画库选择
- **Framer Motion** - 高级动画和手势
- **React Spring** - 物理动画
- **GSAP** - 复杂时间线动画
- **Lottie** - 设计师动画

### 核心交互动画
1. **页面过渡** - 淡入淡出 + 滑动
2. **卡片悬停** - 微妙的抬升和阴影
3. **按钮点击** - 缩放反馈
4. **列表加载** - 骨架屏 → 内容渐显
5. **模态框** - 缩放 + 遮罩淡入
6. **通知提示** - 滑入 + 自动消失
7. **拖拽操作** - 实时预览 + 放置提示
8. **加载状态** - 精致的骨架屏
9. **成功/失败** - Lottie 动画反馈
10. **数据更新** - 数字滚动动画

---

## 🎨 UI 组件库完整清单

### 基础组件 (30+)
```
1. Button (8 variants)
2. Input (6 types)
3. Textarea
4. Select/Dropdown
5. Checkbox
6. Radio
7. Switch
8. Slider
9. Badge
10. Tag
11. Avatar
12. Icon
13. Divider
14. Spacer
15. Container
16. Grid
17. Flex
18. Stack
19. Skeleton
20. Spinner
21. Progress Bar
22. Progress Ring
23. Tooltip
24. Popover
25. Menu
26. Dropdown Menu
27. Context Menu
28. Breadcrumb
29. Pagination
30. Steps
```

### 表单组件 (15+)
```
1. Form
2. Form Item
3. Form Label
4. Form Error
5. Form Helper
6. Input Group
7. Input Addon
8. Color Picker
9. Date Picker
10. Time Picker
11. Date Range Picker
12. File Upload
13. Image Upload
14. Drag & Drop Upload
15. Rich Text Editor
```

### 数据展示组件 (20+)
```
1. Table
2. Data Table (高级)
3. List
4. Tree
5. Timeline
6. Calendar
7. Card
8. Collapse/Accordion
9. Tabs
10. Carousel
11. Image Gallery
12. Empty State
13. Result Page
14. Statistic
15. Description List
16. Code Block
17. JSON Viewer
18. Markdown Viewer
19. PDF Viewer
20. Chart (Recharts)
```

### 反馈组件 (15+)
```
1. Alert
2. Toast/Notification
3. Message
4. Modal/Dialog
5. Drawer
6. Confirm Dialog
7. Loading Overlay
8. Progress Modal
9. Backdrop
10. Snackbar
11. Banner
12. Callout
13. Status Indicator
14. Error Boundary
15. Retry Button
```

### 导航组件 (10+)
```
1. Navbar
2. Sidebar
3. Top Bar
4. Bottom Nav
5. Breadcrumb
6. Pagination
7. Back Top
8. Anchor
9. Page Header
10. Command Palette (⌘K)
```

### 布局组件 (8+)
```
1. Layout
2. Header
3. Sidebar
4. Content
5. Footer
6. Affix
7. Split Pane
8. Responsive Grid
```

---

## 📦 前端技术栈升级

### 核心框架
```json
{
  "react": "^18.2.0",
  "typescript": "^5.3.0",
  "vite": "^5.0.0"
}
```

### UI 和样式
```json
{
  "@radix-ui/react-*": "最新版",  // 全套 Radix UI
  "tailwindcss": "^3.4.0",
  "framer-motion": "^10.0.0",
  "react-spring": "^9.7.0",
  "lottie-react": "^2.4.0",
  "class-variance-authority": "^0.7.0",
  "tailwind-merge": "^2.0.0"
}
```

### 数据可视化
```json
{
  "recharts": "^2.10.0",
  "d3": "^7.8.0",
  "cytoscape": "^3.28.0",
  "react-force-graph": "^1.44.0",
  "victory": "^36.9.0",
  "@nivo/core": "^0.84.0"
}
```

### 富文本和编辑器
```json
{
  "@tiptap/react": "^2.1.0",
  "@tiptap/starter-kit": "^2.1.0",
  "react-markdown": "^9.0.0",
  "react-syntax-highlighter": "^15.5.0",
  "monaco-editor": "^0.45.0",
  "@monaco-editor/react": "^4.6.0"
}
```

### 文件处理
```json
{
  "react-dropzone": "^14.2.0",
  "react-pdf": "^7.6.0",
  "pdf.js": "^4.0.0",
  "mammoth": "^1.6.0",  // Word 预览
  "xlsx": "^0.18.0"      // Excel 处理
}
```

### 状态和数据
```json
{
  "@tanstack/react-query": "^5.14.0",
  "zustand": "^4.4.0",
  "immer": "^10.0.0",
  "axios": "^1.6.0",
  "socket.io-client": "^4.6.0"  // 实时通信
}
```

### 工具库
```json
{
  "date-fns": "^2.30.0",
  "lodash-es": "^4.17.0",
  "nanoid": "^5.0.0",
  "copy-to-clipboard": "^3.3.0",
  "file-saver": "^2.0.0",
  "js-cookie": "^3.0.0"
}
```

---

## 📋 开发里程碑计划

### 第一阶段：基础设施 (1-2 天)
- [ ] 完整的 UI 组件库（shadcn/ui + 自定义）
- [ ] 设计系统和主题配置
- [ ] 布局和导航系统
- [ ] 全局状态管理架构
- [ ] API 客户端完整封装

### 第二阶段：核心功能页面 (2-3 天)
- [ ] 认证系统（登录/注册）
- [ ] Dashboard（总览/工作台）
- [ ] 项目管理（列表/详情/设置）
- [ ] 文档管理（上传/列表/详情）
- [ ] 上传进度系统（完整实现）

### 第三阶段：高级功能 (2-3 天)
- [ ] 知识图谱可视化（D3.js/Cytoscape.js）
- [ ] AI 对话界面
- [ ] 数据质量模块
- [ ] 报告和分析
- [ ] 搜索系统

### 第四阶段：协作和管理 (1-2 天)
- [ ] 团队协作功能
- [ ] 权限管理
- [ ] 审计日志
- [ ] 系统设置

### 第五阶段：优化和完善 (1-2 天)
- [ ] 性能优化
- [ ] 动画打磨
- [ ] 响应式适配
- [ ] 无障碍优化
- [ ] 错误边界和降级

### 第六阶段：测试和文档 (1 天)
- [ ] 组件测试
- [ ] E2E 测试
- [ ] 使用文档
- [ ] Storybook

---

## 💡 下一步行动

我建议我们现在一起：

1. **确认设计方向** - 我们要参考哪些产品的设计？
2. **优先级排序** - 哪些页面最重要，先做哪些？
3. **设计评审** - 我先设计几个核心页面的原型，您审核后再开发
4. **组件优先** - 先完成 UI 组件库，建立设计系统
5. **渐进开发** - 一个模块一个模块完整做好，不要同时开多条线

您觉得这个计划如何？我们从哪里开始？
