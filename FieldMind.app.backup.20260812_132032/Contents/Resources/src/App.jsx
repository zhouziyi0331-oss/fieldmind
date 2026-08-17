import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import IngestView from './views/IngestView'
import SearchView from './views/SearchView'
import TimelineView from './views/TimelineView'
import GraphView from './views/GraphView'
import AgentView from './views/AgentView'
import KeywordsView from './views/KeywordsView'
import BusinessView from './views/BusinessView'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('ingest')

  return (
    <Router>
      <div className="app">
        {/* 侧边栏导航 */}
        <aside className="sidebar">
          <div className="logo">
            <h1>📚 FieldMind</h1>
            <p>田野调查知识引擎</p>
          </div>

          <nav className="nav">
            <Link
              to="/ingest"
              className={`nav-item ${activeTab === 'ingest' ? 'active' : ''}`}
              onClick={() => setActiveTab('ingest')}
            >
              <span className="icon">📥</span>
              <span>文件摄入</span>
            </Link>

            <Link
              to="/keywords"
              className={`nav-item ${activeTab === 'keywords' ? 'active' : ''}`}
              onClick={() => setActiveTab('keywords')}
            >
              <span className="icon">🔑</span>
              <span>关键词解锁</span>
            </Link>

            <Link
              to="/business"
              className={`nav-item ${activeTab === 'business' ? 'active' : ''}`}
              onClick={() => setActiveTab('business')}
            >
              <span className="icon">🏘️</span>
              <span>业态分析</span>
            </Link>

            <Link
              to="/search"
              className={`nav-item ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <span className="icon">🔍</span>
              <span>智能检索</span>
            </Link>

            <Link
              to="/timeline"
              className={`nav-item ${activeTab === 'timeline' ? 'active' : ''}`}
              onClick={() => setActiveTab('timeline')}
            >
              <span className="icon">📅</span>
              <span>时间线</span>
            </Link>

            <Link
              to="/graph"
              className={`nav-item ${activeTab === 'graph' ? 'active' : ''}`}
              onClick={() => setActiveTab('graph')}
            >
              <span className="icon">🕸️</span>
              <span>知识图谱</span>
            </Link>

            <Link
              to="/agent"
              className={`nav-item ${activeTab === 'agent' ? 'active' : ''}`}
              onClick={() => setActiveTab('agent')}
            >
              <span className="icon">💬</span>
              <span>对话Agent</span>
            </Link>
          </nav>

          <div className="sidebar-footer">
            <p className="version">v1.0.0</p>
          </div>
        </aside>

        {/* 主内容区 */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<IngestView />} />
            <Route path="/ingest" element={<IngestView />} />
            <Route path="/keywords" element={<KeywordsView />} />
            <Route path="/business" element={<BusinessView />} />
            <Route path="/search" element={<SearchView />} />
            <Route path="/timeline" element={<TimelineView />} />
            <Route path="/graph" element={<GraphView />} />
            <Route path="/agent" element={<AgentView />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
