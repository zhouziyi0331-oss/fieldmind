import React, { useState, useEffect } from 'react'
import { graphAPI } from '../api/client'
import './TimelineView.css'

function TimelineView() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTimeline()
  }, [])

  const loadTimeline = async () => {
    try {
      const data = await graphAPI.getTimeline()
      setEvents(data)
    } catch (error) {
      console.error('Load timeline failed:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page timeline-page">
      <div className="page-header">
        <h1 className="page-title">📅 时间线</h1>
        <p className="page-description">按时间顺序查看田野调查中的所有事件</p>
      </div>

      {events.length > 0 ? (
        <div className="timeline">
          {events.map((event, index) => (
            <div key={event.event_id || index} className="timeline-item">
              <div className="timeline-marker"></div>
              <div className="timeline-content card">
                <div className="timeline-date">{event.date_text}</div>
                <h3 className="timeline-title">{event.title}</h3>
                <p className="timeline-description">{event.description}</p>
                {event.participants && event.participants.length > 0 && (
                  <div className="timeline-meta">
                    参与者: {event.participants.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📅</div>
          <h3 className="empty-state-title">暂无时间线数据</h3>
          <p className="empty-state-description">
            上传并处理田野调查材料后，系统会自动生成时间线
          </p>
        </div>
      )}
    </div>
  )
}

export default TimelineView
