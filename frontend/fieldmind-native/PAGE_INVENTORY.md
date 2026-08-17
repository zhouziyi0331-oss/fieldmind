# FieldMind 完整页面清单

本文档详细记录HTML中所有30个页面的组件、功能和API调用，用于SwiftUI完整复刻。

## 扫描方法
- 从 index.html 第 3058 行开始扫描所有 page-section
- 记录每个页面的：组件类型、数据展示、交互功能、API端点

---

## 1. page-overview (行 3058) - 项目概览

### 组件清单
- **Hero 区块**
  - hero-eyebrow: "当前项目 · 2024"
  - hero-title: 项目标题（支持换行）
  - hero-sub: 项目描述
  - hero-stats: 5个统计数字（已处理材料、提炼关键词、业态推演、激活Skill、SOP完成度）

- **4个统计卡片 (g4 grid)**
  - stat-card 带颜色主题 (a1/a2/a5/a3)
  - 每个卡片：图标、标签、数值、增量（↑/—）

- **核心工作流 (steps)**
  - 5步流程，每步包含：图标、标题、描述

- **最近处理材料列表 (file-list)**
  - file-item: 图标（audio/video/doc/sheet）、文件名、元数据、状态（done/proc/pend）

- **热门关键词 (prog-list)**
  - prog-item: 关键词名称、出现次数、进度条

- **激活Skill列表**
  - 带绿点、标签、状态tag

### API调用
- 无明确API调用（从全局状态读取）

---

## 2. page-import (行 3126) - 材料导入

### 组件清单
- **上传区 (upload-zone)**
  - 图标、标题、说明文本
  - 支持文件类型标签: MP3, MP4, WAV, MD, XLSX, PDF
  - 上传进度条 (upload-progress)

- **文件选择器**
  - input[type=file] multiple accept

- **AI处理设置卡片**
  - 5个复选框选项

- **快速统计卡片**
  - 本月上传、本周处理、待处理、已完成

- **最近上传记录**
  - 文件列表，带操作按钮

### API调用
- 需要记录具体上传端点

---

## 3. page-keyword (行 3179) - 关键词引擎

### 组件清单
- **页头操作**
  - 按钮：按频次排序、导出关键词表
  
- **关键词云 (kw-cloud)**
  - kw-tag 多种尺寸：xl/lg/md/sm/xs
  - 三种颜色主题：ta/tb/tc
  - 点击打开模态框：openKeywordModal()

- **关键词详情面板 (kw-panel)**
  - 标题 + 统计（出现次数、材料数量）
  - 时间链路 (tl-item)：日期 + 描述文本
  - 材料定位 (src-item)：类型图标 + 文件名 + 时间码/段落位置

- **侧边统计卡片**
  - 关键词分布进度条
  - AI核心洞察文本

### API调用
- 获取关键词列表
- 获取单个关键词详情（时间链路+材料定位）

---

## 4. page-advanced-search (行 3254) - 高级搜索

### 组件清单
- **搜索栏**
  - 带图标的输入框
  - 4个下拉筛选器：项目/类型/时间/自定义
  - 搜索按钮

- **统计概览 (g5 grid)**
  - 5个 kpi-card：文件总数、对话记录、关键词库、图谱实体、数据总量

- **搜索结果列表**
  - 结果计数显示
  - 卡片式结果项：图标、标题、元数据、高亮片段

- **统计图表区**
  - 待读取详细内容

### API调用
- 全文搜索 API
- 统计数据 API

---

## 5. page-busi (行 3579) - 业态分析报告

### 组件清单
待扫描（需要读取详细内容）

---

## 6. page-dashboard (行 3604) - 可视化看板

### 组件清单
- **实时指示器**
  - rt-indicator 带动画圆点

- **5个KPI卡片 (g5 grid)**
  - 处理材料总数、提炼关键词、最高业态可行性、业态推演数量、SOP完成度
  - 每个带增量显示

- **Chart.js 图表（8个）**
  1. chart-trend: 关键词频次趋势（折线图）
  2. chart-biz: 业态可行性评估（柱状图）
  3. chart-type: 材料类型分布（饼图）
  4. chart-kw: 关键词类别分布（饼图）
  5. chart-verify: 模型验证状态（饼图）
  6. chart-sop: SOP完成度（雷达图）
  7. chart-weekly: 材料处理进度（折线图）
  8. 其他图表

- **图例系统**
  - legend/legend-item/legend-line/legend-dot

### API调用
- 仪表盘实时数据 API
- 图表数据 API（多个端点）

---

## 7. page-model (行 3632) - 模型管理

### 组件清单
待扫描

---

## 8. page-skill (行 3651) - Skill生态

### 组件清单
待扫描

---

## 9. page-sop-analysis (行 3675) - SOP分析

### 组件清单
待扫描

---

## 10. page-timeline (行 4003) - 时间线

### 组件清单
待扫描

---

## 11. page-report (行 4091) - 调研报告（类型1）

### 组件清单
待扫描

---

## 12. page-vein (行 5615) - 知识脉络

### 组件清单
待扫描

---

## 13. page-graph-explorer (行 5980) - 知识图谱

### 组件清单
待扫描

---

## 14. page-chronicle (行 6363) - 编年史

### 组件清单
待扫描

---

## 15. page-report3 (行 6626) - 调研报告（类型2）

### 组件清单
待扫描

---

## 16. page-chat (行 7251) - AI对话

### 组件清单
待扫描

---

## 17. page-conversations (行 7431) - 对话历史

### 组件清单
待扫描

---

## 18. page-newproject (行 8066) - 新建项目

### 组件清单
待扫描

---

## 19. page-quality-monitor (行 8133) - 质量监控

### 组件清单
待扫描

---

## 20. page-agent-memory (行 8793) - Agent记忆

### 组件清单
待扫描

---

## 21. page-settings (行 9081) - 设置

### 组件清单
待扫描

---

## 22. page-projects (行 9823) - 项目列表

### 组件清单
待扫描

---

## 23. page-project-detail (行 9964) - 项目详情

### 组件清单
待扫描

---

## 24. page-upload (行 10295) - 文件上传

### 组件清单
待扫描

---

## 25. page-file-manager (行 10442) - 文件管理器

### 组件清单
待扫描

---

## 26. page-photos (行 10738) - 照片管理

### 组件清单
待扫描

---

## 27. page-citations (行 10865) - 引用管理

### 组件清单
待扫描

---

## 28. page-tables (行 11052) - 表格管理

### 组件清单
待扫描

---

## 29. page-sop (行 11203) - SOP管理

### 组件清单
待扫描

---

## 30. page-workflow (需要查找) - 工作流复用

### 组件清单
待扫描

---

## 下一步
逐页扫描HTML，填充每个页面的详细组件清单、数据结构和API调用
