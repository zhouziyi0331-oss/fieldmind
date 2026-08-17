import axios from 'axios';
import type { Project, ProjectStats, FileItem, Conversation, Message, SearchResult, GlobalStats } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Projects
export const projectsApi = {
  getAll: () => api.get<Project[]>('/projects'),
  getById: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post<Project>('/projects', data),
  update: (id: string, data: { name?: string; description?: string }) =>
    api.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  getStats: (id: string) => api.get<ProjectStats>(`/projects/${id}/stats`),
};

// Conversations
export const conversationsApi = {
  getAll: (projectId: string) =>
    api.get<Conversation[]>(`/projects/${projectId}/conversations`),
  getById: (id: string) =>
    api.get<Conversation>(`/conversations/${id}`),
  create: (projectId: string, title?: string) =>
    api.post<Conversation>(`/projects/${projectId}/conversations`, { title }),
  delete: (id: string) =>
    api.delete(`/conversations/${id}`),
  getMessages: (id: string) =>
    api.get<Message[]>(`/conversations/${id}/messages`),
  sendMessage: (id: string, content: string) => {
    // SSE endpoint - handled separately
    return `/api/conversations/${id}/messages`;
  },
};

// Files
export const filesApi = {
  getAll: (projectId: string) =>
    api.get<FileItem[]>(`/projects/${projectId}/files`),
  getById: (id: string) =>
    api.get<FileItem>(`/files/${id}`),
  upload: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<FileItem>(`/projects/${projectId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete: (id: string) =>
    api.delete(`/files/${id}`),
};

// Timeline
export const timelineApi = {
  generate: (projectId: string) => {
    return new EventSource(`/timeline?project_id=${projectId}`);
  },
};

// Narrative
export const narrativeApi = {
  generate: (projectId: string, query: string) => {
    const params = new URLSearchParams({ project_id: projectId, query });
    return new EventSource(`/narrative?${params}`);
  },
};

// Stats & Search
export const statsApi = {
  getGlobal: () => api.get<GlobalStats>('/stats'),
  search: (query: string) => api.get<SearchResult>(`/search?q=${encodeURIComponent(query)}`),
};

export default api;
