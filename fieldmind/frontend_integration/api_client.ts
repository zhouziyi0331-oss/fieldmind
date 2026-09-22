// src/api/client.ts
/**
 * API Client - 统一的后端 API 调用封装
 * 基于 axios 和 React Query
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// ============================================
// 配置
// ============================================

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
}

const defaultConfig: ApiClientConfig = {
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

// ============================================
// API 客户端基类
// ============================================

export class BaseApiClient {
  private instance: AxiosInstance;

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.instance = axios.create({
      ...defaultConfig,
      ...config,
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器 - 添加 token
    this.instance.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器 - 统一错误处理
    this.instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token 过期，尝试刷新
          const refreshed = await this.refreshToken();
          if (refreshed) {
            // 重试原请求
            return this.instance.request(error.config);
          }
          // 刷新失败，跳转登录
          this.handleUnauthorized();
        }
        return Promise.reject(error);
      }
    );
  }

  private getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      return true;
    } catch {
      return false;
    }
  }

  private handleUnauthorized() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }

  // HTTP 方法
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }
}

// ============================================
// 通用类型定义
// ============================================

export interface PaginatedResponse<T> {
  code: number;
  message: string;
  data: T[];
  meta: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface ApiError {
  code: number;
  message: string;
  errors?: Array<{
    field: string;
    message: string;
  }>;
}

export interface QueryParams {
  page?: number;
  page_size?: number;
  sort?: string;
  filter?: string;
  search?: string;
}

// ============================================
// 资源客户端基类
// ============================================

export class ResourceClient<T, CreateT = Partial<T>, UpdateT = Partial<T>> {
  constructor(
    protected client: BaseApiClient,
    protected resourcePath: string
  ) {}

  async list(params?: QueryParams): Promise<PaginatedResponse<T>> {
    return this.client.get<PaginatedResponse<T>>(this.resourcePath, { params });
  }

  async get(id: string): Promise<ApiResponse<T>> {
    return this.client.get<ApiResponse<T>>(`${this.resourcePath}/${id}`);
  }

  async create(data: CreateT): Promise<ApiResponse<T>> {
    return this.client.post<ApiResponse<T>>(this.resourcePath, data);
  }

  async update(id: string, data: UpdateT): Promise<ApiResponse<T>> {
    return this.client.put<ApiResponse<T>>(`${this.resourcePath}/${id}`, data);
  }

  async partialUpdate(id: string, data: Partial<UpdateT>): Promise<ApiResponse<T>> {
    return this.client.patch<ApiResponse<T>>(`${this.resourcePath}/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.client.delete<void>(`${this.resourcePath}/${id}`);
  }

  async search(query: string, params?: QueryParams): Promise<PaginatedResponse<T>> {
    return this.client.post<PaginatedResponse<T>>(`${this.resourcePath}/search`, {
      query,
      ...params,
    });
  }
}

// ============================================
// 具体资源客户端
// ============================================

// User 类型定义
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  name: string;
  password: string;
  role?: string;
}

export interface UserUpdate {
  email?: string;
  name?: string;
  role?: string;
}

// Users Client
export class UsersClient extends ResourceClient<User, UserCreate, UserUpdate> {
  constructor(client: BaseApiClient) {
    super(client, '/users');
  }

  async me(): Promise<ApiResponse<User>> {
    return this.client.get<ApiResponse<User>>('/users/me');
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    return this.client.post('/users/me/password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }
}

// Document 类型定义
export interface Document {
  id: string;
  title: string;
  content: string;
  project_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  title: string;
  content: string;
  project_id: string;
}

export interface DocumentUpdate {
  title?: string;
  content?: string;
}

// Documents Client
export class DocumentsClient extends ResourceClient<Document, DocumentCreate, DocumentUpdate> {
  constructor(client: BaseApiClient) {
    super(client, '/documents');
  }

  async export(id: string, format: 'pdf' | 'markdown' | 'html'): Promise<Blob> {
    return this.client.post(`/documents/${id}/export`, { format }, {
      responseType: 'blob',
    });
  }
}

// Project 类型定义
export interface Project {
  id: string;
  name: string;
  description: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

// Projects Client
export class ProjectsClient extends ResourceClient<Project, ProjectCreate, ProjectUpdate> {
  constructor(client: BaseApiClient) {
    super(client, '/projects');
  }

  async getMembers(id: string): Promise<ApiResponse<User[]>> {
    return this.client.get<ApiResponse<User[]>>(`/projects/${id}/members`);
  }

  async addMember(id: string, userId: string, role: string): Promise<void> {
    return this.client.post(`/projects/${id}/members`, { user_id: userId, role });
  }
}

// ============================================
// API 客户端实例
// ============================================

class ApiClient {
  private baseClient: BaseApiClient;

  // 资源客户端
  public users: UsersClient;
  public documents: DocumentsClient;
  public projects: ProjectsClient;

  constructor() {
    this.baseClient = new BaseApiClient();

    // 初始化资源客户端
    this.users = new UsersClient(this.baseClient);
    this.documents = new DocumentsClient(this.baseClient);
    this.projects = new ProjectsClient(this.baseClient);
  }

  // 认证相关
  async login(email: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
    const response = await this.baseClient.post<ApiResponse<any>>('/auth/login', {
      email,
      password,
    });

    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    return { access_token, refresh_token };
  }

  async logout(): Promise<void> {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }

  async register(data: UserCreate): Promise<ApiResponse<User>> {
    return this.baseClient.post<ApiResponse<User>>('/auth/register', data);
  }
}

// 导出单例
export const apiClient = new ApiClient();

// 默认导出
export default apiClient;
