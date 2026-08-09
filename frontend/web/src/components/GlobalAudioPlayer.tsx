import React, { useEffect, useRef } from 'react';
import { useAppContext } from '../contexts/AppContext';

/**
 * 全局音频播放器组件
 * 这个组件被放在App的最顶层，监听全局audioControl状态
 * 任何页面都可以通过 playAudio(fileId, startTime) 来控制它
 */
export const GlobalAudioPlayer: React.FC = () => {
  const { audioControl, pauseAudio, updateAudioTime } = useAppContext();
  const audioRef = useRef<HTMLAudioElement>(null);

  // 当audioControl改变时，控制播放
  useEffect(() => {
    if (!audioRef.current || !audioControl.fileId) return;

    const audio = audioRef.current;

    // 设置音频源
    const audioUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/documents/${audioControl.fileId}/audio`;

    if (audio.src !== audioUrl) {
      audio.src = audioUrl;
    }

    // 跳转到指定时间
    if (audioControl.currentTime !== audio.currentTime) {
      audio.currentTime = audioControl.currentTime;
    }

    // 控制播放/暂停
    if (audioControl.isPlaying) {
      audio.play().catch(err => {
        console.error('[GlobalAudioPlayer] 播放失败:', err);
      });
    } else {
      audio.pause();
    }
  }, [audioControl]);

  // 监听播放进度，更新全局状态
  const handleTimeUpdate = () => {
    if (audioRef.current) {
      updateAudioTime(audioRef.current.currentTime);
    }
  };

  // 音频结束时暂停
  const handleEnded = () => {
    pauseAudio();
  };

  return (
    <audio
      ref={audioRef}
      onTimeUpdate={handleTimeUpdate}
      onEnded={handleEnded}
      style={{ display: 'none' }} // 隐藏默认播放器，UI由各页面控制
    />
  );
};

/**
 * 音频控制条组件（可选）
 * 显示在页面底部的迷你播放器
 */
export const AudioControlBar: React.FC = () => {
  const { audioControl, playAudio, pauseAudio } = useAppContext();

  if (!audioControl.fileId) {
    return null; // 没有音频时不显示
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-indigo-600 text-white p-3 shadow-lg z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {
              if (audioControl.isPlaying) {
                pauseAudio();
              } else {
                playAudio(audioControl.fileId!, audioControl.currentTime);
              }
            }}
            className="hover:bg-indigo-700 p-2 rounded transition-colors"
          >
            {audioControl.isPlaying ? '⏸️' : '▶️'}
          </button>

          <div className="text-sm">
            <span className="font-mono">{formatTime(audioControl.currentTime)}</span>
          </div>
        </div>

        <div className="text-sm opacity-75">
          文档 #{audioControl.fileId}
        </div>
      </div>
    </div>
  );
};
