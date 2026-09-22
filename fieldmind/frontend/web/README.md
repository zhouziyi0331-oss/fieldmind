# FieldMind Web - 管理后台

田野调查知识管理系统 - React Web管理后台

## 技术栈

- **框架**: React 18 + TypeScript
- **构建**: Vite
- **状态管理**: React Query + Zustand
- **UI组件**: Ant Design / shadcn/ui
- **图表**: Recharts + Plotly
- **路由**: React Router v6
- **网络**: Axios
- **图可视化**: ReactFlow / Cytoscape.js

## 项目结构

```
fieldmind-web/
├── public/
├── src/
│   ├── main.tsx                # 应用入口
│   ├── App.tsx                 # 根组件
│   │
│   ├── pages/                  # 页面组件
│   │   ├── Dashboard/
│   │   │   └── index.tsx
│   │   ├── Documents/
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentDetail.tsx
│   │   │   └── DocumentEditor.tsx
│   │   ├── KnowledgeGraph/
│   │   │   ├── GraphView.tsx
│   │   │   └── EntityManager.tsx
│   │   ├── Search/
│   │   │   └── SearchPage.tsx
│   │   ├── Analytics/
│   │   │   └── AnalyticsPage.tsx
│   │   └── Settings/
│   │       └── SettingsPage.tsx
│   │
│   ├── components/             # 通用组件
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── AudioPlayer/
│   │   │   └── AudioPlayer.tsx
│   │   ├── DocumentCard/
│   │   │   └── DocumentCard.tsx
│   │   └── GraphVisualization/
│   │       └── GraphCanvas.tsx
│   │
│   ├── hooks/                  # 自定义Hooks
│   │   ├── useDocuments.ts
│   │   ├── useSearch.ts
│   │   ├── useKnowledgeGraph.ts
│   │   └── useAuth.ts
│   │
│   ├── services/               # API服务
│   │   ├── api.ts
│   │   ├── documentService.ts
│   │   ├── searchService.ts
│   │   └── graphService.ts
│   │
│   ├── store/                  # 状态管理
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   │
│   ├── types/                  # TypeScript类型
│   │   ├── document.ts
│   │   ├── entity.ts
│   │   └── api.ts
│   │
│   ├── utils/                  # 工具函数
│   │   ├── formatters.ts
│   │   └── validators.ts
│   │
│   └── styles/                 # 样式文件
│       └── globals.css
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 功能模块

### 1. 仪表盘
- 📊 数据统计总览
- 📈 趋势图表
- 🔔 最近活动
- 📋 待办事项

### 2. 文档管理
- 📄 文档列表（表格/卡片视图）
- 🔍 高级搜索和过滤
- ✏️ 在线编辑器
- 📎 附件管理
- 🏷️ 标签管理

### 3. 知识图谱
- 🕸️ 交互式图可视化
- 👤 实体管理（人物/地点/事件/概念）
- 🔗 关系编辑
- 🎯 图查询构建器
- 📊 图统计分析

### 4. 搜索功能
- 🔎 全局搜索
- 🧠 语义搜索
- 📝 全文搜索
- 🕸️ 图搜索
- 📂 高级过滤

### 5. 数据分析
- 📊 主题分布
- 🗺️ 地理热力图
- 📅 时间线视图
- 📈 统计报表

### 6. 系统管理
- 👥 用户管理
- 🔐 权限配置
- ⚙️ 系统设置
- 📦 数据导入/导出

## 快速开始

### 1. 安装依赖
```bash
cd fieldmind-web
npm install
# 或
pnpm install
```

### 2. 配置环境变量
创建 `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### 3. 启动开发服务器
```bash
npm run dev
```

访问: http://localhost:5173

### 4. 构建生产版本
```bash
npm run build
```

## 核心代码示例

### API服务
```typescript
// services/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### React Query Hook
```typescript
// hooks/useDocuments.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentService } from '@/services/documentService'

export function useDocuments() {
  const queryClient = useQueryClient()

  // 获取文档列表
  const { data, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: documentService.getAll,
  })

  // 创建文档
  const createMutation = useMutation({
    mutationFn: documentService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  // 删除文档
  const deleteMutation = useMutation({
    mutationFn: documentService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  return {
    documents: data,
    isLoading,
    error,
    createDocument: createMutation.mutate,
    deleteDocument: deleteMutation.mutate,
  }
}
```

### 知识图谱可视化
```typescript
// components/GraphVisualization/GraphCanvas.tsx
import ReactFlow, { Node, Edge } from 'reactflow'
import 'reactflow/dist/style.css'

interface GraphCanvasProps {
  nodes: Node[]
  edges: Edge[]
}

export function GraphCanvas({ nodes, edges }: GraphCanvasProps) {
  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-left"
      />
    </div>
  )
}
```

## 依赖包

### 核心依赖
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "@tanstack/react-query": "^5.51.0",
    "zustand": "^5.0.0",
    "axios": "^1.7.2",
    "antd": "^5.19.0",
    "reactflow": "^11.11.0",
    "recharts": "^2.12.0",
    "plotly.js": "^2.34.0",
    "react-plotly.js": "^2.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.0",
    "tailwindcss": "^3.4.0"
  }
}
```

## UI组件库选择

### 方案1: Ant Design (推荐)
- ✅ 成熟稳定，组件丰富
- ✅ 中文文档友好
- ✅ 企业级UI设计
- ✅ 开箱即用

### 方案2: shadcn/ui
- ✅ 现代化设计
- ✅ Tailwind CSS集成
- ✅ 完全可定制
- ⚠️ 需要手动组装

## 路由配置

```typescript
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="documents" element={<DocumentList />} />
          <Route path="documents/:id" element={<DocumentDetail />} />
          <Route path="knowledge-graph" element={<GraphView />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  )
}
```

## 状态管理

### Zustand Store示例
```typescript
// store/authStore.ts
import { create } from 'zustand'

interface AuthState {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  
  login: async (email, password) => {
    const { user, token } = await authService.login(email, password)
    localStorage.setItem('token', token)
    set({ user, token })
  },
  
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },
}))
```

## 部署

### 构建
```bash
npm run build
# 输出到 dist/ 目录
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name fieldmind.example.com;
    
    root /var/www/fieldmind-web/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker部署
```dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 开发规范

### 代码风格
- ESLint + Prettier
- TypeScript严格模式
- 函数式组件 + Hooks
- 组件命名：PascalCase
- 文件命名：kebab-case

### Git提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

---

**开发者**: FieldMind Team  
**最后更新**: 2026-07-29
