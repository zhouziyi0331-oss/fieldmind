import React from 'react';
import { reportAPI, analyticsAPI } from '@/services/fieldmind-api';

const reports = [
  { id: 1, name: 'Monthly Analytics', description: 'Comprehensive monthly report', schedule: 'Monthly', downloads: 45 },
  { id: 2, name: 'Workflow Performance', description: 'Detailed workflow metrics', schedule: 'Weekly', downloads: 32 },
  { id: 3, name: 'Asset Utilization', description: 'Asset usage trends', schedule: 'Manual', downloads: 18 },
];

export default function ReportsPage() {
  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Generate and manage automated reports</p>
        </div>
        <button className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E]">New Report</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Total Reports</div>
          <div className="text-2xl font-bold">24</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Scheduled</div>
          <div className="text-2xl font-bold text-green-600">8</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Downloads</div>
          <div className="text-2xl font-bold">156</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Last Generated</div>
          <div className="text-sm font-bold">2h ago</div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-6">All Reports</h3>
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4 flex-1">
                <div className="w-12 h-12 bg-[#27768A]/10 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="font-medium">{report.name}</div>
                  <div className="text-sm text-gray-600">{report.description}</div>
                </div>
                <div className="text-sm text-gray-500">{report.schedule}</div>
                <div className="text-sm text-gray-500">{report.downloads} downloads</div>
              </div>
              <div className="flex gap-2">
                <button className="p-2 hover:bg-gray-100 rounded-lg">
                  <svg className="w-5 h-5 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
