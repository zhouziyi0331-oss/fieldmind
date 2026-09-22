/**
 * AgentResultsViewer - Agent结果查看器
 *
 * 功能：
 * 1. 实体/关系可视化
 * 2. 摘要展示
 * 3. 搜索结果展示
 * 4. 转录结果展示
 * 5. 数据导出功能
 */

import React, { useState, useMemo } from 'react'
import {
  FileText,
  Download,
  Search,
  Tag,
  Link as LinkIcon,
  Users,
  MapPin,
  Building,
  Sparkles
} from 'lucide-react'
import type {
  KnowledgeAnalysisResult,
  SearchQueryResult,
  SummaryResult,
  TranscriptResult
} from '../types/agents'

// 兼容类型 - 适配不同的返回格式
type SearchResult = SearchQueryResult & {
  query?: string
}

interface AgentResultsViewerProps {
  result: KnowledgeAnalysisResult | SearchResult | SummaryResult | TranscriptResult | any
  resultType: 'knowledge' | 'search' | 'summary' | 'transcript'
  onExport?: () => void
}

export const AgentResultsViewer: React.FC<AgentResultsViewerProps> = ({
  result,
  resultType,
  onExport
}) => {
  const [entityFilter, setEntityFilter] = useState<string>('')
  const [selectedEntityType, setSelectedEntityType] = useState<string>('all')

  // 获取实体类型图标
  const getEntityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case '人物':
      case 'person':
        return Users
      case '地名':
      case 'location':
        return MapPin
      case '机构':
      case 'organization':
        return Building
      default:
        return Tag
    }
  }

  // 获取实体类型颜色
  const getEntityColor = (type: string) => {
    const colors: Record<string, string> = {
      '人物': 'bg-blue-100 text-blue-700 border-blue-300',
      'person': 'bg-blue-100 text-blue-700 border-blue-300',
      '地名': 'bg-green-100 text-green-700 border-green-300',
      'location': 'bg-green-100 text-green-700 border-green-300',
      '机构': 'bg-orange-100 text-orange-700 border-orange-300',
      'organization': 'bg-orange-100 text-orange-700 border-orange-300',
      '文化概念': 'bg-purple-100 text-purple-700 border-purple-300',
      'concept': 'bg-purple-100 text-purple-700 border-purple-300'
    }
    return colors[type.toLowerCase()] || 'bg-gray-100 text-gray-700 border-gray-300'
  }

  // 渲染知识分析结果
  const renderKnowledgeResult = (data: KnowledgeAnalysisResult) => {
    const filteredEntities = useMemo(() => {
      if (!data.entities) return []
      return data.entities.filter(entity => {
        const matchesFilter = entityFilter === '' ||
          entity.name.toLowerCase().includes(entityFilter.toLowerCase())
        const matchesType = selectedEntityType === 'all' ||
          entity.type === selectedEntityType
        return matchesFilter && matchesType
      })
    }, [data.entities, entityFilter, selectedEntityType])

    const entityTypes = useMemo(() => {
      if (!data.entities) return []
      return Array.from(new Set(data.entities.map(e => e.type)))
    }, [data.entities])

    return (
      <div className="space-y-6">
        {/* 实体部分 */}
        {data.entities && data.entities.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-gray-900 flex items-center space-x-2">
                <Tag className="w-4 h-4" />
                <span>提取实体 ({filteredEntities.length}/{data.entities.length})</span>
              </h4>

              {/* 过滤器 */}
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="搜索实体..."
                    value={entityFilter}
                    onChange={(e) => setEntityFilter(e.target.value)}
                    className="pl-9 pr-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <select
                  value={selectedEntityType}
                  onChange={(e) => setSelectedEntityType(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="all">所有类型</option>
                  {entityTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredEntities.map((entity, index) => {
                const Icon = getEntityIcon(entity.type)
                const colorClass = getEntityColor(entity.type)

                return (
                  <div
                    key={`${entity.name}-${index}`}
                    className="p-3 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-lg ${colorClass}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {entity.name}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${colorClass}`}>
                            {entity.type}
                          </span>
                          {entity.mentions && (
                            <span className="text-xs text-gray-500">
                              {entity.mentions} 次提及
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* 关系部分 */}
        {data.relations && data.relations.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 flex items-center space-x-2 mb-4">
              <LinkIcon className="w-4 h-4" />
              <span>实体关系 ({data.relations.length})</span>
            </h4>

            <div className="space-y-2">
              {data.relations.map((relation, index) => (
                <div
                  key={`${relation.source}-${relation.target}-${index}`}
                  className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                      {relation.source}
                    </span>
                    <span className="text-xs text-gray-500 font-medium">
                      {relation.relation_type}
                    </span>
                    <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
                      {relation.target}
                    </span>
                    {relation.confidence && (
                      <span className="ml-auto text-xs text-gray-500">
                        置信度: {(relation.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {relation.evidence && (
                    <p className="text-xs text-gray-600 mt-2 pl-2 border-l-2 border-gray-300">
                      {relation.evidence}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 摘要部分 */}
        {data.key_insights && data.key_insights.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 flex items-center space-x-2 mb-3">
              <FileText className="w-4 h-4" />
              <span>关键洞察</span>
            </h4>
            <div className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
              <ul className="space-y-2">
                {data.key_insights.map((insight, index) => (
                  <li key={index} className="text-sm text-gray-800 leading-relaxed flex items-start space-x-2">
                    <span className="text-indigo-600 font-bold">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    )
  }

  // 渲染搜索结果
  const renderSearchResult = (data: SearchResult) => {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-900">
            搜索结果 ({data.results?.length || 0} 条)
          </h4>
          {data.query && (
            <span className="text-xs text-gray-500">
              查询: <span className="font-medium">{data.query}</span>
            </span>
          )}
        </div>

        {data.results && data.results.map((item, index) => (
          <div
            key={`search-${index}`}
            className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">
                  {item.title || `结果 #${index + 1}`}
                </p>
                <p className="text-sm text-gray-700 mt-2 leading-relaxed">
                  {item.content}
                </p>
                {item.metadata && (
                  <div className="flex items-center space-x-3 mt-3 text-xs text-gray-500">
                    {item.metadata.page && (
                      <span>页码: {item.metadata.page}</span>
                    )}
                    {item.metadata.timestamp && (
                      <span>{new Date(item.metadata.timestamp).toLocaleString()}</span>
                    )}
                  </div>
                )}
              </div>
              {item.relevance_score && (
                <span className="ml-4 px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded">
                  {(item.relevance_score * 100).toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // 渲染摘要结果
  const renderSummaryResult = (data: SummaryResult) => {
    return (
      <div className="space-y-6">
        {/* 主摘要 */}
        {data.summary_text && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">摘要内容</h4>
            <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                {data.summary_text}
              </p>
            </div>
          </div>
        )}

        {/* 关键点 */}
        {data.key_points && data.key_points.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">关键要点</h4>
            <ul className="space-y-2">
              {data.key_points.map((point, index) => (
                <li
                  key={`point-${index}`}
                  className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                >
                  <span className="flex-shrink-0 w-6 h-6 bg-indigo-600 text-white text-xs font-bold rounded-full flex items-center justify-center">
                    {index + 1}
                  </span>
                  <span className="text-sm text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 元数据 */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">摘要信息</h4>
          <div className="grid grid-cols-2 gap-3">
            {data.word_count && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">字数</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {data.word_count}
                </p>
              </div>
            )}
            {data.reading_time_minutes && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">阅读时间</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {data.reading_time_minutes} 分钟
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // 渲染转录结果
  const renderTranscriptResult = (data: TranscriptResult) => {
    return (
      <div className="space-y-6">
        {/* 完整文本 */}
        {data.full_text && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">转录文本</h4>
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                {data.full_text}
              </p>
            </div>
          </div>
        )}

        {/* 说话人分段 */}
        {data.segments && data.segments.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">
              分段内容 ({data.segments.length} 段)
            </h4>
            <div className="space-y-3">
              {data.segments.map((segment, index) => (
                <div
                  key={`segment-${index}`}
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-start space-x-3">
                    {segment.speaker && (
                      <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white text-xs font-bold rounded-full flex items-center justify-center">
                        {segment.speaker}
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {segment.speaker && (
                          <span className="text-xs font-medium text-gray-900">
                            说话人 {segment.speaker}
                          </span>
                        )}
                        {segment.start_time !== undefined && segment.end_time !== undefined && (
                          <span className="text-xs text-gray-500">
                            {segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {segment.text}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 元数据 */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">转录信息</h4>
          <div className="grid grid-cols-3 gap-3">
            {data.duration_seconds && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">时长</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {data.duration_seconds.toFixed(1)}s
                </p>
              </div>
            )}
            {data.language_detected && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">语言</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {data.language_detected}
                </p>
              </div>
            )}
            {data.speakers_detected && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">说话人数</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {data.speakers_detected.length}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // 导出数据
  const handleExport = () => {
    if (onExport) {
      onExport()
      return
    }

    // 默认导出为JSON
    const dataStr = JSON.stringify(result, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `agent-result-${resultType}-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Agent分析结果</h3>
              <p className="text-sm text-gray-500">
                类型: <span className="font-medium">{resultType}</span>
              </p>
            </div>
          </div>

          {/* 导出按钮 */}
          <button
            onClick={handleExport}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>导出结果</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {resultType === 'knowledge' && renderKnowledgeResult(result as KnowledgeAnalysisResult)}
        {resultType === 'search' && renderSearchResult(result as SearchResult)}
        {resultType === 'summary' && renderSummaryResult(result as SummaryResult)}
        {resultType === 'transcript' && renderTranscriptResult(result as TranscriptResult)}
      </div>
    </div>
  )
}

export default AgentResultsViewer
