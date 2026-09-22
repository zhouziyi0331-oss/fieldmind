/**
 * WebSocket Service
 *
 * 提供实时通信功能：
 * 1. Agent执行状态实时推送
 * 2. 文档处理状态更新
 * 3. 项目统计实时刷新
 * 4. 自动重连机制
 */

type WebSocketEventType =
  | 'connected'
  | 'agent_execution_start'
  | 'agent_execution_progress'
  | 'agent_execution_complete'
  | 'agent_task_update'
  | 'document_status'
  | 'project_stats';

interface WebSocketMessage {
  type: WebSocketEventType;
  [key: string]: any;
}

type MessageHandler = (message: WebSocketMessage) => void;

interface WebSocketOptions {
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private projectId: number | null = null;
  private handlers: Map<WebSocketEventType, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isIntentionallyClosed = false;

  // Options
  private autoReconnect = true;
  private reconnectInterval = 3000;
  private maxReconnectAttempts = 10;
  private debug = false;

  constructor(options: WebSocketOptions = {}) {
    this.autoReconnect = options.autoReconnect ?? true;
    this.reconnectInterval = options.reconnectInterval ?? 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 10;
    this.debug = options.debug ?? false;
  }

  /**
   * 连接到项目的WebSocket
   */
  connect(projectId: number): void {
    if (this.ws?.readyState === WebSocket.OPEN && this.projectId === projectId) {
      this.log('Already connected to project', projectId);
      return;
    }

    // 关闭现有连接
    if (this.ws) {
      this.isIntentionallyClosed = true;
      this.ws.close();
    }

    this.projectId = projectId;
    this.isIntentionallyClosed = false;
    this.reconnectAttempts = 0;

    this.createConnection();
  }

  /**
   * 创建WebSocket连接
   */
  private createConnection(): void {
    if (!this.projectId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/${this.projectId}`;

    this.log('Connecting to', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      this.log('Failed to create WebSocket', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 处理连接打开
   */
  private handleOpen(event: Event): void {
    this.log('WebSocket connected', event);
    this.reconnectAttempts = 0;

    // 清除重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 处理消息接收
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.log('Received message', message);

      // 分发消息给订阅者
      const handlers = this.handlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Handler error:', error);
          }
        });
      }

      // 通用处理器
      const allHandlers = this.handlers.get('*' as WebSocketEventType);
      if (allHandlers) {
        allHandlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Handler error:', error);
          }
        });
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * 处理错误
   */
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
  }

  /**
   * 处理连接关闭
   */
  private handleClose(event: CloseEvent): void {
    this.log('WebSocket closed', event.code, event.reason);

    if (!this.isIntentionallyClosed && this.autoReconnect) {
      this.scheduleReconnect();
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.min(this.reconnectAttempts, 5);

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.createConnection();
    }, delay);
  }

  /**
   * 订阅事件
   */
  on(eventType: WebSocketEventType | '*', handler: MessageHandler): () => void {
    if (!this.handlers.has(eventType as WebSocketEventType)) {
      this.handlers.set(eventType as WebSocketEventType, new Set());
    }

    this.handlers.get(eventType as WebSocketEventType)!.add(handler);

    // 返回取消订阅函数
    return () => {
      this.off(eventType, handler);
    };
  }

  /**
   * 取消订阅
   */
  off(eventType: WebSocketEventType | '*', handler: MessageHandler): void {
    const handlers = this.handlers.get(eventType as WebSocketEventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 发送消息（如果需要客户端发送）
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.projectId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * 获取连接状态
   */
  getState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 调试日志
   */
  private log(...args: any[]): void {
    if (this.debug) {
      console.log('[WebSocket]', ...args);
    }
  }
}

// 导出单例
export const websocketService = new WebSocketService({
  autoReconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  debug: (import.meta as any).env?.DEV || false // 开发环境开启调试
});

export default websocketService;

// 导出类型
export type { WebSocketMessage, WebSocketEventType, MessageHandler };
