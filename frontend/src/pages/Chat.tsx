import { useState, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useSendMessage, useConversations } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Spinner } from '@/components/ui/spinner'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Send, User, Bot, FileText, Plus, Trash2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: Array<{
    document: string
    page?: number
    snippet: string
  }>
}

export default function Chat() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [currentConversationId, setCurrentConversationId] = useState<string>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: conversations, isLoading: conversationsLoading } = useConversations(projectId)
  const sendMessage = useSendMessage()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || sendMessage.isPending) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')

    try {
      const response = await sendMessage.mutateAsync({
        projectId,
        message: input,
        conversationId: currentConversationId,
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
        citations: response.data.citations,
      }

      setMessages((prev) => [...prev, assistantMessage])

      if (response.data.conversation_id) {
        setCurrentConversationId(response.data.conversation_id)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewConversation = () => {
    setMessages([])
    setCurrentConversationId(undefined)
  }

  if (conversationsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in h-[calc(100vh-8rem)]">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">智能对话</h1>
          <p className="text-text-secondary mt-1">与您的知识库对话</p>
        </div>
        <Button onClick={handleNewConversation}>
          <Plus className="h-4 w-4 mr-2" />
          新对话
        </Button>
      </div>

      <div className="grid grid-cols-12 gap-6 h-full">
        {/* 对话历史侧边栏 */}
        <Card className="col-span-3 h-full overflow-hidden">
          <CardHeader>
            <CardTitle className="text-base">对话历史</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 overflow-y-auto max-h-[calc(100%-5rem)]">
            {conversations?.data?.map((conv: any) => (
              <button
                key={conv.id}
                onClick={() => setCurrentConversationId(conv.id)}
                className={`w-full text-left p-3 rounded-lg border transition-all hover:border-primary ${
                  currentConversationId === conv.id
                    ? 'border-primary bg-primary/5'
                    : 'border-border'
                }`}
              >
                <p className="text-sm font-medium text-text-primary truncate">
                  {conv.title || '未命名对话'}
                </p>
                <p className="text-xs text-text-tertiary mt-1">
                  {formatDistanceToNow(new Date(conv.created_at), {
                    addSuffix: true,
                    locale: zhCN,
                  })}
                </p>
              </button>
            ))}
            {(!conversations?.data || conversations.data.length === 0) && (
              <p className="text-sm text-text-secondary text-center py-8">
                暂无对话历史
              </p>
            )}
          </CardContent>
        </Card>

        {/* 主对话区域 */}
        <Card className="col-span-9 h-full flex flex-col">
          {/* 消息列表 */}
          <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="h-16 w-16 text-primary mb-4" />
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  开始新对话
                </h3>
                <p className="text-sm text-text-secondary max-w-md">
                  您可以询问关于项目文档的任何问题，我会基于知识库为您提供准确答案。
                </p>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <Avatar className="h-8 w-8 flex-shrink-0">
                        <AvatarFallback className="bg-primary text-white">
                          <Bot className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                    )}

                    <div
                      className={`max-w-[70%] ${
                        message.role === 'user' ? 'order-first' : ''
                      }`}
                    >
                      <div
                        className={`rounded-lg p-4 ${
                          message.role === 'user'
                            ? 'bg-primary text-white'
                            : 'bg-surface-hover text-text-primary'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>

                      {/* 引用来源 */}
                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {message.citations.map((citation, index) => (
                            <div
                              key={index}
                              className="flex items-start gap-2 p-2 bg-surface border border-border rounded text-xs"
                            >
                              <FileText className="h-3 w-3 text-primary flex-shrink-0 mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-text-primary truncate">
                                  {citation.document}
                                  {citation.page && ` - 第 ${citation.page} 页`}
                                </p>
                                <p className="text-text-secondary line-clamp-2 mt-0.5">
                                  {citation.snippet}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      <p className="text-xs text-text-tertiary mt-1">
                        {formatDistanceToNow(message.timestamp, {
                          addSuffix: true,
                          locale: zhCN,
                        })}
                      </p>
                    </div>

                    {message.role === 'user' && (
                      <Avatar className="h-8 w-8 flex-shrink-0">
                        <AvatarFallback className="bg-secondary text-white">
                          <User className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                ))}

                {sendMessage.isPending && (
                  <div className="flex gap-3">
                    <Avatar className="h-8 w-8 flex-shrink-0">
                      <AvatarFallback className="bg-primary text-white">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="bg-surface-hover rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <Spinner size="sm" />
                        <span className="text-sm text-text-secondary">正在思考...</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </CardContent>

          {/* 输入区域 */}
          <div className="border-t border-border p-4">
            <div className="flex gap-2">
              <Textarea
                placeholder="输入您的问题... (Shift+Enter 换行，Enter 发送)"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                rows={3}
                className="resize-none"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || sendMessage.isPending}
                loading={sendMessage.isPending}
                className="px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
