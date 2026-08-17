import React, { useState, useEffect } from 'react';
import MediaPlayer from '../components/MediaPlayer';
import DocumentReader from '../components/DocumentReader';
import './KeywordsView.css';

function KeywordsView() {
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [relatedKeywords, setRelatedKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeMaterial, setActiveMaterial] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);

  // 加载关键词列表
  useEffect(() => {
    loadKeywords();
  }, [activeCategory]);

  const loadKeywords = async () => {
    setLoading(true);
    try {
      const url = new URL('http://localhost:8765/api/keywords/');
      if (activeCategory) {
        url.searchParams.append('category', activeCategory);
      }
      const response = await fetch(url);
      const data = await response.json();
      setKeywords(data);
    } catch (error) {
      console.error('加载关键词失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 点击关键词，加载时间链路和材料
  const handleKeywordClick = async (keyword) => {
    setSelectedKeyword(keyword);
    setDetailLoading(true);

    try {
      // 并行加载时间线、材料和相关关键词
      const [timelineRes, materialsRes, relatedRes] = await Promise.all([
        fetch(`http://localhost:8765/api/keywords/${encodeURIComponent(keyword.keyword)}/timeline`),
        fetch(`http://localhost:8765/api/keywords/${encodeURIComponent(keyword.keyword)}/materials`),
        fetch(`http://localhost:8765/api/keywords/${encodeURIComponent(keyword.keyword)}/related`)
      ]);

      const timelineData = await timelineRes.json();
      const materialsData = await materialsRes.json();
      const relatedData = await relatedRes.json();

      setTimeline(timelineData);
      setMaterials(materialsData);
      setRelatedKeywords(relatedData);
    } catch (error) {
      console.error('加载详情失败:', error);
      // 失败时清空数据
      setTimeline([]);
      setMaterials([]);
      setRelatedKeywords([]);
    } finally {
      setDetailLoading(false);
    }
  };

  // 跳转到材料位置
  const handleMaterialClick = (material) => {
    setActiveMaterial(material);
    setShowPlayer(true);
  };

  // 根据重要性计算字体大小
  const getFontSize = (importance) => {
    const minSize = 12;
    const maxSize = 32;
    return minSize + (maxSize - minSize) * importance;
  };

  // 根据分类返回颜色
  const getCategoryColor = (category) => {
    const colors = {
      '人物': '#4CAF7D',
      '地点': '#5B8FD4',
      '事件': '#C8A96E',
      '议题': '#8B6FD4',
      '其他': '#9A9690'
    };
    return colors[category] || colors['其他'];
  };

  return (
    <div className="keywords-view">
      <div className="keywords-header">
        <h1>🔑 关键词解锁</h1>
        <p>点击任意关键词，查看时间链路和材料定位</p>

        {/* 分类筛选 */}
        <div className="category-filter">
          <button
            className={`filter-btn ${activeCategory === null ? 'active' : ''}`}
            onClick={() => setActiveCategory(null)}
          >
            全部
          </button>
          <button
            className={`filter-btn ${activeCategory === '人物' ? 'active' : ''}`}
            onClick={() => setActiveCategory('人物')}
          >
            👤 人物
          </button>
          <button
            className={`filter-btn ${activeCategory === '地点' ? 'active' : ''}`}
            onClick={() => setActiveCategory('地点')}
          >
            📍 地点
          </button>
          <button
            className={`filter-btn ${activeCategory === '事件' ? 'active' : ''}`}
            onClick={() => setActiveCategory('事件')}
          >
            ⚡ 事件
          </button>
          <button
            className={`filter-btn ${activeCategory === '议题' ? 'active' : ''}`}
            onClick={() => setActiveCategory('议题')}
          >
            💭 议题
          </button>
        </div>
      </div>

      {/* 关键词云 */}
      <div className="keywords-cloud">
        <div className="cloud-title">
          核心关键词（共 {keywords.length} 个）
        </div>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : keywords.length === 0 ? (
          <div className="empty-hint">暂无关键词数据，请先导入材料</div>
        ) : (
          <div className="cloud-container">
            {keywords.map((kw, index) => (
              <button
                key={index}
                className={`keyword-tag ${selectedKeyword?.keyword === kw.keyword ? 'active' : ''}`}
                style={{
                  fontSize: `${getFontSize(kw.importance)}px`,
                  color: getCategoryColor(kw.category),
                  borderColor: getCategoryColor(kw.category)
                }}
                onClick={() => handleKeywordClick(kw)}
                title={`${kw.keyword} - 出现 ${kw.frequency} 次`}
              >
                {kw.keyword}
                <span className="keyword-freq">×{kw.frequency}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 关键词详情 */}
      {selectedKeyword && (
        <div className="keyword-detail">
          <div className="detail-header">
            <h2>
              <span style={{ color: getCategoryColor(selectedKeyword.category) }}>
                {selectedKeyword.keyword}
              </span>
              <span className="keyword-meta">
                {selectedKeyword.category} · 出现 {selectedKeyword.frequency} 次 · 重要性 {(selectedKeyword.importance * 100).toFixed(0)}%
              </span>
            </h2>
          </div>

          {detailLoading ? (
            <div className="loading">加载详情中...</div>
          ) : (
            <>
              {/* 相关关键词推荐 */}
              {relatedKeywords.length > 0 && (
                <div className="related-keywords">
                  <h4>🔗 相关关键词</h4>
                  <div className="related-tags">
                    {relatedKeywords.map((kw, index) => (
                      <button
                        key={index}
                        className="related-tag"
                        style={{
                          borderColor: getCategoryColor(kw.category),
                          color: getCategoryColor(kw.category)
                        }}
                        onClick={() => handleKeywordClick(kw)}
                      >
                        {kw.keyword} <span className="related-freq">×{kw.frequency}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="detail-panels">
                {/* 左侧：时间链路 */}
                <div className="detail-section timeline-section">
                  <h3>📅 时间链路</h3>
                  {timeline.length === 0 ? (
                    <div className="empty-hint">暂无时间线数据</div>
                  ) : (
                    <div className="timeline-list">
                      {timeline.map((item, index) => (
                        <div key={index} className="timeline-item">
                          <div className="timeline-dot" />
                          <div className="timeline-content">
                            <div className="timeline-time">
                              {item.time}
                              {item.time_type === 'fuzzy' && <span className="fuzzy-tag">模糊</span>}
                            </div>
                            <div className="timeline-title">{item.title}</div>
                            <div className="timeline-desc">{item.content}</div>
                            <div className="timeline-source">
                              来源: {item.source} · {item.position}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 右侧：材料定位 */}
                <div className="detail-section materials-section">
                  <h3>📄 材料定位</h3>
                  {materials.length === 0 ? (
                    <div className="empty-hint">暂无材料数据</div>
                  ) : (
                    <div className="materials-list">
                      {materials.map((material, index) => (
                        <div
                          key={index}
                          className="material-item"
                          onClick={() => handleMaterialClick(material)}
                        >
                          <div className="material-icon">
                            {material.material_type === 'audio' && '🎵'}
                            {material.material_type === 'video' && '🎥'}
                            {material.material_type === 'text' && '📄'}
                            {material.material_type === 'image' && '🖼️'}
                          </div>
                          <div className="material-content">
                            <div className="material-name">{material.material_name}</div>
                            <div
                              className="material-snippet"
                              dangerouslySetInnerHTML={{ __html: material.snippet }}
                            />
                            <div className="material-position">
                              → 跳转: {material.position}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* 空状态 */}
      {!selectedKeyword && !loading && keywords.length > 0 && (
        <div className="empty-state">
          <div className="empty-icon">👆</div>
          <p>点击上方关键词，查看详细信息</p>
        </div>
      )}

      {/* 媒体播放器 */}
      {showPlayer && activeMaterial && (
        (activeMaterial.material_type === 'audio' || activeMaterial.material_type === 'video') ? (
          <MediaPlayer
            material={activeMaterial}
            onClose={() => {
              setShowPlayer(false);
              setActiveMaterial(null);
            }}
          />
        ) : (
          <DocumentReader
            material={activeMaterial}
            onClose={() => {
              setShowPlayer(false);
              setActiveMaterial(null);
            }}
          />
        )
      )}
    </div>
  );
}

export default KeywordsView;
