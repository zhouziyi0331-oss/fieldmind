import { create } from 'zustand';
import type { Project, ProjectStats } from '../types';
import { projectsApi } from '../services/api';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  currentStats: ProjectStats | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchProjects: () => Promise<void>;
  selectProject: (projectId: string) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<void>;
  updateProject: (id: string, name?: string, description?: string) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  refreshStats: () => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  currentStats: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const response = await projectsApi.getAll();
      set({ projects: response.data, loading: false });

      // Auto-select first project if none selected
      if (!get().currentProject && response.data.length > 0) {
        await get().selectProject(response.data[0].id);
      }
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  selectProject: async (projectId: string) => {
    set({ loading: true, error: null });
    try {
      const [projectRes, statsRes] = await Promise.all([
        projectsApi.getById(projectId),
        projectsApi.getStats(projectId),
      ]);
      set({
        currentProject: projectRes.data,
        currentStats: statsRes.data,
        loading: false,
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  createProject: async (name: string, description?: string) => {
    set({ loading: true, error: null });
    try {
      const response = await projectsApi.create({ name, description });
      set({ loading: false });
      await get().fetchProjects();
      await get().selectProject(response.data.id);
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  updateProject: async (id: string, name?: string, description?: string) => {
    set({ loading: true, error: null });
    try {
      await projectsApi.update(id, { name, description });
      set({ loading: false });
      await get().fetchProjects();
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  deleteProject: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await projectsApi.delete(id);
      set({ currentProject: null, currentStats: null, loading: false });
      await get().fetchProjects();
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  refreshStats: async () => {
    const current = get().currentProject;
    if (!current) return;

    try {
      const response = await projectsApi.getStats(current.id);
      set({ currentStats: response.data });
    } catch (error: any) {
      set({ error: error.message });
    }
  },
}));
