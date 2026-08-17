/**
 * useWebSocket Hook
 *
 * 提供React组件中使用WebSocket的便捷方式
 */

import { useEffect, useCallback, useRef } from 'react';
import websocketService, { WebSocketEventType, MessageHandler, WebSocketMessage } from '../services/websocket';

interface UseWebSocketOptions {
  projectId?: number;
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { projectId, autoConnect = true, onConnect, onDisconnect } = options;
  const handlersRef = useRef<Map<WebSocketEventType | '*', MessageHandler[]>>(new Map());

  // 自动连接
  useEffect(() => {
    if (autoConnect && projectId) {
      websocketService.connect(projectId);

      // 连接成功回调
      const unsubConnect = websocketService.on('connected', () => {
        if (onConnect) onConnect();
      });

      return () => {
        unsubConnect();
        websocketService.disconnect();
        if (onDisconnect) onDisconnect();
      };
    }
  }, [projectId, autoConnect, onConnect, onDisconnect]);

  /**
   * 订阅事件
   */
  const on = useCallback((eventType: WebSocketEventType | '*', handler: MessageHandler) => {
    // 记录handler以便清理
    if (!handlersRef.current.has(eventType)) {
      handlersRef.current.set(eventType, []);
    }
    handlersRef.current.get(eventType)!.push(handler);

    // 订阅WebSocket事件
    const unsubscribe = websocketService.on(eventType, handler);

    return unsubscribe;
  }, []);

  /**
   * 取消订阅
   */
  const off = useCallback((eventType: WebSocketEventType | '*', handler: MessageHandler) => {
    websocketService.off(eventType, handler);

    // 从记录中移除
    const handlers = handlersRef.current.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }, []);

  /**
   * 发送消息
   */
  const send = useCallback((message: any) => {
    websocketService.send(message);
  }, []);

  /**
   * 手动连接
   */
  const connect = useCallback((newProjectId: number) => {
    websocketService.connect(newProjectId);
  }, []);

  /**
   * 手动断开
   */
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  /**
   * 获取连接状态
   */
  const isConnected = useCallback(() => {
    return websocketService.isConnected();
  }, []);

  // 清理所有订阅
  useEffect(() => {
    return () => {
      handlersRef.current.forEach((handlers, eventType) => {
        handlers.forEach(handler => {
          websocketService.off(eventType, handler);
        });
      });
      handlersRef.current.clear();
    };
  }, []);

  return {
    on,
    off,
    send,
    connect,
    disconnect,
    isConnected
  };
}

/**
 * useAgentExecution Hook
 *
 * 专门用于监听Agent执行状态的Hook
 */
interface UseAgentExecutionOptions {
  executionId: string | null;
  projectId?: number;
  onStart?: (message: WebSocketMessage) => void;
  onProgress?: (message: WebSocketMessage) => void;
  onComplete?: (message: WebSocketMessage) => void;
  onTaskUpdate?: (message: WebSocketMessage) => void;
}

export function useAgentExecution(options: UseAgentExecutionOptions) {
  const { executionId, projectId, onStart, onProgress, onComplete, onTaskUpdate } = options;
  const ws = useWebSocket({ projectId, autoConnect: !!projectId });

  useEffect(() => {
    if (!executionId) return;

    const unsubscribers: (() => void)[] = [];

    // 订阅执行开始
    if (onStart) {
      const unsub = ws.on('agent_execution_start', (message) => {
        if (message.execution_id === executionId) {
          onStart(message);
        }
      });
      unsubscribers.push(unsub);
    }

    // 订阅执行进度
    if (onProgress) {
      const unsub = ws.on('agent_execution_progress', (message) => {
        if (message.execution_id === executionId) {
          onProgress(message);
        }
      });
      unsubscribers.push(unsub);
    }

    // 订阅执行完成
    if (onComplete) {
      const unsub = ws.on('agent_execution_complete', (message) => {
        if (message.execution_id === executionId) {
          onComplete(message);
        }
      });
      unsubscribers.push(unsub);
    }

    // 订阅任务更新
    if (onTaskUpdate) {
      const unsub = ws.on('agent_task_update', (message) => {
        if (message.execution_id === executionId) {
          onTaskUpdate(message);
        }
      });
      unsubscribers.push(unsub);
    }

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [executionId, onStart, onProgress, onComplete, onTaskUpdate, ws]);

  return ws;
}

export default useWebSocket;
