#!/bin/bash
# FieldMind Web 项目初始化脚本

echo "🌐 初始化 FieldMind Web 管理后台..."
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装: https://nodejs.org"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 进入 Web 目录
cd fieldmind-web

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 安装 pnpm..."
    npm install -g pnpm
fi

echo "✅ pnpm 版本: $(pnpm --version)"
echo ""

# 使用 Vite 创建项目
echo "🚀 创建 React + TypeScript + Vite 项目..."
echo ""

# 创建 package.json
cat > package.json << 'JSON'
{
  "name": "fieldmind-web",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.6",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.5",
    "reactflow": "^11.10.4",
    "recharts": "^2.10.0",
    "dayjs": "^1.11.10",
    "zustand": "^4.4.7"
  },
  "devDependencies": {
    "@types/react": "^18.2.47",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.17.0",
    "@typescript-eslint/parser": "^6.17.0",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "typescript": "^5.3.3",
    "vite": "^5.0.11"
  }
}
JSON

# 创建 tsconfig.json
cat > tsconfig.json << 'JSON'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
JSON

# 创建 vite.config.ts
cat > vite.config.ts << 'TS'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
TS

# 创建目录结构
mkdir -p src/{api,components,pages,hooks,stores,types,utils}
mkdir -p src/components/{Layout,Audio,RAG,KnowledgeGraph,Common}
mkdir -p src/pages/{Dashboard,Audio,Documents,KnowledgeGraph,Search,Settings}
mkdir -p public

# 创建 API 服务
cat > src/api/client.ts << 'TS'
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

class APIClient {
  private instance: AxiosInstance;

  constructor(baseURL: string = '/api/v1') {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.get(url, config);
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.post(url, data, config);
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.put(url, data, config);
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.delete(url, config);
  }

  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.instance.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  }
}

export const apiClient = new APIClient();
TS

# 创建 API 服务模块
cat > src/api/audio.ts << 'TS'
import { apiClient } from './client';
import { AudioFile, TranscriptionResult } from '@/types';

export const audioAPI = {
  upload: (file: File, metadata?: Record<string, any>, onProgress?: (progress: number) => void) => 
    apiClient.upload<AudioFile>('/audio/upload', file, onProgress),

  transcribe: (fileId: string, language: string = 'zh') =>
    apiClient.post<TranscriptionResult>(`/audio/transcribe/${fileId}`, { language }),

  getAudioFile: (fileId: string) =>
    apiClient.get<AudioFile>(`/audio/${fileId}`),

  listAudioFiles: (params?: { skip?: number; limit?: number }) =>
    apiClient.get<AudioFile[]>('/audio', { params }),
};
TS

cat > src/api/rag.ts << 'TS'
import { apiClient } from './client';
import { RAGResponse, RAGDocument } from '@/types';

export const ragAPI = {
  query: (question: string, topK: number = 5) =>
    apiClient.post<RAGResponse>('/rag/query', { question, top_k: topK, return_sources: true }),

  search: (query: string, topK: number = 10) =>
    apiClient.post<RAGDocument[]>('/rag/search', { query, top_k: topK }),

  indexDocuments: (documents: any[]) =>
    apiClient.post('/rag/index', { documents }),

  deleteDocument: (documentId: string) =>
    apiClient.delete(`/rag/document/${documentId}`),
};
TS

cat > src/api/knowledgeGraph.ts << 'TS'
import { apiClient } from './client';
import { KGEntity, KGRelationship, GraphData } from '@/types';

export const kgAPI = {
  createEntity: (entityType: string, properties: Record<string, any>) =>
    apiClient.post<KGEntity>('/kg/entities', { entity_type: entityType, properties }),

  createRelationship: (fromId: string, toId: string, relType: string, properties?: Record<string, any>) =>
    apiClient.post('/kg/relationships', { from_id: fromId, to_id: toId, rel_type: relType, properties }),

  getEntity: (entityId: string) =>
    apiClient.get<KGEntity>(`/kg/entities/${entityId}`),

  getNeighbors: (entityId: string, depth: number = 1) =>
    apiClient.get<KGEntity[]>(`/kg/entities/${entityId}/neighbors`, { params: { depth } }),

  searchEntities: (query: string, entityType?: string) =>
    apiClient.post<KGEntity[]>('/kg/entities/search', { query, entity_type: entityType }),

  visualizeGraph: (entityId?: string, limit: number = 100) =>
    apiClient.get<GraphData>('/kg/visualize', { params: { entity_id: entityId, limit } }),
};
TS

# 创建类型定义
cat > src/types/index.ts << 'TS'
// Audio Types
export interface AudioFile {
  id: string;
  filename: string;
  filepath: string;
  filesize: number;
  duration?: number;
  format: string;
  sample_rate?: number;
  channels?: number;
  uploaded_at: string;
  metadata?: Record<string, string>;
}

export interface TranscriptionSegment {
  id: number;
  text: string;
  start: number;
  end: number;
}

export interface TranscriptionResult {
  file_id: string;
  text: string;
  language: string;
  segments: TranscriptionSegment[];
  processing_time: number;
}

// RAG Types
export interface RAGSource {
  id: string;
  content: string;
  score: number;
  metadata?: Record<string, string>;
}

export interface RAGResponse {
  answer: string;
  sources?: RAGSource[];
  processing_time?: number;
}

export interface RAGDocument {
  id: string;
  content: string;
  metadata?: Record<string, any>;
}

// Knowledge Graph Types
export interface KGEntity {
  id: string;
  entity_type: string;
  properties: Record<string, any>;
}

export interface KGRelationship {
  id: string;
  from_id: string;
  to_id: string;
  rel_type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    properties?: Record<string, any>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
  }>;
}
TS

# 创建主入口
cat > src/main.tsx << 'TSX'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
TSX

# 创建 App
cat > src/App.tsx << 'TSX'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import MainLayout from '@/components/Layout/MainLayout'
import Dashboard from '@/pages/Dashboard'
import './App.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="audio" element={<div>音频管理</div>} />
            <Route path="documents" element={<div>文档管理</div>} />
            <Route path="knowledge-graph" element={<div>知识图谱</div>} />
            <Route path="search" element={<div>智能搜索</div>} />
            <Route path="settings" element={<div>系统设置</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
TSX

# 创建基础样式
cat > src/index.css << 'CSS'
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
}

#root {
  min-height: 100vh;
}
CSS

cat > src/App.css << 'CSS'
.app {
  min-height: 100vh;
}
CSS

# 创建布局组件
cat > src/components/Layout/MainLayout.tsx << 'TSX'
import { Layout, Menu } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  AudioOutlined,
  FileTextOutlined,
  PartitionOutlined,
  SearchOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout

const MainLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/audio', icon: <AudioOutlined />, label: '音频管理' },
    { key: '/documents', icon: <FileTextOutlined />, label: '文档管理' },
    { key: '/knowledge-graph', icon: <PartitionOutlined />, label: '知识图谱' },
    { key: '/search', icon: <SearchOutlined />, label: '智能搜索' },
    { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
          <h2>FieldMind</h2>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}>
          <h1>田野调查知识管理系统</h1>
        </Header>
        <Content style={{ margin: '24px', padding: '24px', background: '#fff', minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
TSX

# 创建仪表盘页面
cat > src/pages/Dashboard/index.tsx << 'TSX'
import { Card, Row, Col, Statistic } from 'antd'
import { FileOutlined, AudioOutlined, PartitionOutlined, DatabaseOutlined } from '@ant-design/icons'

const Dashboard = () => {
  return (
    <div>
      <h2>系统概览</h2>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="音频文件"
              value={0}
              prefix={<AudioOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="文档数量"
              value={0}
              prefix={<FileOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="知识实体"
              value={0}
              prefix={<PartitionOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="向量数据"
              value={0}
              prefix={<DatabaseOutlined />}
              suffix="条"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
TSX

# 创建 HTML 模板
cat > index.html << 'HTML'
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FieldMind - 田野调查知识管理系统</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
HTML

# 创建 .gitignore
cat > .gitignore << 'IGNORE'
# Dependencies
node_modules
.pnp
.pnp.js

# Testing
coverage

# Production
dist
build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Editor
.vscode
.idea
*.swp
*.swo
IGNORE

echo ""
echo "✅ Web 项目结构创建完成"
echo ""
echo "📦 安装依赖..."
pnpm install

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FieldMind Web 项目初始化完成！"
echo ""
echo "📁 项目结构:"
echo "  src/api/          - API 服务层"
echo "  src/components/   - React 组件"
echo "  src/pages/        - 页面组件"
echo "  src/types/        - TypeScript 类型"
echo "  src/hooks/        - 自定义 Hooks"
echo "  src/stores/       - 状态管理"
echo ""
echo "🚀 启动开发服务器:"
echo "  cd fieldmind-web"
echo "  pnpm dev"
echo ""
echo "🌐 访问地址:"
echo "  http://localhost:3000"
echo ""
echo "📝 API 代理配置:"
echo "  /api -> http://localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
