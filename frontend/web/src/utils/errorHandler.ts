/**
 * 统一错误处理工具
 * 提供友好的错误提示
 */

import { AxiosError } from 'axios'

export interface ErrorResponse {
  success: false
  message: string
  error?: string
  error_code?: string
  timestamp?: string
}

export class AppError extends Error {
  code: string
  details?: any

  constructor(message: string, code: string = 'UNKNOWN_ERROR', details?: any) {
    super(message)
    this.name = 'AppError'
    this.code = code
    this.details = details
  }
}

/**
 * 解析API错误响应
 */
export function parseAPIError(error: unknown): AppError {
  // Axios错误
  if ((error as AxiosError).isAxiosError) {
    const axiosError = error as AxiosError<ErrorResponse>

    // 服务器返回的错误
    if (axiosError.response?.data) {
      const data = axiosError.response.data
      return new AppError(
        data.message || '服务器错误',
        data.error_code || `HTTP_${axiosError.response.status}`,
        data.error
      )
    }

    // 网络错误
    if (axiosError.code === 'ERR_NETWORK') {
      return new AppError(
        '无法连接到服务器，请检查网络连接',
        'NETWORK_ERROR'
      )
    }

    // 超时
    if (axiosError.code === 'ECONNABORTED') {
      return new AppError(
        '请求超时，请稍后重试',
        'TIMEOUT_ERROR'
      )
    }

    // 其他Axios错误
    return new AppError(
      axiosError.message || '请求失败',
      axiosError.code || 'REQUEST_ERROR'
    )
  }

  // AppError
  if (error instanceof AppError) {
    return error
  }

  // 普通Error
  if (error instanceof Error) {
    return new AppError(error.message, 'UNKNOWN_ERROR')
  }

  // 其他类型
  return new AppError('发生未知错误', 'UNKNOWN_ERROR', error)
}

/**
 * 获取用户友好的错误消息
 */
export function getUserFriendlyMessage(error: AppError): string {
  const errorMessages: Record<string, string> = {
    // 网络错误
    NETWORK_ERROR: '网络连接失败，请检查您的网络',
    TIMEOUT_ERROR: '请求超时，请稍后重试',

    // 认证错误
    UNAUTHORIZED: '您尚未登录或登录已过期，请重新登录',
    FORBIDDEN: '您没有权限执行此操作',
    INVALID_CREDENTIALS: '用户名或密码错误',
    TOKEN_EXPIRED: '登录已过期，请重新登录',

    // 资源错误
    NOT_FOUND: '请求的资源不存在',
    RESOURCE_NOT_FOUND: '找不到指定的内容',

    // 业务错误
    VALIDATION_ERROR: '输入的数据格式不正确，请检查',
    DUPLICATE_ENTRY: '该记录已存在',
    FILE_TOO_LARGE: '文件太大，请选择较小的文件',
    UNSUPPORTED_FILE_TYPE: '不支持的文件格式',

    // 服务器错误
    INTERNAL_SERVER_ERROR: '服务器内部错误，请稍后重试',
    SERVICE_UNAVAILABLE: '服务暂时不可用，请稍后重试',

    // HTTP状态码
    HTTP_400: '请求参数错误',
    HTTP_401: '未授权，请先登录',
    HTTP_403: '无权限访问',
    HTTP_404: '请求的内容不存在',
    HTTP_500: '服务器错误，请稍后重试',
    HTTP_503: '服务暂时不可用',
  }

  return errorMessages[error.code] || error.message
}

/**
 * 错误处理器 - 显示错误提示
 */
export function handleError(error: unknown, showNotification?: (message: string, type: 'error') => void) {
  const appError = parseAPIError(error)
  const message = getUserFriendlyMessage(appError)

  // 如果提供了通知函数，显示通知
  if (showNotification) {
    showNotification(message, 'error')
  } else {
    // 默认使用console.error
    console.error('❌ Error:', message, appError)
  }

  // 特殊处理：401跳转到登录页
  if (appError.code === 'UNAUTHORIZED' || appError.code === 'HTTP_401') {
    // 清除token
    localStorage.removeItem('auth_token')
    // 跳转登录（延迟以便显示错误消息）
    setTimeout(() => {
      window.location.href = '/login'
    }, 1500)
  }

  return appError
}

/**
 * 异步操作错误处理装饰器
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  errorHandler?: (error: AppError) => void
): T {
  return (async (...args: any[]) => {
    try {
      return await fn(...args)
    } catch (error) {
      const appError = parseAPIError(error)
      if (errorHandler) {
        errorHandler(appError)
      } else {
        handleError(error)
      }
      throw appError
    }
  }) as T
}

/**
 * 表单验证错误提取
 */
export function extractValidationErrors(error: AppError): Record<string, string> {
  if (error.code !== 'VALIDATION_ERROR' || !error.details?.errors) {
    return {}
  }

  const errors: Record<string, string> = {}
  for (const err of error.details.errors) {
    errors[err.field] = err.message
  }
  return errors
}
