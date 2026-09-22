import React from 'react';
import { analyticsAPI, dashboardAPI } from '@/services/fieldmind-api';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const activityData = [
  { name: 'Mon', value: 120 },
  { name: 'Tue', value: 200 },
  { name: 'Wed', value: 150 },
  { name: 'Thu', value: 80 },
  { name: 'Fri', value: 70 },
  { name: 'Sat', value: 110 },
  { name: 'Sun', value: 130 },
];

const pieData = [
  { name: 'Documents', value: 400, color: '#27768A' },
  { name: 'Workflows', value: 300, color: '#748D44' },
  { name: 'Assets', value: 200, color: '#F8B042' },
  { name: 'Reports', value: 100, color: '#EC6A52' },
];

export default function AnalyticsPage() {
  return (
    <div className="p-8 space-y-8">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p className="page-subtitle">Data insights and performance metrics</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-2">Total Usage</div>
          <div className="text-3xl font-bold">94.2%</div>
          <div className="text-sm text-green-600 mt-2">+12.5%</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-2">Performance</div>
          <div className="text-3xl font-bold">87.3%</div>
          <div className="text-sm text-green-600 mt-2">+5.2%</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-2">Success Rate</div>
          <div className="text-3xl font-bold">96.8%</div>
          <div className="text-sm text-green-600 mt-2">+3.1%</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-2">Avg Time</div>
          <div className="text-3xl font-bold">2.4s</div>
          <div className="text-sm text-red-600 mt-2">-0.3s</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Activity Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="name" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#27768A" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Resource Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label>
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Items */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">Top Projects</h3>
        <div className="space-y-4">
          {[
            { name: 'Data Analysis', value: 1247, percent: 85 },
            { name: 'ML Pipeline', value: 892, percent: 72 },
            { name: 'Research Docs', value: 634, percent: 58 },
          ].map((item, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">{item.name}</span>
                  <span className="text-sm text-gray-600">{item.value}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-[#27768A] h-2 rounded-full" style={{ width: `${item.percent}%` }}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
