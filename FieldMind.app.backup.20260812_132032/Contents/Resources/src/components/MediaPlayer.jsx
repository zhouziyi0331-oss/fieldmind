import React, { useRef, useEffect } from 'react';
import './MediaPlayer.css';

function MediaPlayer({ material, onClose }) {
  const audioRef = useRef(null);
  const videoRef = useRef(null);

  useEffect(() => {
    // 如果有时间码，自动跳转
    if (material.position && material.material_type !== 'text') {
      const timeInSeconds = parseTimeCode(material.position);
      if (audioRef.current) {
        audioRef.current.currentTime = timeInSeconds;
        audioRef.current.play();
      }
      if (videoRef.current) {
        videoRef.current.currentTime = timeInSeconds;
        videoRef.current.play();
      }
    }
  }, [material]);

  // 解析时间码 "00:14:32" -> 秒数
  const parseTimeCode = (timeCode) => {
    const parts = timeCode.split(':');
    if (parts.length === 3) {
      const hours = parseInt(parts[0]);
      const minutes = parseInt(parts[1]);
      const seconds = parseInt(parts[2]);
      return hours * 3600 + minutes * 60 + seconds;
    }
    return 0;
  };

  // 格式化时间显示
  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="media-player-overlay" onClick={onClose}>
      <div className="media-player-container" onClick={(e) => e.stopPropagation()}>
        <div className="player-header">
          <div className="player-title">
            <span className="material-icon">
              {material.material_type === 'audio' && '🎵'}
              {material.material_type === 'video' && '🎥'}
            </span>
            <span>{material.material_name}</span>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="player-body">
          {material.material_type === 'audio' && (
            <div className="audio-player">
              <div className="audio-visual">
                <div className="audio-icon">🎵</div>
                <div className="audio-info">
                  <div className="audio-name">{material.material_name}</div>
                  <div className="audio-position">跳转到: {material.position}</div>
                </div>
              </div>
              <audio
                ref={audioRef}
                controls
                className="audio-controls"
                src={`http://localhost:8765/api/media/${material.material_id}`}
              >
                您的浏览器不支持音频播放
              </audio>
            </div>
          )}

          {material.material_type === 'video' && (
            <div className="video-player">
              <video
                ref={videoRef}
                controls
                className="video-controls"
                src={`http://localhost:8765/api/media/${material.material_id}`}
              >
                您的浏览器不支持视频播放
              </video>
              <div className="video-info">
                <span>跳转到: {material.position}</span>
              </div>
            </div>
          )}

          {/* 显示相关片段 */}
          <div className="material-context">
            <h4>相关内容</h4>
            <div
              className="context-text"
              dangerouslySetInnerHTML={{ __html: material.snippet }}
            />
          </div>
        </div>

        <div className="player-footer">
          <div className="player-tips">
            💡 提示：播放器已自动跳转到 <strong>{material.position}</strong>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MediaPlayer;
