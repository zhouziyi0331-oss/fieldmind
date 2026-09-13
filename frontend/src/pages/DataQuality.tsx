import { useParams } from 'react-router-dom'
import { dataCleaningAPI, validationAPI } from '@/services/fieldmind-api';
import { useDataQuality } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Progress } from '@/components/ui/progress'
import { BarChart3, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const COLORS = ['#27768A', '#748D44', '#F8B042', '#EC6A52', '#589DA4']

export default function DataQuality() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data, isLoading } = useDataQuality(projectId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const quality = data || {
    total_insights: 0,
    avg_confidence: 0,
    high_quality_rate: 0,
    dimension_coverage: [],
  }

  const pieData = quality.dimension_coverage.map((item) => ({
    name: item.dimension,
    value: item.count,
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-text-primary">数据质量</h1>
        <p className="text-text-secondary mt-1">查看数据质量指标和分析</p>
      </div>

      {/* 质量指标卡片 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card hover className="animate-slide-in-up" style={{ animationDelay: '0ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              总洞察数
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{quality.total_insights}</div>
            <p className="text-xs text-text-secondary mt-1">结构化数据</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              平均置信度
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary">
              {quality.avg_confidence.toFixed(2)}
            </div>
            <p className="text-xs text-text-secondary mt-1">数据可信度</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              高质量率
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-success">
              {quality.high_quality_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-text-secondary mt-1">优质数据比例</p>
          </CardContent>
        </Card>
      </div>

      {/* 图表区域 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* 维度覆盖 */}
        <Card className="animate-slide-in-up" style={{ animationDelay: '300ms' }}>
          <CardHeader>
            <CardTitle>维度覆盖</CardTitle>
          </CardHeader>
          <CardContent>
            {quality.dimension_coverage.length === 0 ? (
              <div className="flex items-center justify-center h-64 text-text-secondary">
                暂无数据
              </div>
            ) : (
              <div className="space-y-4">
                {quality.dimension_coverage.map((item, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-text-primary">
                        {item.dimension}
                      </span>
                      <span className="text-sm text-text-secondary">{item.count}</span>
                    </div>
                    <Progress
                      value={
                        quality.total_insights > 0
                          ? (item.count / quality.total_insights) * 100
                          : 0
                      }
                      className="h-2"
                      indicatorClassName={`bg-gradient-to-r from-primary to-secondary`}
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 维度分布饼图 */}
        <Card className="animate-slide-in-up" style={{ animationDelay: '400ms' }}>
          <CardHeader>
            <CardTitle>维度分布</CardTitle>
          </CardHeader>
          <CardContent>
            {pieData.length === 0 ? (
              <div className="flex items-center justify-center h-64 text-text-secondary">
                暂无数据
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
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
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 质量建议 */}
      <Card className="animate-slide-in-up" style={{ animationDelay: '500ms' }}>
        <CardHeader>
          <CardTitle>质量改进建议</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {quality.high_quality_rate < 80 && (
              <div className="flex items-start gap-3 p-3 bg-warning/10 border border-warning rounded-lg">
                <AlertCircle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    高质量数据比例偏低
                  </p>
                  <p className="text-xs text-text-secondary mt-1">
                    建议：检查数据源质量，优化数据清洗流程
                  </p>
                </div>
              </div>
            )}

            {quality.avg_confidence < 0.7 && (
              <div className="flex items-start gap-3 p-3 bg-warning/10 border border-warning rounded-lg">
                <AlertCircle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    平均置信度较低
                  </p>
                  <p className="text-xs text-text-secondary mt-1">
                    建议：增加数据验证规则，提升数据准确性
                  </p>
                </div>
              </div>
            )}

            {quality.dimension_coverage.length < 5 && (
              <div className="flex items-start gap-3 p-3 bg-info/10 border border-info rounded-lg">
                <AlertCircle className="h-5 w-5 text-info flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    维度覆盖不足
                  </p>
                  <p className="text-xs text-text-secondary mt-1">
                    建议：扩展分析维度，获取更全面的数据洞察
                  </p>
                </div>
              </div>
            )}

            {quality.high_quality_rate >= 80 &&
              quality.avg_confidence >= 0.7 &&
              quality.dimension_coverage.length >= 5 && (
                <div className="flex items-start gap-3 p-3 bg-success/10 border border-success rounded-lg">
                  <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      数据质量良好
                    </p>
                    <p className="text-xs text-text-secondary mt-1">
                      您的数据质量达到优秀水平，继续保持！
                    </p>
                  </div>
                </div>
              )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
