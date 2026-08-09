import React from 'react'
import { Navigate } from 'react-router-dom'
import { authService } from '../services/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * 受保护的路由组件
 * 如果用户未登录，重定向到登录页
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
