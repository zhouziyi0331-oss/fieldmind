import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// 全局状态管理器
import { AppProvider } from './contexts/AppContext';

// 全局组件
import { GlobalAudioPlayer, AudioControlBar } from './components/GlobalAudioPlayer';

// 认证页面
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// 页面组件
import HomePage from './pages/HomePage';
import ProjectListPage from './pages/ProjectListPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import DocumentsPage from './pages/DocumentsPage';
import ChatPage from './pages/ChatPage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import TimelinePage from './pages/TimelinePage';
import AnalysisPage from './pages/AnalysisPage';
import MindMapDemo from './demo/MindMapDemo';

// 布局和保护组件
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppProvider>
          {/* 全局音频播放器 - 隐藏但全局可控 */}
          <GlobalAudioPlayer />

          {/* 底部音频控制条 */}
          <AudioControlBar />

          <Routes>
          {/* 公开路由 - 认证页面 */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* 受保护的路由 - 需要登录 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <HomePage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProjectListPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProjectDetailPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId/documents"
            element={
              <ProtectedRoute>
                <Layout>
                  <DocumentsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId/chat"
            element={
              <ProtectedRoute>
                <Layout>
                  <ChatPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId/knowledge-graph"
            element={
              <ProtectedRoute>
                <Layout>
                  <KnowledgeGraphPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId/timeline"
            element={
              <ProtectedRoute>
                <Layout>
                  <TimelinePage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId/analysis"
            element={
              <ProtectedRoute>
                <Layout>
                  <AnalysisPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* 演示页面（无需认证） */}
          <Route path="/demo/mindmap" element={<MindMapDemo />} />

          {/* 404重定向 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </AppProvider>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
