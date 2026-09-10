# FieldMind Frontend

现代化的知识管理系统前端应用

## ✨ 特性

- 🎨 **美观的 UI** - 基于 Radix UI + Tailwind CSS
- 🚀 **高性能** - Vite + React 18 + TypeScript
- 📊 **数据可视化** - D3.js 知识图谱 + Recharts 图表
- 📱 **响应式设计** - 完美适配所有设备
- 🎭 **流畅动画** - Framer Motion
- 🔒 **类型安全** - TypeScript 严格模式
- ♿ **无障碍** - WCAG 2.1 AA 标准

## 🚀 快速开始

### 环境要求

- Node.js >= 16
- npm >= 8

### 安装

```bash
# 克隆项目
cd frontend

# 安装依赖
npm install

# 复制环境配置
cp .env.example .env

# 配置 API 地址
# 编辑 .env 文件，设置 VITE_API_BASE_URL
```

### 开发

```bash
# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

### 构建

```bash
# 生产构建
npm run build

# 预览构建结果
npm run preview
```

## 📦 技术栈

### 核心框架
- React 18.2.0
- TypeScript 5.2.2
- Vite 5.0.8
- React Router 6.20.0

### UI 组件
- Radix UI（无障碍组件库）
- Tailwind CSS 3.4.0
- Lucide React（图标库）
- Framer Motion（动画库）

### 数据可视化
- D3.js 7.8.5（知识图谱）
- Recharts 2.10.3（统计图表）

### 状态管理
- Zustand 4.4.7
- TanStack Query 5.14.0

### 其他
- Axios（HTTP 客户端）
- date-fns（日期处理）
- react-dropzone（文件上传）

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # 组件
│   │   ├── ui/             # UI 组件库（30个）
│   │   ├── layout/         # 布局组件
│   │   ├── ErrorBoundary.tsx
│   │   └── GlobalLoading.tsx
│   │
│   ├── pages/              # 页面（9个）
│   │   ├── Dashboard.tsx
│   │   ├── Projects.tsx
│   │   ├── ProjectDetail.tsx
│   │   ├── Documents.tsx
│   │   ├── KnowledgeGraph.tsx
│   │   ├── DataQuality.tsx
│   │   ├── Login.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   │
│   ├── hooks/              # 自定义 Hooks
│   │   └── useFieldMind.ts
│   │
│   ├── services/           # API 服务
│   │   ├── api.ts
│   │   └── fieldmind.ts
│   │
│   ├── store/              # 状态管理
│   │   └── authStore.ts
│   │
│   ├── lib/                # 工具函数
│   │   └── utils.ts
│   │
│   ├── App.tsx             # 应用入口
│   ├── main.tsx            # 主文件
│   └── index.css           # 全局样式
│
├── public/                 # 静态资源
├── .env.example            # 环境配置示例
├── package.json            # 依赖配置
├── tsconfig.json           # TypeScript 配置
├── vite.config.ts          # Vite 配置
└── tailwind.config.js      # Tailwind 配置
```

## 🎨 UI 组件库

### 基础组件（11个）
- Button, Input, Textarea, Label
- Badge, Avatar, Spinner, Skeleton
- Progress, Slider, Empty State

### 表单组件（5个）
- Checkbox, Switch, Radio Group
- Select, FileUpload

### 反馈组件（7个）
- Toast, Alert, Dialog, Tooltip
- Popover, Toaster, use-toast

### 数据展示（4个）
- Card, Table, Tabs
- KnowledgeGraphVisualization

### 导航组件（3个）
- Dropdown Menu, Breadcrumb, Pagination

## 🔥 核心功能

### 1. 知识图谱可视化
- D3.js 力导向图
- 拖拽节点
- 缩放/平移
- 节点搜索和筛选
- 实时交互

### 2. 文件上传系统
- 拖拽上传
- 批量上传
- 实时进度
- 5种状态反馈
- Framer Motion 动画

### 3. 数据分析
- 统计图表（Recharts）
- 趋势分析
- 质量监控

### 4. 响应式设计
- 移动端适配
- 可收缩侧边栏
- 触摸友好

## 🎯 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 📝 开发规范

### 代码风格
- 使用 ESLint + TypeScript
- 组件使用函数式 + Hooks
- 严格的类型检查

### 命名规范
- 组件：PascalCase
- 文件：kebab-case.tsx
- 函数：camelCase
- 常量：UPPER_CASE

### Git 提交
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
perf: 性能优化
test: 测试
chore: 构建/工具
```

## 🔧 配置说明

### 环境变量
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=FieldMind
VITE_APP_VERSION=1.0.0
```

### 代理配置
开发环境自动代理 `/api` 到后端服务器

## 📚 文档

- [组件文档](./docs/components.md)
- [API 文档](./docs/api.md)
- [开发指南](./docs/development.md)

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 👥 团队

FieldMind 开发团队

---

**版本**: 1.0.0  
**更新时间**: 2026-09-10
