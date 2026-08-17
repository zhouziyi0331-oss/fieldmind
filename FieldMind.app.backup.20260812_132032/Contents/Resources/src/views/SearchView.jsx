import React, { useState } from 'react'
import { searchAPI } from '../api/client'
import './SearchView.css'

function SearchView() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()

    if (!query.trim()) return

    setLoading(true)
    setSearched(true)

    try {
      const data = await searchAPI.search(query, mode)
      setResults(data)
    } catch (error) {
      console.error('Search failed:', error)
      alert('搜索失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const highlightText = (text, query) => {
    if (!query) return text

    const parts = text.split(new RegExp(`(${query})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i}>{part}</mark>
      ) : (
        part
      )
    )
  }

  return (
    <div className="page search-page">
      <div className="page-header">
        <h1 className="page-title">🔍 智能检索</h1>
        <p className="page-description">
          搜索您的田野调查材料，支持关键词和语义检索
        </p>
      </div>

      {/* 搜索框 */}
      <div className="card">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <input
              type="text"
              className="search-input"
              placeholder="输入关键词或问题，如：水利纠纷、村民信仰..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '搜索中...' : '搜索'}
            </button>
          </div>

          <div className="search-options">
            <label>
              <input
                type="radio"
                name="mode"
                value="hybrid"
                checked={mode === 'hybrid'}
                onChange={(e) => setMode(e.target.value)}
              />
              <span>混合搜索（推荐）</span>
            </label>
            <label>
              <input
                type="radio"
                name="mode"
                value="semantic"
                checked={mode === 'semantic'}
                onChange={(e) => setMode(e.target.value)}
              />
              <span>语义搜索</span>
            </label>
            <label>
              <input
                type="radio"
                name="mode"
                value="keyword"
                checked={mode === 'keyword'}
                onChange={(e) => setMode(e.target.value)}
              />
              <span>关键词搜索</span>
            </label>
          </div>
        </form>
      </div>

      {/* 搜索结果 */}
      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>正在搜索...</p>
        </div>
      )}

      {!loading && searched && results.length > 0 && (
        <div className="card">
          <h2 className="card-title">搜索结果 ({results.length})</h2>

          <div className="result-list">
            {results.map((result, index) => (
              <div key={index} className="result-item">
                <div className="result-header">
                  <span className="result-type">{result.media_type}</span>
                  <span className="result-file">{result.file_name}</span>
                  {result.timestamp && (
                    <span className="result-timestamp">⏱ {result.timestamp}</span>
                  )}
                  <span className="result-score">
                    相关度: {(result.score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="result-content">
                  {highlightText(result.content, query)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <h3 className="empty-state-title">未找到相关结果</h3>
          <p className="empty-state-description">
            尝试使用不同的关键词或切换搜索模式
          </p>
        </div>
      )}

      {!loading && !searched && (
        <div className="empty-state">
          <div className="empty-state-icon">🔎</div>
          <h3 className="empty-state-title">开始搜索</h3>
          <p className="empty-state-description">
            在上方输入框输入关键词或问题，即可检索相关材料
          </p>
        </div>
      )}
    </div>
  )
}

export default SearchView
