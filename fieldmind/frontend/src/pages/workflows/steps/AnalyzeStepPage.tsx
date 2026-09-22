import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function AnalyzeStepPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();

  const insights = [
    { id: 1, title: 'Key Finding #1', description: 'High correlation between variables A and B', value: '0.89', color: '#27768A' },
    { id: 2, title: 'Key Finding #2', description: 'Significant pattern in time series', value: '94%', color: '#748D44' },
    { id: 3, title: 'Key Finding #3', description: 'Outliers identified', value: '12', color: '#F8B042' },
  ];

  return (
    <div className="p-8 space-y-8">
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          {['Collect', 'Process', 'Understand', 'Analyze', 'Collaborate', 'Reuse'].map((step, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${i < 4 ? 'bg-[#27768A] text-white' : 'bg-gray-200 text-gray-400'}`}>{i + 1}</div>
              <span className="text-xs mt-2">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 h-1 rounded-full">
          <div className="bg-[#27768A] h-1 rounded-full" style={{ width: '66.67%' }}></div>
        </div>
      </div>

      <div className="bg-gradient-to-r from-[#589DA4] to-[#6CADB3] rounded-lg p-8 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm text-3xl">📊</div>
          <div>
            <h1 className="text-3xl font-bold">Analyze Insights</h1>
            <p className="text-white/90">Extract actionable insights</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {insights.map((insight) => (
          <div key={insight.id} className="card p-6">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center text-white mb-4" style={{ backgroundColor: insight.color }}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="font-semibold mb-2">{insight.title}</h3>
            <p className="text-sm text-gray-600 mb-4">{insight.description}</p>
            <div className="text-3xl font-bold" style={{ color: insight.color }}>{insight.value}</div>
          </div>
        ))}
      </div>

      <div className="flex justify-between">
        <button onClick={() => navigate(`/projects/${projectId}/workflow/understand`)} className="px-6 py-3 border rounded-lg hover:bg-gray-50">← Previous</button>
        <button onClick={() => navigate(`/projects/${projectId}/workflow/collaborate`)} className="px-6 py-3 bg-[#589DA4] text-white rounded-lg hover:bg-[#467E83]">Next: Collaborate →</button>
      </div>
    </div>
  );
}
