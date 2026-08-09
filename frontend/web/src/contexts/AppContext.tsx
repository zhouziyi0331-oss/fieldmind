import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

/**
 * 全局应用状态
 * 这是整个系统的"神经中枢"，所有页面通过它共享状态
 */
interface AppState {
  // 当前项目ID - 所有API请求必须使用这个ID
  currentProjectId: number | null;

  // 当前会话ID
  currentConversationId: number | null;

  // 最后上传的文件ID - 用于导入页→看板页的跳转
  lastUploadedFileId: number | null;

  // 刷新触发器 - 任何模块更新数据后，改变这个值强制其他模块刷新
  refreshTrigger: number;

  // 音频播放控制
  audioControl: {
    fileId: number | null;
    currentTime: number;
    isPlaying: boolean;
  };

  // 选中的实体 - 用于图谱→聊天的跳转
  selectedEntity: {
    name: string;
    type: string;
  } | null;
}

interface AppContextValue extends AppState {
  // 更新方法
  setCurrentProjectId: (id: number | null) => void;
  setCurrentConversationId: (id: number | null) => void;
  setLastUploadedFileId: (id: number | null) => void;
  triggerRefresh: () => void;

  // 音频控制
  playAudio: (fileId: number, startTime: number) => void;
  pauseAudio: () => void;
  updateAudioTime: (time: number) => void;

  // 实体选择
  selectEntity: (name: string, type: string) => void;
  clearSelectedEntity: () => void;

  // 导航助手 - 带状态的页面跳转
  navigateToGraph: (entityName?: string) => void;
  navigateToChat: (question?: string) => void;
  navigateToDashboard: () => void;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const params = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  // 初始化状态
  const [state, setState] = useState<AppState>({
    currentProjectId: null,
    currentConversationId: null,
    lastUploadedFileId: null,
    refreshTrigger: 0,
    audioControl: {
      fileId: null,
      currentTime: 0,
      isPlaying: false,
    },
    selectedEntity: null,
  });

  // 从URL同步projectId到全局状态
  useEffect(() => {
    if (params.projectId) {
      const projectId = parseInt(params.projectId);
      if (!isNaN(projectId) && projectId !== state.currentProjectId) {
        setState(prev => ({ ...prev, currentProjectId: projectId }));
      }
    }
  }, [params.projectId]);

  // 持久化到localStorage
  useEffect(() => {
    if (state.currentProjectId) {
      localStorage.setItem('lastProjectId', state.currentProjectId.toString());
    }
  }, [state.currentProjectId]);

  // 提供给组件的方法
  const value: AppContextValue = {
    ...state,

    setCurrentProjectId: (id: number | null) => {
      setState(prev => ({ ...prev, currentProjectId: id }));
    },

    setCurrentConversationId: (id: number | null) => {
      setState(prev => ({ ...prev, currentConversationId: id }));
    },

    setLastUploadedFileId: (id: number | null) => {
      setState(prev => ({ ...prev, lastUploadedFileId: id }));
    },

    // 触发全局刷新 - 任何数据变更后调用这个
    triggerRefresh: () => {
      setState(prev => ({ ...prev, refreshTrigger: Date.now() }));
      console.log('[AppContext] 触发全局刷新', Date.now());
    },

    // 音频控制
    playAudio: (fileId: number, startTime: number) => {
      setState(prev => ({
        ...prev,
        audioControl: {
          fileId,
          currentTime: startTime,
          isPlaying: true,
        },
      }));
      console.log(`[AppContext] 播放音频 fileId=${fileId} time=${startTime}`);
    },

    pauseAudio: () => {
      setState(prev => ({
        ...prev,
        audioControl: { ...prev.audioControl, isPlaying: false },
      }));
    },

    updateAudioTime: (time: number) => {
      setState(prev => ({
        ...prev,
        audioControl: { ...prev.audioControl, currentTime: time },
      }));
    },

    // 实体选择
    selectEntity: (name: string, type: string) => {
      setState(prev => ({
        ...prev,
        selectedEntity: { name, type },
      }));
      console.log(`[AppContext] 选中实体 ${name} (${type})`);
    },

    clearSelectedEntity: () => {
      setState(prev => ({ ...prev, selectedEntity: null }));
    },

    // 导航助手
    navigateToGraph: (entityName?: string) => {
      if (!state.currentProjectId) {
        console.error('[AppContext] navigateToGraph: 没有当前项目ID');
        return;
      }

      const url = `/projects/${state.currentProjectId}/knowledge-graph`;
      navigate(url);

      if (entityName) {
        // 延迟设置选中实体，确保图谱页面已加载
        setTimeout(() => {
          value.selectEntity(entityName, 'unknown');
        }, 100);
      }
    },

    navigateToChat: (question?: string) => {
      if (!state.currentProjectId) {
        console.error('[AppContext] navigateToChat: 没有当前项目ID');
        return;
      }

      const url = `/projects/${state.currentProjectId}/chat`;
      navigate(url);

      if (question) {
        // 将问题存储到sessionStorage，让ChatPage读取
        sessionStorage.setItem('pendingQuestion', question);
      }
    },

    navigateToDashboard: () => {
      if (!state.currentProjectId) {
        console.error('[AppContext] navigateToDashboard: 没有当前项目ID');
        return;
      }

      const url = `/projects/${state.currentProjectId}`;
      navigate(url);
    },
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

/**
 * 使用全局状态的Hook
 * 所有页面组件必须用这个Hook来访问全局状态
 */
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

/**
 * 监听刷新触发器的Hook
 * 用法：useRefreshListener(() => { 重新加载数据... })
 */
export const useRefreshListener = (callback: () => void) => {
  const { refreshTrigger } = useAppContext();

  useEffect(() => {
    if (refreshTrigger > 0) {
      console.log('[useRefreshListener] 检测到刷新信号，执行回调');
      callback();
    }
  }, [refreshTrigger]);
};
