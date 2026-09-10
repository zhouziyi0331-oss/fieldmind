import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useBusinessAnalysis } from '@/hooks/useFieldMind'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, Users, Target, DollarSign, Activity, Brain, Download } from 'lucide-react'

const COLORS = ['#27768A', '#748D44', '#F8B042', '#E07A5F', '#81B29A', '#F2CC8F']

export default function BusinessAnalysis() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const [activeTab, setActiveTab] = useState('overview')

  const { data: analysis, isLoading } = useBusinessAnalysis(projectId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const metrics = analysis?.metrics || {
    revenue: 1250000,
    growth: 23.5,
    customers: 1842,
    retention: 87.3,
  }

  const trendData = analysis?.trends || [
    { month: '1月', revenue: 980000, customers: 1520 },
    { month: '2月', revenue: 1050000, customers: 1620 },
    { month: '3月', revenue: 1120000, customers: 1720 },
    { month: '4月', revenue: 1180000, customers: 1780 },
    { month: '5月', revenue: 1220000, customers: 1820 },
    { month: '6月', revenue: 1250000, customers: 1842 },
  ]

  const segmentData = analysis?.segments || [
    { name: '企业客户', value: 45, count: 234 },
    { name: '中小企业', value: 35, count: 456 },
    { name: '个人用户', value: 20, count: 1152 },
  ]

  const productData = analysis?.products || [
    { name: '产品A', revenue: 450000, margin: 35 },
    { name: '产品B', revenue: 380000, margin: 42 },
    { name: '产品C', revenue: 280000, margin: 28 },
    { name: '产品D', revenue: 140000, margin: 51 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="h-8 w-8 text-[#27768A]" />
            商业分析
          </h1>
          <p className="text-gray-600 mt-1">深度商业洞察和数据分析</p>
        </div>
        <Button>
          <Download className="h-4 w-4 mr-2" />
          导出报告
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总收入</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ¥{(metrics.revenue / 10000).toFixed(1)}万
              </p>
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp className="h-3 w-3 text-green-600" />
                <span className="text-sm text-green-600">+{metrics.growth}%</span>
              </div>
            </div>
            <div className="h-12 w-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <DollarSign className="h-6 w-6 text-[#27768A]" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">客户数量</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {metrics.customers.toLocaleString()}
              </p>
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp className="h-3 w-3 text-green-600" />
                <span className="text-sm text-green-600">+15.2%</span>
              </div>
            </div>
            <div className="h-12 w-12 bg-green-50 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-[#748D44]" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">客户留存率</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{metrics.retention}%</p>
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp className="h-3 w-3 text-green-600" />
                <span className="text-sm text-green-600">+2.1%</span>
              </div>
            </div>
            <div className="h-12 w-12 bg-purple-50 rounded-lg flex items-center justify-center">
              <Target className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">活跃度</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">92.4%</p>
              <div className="flex items-center gap-1 mt-2">
                <Activity className="h-3 w-3 text-green-600" />
                <span className="text-sm text-green-600">稳定</span>
              </div>
            </div>
            <div className="h-12 w-12 bg-orange-50 rounded-lg flex items-center justify-center">
              <Activity className="h-6 w-6 text-[#F8B042]" />
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="border-b border-gray-200">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'overview'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              总览
            </button>
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
              onClick={() => setActiveTab('segments')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'segments'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              客户细分
            </button>
            <button
              onClick={() => setActiveTab('products')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'products'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              产品分析
            </button>
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="mt-6 space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">收入和客户趋势</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#27768A" name="收入" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="customers" stroke="#748D44" name="客户数" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <div className="mt-6 space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">月度收入趋势</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="revenue" fill="#27768A" name="收入" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {/* Segments Tab */}
        {activeTab === 'segments' && (
          <div className="mt-6 space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">客户分布</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={segmentData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name} ${entry.value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {segmentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">细分详情</h3>
                <div className="space-y-4 mt-8">
                  {segmentData.map((segment, index) => (
                    <div key={segment.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="text-sm font-medium">{segment.name}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold">{segment.count} 客户</div>
                        <div className="text-xs text-gray-500">{segment.value}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* Products Tab */}
        {activeTab === 'products' && (
          <div className="mt-6 space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">产品收入对比</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={productData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="revenue" fill="#27768A" name="收入" />
                  <Bar dataKey="margin" fill="#748D44" name="利润率 (%)" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}
      </Tabs>
    </div>
  )
}
