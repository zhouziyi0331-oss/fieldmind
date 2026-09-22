#!/usr/bin/env python3
"""
Week 10-11 Day 1: 前端架构分析与设计

功能：
1. 分析现有前端代码结构
2. 识别前端技术栈
3. 设计前后端集成方案
4. 生成前端 API 客户端
5. 创建状态管理方案
"""

import os
import json
import re
from typing import Dict, List, Set
from collections import defaultdict
from datetime import datetime


class FrontendArchitectAnalyzer:
    """前端架构分析器"""

    def __init__(self, frontend_dir: str, api_spec_file: str, output_dir: str):
        self.frontend_dir = frontend_dir
        self.api_spec_file = api_spec_file
        self.output_dir = output_dir

        os.makedirs(f"{output_dir}/frontend_integration", exist_ok=True)

        # 加载 API 规范
        if os.path.exists(api_spec_file):
            with open(api_spec_file, 'r') as f:
                self.api_spec = json.load(f)
        else:
            self.api_spec = None

    def analyze_frontend_structure(self) -> Dict:
        """分析前端代码结构"""
        print("🔍 分析前端代码结构...")

        if not os.path.exists(self.frontend_dir):
            print(f"   ⚠️  前端目录不存在: {self.frontend_dir}")
            return self._create_default_structure()

        structure = {
            'total_files': 0,
            'by_extension': defaultdict(int),
            'by_type': defaultdict(list),
            'framework': None,
            'package_manager': None,
            'dependencies': {},
        }

        # 扫描文件
        for root, dirs, files in os.walk(self.frontend_dir):
            # 跳过 node_modules
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build']]

            for file in files:
                structure['total_files'] += 1
                ext = os.path.splitext(file)[1]
                structure['by_extension'][ext] += 1

                # 分类文件
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.frontend_dir)

                if ext in ['.jsx', '.tsx']:
                    structure['by_type']['components'].append(rel_path)
                elif ext in ['.js', '.ts']:
                    if 'api' in rel_path.lower() or 'service' in rel_path.lower():
                        structure['by_type']['api_clients'].append(rel_path)
                    elif 'store' in rel_path.lower() or 'redux' in rel_path.lower():
                        structure['by_type']['state_management'].append(rel_path)
                    elif 'hook' in rel_path.lower():
                        structure['by_type']['hooks'].append(rel_path)
                    else:
                        structure['by_type']['scripts'].append(rel_path)
                elif ext in ['.css', '.scss', '.less']:
                    structure['by_type']['styles'].append(rel_path)
                elif file == 'package.json':
                    structure['by_type']['configs'].append(rel_path)
                    self._analyze_package_json(file_path, structure)

        # 推断框架
        structure['framework'] = self._detect_framework(structure)

        # 转换 defaultdict
        structure['by_extension'] = dict(structure['by_extension'])
        structure['by_type'] = dict(structure['by_type'])

        print(f"   ✓ 扫描文件: {structure['total_files']}")
        print(f"   ✓ 检测框架: {structure['framework'] or '未知'}")
        print(f"   ✓ 包管理器: {structure['package_manager'] or '未知'}")

        return structure

    def _create_default_structure(self) -> Dict:
        """创建默认结构（如果前端目录不存在）"""
        return {
            'total_files': 0,
            'by_extension': {},
            'by_type': {},
            'framework': 'React',  # 假设使用 React
            'package_manager': 'npm',
            'dependencies': {},
        }

    def _analyze_package_json(self, file_path: str, structure: Dict):
        """分析 package.json"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)

            structure['dependencies'] = {
                **package_data.get('dependencies', {}),
                **package_data.get('devDependencies', {}),
            }

            # 检测包管理器
            if os.path.exists(os.path.join(os.path.dirname(file_path), 'pnpm-lock.yaml')):
                structure['package_manager'] = 'pnpm'
            elif os.path.exists(os.path.join(os.path.dirname(file_path), 'yarn.lock')):
                structure['package_manager'] = 'yarn'
            elif os.path.exists(os.path.join(os.path.dirname(file_path), 'package-lock.json')):
                structure['package_manager'] = 'npm'

        except Exception as e:
            print(f"   ⚠️  解析 package.json 失败: {e}")

    def _detect_framework(self, structure: Dict) -> str:
        """检测前端框架"""
        deps = structure.get('dependencies', {})

        if 'react' in deps:
            if 'next' in deps:
                return 'Next.js'
            return 'React'
        elif 'vue' in deps:
            if 'nuxt' in deps:
                return 'Nuxt.js'
            return 'Vue'
        elif 'angular' in deps or '@angular/core' in deps:
            return 'Angular'
        elif 'svelte' in deps:
            return 'Svelte'

        # 检查文件扩展名
        if '.jsx' in structure['by_extension'] or '.tsx' in structure['by_extension']:
            return 'React'
        elif '.vue' in structure['by_extension']:
            return 'Vue'

        return None

    def design_integration_architecture(self, frontend_structure: Dict) -> Dict:
        """设计前后端集成架构"""
        print("\n🎨 设计前后端集成架构...")

        framework = frontend_structure['framework'] or 'React'

        architecture = {
            'framework': framework,
            'layers': {
                'api_client': {
                    'description': 'API 客户端层 - 封装所有后端 API 调用',
                    'components': [
                        'BaseAPIClient',
                        'ResourceClients (users, documents, etc.)',
                        'RequestInterceptor',
                        'ResponseHandler',
                        'ErrorHandler',
                    ],
                    'technologies': ['axios', 'fetch'],
                },
                'state_management': {
                    'description': '状态管理层 - 管理全局应用状态',
                    'components': [
                        'Store Configuration',
                        'Actions',
                        'Reducers/Mutations',
                        'Selectors',
                        'Middleware',
                    ],
                    'technologies': self._get_state_management_tech(framework),
                },
                'data_hooks': {
                    'description': '数据钩子层 - 封装数据获取逻辑',
                    'components': [
                        'useQuery hooks',
                        'useMutation hooks',
                        'useInfiniteQuery hooks',
                        'Cache management',
                    ],
                    'technologies': ['React Query', 'SWR', 'Apollo Client'],
                },
                'ui_components': {
                    'description': 'UI 组件层 - 可复用的 UI 组件',
                    'components': [
                        'Layout Components',
                        'Form Components',
                        'Data Display Components',
                        'Feedback Components',
                    ],
                    'technologies': ['Ant Design', 'Material-UI', 'Tailwind CSS'],
                },
            },
            'patterns': {
                'data_fetching': 'React Query / SWR',
                'form_handling': 'React Hook Form',
                'routing': 'React Router',
                'authentication': 'JWT with Refresh Token',
                'error_handling': 'Error Boundary + Global Error Handler',
            },
        }

        print(f"   ✓ 框架: {framework}")
        print(f"   ✓ 设计了 {len(architecture['layers'])} 个架构层")

        return architecture

    def _get_state_management_tech(self, framework: str) -> List[str]:
        """获取状态管理技术"""
        if framework in ['React', 'Next.js']:
            return ['Redux Toolkit', 'Zustand', 'Jotai', 'Context API']
        elif framework in ['Vue', 'Nuxt.js']:
            return ['Vuex', 'Pinia']
        elif framework == 'Angular':
            return ['NgRx', 'Akita']
        else:
            return ['Redux']

    def generate_api_client(self, architecture: Dict) -> str:
        """生成 API 客户端代码"""
        print("\n💻 生成 API 客户端代码...")

        framework = architecture['framework']

        # 根据框架生成不同的客户端
        if framework in ['React', 'Next.js']:
            return self._generate_react_api_client()
        elif framework in ['Vue', 'Nuxt.js']:
            return self._generate_vue_api_client()
        else:
            return self._generate_generic_api_client()

    def _generate_react_api_client(self) -> str:
        """生成 React API 客户端"""

        client_code = """// src/api/client.ts
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
"""

        # 保存代码
        client_file = f"{self.output_dir}/frontend_integration/api_client.ts"
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(client_code)

        print(f"   ✓ 生成 API 客户端: {client_file}")

        return client_file

    def _generate_vue_api_client(self) -> str:
        """生成 Vue API 客户端"""
        # 简化版，与 React 类似
        return self._generate_react_api_client()

    def _generate_generic_api_client(self) -> str:
        """生成通用 API 客户端"""
        return self._generate_react_api_client()

    def generate_react_hooks(self) -> str:
        """生成 React 数据钩子"""
        print("\n🪝 生成 React Hooks...")

        hooks_code = """// src/hooks/useApi.ts
/**
 * React Query Hooks - 封装数据获取和缓存
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { apiClient, QueryParams, PaginatedResponse, ApiResponse } from '../api/client';
import type { User, UserCreate, UserUpdate } from '../api/client';
import type { Document, DocumentCreate, DocumentUpdate } from '../api/client';
import type { Project, ProjectCreate, ProjectUpdate } from '../api/client';

// ============================================
// Query Keys
// ============================================

export const queryKeys = {
  users: {
    all: ['users'] as const,
    lists: () => [...queryKeys.users.all, 'list'] as const,
    list: (params?: QueryParams) => [...queryKeys.users.lists(), params] as const,
    details: () => [...queryKeys.users.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
    me: () => [...queryKeys.users.all, 'me'] as const,
  },
  documents: {
    all: ['documents'] as const,
    lists: () => [...queryKeys.documents.all, 'list'] as const,
    list: (params?: QueryParams) => [...queryKeys.documents.lists(), params] as const,
    details: () => [...queryKeys.documents.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.documents.details(), id] as const,
  },
  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    list: (params?: QueryParams) => [...queryKeys.projects.lists(), params] as const,
    details: () => [...queryKeys.projects.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
  },
};

// ============================================
// Users Hooks
// ============================================

export function useUsers(params?: QueryParams, options?: UseQueryOptions<PaginatedResponse<User>>) {
  return useQuery({
    queryKey: queryKeys.users.list(params),
    queryFn: () => apiClient.users.list(params),
    ...options,
  });
}

export function useUser(id: string, options?: UseQueryOptions<ApiResponse<User>>) {
  return useQuery({
    queryKey: queryKeys.users.detail(id),
    queryFn: () => apiClient.users.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useCurrentUser(options?: UseQueryOptions<ApiResponse<User>>) {
  return useQuery({
    queryKey: queryKeys.users.me(),
    queryFn: () => apiClient.users.me(),
    ...options,
  });
}

export function useCreateUser(options?: UseMutationOptions<ApiResponse<User>, Error, UserCreate>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UserCreate) => apiClient.users.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
    ...options,
  });
}

export function useUpdateUser(options?: UseMutationOptions<ApiResponse<User>, Error, { id: string; data: UserUpdate }>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => apiClient.users.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
    },
    ...options,
  });
}

export function useDeleteUser(options?: UseMutationOptions<void, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.users.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
    ...options,
  });
}

// ============================================
// Documents Hooks
// ============================================

export function useDocuments(params?: QueryParams, options?: UseQueryOptions<PaginatedResponse<Document>>) {
  return useQuery({
    queryKey: queryKeys.documents.list(params),
    queryFn: () => apiClient.documents.list(params),
    ...options,
  });
}

export function useDocument(id: string, options?: UseQueryOptions<ApiResponse<Document>>) {
  return useQuery({
    queryKey: queryKeys.documents.detail(id),
    queryFn: () => apiClient.documents.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useCreateDocument(options?: UseMutationOptions<ApiResponse<Document>, Error, DocumentCreate>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DocumentCreate) => apiClient.documents.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
    },
    ...options,
  });
}

export function useUpdateDocument(options?: UseMutationOptions<ApiResponse<Document>, Error, { id: string; data: DocumentUpdate }>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => apiClient.documents.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.lists() });
    },
    ...options,
  });
}

export function useDeleteDocument(options?: UseMutationOptions<void, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.documents.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
    },
    ...options,
  });
}

export function useSearchDocuments(query: string, params?: QueryParams, options?: UseQueryOptions<PaginatedResponse<Document>>) {
  return useQuery({
    queryKey: [...queryKeys.documents.lists(), 'search', query, params],
    queryFn: () => apiClient.documents.search(query, params),
    enabled: !!query,
    ...options,
  });
}

// ============================================
// Projects Hooks
// ============================================

export function useProjects(params?: QueryParams, options?: UseQueryOptions<PaginatedResponse<Project>>) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: () => apiClient.projects.list(params),
    ...options,
  });
}

export function useProject(id: string, options?: UseQueryOptions<ApiResponse<Project>>) {
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => apiClient.projects.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useCreateProject(options?: UseMutationOptions<ApiResponse<Project>, Error, ProjectCreate>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProjectCreate) => apiClient.projects.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
    ...options,
  });
}

export function useUpdateProject(options?: UseMutationOptions<ApiResponse<Project>, Error, { id: string; data: ProjectUpdate }>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => apiClient.projects.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
    },
    ...options,
  });
}

export function useDeleteProject(options?: UseMutationOptions<void, Error, string>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.projects.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
    ...options,
  });
}

// ============================================
// 通用 Hook 工厂
// ============================================

export function createResourceHooks<T, CreateT = Partial<T>, UpdateT = Partial<T>>(
  resourceName: string,
  client: any
) {
  return {
    useList: (params?: QueryParams, options?: UseQueryOptions<PaginatedResponse<T>>) => {
      return useQuery({
        queryKey: [resourceName, 'list', params],
        queryFn: () => client.list(params),
        ...options,
      });
    },

    useGet: (id: string, options?: UseQueryOptions<ApiResponse<T>>) => {
      return useQuery({
        queryKey: [resourceName, 'detail', id],
        queryFn: () => client.get(id),
        enabled: !!id,
        ...options,
      });
    },

    useCreate: (options?: UseMutationOptions<ApiResponse<T>, Error, CreateT>) => {
      const queryClient = useQueryClient();

      return useMutation({
        mutationFn: (data: CreateT) => client.create(data),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: [resourceName] });
        },
        ...options,
      });
    },

    useUpdate: (options?: UseMutationOptions<ApiResponse<T>, Error, { id: string; data: UpdateT }>) => {
      const queryClient = useQueryClient();

      return useMutation({
        mutationFn: ({ id, data }) => client.update(id, data),
        onSuccess: (_, variables) => {
          queryClient.invalidateQueries({ queryKey: [resourceName, 'detail', variables.id] });
          queryClient.invalidateQueries({ queryKey: [resourceName, 'list'] });
        },
        ...options,
      });
    },

    useDelete: (options?: UseMutationOptions<void, Error, string>) => {
      const queryClient = useQueryClient();

      return useMutation({
        mutationFn: (id: string) => client.delete(id),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: [resourceName] });
        },
        ...options,
      });
    },
  };
}
"""

        hooks_file = f"{self.output_dir}/frontend_integration/useApi.ts"
        with open(hooks_file, 'w', encoding='utf-8') as f:
            f.write(hooks_code)

        print(f"   ✓ 生成 React Hooks: {hooks_file}")

        return hooks_file

    def generate_integration_guide(self, frontend_structure: Dict, architecture: Dict):
        """生成前端集成指南"""
        print("\n📖 生成前端集成指南...")

        framework = architecture['framework']

        guide = f"""# FieldMind 前端集成指南

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、前端架构概览

### 技术栈
- **框架**: {framework}
- **状态管理**: {', '.join(architecture['patterns'].get('data_fetching', ['React Query']))}
- **API 客户端**: Axios
- **表单处理**: {architecture['patterns'].get('form_handling', 'React Hook Form')}
- **路由**: {architecture['patterns'].get('routing', 'React Router')}

### 架构分层

```
┌─────────────────────────────────────────┐
│         UI Components Layer              │
│  - Pages, Layouts, Components            │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Data Hooks Layer                 │
│  - useUsers, useDocuments, etc.          │
│  - React Query / SWR                     │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         API Client Layer                 │
│  - ResourceClients (typed)               │
│  - Request/Response interceptors         │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Backend API (RESTful)            │
│  - /api/v1/users, /api/v1/documents      │
└─────────────────────────────────────────┘
```

---

## 二、快速开始

### 1. 安装依赖

```bash
# 核心依赖
npm install axios @tanstack/react-query

# TypeScript 支持
npm install -D @types/node

# 可选：表单处理
npm install react-hook-form

# 可选：UI 库
npm install antd
# 或
npm install @mui/material @emotion/react @emotion/styled
```

### 2. 配置 API 客户端

创建 `.env` 文件:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_API_TIMEOUT=30000
```

### 3. 初始化 React Query

```tsx
// src/App.tsx
import {{ QueryClient, QueryClientProvider }} from '@tanstack/react-query';
import {{ ReactQueryDevtools }} from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({{
  defaultOptions: {{
    queries: {{
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }},
  }},
}});

function App() {{
  return (
    <QueryClientProvider client={{queryClient}}>
      {{/* Your app */}}
      <ReactQueryDevtools initialIsOpen={{false}} />
    </QueryClientProvider>
  );
}}

export default App;
```

### 4. 使用 API Hooks

```tsx
// src/pages/UsersList.tsx
import {{ useUsers, useDeleteUser }} from '../hooks/useApi';

function UsersList() {{
  // 获取用户列表
  const {{ data, isLoading, error }} = useUsers({{
    page: 1,
    page_size: 20,
  }});

  // 删除用户
  const deleteUser = useDeleteUser({{
    onSuccess: () => {{
      alert('User deleted successfully');
    }},
  }});

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {{error.message}}</div>;

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {{data?.data.map(user => (
          <li key={{user.id}}>
            {{user.name}} ({{user.email}})
            <button onClick={{() => deleteUser.mutate(user.id)}}>
              Delete
            </button>
          </li>
        ))}}
      </ul>
    </div>
  );
}}
```

---

## 三、API 客户端详解

### 基础使用

```typescript
import {{ apiClient }} from './api/client';

// 登录
await apiClient.login('user@example.com', 'password');

// 获取用户列表
const users = await apiClient.users.list({{ page: 1, page_size: 20 }});

// 创建用户
const newUser = await apiClient.users.create({{
  email: 'new@example.com',
  name: 'New User',
  password: 'password123',
}});

// 更新用户
await apiClient.users.update('user-id', {{
  name: 'Updated Name',
}});

// 删除用户
await apiClient.users.delete('user-id');
```

### 认证流程

```typescript
// 登录
const {{ access_token, refresh_token }} = await apiClient.login(email, password);

// Token 自动保存到 localStorage
// 后续请求自动添加 Authorization header

// 登出
await apiClient.logout();
```

### Token 自动刷新

API 客户端会自动处理 token 刷新:

1. 请求返回 401
2. 自动使用 refresh_token 刷新
3. 重试原请求
4. 如果刷新失败，跳转登录页

---

## 四、数据 Hooks 详解

### useUsers - 用户列表

```tsx
const {{ data, isLoading, error, refetch }} = useUsers({{
  page: 1,
  page_size: 20,
  sort: 'created_at:desc',
  filter: 'role:admin',
}});

// 数据结构
// data.data: User[]
// data.meta: {{ page, page_size, total, total_pages }}
```

### useUser - 单个用户

```tsx
const {{ data, isLoading, error }} = useUser(userId, {{
  enabled: !!userId, // 只在 userId 存在时请求
  refetchInterval: 30000, // 每 30 秒自动刷新
}});

// 数据结构
// data.data: User
```

### useCreateUser - 创建用户

```tsx
const createUser = useCreateUser({{
  onSuccess: (data) => {{
    console.log('Created:', data.data);
  }},
  onError: (error) => {{
    console.error('Failed:', error);
  }},
}});

// 使用
const handleSubmit = async (formData) => {{
  await createUser.mutateAsync(formData);
}};

// 或
createUser.mutate(formData);
```

### useUpdateUser - 更新用户

```tsx
const updateUser = useUpdateUser();

updateUser.mutate({{
  id: 'user-id',
  data: {{ name: 'New Name' }},
}});
```

### useDeleteUser - 删除用户

```tsx
const deleteUser = useDeleteUser({{
  onSuccess: () => {{
    // 自动 invalidate 相关查询
    alert('Deleted successfully');
  }},
}});

deleteUser.mutate('user-id');
```

---

## 五、完整示例

### 示例 1: 用户管理页面

```tsx
// src/pages/Users.tsx
import React, {{ useState }} from 'react';
import {{
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
}} from '../hooks/useApi';
import type {{ UserCreate }} from '../api/client';

export function UsersPage() {{
  const [page, setPage] = useState(1);
  const [isCreating, setIsCreating] = useState(false);

  // 获取用户列表
  const {{ data, isLoading }} = useUsers({{ page, page_size: 20 }});

  // Mutations
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const handleCreate = async (formData: UserCreate) => {{
    await createUser.mutateAsync(formData);
    setIsCreating(false);
  }};

  const handleDelete = (id: string) => {{
    if (confirm('Are you sure?')) {{
      deleteUser.mutate(id);
    }}
  }};

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Users Management</h1>

      <button onClick={{() => setIsCreating(true)}}>
        Create New User
      </button>

      {{isCreating && (
        <UserForm onSubmit={{handleCreate}} onCancel={{() => setIsCreating(false)}} />
      )}}

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {{data?.data.map(user => (
            <tr key={{user.id}}>
              <td>{{user.name}}</td>
              <td>{{user.email}}</td>
              <td>{{user.role}}</td>
              <td>
                <button onClick={{() => handleDelete(user.id)}}>
                  Delete
                </button>
              </td>
            </tr>
          ))}}
        </tbody>
      </table>

      {{/* 分页 */}}
      <div>
        <button
          disabled={{page === 1}}
          onClick={{() => setPage(p => p - 1)}}
        >
          Previous
        </button>
        <span>Page {{page}} of {{data?.meta.total_pages}}</span>
        <button
          disabled={{page === data?.meta.total_pages}}
          onClick={{() => setPage(p => p + 1)}}
        >
          Next
        </button>
      </div>
    </div>
  );
}}
```

### 示例 2: 文档编辑器

```tsx
// src/pages/DocumentEditor.tsx
import React, {{ useEffect }} from 'react';
import {{ useParams, useNavigate }} from 'react-router-dom';
import {{ useDocument, useUpdateDocument }} from '../hooks/useApi';
import {{ useForm }} from 'react-hook-form';
import type {{ DocumentUpdate }} from '../api/client';

export function DocumentEditor() {{
  const {{ id }} = useParams<{{ id: string }}>();
  const navigate = useNavigate();

  const {{ data, isLoading }} = useDocument(id!);
  const updateDocument = useUpdateDocument();

  const {{ register, handleSubmit, reset }} = useForm<DocumentUpdate>();

  useEffect(() => {{
    if (data?.data) {{
      reset({{
        title: data.data.title,
        content: data.data.content,
      }});
    }}
  }}, [data, reset]);

  const onSubmit = async (formData: DocumentUpdate) => {{
    await updateDocument.mutateAsync({{ id: id!, data: formData }});
    alert('Saved successfully');
  }};

  if (isLoading) return <div>Loading...</div>;
  if (!data) return <div>Document not found</div>;

  return (
    <div>
      <h1>Edit Document</h1>

      <form onSubmit={{handleSubmit(onSubmit)}}>
        <div>
          <label>Title</label>
          <input
            type="text"
            {{...register('title', {{ required: true }})}}
          />
        </div>

        <div>
          <label>Content</label>
          <textarea
            rows={{20}}
            {{...register('content')}}
          />
        </div>

        <button type="submit" disabled={{updateDocument.isPending}}>
          {{updateDocument.isPending ? 'Saving...' : 'Save'}}
        </button>

        <button type="button" onClick={{() => navigate('/documents')}}>
          Cancel
        </button>
      </form>
    </div>
  );
}}
```

### 示例 3: 搜索功能

```tsx
// src/components/DocumentSearch.tsx
import React, {{ useState, useEffect }} from 'react';
import {{ useSearchDocuments }} from '../hooks/useApi';
import {{ useDebounce }} from '../hooks/useDebounce';

export function DocumentSearch() {{
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);

  const {{ data, isLoading }} = useSearchDocuments(
    debouncedQuery,
    {{ page_size: 10 }},
    {{
      enabled: debouncedQuery.length > 2, // 至少 3 个字符才搜索
    }}
  );

  return (
    <div>
      <input
        type="search"
        placeholder="Search documents..."
        value={{query}}
        onChange={{e => setQuery(e.target.value)}}
      />

      {{isLoading && <div>Searching...</div>}}

      {{data && (
        <ul>
          {{data.data.map(doc => (
            <li key={{doc.id}}>
              <a href={{`/documents/${{doc.id}}`}}>
                {{doc.title}}
              </a>
            </li>
          ))}}
        </ul>
      )}}
    </div>
  );
}}
```

---

## 六、错误处理

### 全局错误处理

```tsx
// src/components/ErrorBoundary.tsx
import React, {{ Component, ReactNode }} from 'react';

interface Props {{
  children: ReactNode;
}}

interface State {{
  hasError: boolean;
  error: Error | null;
}}

export class ErrorBoundary extends Component<Props, State> {{
  state: State = {{ hasError: false, error: null }};

  static getDerivedStateFromError(error: Error) {{
    return {{ hasError: true, error }};
  }}

  componentDidCatch(error: Error, errorInfo: any) {{
    console.error('ErrorBoundary caught:', error, errorInfo);
  }}

  render() {{
    if (this.state.hasError) {{
      return (
        <div>
          <h1>Something went wrong</h1>
          <p>{{this.state.error?.message}}</p>
          <button onClick={{() => window.location.reload()}}>
            Reload
          </button>
        </div>
      );
    }}

    return this.props.children;
  }}
}}
```

### Query 错误处理

```tsx
const {{ data, error }} = useUsers();

if (error) {{
  // 根据错误类型显示不同消息
  if (error.message.includes('401')) {{
    return <div>Please login</div>;
  }}
  if (error.message.includes('403')) {{
    return <div>Access denied</div>;
  }}
  return <div>Error: {{error.message}}</div>;
}}
```

### Mutation 错误处理

```tsx
const createUser = useCreateUser({{
  onError: (error: any) => {{
    if (error.response?.data?.errors) {{
      // 显示字段级别错误
      const errors = error.response.data.errors;
      errors.forEach((err: any) => {{
        console.log(`${{err.field}}: ${{err.message}}`);
      }});
    }} else {{
      alert(error.message);
    }}
  }},
}});
```

---

## 七、性能优化

### 1. 分页和虚拟滚动

```tsx
import {{ useInfiniteQuery }} from '@tanstack/react-query';

function useInfiniteUsers() {{
  return useInfiniteQuery({{
    queryKey: ['users', 'infinite'],
    queryFn: ({{ pageParam = 1 }}) =>
      apiClient.users.list({{ page: pageParam, page_size: 20 }}),
    getNextPageParam: (lastPage) => {{
      const {{ page, total_pages }} = lastPage.meta;
      return page < total_pages ? page + 1 : undefined;
    }},
  }});
}}
```

### 2. 预加载数据

```tsx
import {{ useQueryClient }} from '@tanstack/react-query';

function UserRow({{ user }}) {{
  const queryClient = useQueryClient();

  const prefetchUser = () => {{
    queryClient.prefetchQuery({{
      queryKey: queryKeys.users.detail(user.id),
      queryFn: () => apiClient.users.get(user.id),
    }});
  }};

  return (
    <tr onMouseEnter={{prefetchUser}}>
      <td>{{user.name}}</td>
    </tr>
  );
}}
```

### 3. 乐观更新

```tsx
const updateUser = useUpdateUser({{
  onMutate: async ({{ id, data }}) => {{
    // 取消正在进行的查询
    await queryClient.cancelQueries({{ queryKey: queryKeys.users.detail(id) }});

    // 保存当前数据
    const previousUser = queryClient.getQueryData(queryKeys.users.detail(id));

    // 乐观更新
    queryClient.setQueryData(queryKeys.users.detail(id), (old: any) => ({{
      ...old,
      data: {{ ...old.data, ...data }},
    }}));

    return {{ previousUser }};
  }},
  onError: (err, variables, context) => {{
    // 回滚
    if (context?.previousUser) {{
      queryClient.setQueryData(
        queryKeys.users.detail(variables.id),
        context.previousUser
      );
    }}
  }},
}});
```

---

## 八、测试

### 单元测试

```tsx
// src/hooks/__tests__/useApi.test.tsx
import {{ renderHook, waitFor }} from '@testing-library/react';
import {{ QueryClient, QueryClientProvider }} from '@tanstack/react-query';
import {{ useUsers }} from '../useApi';

const createWrapper = () => {{
  const queryClient = new QueryClient({{
    defaultOptions: {{ queries: {{ retry: false }} }},
  }});

  return ({{ children }}) => (
    <QueryClientProvider client={{queryClient}}>
      {{children}}
    </QueryClientProvider>
  );
}};

test('useUsers fetches users', async () => {{
  const {{ result }} = renderHook(() => useUsers(), {{
    wrapper: createWrapper(),
  }});

  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  expect(result.current.data).toBeDefined();
  expect(result.current.data?.data).toBeInstanceOf(Array);
}});
```

---

## 九、部署

### 环境变量

```bash
# .env.development
REACT_APP_API_URL=http://localhost:8000/api/v1

# .env.production
REACT_APP_API_URL=https://api.fieldmind.com/api/v1
```

### 构建

```bash
npm run build
```

### Nginx 配置

```nginx
server {{
  listen 80;
  server_name app.fieldmind.com;

  root /var/www/fieldmind-frontend/build;
  index index.html;

  location / {{
    try_files $uri $uri/ /index.html;
  }}

  location /api {{
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }}
}}
```

---

**FieldMind 前端集成项目**
Week 10-11 集成指南
Version 1.0
"""

        guide_file = f"{self.output_dir}/frontend_integration/FRONTEND_INTEGRATION_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)

        print(f"   ✓ 保存到: {guide_file}")

        return guide_file

    def run(self):
        """执行完整分析流程"""
        print("=" * 70)
        print("Week 10-11 Day 1: 前端架构分析与设计")
        print("=" * 70)

        # 1. 分析前端结构
        frontend_structure = self.analyze_frontend_structure()

        # 2. 设计集成架构
        architecture = self.design_integration_architecture(frontend_structure)

        # 3. 生成 API 客户端
        api_client_file = self.generate_api_client(architecture)

        # 4. 生成 React Hooks
        hooks_file = self.generate_react_hooks()

        # 5. 生成集成指南
        guide_file = self.generate_integration_guide(frontend_structure, architecture)

        print("\n" + "=" * 70)
        print("前端架构分析与设计完成")
        print("=" * 70)

        print(f"\n📊 分析结果:")
        print(f"  前端文件数: {frontend_structure['total_files']}")
        print(f"  检测框架: {frontend_structure['framework'] or '未知'}")
        print(f"  架构层级: {len(architecture['layers'])}")

        print(f"\n📁 输出文件:")
        print(f"  - API 客户端: {api_client_file}")
        print(f"  - React Hooks: {hooks_file}")
        print(f"  - 集成指南: {guide_file}")

        return {
            'frontend_structure': frontend_structure,
            'architecture': architecture,
        }


def main():
    frontend_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/frontend"
    api_spec_file = "/Users/alwan/Downloads/FieldMind/fieldmind/consolidated_api/consolidated_design.json"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind"

    analyzer = FrontendArchitectAnalyzer(frontend_dir, api_spec_file, output_dir)
    result = analyzer.run()

    print("\n✅ 前端架构分析与设计完成！")


if __name__ == "__main__":
    main()
