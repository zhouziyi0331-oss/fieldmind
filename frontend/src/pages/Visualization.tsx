import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useVisualizations } from '@/hooks/useFieldMind'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs } from '@/components/ui/tabs'
import { Spinner } from '@/components/ui/spinner'
import { Select } from '@/components/ui/select'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  RadarChart,
  Radar,
  ScatterChart,
  Scatter,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts'
import { BarChart3, Download, Settings, Palette, TrendingUp } from 'lucide-react'

const COLORS = ['#27768A', '#748D44', '#F8B042', '#E07A5F', '#81B29A', '#F2CC8F']

export default function Visualization() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)

  const [activeTab, setActiveTab] = useState('trends')
  const [chartType, setChartType] = useState('line')
  const [timeRange, setTimeRange] = useState('30d')

  const { data: visualizationData, isLoading } = useVisualizations(projectId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const trendData = visualizationData?.trends || [
    { date: '1/1', value: 120, category: 'A' },
    { date: '1/2', value: 132, category: 'A' },
    { date: '1/3', value: 145, category: 'A' },
    { date: '1/4', value: 138, category: 'A' },
    { date: '1/5', value: 155, category: 'A' },
    { date: '1/6', value: 168, category: 'A' },
    { date: '1/7', value: 182, category: 'A' },
  ]

  const categoryData = visualizationData?.categories || [
    { name: '人物', value: 320 },
    { name: '地点', value: 280 },
    { name: '事件', value: 210 },
    { name: '概念', value: 180 },
    { name: '组织', value: 150 },
  ]

  const radarData = visualizationData?.radar || [
    { subject: '准确性', A: 120, B: 110, fullMark: 150 },
    { subject: '完整性', A: 98, B: 130, fullMark: 150 },
    { subject: '一致性', A: 86, B: 130, fullMark: 150 },
    { subject: '时效性', A: 99, B: 100, fullMark: 150 },
    { subject: '相关性', A: 85, B: 90, fullMark: 150 },
  ]

  const scatterData = visualizationData?.scatter || [
    { x: 100, y: 200, z: 200 },
    { x: 120, y: 100, z: 260 },
    { x: 170, y: 300, z: 400 },
    { x: 140, y: 250, z: 280 },
    { x: 150, y: 400, z: 500 },
    { x: 110, y: 280, z: 200 },
  ]

  const comparisonData = visualizationData?.comparison || [
    { month: '1月', docs: 120, entities: 450, relations: 320 },
    { month: '2月', docs: 145, entities: 520, relations: 380 },
    { month: '3月', docs: 168, entities: 680, relations: 450 },
    { month: '4月', docs: 182, entities: 720, relations: 520 },
    { month: '5月', docs: 195, entities: 820, relations: 580 },
    { month: '6月', docs: 210, entities: 890, relations: 650 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-[#27768A]" />
            数据可视化
          </h1>
          <p className="text-gray-600 mt-1">多维度数据分析和可视化展示</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <option value="7d">最近 7 天</option>
            <option value="30d">最近 30 天</option>
            <option value="90d">最近 90 天</option>
            <option value="1y">最近 1 年</option>
          </Select>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            设置
          </Button>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="border-b border-gray-200">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('trends')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'trends'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              趋势分析
            </button>
            <button
              onClick={() => setActiveTab('distribution')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'distribution'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              分布分析
            </button>
            <button
              onClick={() => setActiveTab('comparison')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'comparison'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              对比分析
            </button>
            <button
              onClick={() => setActiveTab('correlation')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'correlation'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              相关性分析
            </button>
          </div>
        </div>

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <div className="mt-6 space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">数据趋势</h3>
                <div className="flex items-center gap-2">
                  <Palette className="h-4 w-4 text-gray-400" />
                  <select
                    value={chartType}
                    onChange={(e) => setChartType(e.target.value)}
                    className="px-3 py-1 text-sm border rounded-md"
                  >
                    <option value="line">折线图</option>
                    <option value="area">面积图</option>
                    <option value="bar">柱状图</option>
                  </select>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={350}>
                {chartType === 'line' ? (
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="value" stroke="#27768A" strokeWidth={2} />
                  </LineChart>
                ) : chartType === 'area' ? (
                  <AreaChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="value" stroke="#27768A" fill="#27768A" fillOpacity={0.3} />
                  </AreaChart>
                ) : (
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#27768A" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </Card>

            <div className="grid grid-cols-3 gap-6">
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <span className="text-sm text-gray-600">增长率</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">+23.5%</p>
                <p className="text-xs text-gray-500 mt-1">相比上期</p>
              </Card>

              <Card className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                  <span className="text-sm text-gray-600">平均值</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">156</p>
                <p className="text-xs text-gray-500 mt-1">数据点平均</p>
              </Card>

              <Card className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="h-5 w-5 text-purple-600" />
                  <span className="text-sm text-gray-600">峰值</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">182</p>
                <p className="text-xs text-gray-500 mt-1">最高记录</p>
              </Card>
            </div>
          </div>
        )}

        {/* Distribution Tab */}
        {activeTab === 'distribution' && (
          <div className="mt-6 space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">类别分布</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name}: ${entry.value}`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">质量雷达图</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis />
                    <Radar name="当前" dataKey="A" stroke="#27768A" fill="#27768A" fillOpacity={0.6} />
                    <Radar name="目标" dataKey="B" stroke="#748D44" fill="#748D44" fillOpacity={0.6} />
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === 'comparison' && (
          <div className="mt-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">多维度对比</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="docs" fill="#27768A" name="文档数" />
                  <Bar dataKey="entities" fill="#748D44" name="实体数" />
                  <Bar dataKey="relations" fill="#F8B042" name="关系数" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {/* Correlation Tab */}
        {activeTab === 'correlation' && (
          <div className="mt-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">散点图分析</h3>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid />
                  <XAxis type="number" dataKey="x" name="指标X" />
                  <YAxis type="number" dataKey="y" name="指标Y" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="数据点" data={scatterData} fill="#27768A" />
                </ScatterChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}
      </Tabs>
    </div>
  )
}
