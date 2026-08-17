import React, { useState } from 'react';
import './BusinessView.css';

function BusinessView() {
  const [keyword, setKeyword] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // 分析业态
  const handleAnalyze = async () => {
    if (!keyword.trim()) {
      alert('请输入关键词');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8765/api/business/${encodeURIComponent(keyword)}`
      );
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('分析失败:', error);
      alert('分析失败，请检查后端服务是否运行');
    } finally {
      setLoading(false);
    }
  };

  // 获取可行性星星
  const getStars = (feasibility) => {
    return '⭐'.repeat(feasibility);
  };

  // 获取成本颜色
  const getCostColor = (level) => {
    const colors = {
      '低': '#4CAF7D',
      '中': '#D4A44C',
      '高': '#D46B5B'
    };
    return colors[level] || '#9A9690';
  };

  return (
    <div className="business-view">
      <div className="business-header">
        <h1>🏘️ 在地业态分析</h1>
        <p>AI 基于真实材料分析业态可能性</p>
      </div>

      {/* 搜索框 */}
      <div className="search-box">
        <input
          type="text"
          placeholder="输入关键词（如：布依族山歌、梯田、刺绣...）"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
        />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? '分析中...' : '开始分析'}
        </button>
      </div>

      {/* 分析结果 */}
      {analysis && (
        <div className="analysis-result">
          <div className="result-header">
            <h2>📊 "{analysis.keyword}" 的业态分析</h2>
          </div>

          {/* 现有业态 */}
          <div className="section existing-section">
            <h3>🏢 现有业态梳理</h3>
            <div className="existing-list">
              {analysis.existing_businesses.length > 0 ? (
                analysis.existing_businesses.map((business, index) => (
                  <div key={index} className="existing-card">
                    <div className="card-icon">{business.icon}</div>
                    <div className="card-content">
                      <div className="card-name">{business.name}</div>
                      <div className="card-status">{business.status}</div>
                      <div className="card-meta">
                        <span className={`strength-badge ${business.strength_level}`}>
                          {business.strength === '强' && '💪 强'}
                          {business.strength === '弱' && '⚠️ 弱'}
                          {business.strength === '有潜力' && '✨ 有潜力'}
                        </span>
                        <span className="source-link">
                          📎 来源: {business.source}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-message">暂无现有业态数据</div>
              )}
            </div>
          </div>

          {/* 可能业态 */}
          <div className="section possible-section">
            <h3>💡 可能业态推演</h3>
            <div className="possible-grid">
              {analysis.possible_businesses.length > 0 ? (
                analysis.possible_businesses.map((business, index) => (
                  <div key={index} className="possible-card">
                    <div className="card-header">
                      <div className="card-icon-large">{business.icon}</div>
                      <div>
                        <div className="card-name">{business.name}</div>
                        <div className="card-audience">
                          目标: {business.target_audience}
                        </div>
                      </div>
                    </div>

                    <div className="card-desc">{business.description}</div>

                    <div className="card-basis">
                      <div className="basis-title">📋 材料依据</div>
                      <div className="basis-content">{business.basis}</div>
                    </div>

                    <div className="card-footer">
                      <div className="feasibility">
                        <span className="label">可行性</span>
                        <span className="stars">{getStars(business.feasibility)}</span>
                      </div>
                      <div className="cost">
                        <span className="label">成本</span>
                        <span
                          className="cost-value"
                          style={{ color: getCostColor(business.cost_level) }}
                        >
                          {business.cost_level}
                        </span>
                      </div>
                    </div>

                    {business.risk && (
                      <div className="card-risk">
                        ⚠️ 风险提示: {business.risk}
                      </div>
                    )}

                    <div className="card-sources">
                      {business.sources.map((source, idx) => (
                        <span key={idx} className="source-tag">
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-message">暂无可能业态推演</div>
              )}
            </div>
          </div>

          {/* AI 综合建议 */}
          <div className="section recommendation-section">
            <h3>🤖 AI 综合建议</h3>
            <div className="recommendation-box">
              <div
                className="recommendation-content"
                dangerouslySetInnerHTML={{
                  __html: analysis.ai_recommendation.replace(/\n/g, '<br/>')
                }}
              />
            </div>
          </div>

          {/* 缺失信息 */}
          {analysis.missing_info && analysis.missing_info.length > 0 && (
            <div className="section missing-section">
              <h3>⚠️ 需要补充的信息</h3>
              <div className="missing-list">
                {analysis.missing_info.map((info, index) => (
                  <div key={index} className="missing-item">
                    <div className="missing-icon">💡</div>
                    <div className="missing-text">{info}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 空状态 */}
      {!analysis && !loading && (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <p>输入关键词，开始分析在地业态可能性</p>
          <div className="example-keywords">
            <span>示例:</span>
            <button onClick={() => setKeyword('布依族山歌')}>布依族山歌</button>
            <button onClick={() => setKeyword('梯田')}>梯田</button>
            <button onClick={() => setKeyword('刺绣')}>刺绣</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default BusinessView;
