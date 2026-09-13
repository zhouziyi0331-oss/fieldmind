import React from 'react';
import { workflowAPI } from '@/services/fieldmind-api';

const workflows = [
  { id: 1, name: 'Data Processing Pipeline', description: 'Complete 6-step workflow', status: 'Active', runs: 42, color: '#27768A' },
  { id: 2, name: 'Document Analysis', description: 'Automated document processing', status: 'Running', runs: 28, color: '#748D44' },
  { id: 3, name: 'Knowledge Builder', description: 'Build knowledge base', status: 'Completed', runs: 15, color: '#F8B042' },
];

export default function WorkflowsPage() {
  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="page-title">Workflows</h1>
          <p className="page-subtitle">Manage and execute workflows</p>
        </div>
        <button className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] transition-colors">
          New Workflow
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workflows.map((wf) => (
          <div key={wf.id} className="card p-6 hover:shadow-lg transition-all cursor-pointer">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center text-white" style={{ backgroundColor: wf.color }}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <h3 className="text-lg font-semibold mb-2">{wf.name}</h3>
            <p className="text-sm text-gray-600 mb-4">{wf.description}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">{wf.runs} runs</span>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                wf.status === 'Active' ? 'bg-green-100 text-green-800' :
                wf.status === 'Running' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {wf.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
