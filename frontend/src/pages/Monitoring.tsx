import { useState, useEffect } from 'react'
import { monitoringAPI } from '@/services/fieldmind-api';
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { monitoringService } from '@/services/fieldmind'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, Server, Database, HardDrive, Cpu, Zap, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react'

export default function Monitoring() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ['system-status', projectId],
    queryFn: () => monitoringService.getMetrics(),
    refetchInterval: 5000,
    enabled: !!projectId,
  })

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      refetch()
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [autoRefresh, refetch])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const metrics = status?.metrics || {
    cpu: 45.2,
    memory: 68.5,
    disk: 42.8,
    network: 125.3,
  }

  const services = status?.services || [
    { name: 'API Server', status: 'healthy', uptime: '99.98%', responseTime: 45 },
    { name: 'Database', status: 'healthy', uptime: '99.99%', responseTime: 12 },
    { name: 'Redis Cache', status: 'healthy', uptime: '99.95%', responseTime: 3 },
    { name: 'OCR Service', status: 'warning', uptime: '98.50%', responseTime: 230 },
    { name: 'AI Model', status: 'healthy', uptime: '99.92%', responseTime: 180 },
    { name: 'File Storage', status: 'healthy', uptime: '100.00%', responseTime: 8 },
  ]

  const cpuHistory = status?.cpuHistory || [
    { time: '10:00', value: 42 },
    { time: '10:05', value: 45 },
    { time: '10:10', value: 48 },
    { time: '10:15', value: 43 },
    { time: '10:20', value: 46 },
    { time: '10:25', value: 45 },
  ]

  const memoryHistory = status?.memoryHistory || [
    { time: '10:00', value: 65 },
    { time: '10:05', value: 66 },
    { time: '10:10', value: 68 },
    { time: '10:15', value: 67 },
    { time: '10:20', value: 69 },
    { time: '10:25', value: 68 },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-red-600" />
      default:
        return <Activity className="h-5 w-5 text-gray-600" />
    }
  }

  const getMetricColor = (value: number) => {
    if (value >= 80) return 'text-red-600'
    if (value >= 60) return 'text-yellow-600'
    return 'text-green-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="h-8 w-8 text-[#27768A]" />
            系统监控
          </h1>
          <p className="text-gray-600 mt-1">实时监控系统状态和性能指标</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? '自动刷新' : '手动刷新'}
          </Button>
          <Button onClick={() => refetch()} size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            立即刷新
          </Button>
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="h-10 w-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <Cpu className="h-5 w-5 text-[#27768A]" />
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(metrics.cpu)}`}>
              {metrics.cpu}%
            </span>
          </div>
          <p className="text-sm text-gray-600">CPU 使用率</p>
          <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${metrics.cpu >= 80 ? 'bg-red-500' : metrics.cpu >= 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
              style={{ width: `${metrics.cpu}%` }}
            />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="h-10 w-10 bg-green-50 rounded-lg flex items-center justify-center">
              <Server className="h-5 w-5 text-[#748D44]" />
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(metrics.memory)}`}>
              {metrics.memory}%
            </span>
          </div>
          <p className="text-sm text-gray-600">内存使用率</p>
          <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${metrics.memory >= 80 ? 'bg-red-500' : metrics.memory >= 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
              style={{ width: `${metrics.memory}%` }}
            />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="h-10 w-10 bg-purple-50 rounded-lg flex items-center justify-center">
              <HardDrive className="h-5 w-5 text-purple-600" />
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(metrics.disk)}`}>
              {metrics.disk}%
            </span>
          </div>
          <p className="text-sm text-gray-600">磁盘使用率</p>
          <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${metrics.disk >= 80 ? 'bg-red-500' : metrics.disk >= 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
              style={{ width: `${metrics.disk}%` }}
            />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="h-10 w-10 bg-orange-50 rounded-lg flex items-center justify-center">
              <Zap className="h-5 w-5 text-[#F8B042]" />
            </div>
            <span className="text-2xl font-bold text-gray-900">
              {metrics.network} MB/s
            </span>
          </div>
          <p className="text-sm text-gray-600">网络流量</p>
          <div className="mt-2 text-xs text-gray-500">
            入: 82 MB/s | 出: 43 MB/s
          </div>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">CPU 使用历史</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={cpuHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#27768A" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">内存使用历史</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={memoryHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#748D44" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Services Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">服务状态</h3>
        <div className="grid gap-4">
          {services.map((service) => (
            <div
              key={service.name}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-4">
                {getStatusIcon(service.status)}
                <div>
                  <p className="font-medium text-gray-900">{service.name}</p>
                  <p className="text-sm text-gray-500">响应时间: {service.responseTime}ms</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-sm text-gray-600">运行时间</p>
                  <p className="text-sm font-semibold">{service.uptime}</p>
                </div>
                <Badge className={getStatusColor(service.status)}>
                  {service.status === 'healthy' ? '正常' : service.status === 'warning' ? '警告' : '错误'}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
