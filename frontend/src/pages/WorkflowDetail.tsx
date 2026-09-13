import React from 'react';
import { workflowAPI } from '@/services/fieldmind-api';
import { useParams, useNavigate } from 'react-router-dom';

export default function WorkflowDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const steps = [
    { name: 'Collect', status: 'completed', icon: 'FolderAdd' },
    { name: 'Process', status: 'completed', icon: 'Cog' },
    { name: 'Understand', status: 'running', icon: 'Book' },
    { name: 'Analyze', status: 'pending', icon: 'Chart' },
    { name: 'Collaborate', status: 'pending', icon: 'Users' },
    { name: 'Reuse', status: 'pending', icon: 'Box' },
  ];

  return (
    <div className="p-8 space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm">
        <button onClick={() => navigate('/workflows')} className="text-gray-600 hover:text-gray-900">Workflows</button>
        <span className="text-gray-400">/</span>
        <span className="text-gray-900 font-medium">Workflow Details</span>
      </nav>

      {/* Header */}
      <div className="bg-gradient-to-r from-[#748D44] to-[#85A156] rounded-lg p-8 text-white">
        <div className="flex items-start justify-between">
          <div className="flex gap-6">
            <div className="w-20 h-20 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-2">Data Processing Pipeline</h1>
              <p className="text-white/90">Complete 6-step workflow for data analysis</p>
              <div className="flex items-center gap-4 mt-4">
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm backdrop-blur-sm">Running</span>
                <span className="text-sm">Version 2.1</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors">Edit</button>
            <button className="px-4 py-2 bg-white text-[#748D44] rounded-lg hover:bg-white/90 transition-colors font-medium">Execute</button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Total Executions</div>
          <div className="text-2xl font-bold">142</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Success Rate</div>
          <div className="text-2xl font-bold text-green-600">94%</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Avg Duration</div>
          <div className="text-2xl font-bold">3.5h</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Last Run</div>
          <div className="text-2xl font-bold">3h ago</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Steps */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-6">Workflow Steps</h3>
            <div className="space-y-4">
              {steps.map((step, i) => (
                <div key={i} className="relative flex items-start gap-4">
                  {i < steps.length - 1 && (
                    <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-gray-200"></div>
                  )}
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    step.status === 'completed' ? 'bg-green-100 text-green-600' :
                    step.status === 'running' ? 'bg-blue-100 text-blue-600' :
                    'bg-gray-100 text-gray-400'
                  }`}>
                    <span className="font-bold">{i + 1}</span>
                  </div>
                  <div className="flex-1 pb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">{step.name}</h4>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        step.status === 'completed' ? 'bg-green-100 text-green-800' :
                        step.status === 'running' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {step.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">Step description and configuration</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Execution History */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Execution History</h3>
            <div className="space-y-3">
              {[
                { id: 1, status: 'success', time: '3h ago', duration: '3h 24m' },
                { id: 2, status: 'running', time: '5h ago', duration: '1h 30m' },
                { id: 3, status: 'success', time: '1d ago', duration: '3h 18m' },
              ].map((exec) => (
                <div key={exec.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      exec.status === 'success' ? 'bg-green-500' :
                      exec.status === 'running' ? 'bg-blue-500' :
                      'bg-red-500'
                    }`}></div>
                    <span className="text-sm font-medium">Run #{exec.id}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>{exec.duration}</span>
                    <span>{exec.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Configuration</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500 mb-1">Timeout</div>
                <div className="text-sm font-medium">7200s</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Retry Policy</div>
                <div className="text-sm">3 attempts</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Notifications</div>
                <div className="text-sm">Enabled</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
