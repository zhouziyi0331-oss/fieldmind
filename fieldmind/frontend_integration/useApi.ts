// src/hooks/useApi.ts
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
