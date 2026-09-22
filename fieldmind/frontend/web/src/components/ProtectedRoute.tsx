import React from 'react'
import { Navigate } from 'react-router-dom'
import { authService } from '../services/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * 受保护的路由组件
 * 如果用户未登录，重定向到登录页
 *
 * 临时禁用：后端暂无认证系统
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // 临时禁用认证检查 - 后端暂无认证系统
  // if (!authService.isAuthenticated()) {
  //   return <Navigate to="/login" replace />
  // }

  return <>{children}</>
}

export default ProtectedRoute
