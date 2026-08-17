import { create } from 'zustand';
import type { FileItem } from '../types';
import { filesApi } from '../services/api';

interface FileState {
  files: FileItem[];
  loading: boolean;
  uploading: boolean;
  error: string | null;

  // Actions
  fetchFiles: (projectId: string) => Promise<void>;
  uploadFile: (projectId: string, file: File) => Promise<void>;
  deleteFile: (fileId: string) => Promise<void>;
  getFilesByType: (type: string) => FileItem[];
  getReadyFiles: () => FileItem[];
}

export const useFileStore = create<FileState>((set, get) => ({
  files: [],
  loading: false,
  uploading: false,
  error: null,

  fetchFiles: async (projectId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await filesApi.getAll(projectId);
      set({ files: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  uploadFile: async (projectId: string, file: File) => {
    set({ uploading: true, error: null });
    try {
      await filesApi.upload(projectId, file);
      set({ uploading: false });
      await get().fetchFiles(projectId);
    } catch (error: any) {
      set({ error: error.message, uploading: false });
    }
  },

  deleteFile: async (fileId: string) => {
    set({ loading: true, error: null });
    try {
      await filesApi.delete(fileId);
      set({
        files: get().files.filter(f => f.id !== fileId),
        loading: false
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  getFilesByType: (type: string) => {
    return get().files.filter(f => f.media_type === type);
  },

  getReadyFiles: () => {
    return get().files.filter(f => f.status === 'ready');
  },
}));
