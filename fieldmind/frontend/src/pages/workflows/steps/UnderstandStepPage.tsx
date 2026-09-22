import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function UnderstandStepPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const startAnalysis = () => {
    setAnalyzing(true);
    setTimeout(() => {
      setResults([
        { id: 1, title: 'Key Topics Identified', content: 'Main topics: data analysis, ML, business intelligence', confidence: 92 },
        { id: 2, title: 'Document Summary', content: 'Comprehensive analysis of data methodologies', confidence: 88 },
      ]);
      setAnalyzing(false);
    }, 2000);
  };

  return (
    <div className="p-8 space-y-8">
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          {['Collect', 'Process', 'Understand', 'Analyze', 'Collaborate', 'Reuse'].map((step, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                i < 3 ? 'bg-[#27768A] text-white' : 'bg-gray-200 text-gray-400'
              }`}>{i + 1}</div>
              <span className="text-xs mt-2">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 h-1 rounded-full">
          <div className="bg-[#27768A] h-1 rounded-full" style={{ width: '50%' }}></div>
        </div>
      </div>

      <div className="bg-gradient-to-r from-[#F8B042] to-[#FFB84D] rounded-lg p-8 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm text-3xl">📖</div>
          <div>
            <h1 className="text-3xl font-bold">Understand Content</h1>
            <p className="text-white/90">AI-powered content analysis</p>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">AI Analysis</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Select AI Model</label>
            <select className="w-full p-3 border rounded-lg">
              <option>GPT-4</option>
              <option>Claude</option>
              <option>Custom Model</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Analysis Focus</label>
            <div className="flex flex-wrap gap-2">
              {['Key Topics', 'Sentiment', 'Entities', 'Summary'].map((item) => (
                <label key={item} className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input type="checkbox" defaultChecked />
                  <span className="text-sm">{item}</span>
                </label>
              ))}
            </div>
          </div>
          <button onClick={startAnalysis} disabled={analyzing} className="px-6 py-3 bg-[#F8B042] text-white rounded-lg hover:bg-[#E09F3A] disabled:opacity-50">
            {analyzing ? 'Analyzing...' : 'Start Analysis'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Analysis Results</h3>
          <div className="space-y-4">
            {results.map((result) => (
              <div key={result.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{result.title}</h4>
                  <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">{result.confidence}% confidence</span>
                </div>
                <p className="text-sm text-gray-600">{result.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-between">
        <button onClick={() => navigate(`/projects/${projectId}/workflow/process`)} className="px-6 py-3 border rounded-lg hover:bg-gray-50">← Previous</button>
        <button onClick={() => navigate(`/projects/${projectId}/workflow/analyze`)} disabled={results.length === 0} className="px-6 py-3 bg-[#F8B042] text-white rounded-lg hover:bg-[#E09F3A] disabled:opacity-50">Next: Analyze →</button>
      </div>
    </div>
  );
}
