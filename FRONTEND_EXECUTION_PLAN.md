# FieldMind 前端开发执行文档

## 🎨 确认的设计方案

**方案**: 方案 C（混合数据+协作风格）+ 定制配色

### 核心设计原则
- ✅ 蓝绿色系为主色调
- ✅ 金色/橙色作为点缀
- ✅ 卡片式设计，圆角（无 emoji）
- ✅ 响应式布局，紧凑不拥挤
- ✅ 可收缩侧边栏
- ✅ 项目独立数据展示
- ✅ 丰富交互体验

---

## 🎨 配色系统（基于您提供的色板）

### 主色调 - 蓝绿色系

**方案 1: Sporty Fun**
```css
--primary: #178AB7;        /* 深青色 - 主要按钮 */
--primary-light: #6FA7B6;  /* 浅青色 - 悬停状态 */
--secondary: #9FAC24;      /* 黄绿色 - 次要操作 */
--accent-warm: #D9BC92;    /* 暖米色 - 卡片背景 */
--accent-dark: #45481D;    /* 深橄榄绿 - 文字强调 */
```

**方案 2: Succulents（推荐）**
```css
--primary: #27768A;        /* 深青蓝 - 主要按钮、导航 */
--primary-light: #589DA4;  /* 中青蓝 - 悬停、辅助 */
--secondary: #748D44;      /* 橄榄绿 - 次要操作、标签 */
--accent-light: #85A156;   /* 浅绿 - 成功状态 */
--background: #F0F5E2;     /* 极浅绿 - 页面背景 */
```

**方案 3: Tutti Frutti**
```css
--primary: #93AEC1;        /* 灰蓝 - 主色调 */
--secondary: #9DBDBA;      /* 青灰 - 次要元素 */
--accent-gold: #F8B042;    /* 金黄色 - 重要提示、成功 */
--accent-coral: #EC6A52;   /* 珊瑚红 - 警告、错误 */
--accent-pink: #F3B7AD;    /* 浅粉 - 柔和提示 */
```

### 最终配色方案（混合优化）

```css
:root {
  /* 主色调 - 蓝绿系 */
  --color-primary: #27768A;           /* 深青蓝 */
  --color-primary-light: #589DA4;     /* 中青蓝 */
  --color-primary-lighter: #93AEC1;   /* 灰蓝 */
  --color-primary-dark: #1E5A6B;      /* 更深青蓝 */
  
  /* 次色调 - 绿色系 */
  --color-secondary: #748D44;         /* 橄榄绿 */
  --color-secondary-light: #85A156;   /* 浅绿 */
  --color-secondary-lighter: #9FAC24; /* 黄绿 */
  
  /* 强调色 - 金色/橙色 */
  --color-accent-gold: #F8B042;       /* 金黄色 */
  --color-accent-orange: #D9BC92;     /* 暖米色 */
  --color-accent-coral: #EC6A52;      /* 珊瑚橙 */
  
  /* 语义化颜色 */
  --color-success: #85A156;           /* 成功 - 浅绿 */
  --color-warning: #F8B042;           /* 警告 - 金黄 */
  --color-error: #EC6A52;             /* 错误 - 珊瑚红 */
  --color-info: #589DA4;              /* 信息 - 中青蓝 */
  
  /* 背景色 */
  --color-background: #F8FAFB;        /* 主背景 */
  --color-surface: #FFFFFF;           /* 卡片背景 */
  --color-surface-hover: #F0F5E2;     /* 悬停背景 */
  
  /* 文字颜色 */
  --color-text-primary: #1A1A1A;      /* 主文字 */
  --color-text-secondary: #666666;    /* 次文字 */
  --color-text-tertiary: #999999;     /* 辅助文字 */
  
  /* 边框颜色 */
  --color-border: #E5E7EB;            /* 默认边框 */
  --color-border-hover: #589DA4;      /* 悬停边框 */
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(39, 118, 138, 0.05);
  --shadow-md: 0 4px 6px rgba(39, 118, 138, 0.08);
  --shadow-lg: 0 10px 15px rgba(39, 118, 138, 0.1);
  --shadow-xl: 0 20px 25px rgba(39, 118, 138, 0.12);
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
}
```

---

## 📋 开发优先级和计划

### 第一阶段：基础设施（P0 - 关键）⏰ 2-3天

#### 1.1 设计系统配置 ✅
- [x] Tailwind 配置（自定义配色）
- [x] CSS 变量系统
- [x] 字体配置（Inter）
- [x] 响应式断点

#### 1.2 核心 UI 组件库 🔥 **最优先**
**必须组件（30个）**
- [ ] Button (6 variants: primary, secondary, outline, ghost, link, icon)
- [ ] Input (text, email, password, search)
- [ ] Textarea
- [ ] Select / Dropdown
- [ ] Checkbox
- [ ] Radio
- [ ] Switch
- [ ] Slider
- [ ] Badge
- [ ] Tag
- [ ] Avatar
- [ ] Card
- [ ] Dialog / Modal
- [ ] Toast / Notification
- [ ] Tooltip
- [ ] Popover
- [ ] Tabs
- [ ] Progress Bar
- [ ] Progress Ring
- [ ] Skeleton
- [ ] Spinner / Loader
- [ ] Empty State
- [ ] Divider
- [ ] Alert
- [ ] Breadcrumb
- [ ] Pagination
- [ ] Table
- [ ] Drawer
- [ ] Collapse / Accordion
- [ ] Menu / Dropdown Menu

#### 1.3 布局系统
- [ ] 主布局组件（Layout）
- [ ] 侧边栏组件（可收缩）
- [ ] 顶部导航栏
- [ ] 面包屑导航
- [ ] 页面容器

#### 1.4 动画系统
- [ ] Framer Motion 配置
- [ ] 页面过渡动画
- [ ] 卡片悬停动画
- [ ] 加载动画
- [ ] 上传进度动画

---

### 第二阶段：核心功能页面（P1 - 重要）⏰ 3-4天

#### 2.1 认证系统 🔑
- [ ] 登录页（/login）
  - 表单验证
  - 错误提示
  - 记住我功能
  - 加载状态
  
- [ ] 注册页（/register）
  - 多步骤表单
  - 实时验证
  - 密码强度指示
  
- [ ] 忘记密码（/forgot-password）
  - 邮箱验证
  - 重置流程

#### 2.2 Dashboard 模块 📊 **核心**
- [ ] 总览 Dashboard（/dashboard）
  - 统计卡片（4个）
    - 项目总数
    - 文档总数
    - 知识节点
    - 数据质量
  - 数据趋势图（Recharts）
    - 文档增长曲线
    - 处理速度图表
  - 最近项目列表
  - 快速操作入口
  - 活动时间线

- [ ] 工作台（/dashboard/workspace）
  - 我的项目（卡片视图）
  - 收藏的文档
  - 待办事项
  - 最近访问

#### 2.3 项目管理模块 📁 **核心**
- [ ] 项目列表（/projects）
  - 网格/列表视图切换
  - 搜索和筛选
  - 排序功能
  - 创建项目按钮
  - 项目卡片（含统计）
  
- [ ] 创建项目对话框
  - 名称、描述输入
  - 模板选择
  - 成员邀请
  - 创建成功提示

- [ ] 项目详情（/projects/:id）
  - 项目头部信息
  - Tab 导航（概览/文档/图谱/分析）
  - 统计卡片
  - 快速操作

- [ ] 项目设置（/projects/:id/settings）
  - 基本信息编辑
  - 成员管理
  - 权限配置
  - 删除项目

---

### 第三阶段：文档管理（P1 - 重要）⏰ 3-4天

#### 3.1 文档列表 📄
- [ ] 文档列表页（/projects/:id/documents）
  - 表格视图
  - 卡片视图
  - 列表视图切换
  - 搜索和筛选
  - 批量操作
  - 上传按钮

#### 3.2 文档上传系统 📤 **重点功能**
- [ ] 上传区域
  - 拖拽上传（react-dropzone）
  - 点击选择文件
  - 文件类型验证
  - 大小限制提示
  - 多文件批量上传

- [ ] 上传进度组件 🔥 **核心交互**
  ```
  状态流程：
  1. 准备中（validating）
     - 旋转加载器
     - "验证文件..."
  
  2. 上传中（uploading）
     - 进度条（0-100%）
     - 实时速度（KB/s, MB/s）
     - 剩余时间估算
     - 百分比数字动画
     - 可暂停/取消
  
  3. 处理中（processing）
     - 脉动动画
     - 处理阶段提示
       - "文件解析中..."
       - "内容提取中..."
       - "索引构建中..."
  
  4. 完成（success）
     - ✓ 勾选动画（Lottie）
     - "上传成功！"
     - 查看文档按钮
  
  5. 错误（error）
     - 抖动动画
     - 错误信息
     - 重试按钮
  ```

- [ ] 上传队列管理
  - 队列列表
  - 单个文件进度
  - 暂停/继续/取消
  - 全部暂停/继续
  - 失败重试

#### 3.3 文档详情和操作
- [ ] 文档详情页（/projects/:id/documents/:docId）
  - 文档信息卡片
  - 处理状态展示
  - 分块预览
  - 元数据展示
  - 操作按钮（下载/删除/分享）

- [ ] 文档预览（/projects/:id/documents/:docId/preview）
  - PDF 预览（react-pdf）
  - 文本预览
  - 分页浏览

---

### 第四阶段：数据可视化（P1 - 重要）⏰ 3-4天

#### 4.1 知识图谱 🕸️ **亮点功能**
- [ ] 图谱页面（/projects/:id/knowledge-graph）
  - 力导向图（Cytoscape.js 或 D3.js）
  - 节点交互
    - 拖拽移动
    - 点击查看详情
    - 双击展开关联
  - 缩放和平移
  - 节点搜索
  - 关系筛选
  - 布局切换（力导向/层次/放射）
  - 图例说明
  - 导出功能

- [ ] 实体管理（/projects/:id/knowledge-graph/entities）
  - 实体列表
  - 实体类型筛选
  - 实体详情面板
  - 实体编辑

#### 4.2 数据质量 📈
- [ ] 质量总览（/projects/:id/data-quality）
  - 质量评分卡片
  - 趋势图表
  - 维度分布
  - 问题列表

- [ ] 质量报告（/projects/:id/data-quality/reports）
  - 报告生成
  - 报告下载
  - 历史记录

#### 4.3 数据分析和报告
- [ ] 报告中心（/projects/:id/reports）
  - 报告列表
  - 报告类型
  - 生成报告

- [ ] 可视化页面（/projects/:id/visualize）
  - 图表库（Recharts）
    - 折线图
    - 柱状图
    - 饼图
    - 雷达图
    - 散点图
  - 自定义配置
  - 导出图片

---

### 第五阶段：AI 对话和协作（P2 - 次要）⏰ 2-3天

#### 5.1 AI 对话
- [ ] 对话界面（/projects/:id/chat）
  - 消息列表
  - 输入框
  - 发送按钮
  - 流式响应
  - 引用文档
  - 历史记录

#### 5.2 团队协作
- [ ] 团队管理（/teams）
  - 团队列表
  - 创建团队
  - 成员管理

- [ ] 项目协作（/projects/:id/collaboration）
  - 成员列表
  - 邀请链接
  - 权限设置

---

### 第六阶段：系统设置和管理（P2 - 次要）⏰ 2-3天

#### 6.1 个人设置
- [ ] 个人资料（/settings/profile）
- [ ] 账户安全（/settings/security）
- [ ] 通知设置（/settings/notifications）

#### 6.2 系统管理
- [ ] API 管理（/settings/api-keys）
- [ ] 集成配置（/settings/integrations）
- [ ] 审计日志（/settings/audit-log）

---

### 第七阶段：优化和完善（P3 - 锦上添花）⏰ 2-3天

#### 7.1 性能优化
- [ ] 代码分割
- [ ] 路由懒加载
- [ ] 图片优化
- [ ] 虚拟滚动

#### 7.2 体验优化
- [ ] 骨架屏
- [ ] 错误边界
- [ ] 离线提示
- [ ] 快捷键
- [ ] 搜索建议

#### 7.3 响应式优化
- [ ] 移动端适配
- [ ] 平板适配
- [ ] 触摸手势

---

## 📝 开发追踪表

### 当前进度

| 阶段 | 任务 | 状态 | 完成度 | 备注 |
|-----|------|------|--------|------|
| P0 基础设施 | 设计系统配置 | ✅ 完成 | 100% | Tailwind + 配色完成 |
| P0 基础设施 | UI 组件库 | 🚧 进行中 | 50% | **进行中** |
| P0 基础设施 | 布局系统 | ⏳ 待开始 | 0% | - |
| P0 基础设施 | 动画系统 | ⏳ 待开始 | 0% | - |

### UI 组件库进度 (15/30 完成)

**已完成组件** ✅
- [x] Button (6 variants + loading)
- [x] Input (带 label + error)
- [x] Textarea (带 label + error)
- [x] Card (Header/Content/Footer)
- [x] Badge (6 variants)
- [x] Avatar (Image/Fallback)
- [x] Progress (带百分比)
- [x] Spinner (3 sizes)
- [x] Toast/Notification
- [x] Tabs
- [x] Dialog/Modal
- [x] Label
- [x] Skeleton
- [x] use-toast Hook
- [x] Toaster

**待完成组件** ⏳
- [ ] Select/Dropdown
- [ ] Checkbox
- [ ] Radio
- [ ] Switch
- [ ] Slider
- [ ] Tooltip
- [ ] Popover
- [ ] Alert
- [ ] Breadcrumb
- [ ] Pagination
- [ ] Table
- [ ] Dropdown Menu
- [ ] Empty State
- [ ] Divider
- [ ] Menu
| P1 核心功能 | 认证系统 | ⏳ 待开始 | 0% | - |
| P1 核心功能 | Dashboard | ⏳ 待开始 | 0% | - |
| P1 核心功能 | 项目管理 | ⏳ 待开始 | 0% | - |
| P1 核心功能 | 文档管理 | ⏳ 待开始 | 0% | - |
| P1 核心功能 | 知识图谱 | ⏳ 待开始 | 0% | - |
| P1 核心功能 | 数据质量 | ⏳ 待开始 | 0% | - |
| P2 次要功能 | AI 对话 | ⏳ 待开始 | 0% | - |
| P2 次要功能 | 团队协作 | ⏳ 待开始 | 0% | - |
| P2 次要功能 | 系统设置 | ⏳ 待开始 | 0% | - |
| P3 优化完善 | 性能优化 | ⏳ 待开始 | 0% | - |

### 总体进度
- **P0 基础设施**: 0/4 ⬜⬜⬜⬜
- **P1 核心功能**: 0/6 ⬜⬜⬜⬜⬜⬜
- **P2 次要功能**: 0/3 ⬜⬜⬜
- **P3 优化完善**: 0/1 ⬜

**总完成度**: 0/14 (0%)

---

## 🎯 下一步行动

### 立即开始：UI 组件库开发

**今天的任务**：
1. ✅ 确认配色方案
2. 🚀 创建 Tailwind 配置
3. 🚀 实现第一批组件（Button, Input, Card）
4. 🚀 搭建 Storybook（可选）

**明天的任务**：
1. 完成剩余基础组件
2. 创建布局系统
3. 开始 Dashboard 页面

---

## 📋 组件开发顺序

### 第一批（今天）
1. Button - 最基础
2. Input - 表单基础
3. Card - 容器基础

### 第二批（明天上午）
4. Modal/Dialog - 弹窗
5. Toast - 通知
6. Dropdown - 下拉

### 第三批（明天下午）
7. Tabs - 标签页
8. Table - 表格
9. Pagination - 分页

### 后续批次
按需开发其他组件...

---

## 🎨 视觉效果预期

### 按钮效果
```
主按钮：深青蓝背景 + 白色文字 + 悬停加深
次按钮：橄榄绿背景 + 白色文字
金色按钮：金黄色背景 + 深色文字（特殊操作）
```

### 卡片效果
```
白色背景 + 浅阴影
圆角 8px
悬停时阴影加深 + 轻微上移
```

### 数据展示
```
数字使用金黄色强调
图表使用蓝绿渐变
进度条使用青蓝到浅绿渐变
```

---

## ✅ 确认事项

- [x] 方案 C（混合风格）
- [x] 蓝绿色系配色
- [x] 卡片圆角，无 emoji
- [x] 响应式布局
- [x] 可收缩侧边栏
- [x] 项目独立数据
- [x] 丰富交互

**准备就绪！现在开始执行计划！** 🚀
