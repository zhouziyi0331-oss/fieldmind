import { useParams } from 'react-router-dom'
import { useAnalyticsMetrics, useChartData } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart3, TrendingUp, PieChart, Activity } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart as RechartsPie, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#27768A', '#748D44', '#589DA4', '#F8B042', '#EC6A52']

// 模拟数据
const mockTrendData = [
  { date: '2024-01', documents: 12, insights: 45, quality: 85 },
  { date: '2024-02', documents: 19, insights: 68, quality: 87 },
  { date: '2024-03', documents: 25, insights: 92, quality: 89 },
  { date: '2024-04', documents: 32, insights: 115, quality: 91 },
  { date: '2024-05', documents: 38, insights: 138, quality: 93 },
  { date: '2024-06', documents: 45, insights: 162, quality: 94 },
]

const mockCategoryData = [
  { name: '技术文档', value: 35 },
  { name: '业务分析', value: 28 },
  { name: '项目报告', value: 22 },
  { name: '会议记录', value: 15 },
]

export default function Analytics() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data: metricsData, isLoading } = useAnalyticsMetrics(projectId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const metrics = metricsData?.data || {
    total_documents: 45,
    total_insights: 162,
    avg_quality: 94,
    processing_rate: 98,
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-text-primary">数据分析</h1>
        <p className="text-text-secondary mt-1">深入了解项目数据和趋势</p>
      </div>

      {/* 核心指标 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card hover className="animate-slide-in-up" style={{ animationDelay: '0ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              文档总数
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{metrics.total_documents}</div>
            <p className="text-xs text-success mt-1">↑ 12% 较上月</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              洞察数量
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary">{metrics.total_insights}</div>
            <p className="text-xs text-success mt-1">↑ 18% 较上月</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              平均质量
            </CardTitle>
            <Activity className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-success">{metrics.avg_quality}%</div>
            <p className="text-xs text-success mt-1">↑ 2% 较上月</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '300ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              处理成功率
            </CardTitle>
            <PieChart className="h-4 w-4 text-info" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-info">{metrics.processing_rate}%</div>
            <p className="text-xs text-text-secondary mt-1">稳定运行</p>
          </CardContent>
        </Card>
      </div>

      {/* 图表标签页 */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
          <TabsTrigger value="distribution">分布分析</TabsTrigger>
          <TabsTrigger value="quality">质量分析</TabsTrigger>
        </TabsList>

        {/* 趋势分析 */}
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>数据增长趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={mockTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="date" stroke="#666666" fontSize={12} />
                  <YAxis stroke="#666666" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="documents"
                    name="文档数"
                    stroke="#27768A"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="insights"
                    name="洞察数"
                    stroke="#748D44"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>质量趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="date" stroke="#666666" fontSize={12} />
                  <YAxis stroke="#666666" fontSize={12} domain={[80, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="quality"
                    name="质量分数"
                    stroke="#85A156"
                    strokeWidth={3}
                    dot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 分布分析 */}
        <TabsContent value="distribution" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>文档类型分布</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPie>
                    <Pie
                      data={mockCategoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {mockCategoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPie>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>文档数量对比</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mockCategoryData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="name" stroke="#666666" fontSize={12} />
                    <YAxis stroke="#666666" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="value" fill="#27768A" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 质量分析 */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>质量指标详情</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">数据完整性</span>
                    <span className="text-sm text-text-secondary">96%</span>
                  </div>
                  <div className="h-2 bg-primary/20 rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: '96%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">数据准确性</span>
                    <span className="text-sm text-text-secondary">94%</span>
                  </div>
                  <div className="h-2 bg-secondary/20 rounded-full overflow-hidden">
                    <div className="h-full bg-secondary" style={{ width: '94%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">数据一致性</span>
                    <span className="text-sm text-text-secondary">92%</span>
                  </div>
                  <div className="h-2 bg-success/20 rounded-full overflow-hidden">
                    <div className="h-full bg-success" style={{ width: '92%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">处理速度</span>
                    <span className="text-sm text-text-secondary">98%</span>
                  </div>
                  <div className="h-2 bg-info/20 rounded-full overflow-hidden">
                    <div className="h-full bg-info" style={{ width: '98%' }} />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
