import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { ingestAPI } from '../api/client'
import './IngestView.css'

function IngestView() {
  const [tasks, setTasks] = useState([])
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return

    setUploading(true)

    try {
      // 批量上传
      const newTasks = await ingestAPI.uploadBatch(acceptedFiles)
      setTasks([...newTasks, ...tasks])

      // 轮询任务状态
      newTasks.forEach((task) => {
        pollTaskStatus(task.task_id)
      })
    } catch (error) {
      console.error('Upload failed:', error)
      alert('上传失败: ' + error.message)
    } finally {
      setUploading(false)
    }
  }, [tasks])

  const pollTaskStatus = async (taskId) => {
    const maxAttempts = 60 // 最多轮询60次
    let attempts = 0

    const poll = setInterval(async () => {
      attempts++

      try {
        const task = await ingestAPI.getTaskStatus(taskId)

        // 更新任务状态
        setTasks((prevTasks) =>
          prevTasks.map((t) => (t.task_id === taskId ? task : t))
        )

        // 如果完成或失败，停止轮询
        if (task.status === 'completed' || task.status === 'failed' || attempts >= maxAttempts) {
          clearInterval(poll)
        }
      } catch (error) {
        console.error('Poll task failed:', error)
        clearInterval(poll)
      }
    }, 2000) // 每2秒轮询一次
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/*': ['.txt', '.md'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'audio/*': ['.mp3', '.wav', '.m4a', '.aac'],
      'image/*': ['.jpg', '.jpeg', '.png'],
      'video/*': ['.mp4', '.mov', '.mkv'],
    },
  })

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'var(--color-success)'
      case 'failed':
        return 'var(--color-error)'
      case 'processing':
        return 'var(--color-primary)'
      default:
        return 'var(--color-secondary)'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return '等待中'
      case 'processing':
        return '处理中'
      case 'completed':
        return '已完成'
      case 'failed':
        return '失败'
      default:
        return status
    }
  }

  return (
    <div className="page ingest-page">
      <div className="page-header">
        <h1 className="page-title">📥 文件摄入</h1>
        <p className="page-description">
          上传您的田野调查材料，支持文字、音频、图片、视频多种格式
        </p>
      </div>

      {/* 上传区域 */}
      <div className="card">
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-content">
            <div className="dropzone-icon">📁</div>
            {isDragActive ? (
              <p className="dropzone-text">松开鼠标开始上传...</p>
            ) : (
              <>
                <p className="dropzone-text">拖拽文件到此处，或点击选择文件</p>
                <p className="dropzone-hint">
                  支持: TXT, PDF, Word, MP3, WAV, JPG, PNG, MP4, MOV
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 任务列表 */}
      {tasks.length > 0 && (
        <div className="card">
          <h2 className="card-title">处理任务 ({tasks.length})</h2>

          <div className="task-list">
            {tasks.map((task) => (
              <div key={task.task_id} className="task-item">
                <div className="task-info">
                  <div className="task-name">
                    {task.file_path.split('/').pop()}
                  </div>
                  <div className="task-meta">
                    <span className="task-type">{task.media_type}</span>
                    <span
                      className="task-status"
                      style={{ color: getStatusColor(task.status) }}
                    >
                      {getStatusText(task.status)}
                    </span>
                  </div>
                </div>

                <div className="task-progress">
                  <div
                    className="task-progress-bar"
                    style={{
                      width: `${task.progress * 100}%`,
                      background: getStatusColor(task.status),
                    }}
                  />
                </div>

                {task.error_message && (
                  <div className="task-error">{task.error_message}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {tasks.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📂</div>
          <h3 className="empty-state-title">还没有上传任何文件</h3>
          <p className="empty-state-description">
            拖拽文件到上方区域开始处理您的田野调查材料
          </p>
        </div>
      )}
    </div>
  )
}

export default IngestView
