import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function CollectStepPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [files, setFiles] = useState<any[]>([]);

  const dataSources = [
    { id: 1, name: 'Local Files', icon: '📁', color: '#27768A' },
    { id: 2, name: 'Google Drive', icon: '☁️', color: '#748D44' },
    { id: 3, name: 'Database', icon: '🗄️', color: '#F8B042' },
    { id: 4, name: 'API', icon: '🔌', color: '#EC6A52' },
  ];

  return (
    <div className="p-8 space-y-8">
      {/* Progress Bar */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          {['Collect', 'Process', 'Understand', 'Analyze', 'Collaborate', 'Reuse'].map((step, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                i === 0 ? 'bg-[#27768A] text-white' : 'bg-gray-200 text-gray-400'
              }`}>
                {i + 1}
              </div>
              <span className="text-xs mt-2">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 h-1 rounded-full">
          <div className="bg-[#27768A] h-1 rounded-full" style={{ width: '16.67%' }}></div>
        </div>
      </div>

      {/* Header */}
      <div className="bg-gradient-to-r from-[#27768A] to-[#589DA4] rounded-lg p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm text-3xl">
            📥
          </div>
          <div>
            <h1 className="text-3xl font-bold">Collect Data</h1>
            <p className="text-white/90">Gather data from various sources</p>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div className="card p-8">
        <h3 className="text-lg font-semibold mb-4">Upload Documents</h3>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-[#27768A] transition-colors cursor-pointer">
          <div className="text-5xl mb-4">📤</div>
          <div className="text-lg font-medium mb-2">Drop files here or click to upload</div>
          <div className="text-sm text-gray-500">Supported: PDF, DOC, DOCX, TXT, CSV, Excel</div>
        </div>
      </div>

      {/* Data Sources */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">Connect Data Sources</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {dataSources.map((source) => (
            <button key={source.id} className="p-6 border-2 rounded-lg hover:border-[#27768A] transition-colors text-center">
              <div className="text-4xl mb-3">{source.icon}</div>
              <div className="font-medium">{source.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Collected Items */}
      {files.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Collected Items ({files.length})</h3>
          <div className="space-y-2">
            {files.map((file, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#27768A]/10 rounded-lg flex items-center justify-center">
                    📄
                  </div>
                  <div>
                    <div className="font-medium text-sm">{file.name}</div>
                    <div className="text-xs text-gray-500">{file.size}</div>
                  </div>
                </div>
                <button className="text-red-500 hover:text-red-700">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button onClick={() => navigate(`/projects/${projectId}`)} className="px-6 py-3 border rounded-lg hover:bg-gray-50">
          Cancel
        </button>
        <button onClick={() => navigate(`/projects/${projectId}/workflow/process`)} disabled={files.length === 0} className="px-6 py-3 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] disabled:opacity-50 disabled:cursor-not-allowed">
          Next: Process →
        </button>
      </div>
    </div>
  );
}
