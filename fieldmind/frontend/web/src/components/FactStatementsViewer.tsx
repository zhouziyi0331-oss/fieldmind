import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import AudioPlayer from './AudioPlayer';
import { useAppContext } from '../contexts/AppContext';

interface FactStatementsViewerProps {
  documentId: number;
}

interface FactStatement {
  statement: string;
  start_sec: number | null;
  end_sec: number | null;
  confidence_score: number;
  speaker: string | null;
}

const FactStatementsViewer: React.FC<FactStatementsViewerProps> = ({ documentId }) => {
  const [seekToTime, setSeekToTime] = useState<number | undefined>(undefined);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const { playAudio, audioControl } = useAppContext();

  const { data, isLoading, error } = useQuery({
    queryKey: ['factStatements', documentId],
    queryFn: () => api.documents.getFactStatements(documentId),
  });

  // 点击时间戳使用全局音频播放器
  const handleTimestampClick = (startSec: number) => {
    playAudio(documentId, startSec);
    console.log('[FactStatementsViewer] 播放音频:', documentId, startSec);
  };

  // 同步全局播放器的时间到本地状态
  React.useEffect(() => {
    if (audioControl.fileId === documentId && audioControl.isPlaying) {
      setCurrentTime(audioControl.currentTime);
    }
  }, [audioControl, documentId]);

  // 判断当前fact是否正在播放
  const isStatementPlaying = (startSec: number | null, endSec: number | null): boolean => {
    if (startSec === null) return false;
    if (endSec === null) return currentTime >= startSec;
    return currentTime >= startSec && currentTime <= endSec;
  };

  const formatTime = (seconds: number | null): string => {
    if (seconds === null) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        加载失败：{error instanceof Error ? error.message : '未知错误'}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const {
    filename,
    file_type,
    audio_url,
    total_statements,
    statements_with_timestamps,
    timestamp_coverage,
    fact_statements
  } = data;

  return (
    <div className="space-y-4">
      {/* 提示：音频使用全局播放器 */}
      {audio_url && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
          💡 点击时间戳使用全局音频播放器（页面底部控制条）
        </div>
      )}

      {/* 统计信息 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">📝 事实陈述</h3>
          <div className="flex gap-4 text-sm">
            <span className="text-gray-600">
              总数: <span className="font-semibold text-gray-900">{total_statements}</span>
            </span>
            <span className="text-gray-600">
              带时间戳: <span className="font-semibold text-indigo-600">{statements_with_timestamps}</span>
            </span>
            <span className="text-gray-600">
              覆盖率: <span className="font-semibold text-green-600">{timestamp_coverage.toFixed(1)}%</span>
            </span>
          </div>
        </div>

        {/* 文件信息 */}
        <div className="text-sm text-gray-500 mb-4">
          文件: {filename} ({file_type})
        </div>

        {/* 时间戳覆盖率进度条 */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all"
            style={{ width: `${timestamp_coverage}%` }}
          ></div>
        </div>
      </div>

      {/* Fact Statements列表 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-y-auto max-h-[600px]">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                  时间
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  内容
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                  置信度
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fact_statements.map((statement: FactStatement, index: number) => {
                const isPlaying = isStatementPlaying(statement.start_sec, statement.end_sec);

                return (
                  <tr
                    key={index}
                    className={`transition-colors ${
                      isPlaying
                        ? 'bg-indigo-50 border-l-4 border-indigo-500'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="px-4 py-3 text-sm font-mono text-gray-900 whitespace-nowrap">
                      {statement.start_sec !== null ? (
                        <button
                          onClick={() => handleTimestampClick(statement.start_sec!)}
                          className="flex flex-col items-start hover:bg-indigo-100 rounded px-2 py-1 transition-colors cursor-pointer"
                          disabled={!audio_url}
                          title={audio_url ? '点击跳转到此时间' : '无音频文件'}
                        >
                          <span className={`${audio_url ? 'text-indigo-600 hover:text-indigo-800' : 'text-gray-500'} ${isPlaying ? 'font-bold' : ''}`}>
                            {isPlaying ? '▶ ' : ''}{formatTime(statement.start_sec)}
                          </span>
                          {statement.end_sec !== null && (
                            <span className="text-gray-400 text-xs">
                              -{formatTime(statement.end_sec)}
                            </span>
                          )}
                        </button>
                      ) : (
                        <span className="text-gray-400">--:--</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {statement.statement}
                    </td>
                    <td className="px-4 py-3 text-sm text-center">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        statement.confidence_score >= 0.7
                          ? 'bg-green-100 text-green-800'
                          : statement.confidence_score >= 0.5
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {(statement.confidence_score * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {fact_statements.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            暂无事实陈述
          </div>
        )}
      </div>
    </div>
  );
};

export default FactStatementsViewer;
