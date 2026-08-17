import React, { useState, useRef, useEffect } from 'react'
import { agentAPI } from '../api/client'
import './AgentView.css'

function AgentView() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [useWeb, setUseWeb] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()

    if (!input.trim() || loading) return

    const userMessage = {
      role: 'user',
      content: input.trim(),
    }

    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      // 构建历史对话
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }))

      // 调用Agent API
      const response = await agentAPI.chat(userMessage.content, history, useWeb)

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        webResults: response.web_results || [],
      }

      setMessages([...messages, userMessage, assistantMessage])
    } catch (error) {
      console.error('Chat failed:', error)
      const errorMessage = {
        role: 'assistant',
        content: '抱歉，回答失败了：' + error.message,
        error: true,
      }
      setMessages([...messages, userMessage, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(e)
    }
  }

  const clearChat = () => {
    if (window.confirm('确定要清空对话历史吗？')) {
      setMessages([])
    }
  }

  return (
    <div className="page agent-page">
      <div className="page-header">
        <h1 className="page-title">💬 对话Agent</h1>
        <p className="page-description">
          用自然语言提问，Agent会从您的材料中寻找答案
        </p>
      </div>

      <div className="card chat-container">
        {/* 对话历史 */}
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <div className="welcome-icon">👋</div>
              <h3>您好！我是田野调查知识助手</h3>
              <p>您可以问我：</p>
              <ul className="example-questions">
                <li>"村里谁最了解水利纠纷？"</li>
                <li>"关于祭祀仪式有哪些记录？"</li>
                <li>"去年发生了哪些重要事件？"</li>
                <li>"帮我总结外出务工的情况"</li>
              </ul>
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'} ${msg.error ? 'error-message' : ''}`}
            >
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-text">{msg.content}</div>

                {/* 来源引用 */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-title">📎 来源引用：</div>
                    {msg.sources.map((source, i) => (
                      <div key={i} className="source-item">
                        <div className="source-header">
                          <span className="source-file">{source.file_name}</span>
                          {source.timestamp && (
                            <span className="source-time">⏱ {source.timestamp}</span>
                          )}
                        </div>
                        <div className="source-preview">{source.content_preview}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 网络搜索结果 */}
                {msg.webResults && msg.webResults.length > 0 && (
                  <div className="message-web-results">
                    <div className="web-results-title">🌐 网络补充：</div>
                    {msg.webResults.map((result, i) => (
                      <div key={i} className="web-result-item">
                        {result.title}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant-message">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="chat-input-container">
          <div className="chat-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={useWeb}
                onChange={(e) => setUseWeb(e.target.checked)}
              />
              <span>联网增强（补充背景知识）</span>
            </label>

            {messages.length > 0 && (
              <button className="btn-clear" onClick={clearChat}>
                🗑️ 清空对话
              </button>
            )}
          </div>

          <form onSubmit={handleSend} className="chat-input-form">
            <textarea
              className="chat-input"
              placeholder="输入您的问题... (按Enter发送，Shift+Enter换行)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              disabled={loading}
            />
            <button
              type="submit"
              className="btn btn-primary btn-send"
              disabled={loading || !input.trim()}
            >
              {loading ? '思考中...' : '发送'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default AgentView
