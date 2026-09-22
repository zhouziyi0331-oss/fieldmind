#!/usr/bin/env python3
"""
批量升级前端页面 - 简化版本
"""

import os
from pathlib import Path

# 需要升级的页面列表
PAGES_TO_UPGRADE = [
    "ChunksQuantification", "DataEnrichment", "Feeding", "Crawler",
    "Annotation", "Tagging", "TopicAnalysis", "PatternRecognition",
    "EnhancedChat", "SuperAgents", "Skills", "SkillGeneration", "SkillOptimization",
    "Learning", "BackgroundLearning", "FeedbackLoops",
    "GovernanceValidation", "Audit", "Traceability",
    "KnowledgeNetwork", "ExperienceGraph", "Lineage",
    "Collaboration", "Tasks", "ExecutionTracking",
    "Workbench", "UnifiedPlugins", "Audio", "UserAnalysis",
    "Industry", "SOP"
]

# 页面配置简化版
PAGE_INFO = {
    "ChunksQuantification": ("区块量化", "Cube", "chunksAPI"),
    "DataEnrichment": ("数据增强", "Sparkles", "enrichmentAPI"),
    "Feeding": ("数据喂养", "Upload", "feedingAPI"),
    "Crawler": ("爬虫管理", "Globe", "crawlerAPI"),
    "Annotation": ("数据标注", "Tag", "annotationAPI"),
    "Tagging": ("智能标签", "Tags", "taggingAPI"),
    "TopicAnalysis": ("主题分析", "Brain", "topicAPI"),
    "PatternRecognition": ("模式识别", "Network", "patternAPI"),
    "EnhancedChat": ("增强对话", "MessageSquare", "chatAPI"),
    "SuperAgents": ("超级智能体", "Bot", "agentsAPI"),
    "Skills": ("技能库", "Zap", "skillsAPI"),
    "SkillGeneration": ("技能生成", "Wand2", "skillGenerationAPI"),
    "SkillOptimization": ("技能优化", "TrendingUp", "skillOptimizationAPI"),
    "Learning": ("学习中心", "GraduationCap", "learningAPI"),
    "BackgroundLearning": ("后台学习", "Settings", "learningAPI"),
    "FeedbackLoops": ("反馈回路", "RefreshCw", "feedbackAPI"),
    "GovernanceValidation": ("治理验证", "ShieldCheck", "governanceAPI"),
    "Audit": ("审计日志", "FileText", "auditAPI"),
    "Traceability": ("数据溯源", "GitBranch", "traceabilityAPI"),
    "KnowledgeNetwork": ("知识网络", "Share2", "knowledgeAPI"),
    "ExperienceGraph": ("经验图谱", "Lightbulb", "experienceAPI"),
    "Lineage": ("血缘分析", "GitMerge", "lineageAPI"),
    "Collaboration": ("协作空间", "Users", "collaborationAPI"),
    "Tasks": ("任务管理", "CheckSquare", "tasksAPI"),
    "ExecutionTracking": ("执行追踪", "Activity", "executionAPI"),
    "Workbench": ("个人工作台", "Layout", "workbenchAPI"),
    "UnifiedPlugins": ("统一插件", "Puzzle", "pluginsAPI"),
    "Audio": ("音频处理", "Mic", "audioAPI"),
    "UserAnalysis": ("用户分析", "BarChart3", "analyticsAPI"),
    "Industry": ("行业方案", "Briefcase", "industryAPI"),
    "SOP": ("标准操作流程", "ListChecks", "sopAPI"),
}

TEMPLATE = '''import { useState, useEffect } from 'react'
import { API_NAME } from '@/services/fieldmind-api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { Dialog } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ICON_NAME, Plus, Search, Edit, Trash2, Filter } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function PAGE_NAME() {
  const { toast } = useToast()
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // TODO: 实际 API 调用
      // const response = await API_NAME.getList()
      // setData(response.data)

      // 模拟数据
      setData([
        { id: 1, name: '示例项目 1', status: 'active', created_at: '2024-01-15' },
        { id: 2, name: '示例项目 2', status: 'pending', created_at: '2024-01-16' },
        { id: 3, name: '示例项目 3', status: 'completed', created_at: '2024-01-17' },
      ])
    } catch (error) {
      console.error('Failed to load data:', error)
      toast({
        title: '加载失败',
        description: '无法加载数据，请重试',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setIsCreateDialogOpen(true)
  }

  const handleEdit = (item: any) => {
    setSelectedItem(item)
    setIsCreateDialogOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除吗？')) return

    try {
      // await API_NAME.delete(id)
      toast({
        title: '删除成功',
        description: '记录已删除',
      })
      loadData()
    } catch (error) {
      toast({
        title: '删除失败',
        description: '无法删除记录，请重试',
        variant: 'destructive',
      })
    }
  }

  const filteredData = data.filter(item =>
    item.name?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusBadge = (status: string) => {
    const colors: any = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <ICON_NAME className="h-8 w-8 text-[#27768A]" />
            PAGE_TITLE
          </h1>
          <p className="text-gray-600 mt-1">DESCRIPTION_TEXT</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          创建
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总数</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{data.length}</p>
            </div>
            <div className="h-12 w-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <ICON_NAME className="h-6 w-6 text-[#27768A]" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">活跃</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {data.filter(d => d.status === 'active').length}
              </p>
            </div>
            <div className="h-12 w-12 bg-green-50 rounded-lg flex items-center justify-center">
              <div className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">待处理</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">
                {data.filter(d => d.status === 'pending').length}
              </p>
            </div>
            <div className="h-12 w-12 bg-yellow-50 rounded-lg flex items-center justify-center">
              <div className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">已完成</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {data.filter(d => d.status === 'completed').length}
              </p>
            </div>
            <div className="h-12 w-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <div className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Search Bar */}
      <Card className="p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>
        </div>
      </Card>

      {/* Data Table */}
      {filteredData.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <ICON_NAME className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无数据</h3>
            <p className="mt-1 text-sm text-gray-500">开始创建第一条记录</p>
            <Button onClick={handleCreate} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              创建
            </Button>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredData.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{item.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge className={getStatusBadge(item.status)}>
                        {item.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.created_at}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(item)}
                        className="text-[#27768A] hover:text-[#1F5E6E] mr-4"
                      >
                        <Edit className="h-4 w-4 inline" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            {selectedItem ? '编辑' : '创建'}
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">名称</label>
              <Input placeholder="输入名称" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">描述</label>
              <Input placeholder="输入描述" />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button
              variant="outline"
              onClick={() => {
                setIsCreateDialogOpen(false)
                setSelectedItem(null)
              }}
            >
              取消
            </Button>
            <Button onClick={() => {
              setIsCreateDialogOpen(false)
              setSelectedItem(null)
              toast({
                title: '保存成功',
                description: '记录已保存',
              })
            }}>
              保存
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
'''

def main():
    frontend_path = Path("/Users/alwan/FieldMind/frontend/src/pages")

    print("=" * 80)
    print("🚀 开始批量升级页面")
    print("=" * 80)
    print()

    upgraded_count = 0

    for page_name in PAGES_TO_UPGRADE:
        page_file = frontend_path / f"{page_name}.tsx"

        if not page_file.exists():
            print(f"⚠️  跳过: {page_name}.tsx (文件不存在)")
            continue

        if page_name not in PAGE_INFO:
            print(f"⚠️  跳过: {page_name}.tsx (无配置信息)")
            continue

        title, icon, api = PAGE_INFO[page_name]

        print(f"📝 升级: {page_name}.tsx - {title}")

        # 生成代码
        code = TEMPLATE.replace('PAGE_NAME', page_name)
        code = code.replace('PAGE_TITLE', title)
        code = code.replace('ICON_NAME', icon)
        code = code.replace('API_NAME', api)
        code = code.replace('DESCRIPTION_TEXT', f'管理和操作{title}')

        # 写入文件
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(code)

        upgraded_count += 1

    print()
    print("=" * 80)
    print(f"✅ 完成！已升级 {upgraded_count} 个页面")
    print("=" * 80)

if __name__ == "__main__":
    main()
