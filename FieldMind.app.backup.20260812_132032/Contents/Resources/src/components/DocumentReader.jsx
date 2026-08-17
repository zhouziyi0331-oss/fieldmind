import React, { useState, useEffect, useRef } from 'react';
import './DocumentReader.css';

function DocumentReader({ material, onClose }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const contentRef = useRef(null);

  useEffect(() => {
    loadDocument();
  }, [material]);

  useEffect(() => {
    // 自动跳转到目标页码
    if (material.position && content) {
      const pageMatch = material.position.match(/第(\d+)页/);
      if (pageMatch) {
        const targetPage = parseInt(pageMatch[1]);
        setCurrentPage(targetPage);
        scrollToHighlight();
      }
    }
  }, [content, material.position]);

  const loadDocument = async () => {
    setLoading(true);
    try {
      // 获取文档内容
      const response = await fetch(
        `http://localhost:8765/api/media/${material.material_id}`
      );
      const data = await response.json();

      setContent(data.content || '');
      setTotalPages(data.total_pages || 1);
      setCurrentPage(data.current_page || 1);
    } catch (error) {
      console.error('加载文档失败:', error);
      setContent('无法加载文档内容');
    } finally {
      setLoading(false);
    }
  };

  const scrollToHighlight = () => {
    // 滚动到高亮的内容
    setTimeout(() => {
      const highlighted = contentRef.current?.querySelector('em');
      if (highlighted) {
        highlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      // TODO: 实际的分页加载逻辑
    }
  };

  return (
    <div className="document-reader-overlay" onClick={onClose}>
      <div className="document-reader-container" onClick={(e) => e.stopPropagation()}>
        <div className="reader-header">
          <div className="reader-title">
            <span className="material-icon">📄</span>
            <span>{material.material_name}</span>
          </div>
          <div className="reader-controls">
            <span className="page-info">
              第 {currentPage} / {totalPages} 页
            </span>
            <button className="close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="reader-body">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>加载文档中...</p>
            </div>
          ) : (
            <>
              <div className="document-content" ref={contentRef}>
                <div
                  className="content-text"
                  dangerouslySetInnerHTML={{ __html: material.snippet || content }}
                />
              </div>

              {/* 分页控制 */}
              {totalPages > 1 && (
                <div className="pagination-controls">
                  <button
                    className="page-btn"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    ← 上一页
                  </button>
                  <div className="page-input-group">
                    <input
                      type="number"
                      value={currentPage}
                      onChange={(e) => handlePageChange(parseInt(e.target.value))}
                      min={1}
                      max={totalPages}
                    />
                    <span>/ {totalPages}</span>
                  </div>
                  <button
                    className="page-btn"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    下一页 →
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <div className="reader-footer">
          <div className="reader-tips">
            💡 提示：文档已自动跳转到 <strong>{material.position}</strong>，关键内容已高亮
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocumentReader;
