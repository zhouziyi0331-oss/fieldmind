import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { useAuthStore } from '@/store/authStore'
import Layout from '@/components/layout/Layout'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Pages
import Dashboard from '@/pages/Dashboard'
import Projects from '@/pages/Projects'
import ProjectDetail from '@/pages/ProjectDetail'
import Documents from '@/pages/Documents'
import DocumentDetail from '@/pages/DocumentDetail'
import KnowledgeGraph from '@/pages/KnowledgeGraph'
import DataQuality from '@/pages/DataQuality'
import Chat from '@/pages/Chat'
import Reports from '@/pages/Reports'
import Analytics from '@/pages/Analytics'
import Timeline from '@/pages/Timeline'
import Workflows from '@/pages/Workflows'
import Citations from '@/pages/Citations'
import Memory from '@/pages/Memory'
import Monitoring from '@/pages/Monitoring'
import BusinessAnalysis from '@/pages/BusinessAnalysis'
import OCR from '@/pages/OCR'
import BatchProcessing from '@/pages/BatchProcessing'
import Visualization from '@/pages/Visualization'
import UserManagement from '@/pages/UserManagement'
import Login from '@/pages/Login'
import Settings from '@/pages/Settings'
import NotFound from '@/pages/NotFound'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Layout>{children}</Layout>
}

// Public Route wrapper (redirect to dashboard if authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects"
              element={
                <ProtectedRoute>
                  <Projects />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id"
              element={
                <ProtectedRoute>
                  <ProjectDetail />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/documents"
              element={
                <ProtectedRoute>
                  <Documents />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/knowledge-graph"
              element={
                <ProtectedRoute>
                  <KnowledgeGraph />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/data-quality"
              element={
                <ProtectedRoute>
                  <DataQuality />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/chat"
              element={
                <ProtectedRoute>
                  <Chat />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/reports"
              element={
                <ProtectedRoute>
                  <Reports />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/analytics"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/timeline"
              element={
                <ProtectedRoute>
                  <Timeline />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/workflows"
              element={
                <ProtectedRoute>
                  <Workflows />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/citations"
              element={
                <ProtectedRoute>
                  <Citations />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/memory"
              element={
                <ProtectedRoute>
                  <Memory />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/monitoring"
              element={
                <ProtectedRoute>
                  <Monitoring />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/business-analysis"
              element={
                <ProtectedRoute>
                  <BusinessAnalysis />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/ocr"
              element={
                <ProtectedRoute>
                  <OCR />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/batch-processing"
              element={
                <ProtectedRoute>
                  <BatchProcessing />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/visualization"
              element={
                <ProtectedRoute>
                  <Visualization />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects/:id/documents/:docId"
              element={
                <ProtectedRoute>
                  <DocumentDetail />
                </ProtectedRoute>
              }
            />

            <Route
              path="/users"
              element={
                <ProtectedRoute>
                  <UserManagement />
                </ProtectedRoute>
              }
            />

            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />

            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 404 Not Found */}
            <Route path="*" element={<NotFound />} />
          </Routes>

          {/* Global Toast Notifications */}
          <Toaster />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
