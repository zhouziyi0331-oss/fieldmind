import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useAppContext } from '../contexts/AppContext';
import { AgentOrchestrationPanel, AgentExecutionMonitor, AgentResultsViewer } from '../components';
import { Sparkles, ChevronRight } from 'lucide-react';

interface Message {
  id: number;
  role: string;
  content: string;
  thinking_process?: string;
  sources?: any[];
  created_at: string;
}

const ChatPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const location = useLocation();
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { selectedEntity, clearSelectedEntity, playAudio } = useAppContext();

  // Agent 面板状态
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [agentExecutionId, setAgentExecutionId] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<any>(null);
  const [agentResultType, setAgentResultType] = useState<'knowledge' | 'search' | 'summary' | 'transcript' | null>(null);

  // 处理从其他页面传来的预填问题
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const question = params.get('question');
    if (question) {
      setMessage(decodeURIComponent(question));
      // 清除URL参数
      window.history.replaceState({}, '', location.pathname);
    }
  }, [location]);

  // 获取会话列表
  const { data: sessionsData } = useQuery({
    queryKey: ['chat-sessions', projectId],
    queryFn: () => api.chat.listSessions(Number(projectId)),
  }) as { data: { sessions: any[]; total: number } | undefined };

  // 获取消息列表
  const { data: messagesData } = useQuery({
    queryKey: ['chat-messages', selectedSession],
    queryFn: () => api.chat.getMessages(selectedSession!),
    enabled: !!selectedSession,
  }) as { data: { messages: Message[]; total: number } | undefined };

  // 创建会话
  const createSessionMutation = useMutation({
    mutationFn: (name: string) =>
      api.chat.createSession({ project_id: Number(projectId), name }),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions', projectId] });
      setSelectedSession(data.id);
      setShowNewSessionModal(false);
      setNewSessionName('');
    },
  });

  // 发送消息
  const sendMessageMutation = useMutation({
    mutationFn: (content: string) =>
      api.chat.sendMessage(selectedSession!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', selectedSession] });
      setMessage('');
    },
  });

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesData]);

  // 自动选择第一个会话
  useEffect(() => {
    if (sessionsData && sessionsData.sessions && sessionsData.sessions.length > 0 && !selectedSession) {
      setSelectedSession(sessionsData.sessions[0].id);
    }
  }, [sessionsData, selectedSession]);

  // 解析消息中的时间戳链接并绑定播放功能
  const parseMessageContent = (content: string) => {
    // 匹配格式: [文件名 HH:MM:SS](file_id)
    const timestampRegex = /\[([^\]]+)\s+(\d{2}:\d{2}:\d{2})\]\((\d+)\)/g;

    const parts: (string | JSX.Element)[] = [];
    let lastIndex = 0;
    let match;

    while ((match = timestampRegex.exec(content)) !== null) {
      // 添加时间戳前的文本
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index));
      }

      const [fullMatch, filename, timestamp, fileId] = match;
      const [hours, minutes, seconds] = timestamp.split(':').map(Number);
      const timeInSeconds = hours * 3600 + minutes * 60 + seconds;

      // 创建可点击的时间戳按钮
      parts.push(
        <button
          key={match.index}
          onClick={() => playAudio(Number(fileId), timeInSeconds)}
          className="inline-flex items-center gap-1 px-2 py-1 mx-1 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded text-sm font-medium transition-colors"
          title={`点击播放: ${filename} ${timestamp}`}
        >
          🎵 {filename} {timestamp}
        </button>
      );

      lastIndex = match.index + fullMatch.length;
    }

    // 添加剩余文本
    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    return parts.length > 0 ? parts : content;
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && selectedSession) {
      sendMessageMutation.mutate(message);
    }
  };

  // Agent 执行完成处理
  const handleAgentComplete = (result: any) => {
    setAgentExecutionId(null);
    // 根据任务类型设置结果
    if (result?.result?.task_results && result.result.task_results.length > 0) {
      const firstTask = result.result.task_results[0];
      setAgentResult(firstTask.result);
      setAgentResultType(firstTask.agent_type as any);
    }
  };

  // Agent 执行开始处理
  const handleAgentExecutionStart = (executionId: string) => {
    setAgentExecutionId(executionId);
    setAgentResult(null);
    setAgentResultType(null);
  };

  // 关闭 Agent 面板
  const closeAgentPanel = () => {
    setShowAgentPanel(false);
    setAgentExecutionId(null);
    setAgentResult(null);
    setAgentResultType(null);
  };

  const messages = messagesData?.messages || [];
  const sessions = sessionsData?.sessions || [];

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 头部 */}
      <div className="bg-white shadow z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={`/projects/${projectId}`}
                className="text-gray-600 hover:text-gray-900"
              >
                ← 返回项目
              </Link>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-2xl font-bold">💬 AI对话</h1>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowAgentPanel(!showAgentPanel)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-colors ${
                  showAgentPanel
                    ? 'bg-purple-600 text-white hover:bg-purple-700'
                    : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                {showAgentPanel ? '隐藏智能助手' : '智能助手'}
              </button>
              <button
                onClick={() => setShowNewSessionModal(true)}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-semibold"
              >
                + 新会话
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 会话列表 */}
        <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-gray-600 mb-3">对话历史</h2>
            {sessions.length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-8">
                还没有会话
              </div>
            ) : (
              <div className="space-y-2">
                {sessions.map((session: any) => (
                  <button
                    key={session.id}
                    onClick={() => setSelectedSession(session.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedSession === session.id
                        ? 'bg-indigo-100 text-indigo-900 font-semibold'
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <div className="text-sm truncate">{session.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {session.message_count} 条消息
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 聊天区域 */}
        <div className="flex-1 flex flex-col">
          {!selectedSession ? (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <svg
                  className="w-24 h-24 mx-auto mb-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
                <h3 className="text-xl font-semibold mb-2">开始对话</h3>
                <p className="text-gray-500 mb-4">
                  选择一个会话或创建新会话
                </p>
                <button
                  onClick={() => setShowNewSessionModal(true)}
                  className="text-indigo-600 hover:text-indigo-700 font-semibold"
                >
                  创建新会话 →
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* 消息列表 */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg: Message) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-3xl rounded-lg p-4 ${
                        msg.role === 'user'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white shadow'
                      }`}
                    >
                      {msg.role === 'assistant' && msg.thinking_process && (
                        <details className="mb-3 pb-3 border-b border-gray-200">
                          <summary className="cursor-pointer text-sm font-semibold text-gray-600 hover:text-gray-900">
                            💭 查看思考过程
                          </summary>
                          <div className="mt-2 text-sm text-gray-600 whitespace-pre-wrap">
                            {msg.thinking_process}
                          </div>
                        </details>
                      )}
                      <div className="whitespace-pre-wrap">
                        {msg.role === 'assistant' ? parseMessageContent(msg.content) : msg.content}
                      </div>
                      <div
                        className={`text-xs mt-2 ${
                          msg.role === 'user'
                            ? 'text-indigo-200'
                            : 'text-gray-500'
                        }`}
                      >
                        {new Date(msg.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* 输入框 */}
              <div className="bg-white border-t border-gray-200 p-4">
                {selectedEntity && (
                  <div className="mb-3 flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-semibold text-blue-900">
                        正在询问关于:
                      </span>
                      <span className="text-blue-700">
                        "{selectedEntity.name}" ({selectedEntity.type})
                      </span>
                    </div>
                    <button
                      onClick={clearSelectedEntity}
                      className="text-blue-600 hover:text-blue-800 font-bold"
                    >
                      ×
                    </button>
                  </div>
                )}
                <form onSubmit={handleSendMessage} className="flex gap-3">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="输入您的问题... (基于项目资料的深度AI对话)"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    disabled={sendMessageMutation.isPending}
                  />
                  <button
                    type="submit"
                    disabled={sendMessageMutation.isPending || !message.trim()}
                    className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {sendMessageMutation.isPending ? '发送中...' : '发送'}
                  </button>
                </form>
                <div className="mt-2 text-xs text-gray-500 flex items-center gap-4">
                  <span>🧠 使用长记忆和深度思考</span>
                  <span>📚 基于 {messagesData?.total || 0} 条历史消息</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Agent 智能助手面板 */}
        {showAgentPanel && (
          <div className="w-[600px] bg-white border-l border-gray-200 overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h2 className="text-lg font-bold text-gray-900">智能助手</h2>
              </div>
              <button
                onClick={closeAgentPanel}
                className="text-gray-500 hover:text-gray-700"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Agent 执行监控器 */}
              {agentExecutionId && (
                <div className="mb-4">
                  <AgentExecutionMonitor
                    executionId={agentExecutionId}
                    projectId={projectId ? Number(projectId) : undefined}
                    autoRefresh={true}
                    refreshInterval={2000}
                    onComplete={handleAgentComplete}
                    onError={(error) => {
                      console.error('Agent execution error:', error);
                      setAgentExecutionId(null);
                    }}
                  />
                </div>
              )}

              {/* Agent 结果查看器 */}
              {agentResult && agentResultType && (
                <div className="mb-4">
                  <AgentResultsViewer
                    result={agentResult}
                    resultType={agentResultType}
                  />
                </div>
              )}

              {/* Agent 编排面板 */}
              {!agentExecutionId && (
                <>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h3 className="font-semibold text-purple-900 mb-2">💡 使用建议</h3>
                    <ul className="text-sm text-purple-700 space-y-1">
                      <li>• 知识提取：分析对话中的关键信息</li>
                      <li>• 语义搜索：在项目文档中查找相关内容</li>
                      <li>• 内容摘要：总结长对话的核心观点</li>
                      <li>• 转写分析：处理音频文件中的对话</li>
                    </ul>
                  </div>

                  <AgentOrchestrationPanel
                    projectId={projectId ? Number(projectId) : undefined}
                    documentIds={[]}
                    onExecutionStart={handleAgentExecutionStart}
                    onComplete={handleAgentComplete}
                  />
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 新建会话模态框 */}
      {showNewSessionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4">新建对话会话</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (newSessionName.trim()) {
                  createSessionMutation.mutate(newSessionName);
                }
              }}
            >
              <div className="mb-6">
                <label className="block text-gray-700 font-semibold mb-2">
                  会话名称 *
                </label>
                <input
                  type="text"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="例如：方言调研讨论"
                  required
                  autoFocus
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={createSessionMutation.isPending}
                  className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors font-semibold disabled:opacity-50"
                >
                  {createSessionMutation.isPending ? '创建中...' : '创建'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowNewSessionModal(false)}
                  className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
