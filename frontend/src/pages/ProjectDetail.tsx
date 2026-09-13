import React from 'react';
import { projectAPI, documentAPI, knowledgeGraphAPI } from '@/services/fieldmind-api';
import { useParams, useNavigate } from 'react-router-dom';

export default function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="p-8 space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm">
        <button onClick={() => navigate('/projects')} className="text-gray-600 hover:text-gray-900">Projects</button>
        <span className="text-gray-400">/</span>
        <span className="text-gray-900 font-medium">Project Details</span>
      </nav>

      {/* Header */}
      <div className="bg-gradient-to-r from-[#27768A] to-[#589DA4] rounded-lg p-8 text-white">
        <div className="flex items-start justify-between">
          <div className="flex gap-6">
            <div className="w-20 h-20 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-2">Data Analysis Project</h1>
              <p className="text-white/90">Comprehensive data analysis and visualization</p>
              <div className="flex items-center gap-4 mt-4">
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm backdrop-blur-sm">Active</span>
                <span className="flex items-center gap-1 text-sm">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Created 2024-01-15
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors">Edit</button>
            <button className="px-4 py-2 bg-white text-[#27768A] rounded-lg hover:bg-white/90 transition-colors font-medium">Start Workflow</button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Total Tasks</div>
          <div className="text-2xl font-bold">24</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Completed</div>
          <div className="text-2xl font-bold text-green-600">18</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">In Progress</div>
          <div className="text-2xl font-bold text-blue-600">4</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Team Members</div>
          <div className="text-2xl font-bold">5</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Activity */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-4">
              {[
                { action: 'Workflow executed', time: '2 hours ago', user: 'John Doe' },
                { action: 'Document uploaded', time: '5 hours ago', user: 'Jane Smith' },
                { action: 'Analysis completed', time: '1 day ago', user: 'Bob Wilson' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3 pb-4 border-b last:border-b-0">
                  <div className="w-8 h-8 bg-[#27768A]/10 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm">{item.action}</div>
                    <div className="text-xs text-gray-500 mt-1">by {item.user} · {item.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Workflows */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Workflows</h3>
              <button className="text-sm text-[#27768A] hover:text-[#1F5E6E]">View All</button>
            </div>
            <div className="space-y-3">
              {['Data Processing', 'Analysis Pipeline', 'Report Generation'].map((wf, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-[#27768A] rounded-lg flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <span className="font-medium">{wf}</span>
                  </div>
                  <span className="text-xs text-gray-500">Last run: 2h ago</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Project Info */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Project Info</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500 mb-1">Owner</div>
                <div className="text-sm font-medium">John Doe</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Created</div>
                <div className="text-sm">Jan 15, 2024</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Last Updated</div>
                <div className="text-sm">2 hours ago</div>
              </div>
            </div>
          </div>

          {/* Team */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Team Members</h3>
            <div className="space-y-3">
              {['JD', 'JS', 'BW', 'AK', 'ML'].map((initial, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#27768A] flex items-center justify-center text-white text-xs font-medium">
                    {initial}
                  </div>
                  <div className="text-sm">Team Member {i + 1}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
