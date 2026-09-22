import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function ReuseStepPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [assetName, setAssetName] = useState('');
  const [created, setCreated] = useState(false);

  const createAsset = () => {
    setCreated(true);
    setTimeout(() => {
      navigate(`/projects/${projectId}`);
    }, 2000);
  };

  return (
    <div className="p-8 space-y-8">
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          {['Collect', 'Process', 'Understand', 'Analyze', 'Collaborate', 'Reuse'].map((step, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className="w-10 h-10 rounded-full flex items-center justify-center font-semibold bg-[#27768A] text-white">{i + 1}</div>
              <span className="text-xs mt-2">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-[#27768A] h-1 rounded-full"></div>
      </div>

      <div className="bg-gradient-to-r from-[#85A156] to-[#96B266] rounded-lg p-8 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm text-3xl">📦</div>
          <div>
            <h1 className="text-3xl font-bold">Create Reusable Asset</h1>
            <p className="text-white/90">Save your work for future use</p>
          </div>
        </div>
      </div>

      {!created ? (
        <>
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Asset Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Asset Name</label>
                <input type="text" value={assetName} onChange={(e) => setAssetName(e.target.value)} className="w-full p-3 border rounded-lg" placeholder="Enter asset name" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Asset Type</label>
                <select className="w-full p-3 border rounded-lg">
                  <option>Template</option>
                  <option>Model</option>
                  <option>Dataset</option>
                  <option>Report</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea className="w-full p-3 border rounded-lg" rows={3} placeholder="Describe your asset..."></textarea>
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <button onClick={() => navigate(`/projects/${projectId}/workflow/collaborate`)} className="px-6 py-3 border rounded-lg hover:bg-gray-50">← Previous</button>
            <button onClick={createAsset} disabled={!assetName} className="px-6 py-3 bg-[#85A156] text-white rounded-lg hover:bg-[#6A8145] disabled:opacity-50">
              ✓ Complete Workflow
            </button>
          </div>
        </>
      ) : (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold mb-2">Workflow Completed!</h2>
          <p className="text-gray-600 mb-6">Your asset has been created successfully</p>
          <div className="inline-block">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#85A156] mx-auto"></div>
            <p className="text-sm text-gray-500 mt-4">Redirecting...</p>
          </div>
        </div>
      )}
    </div>
  );
}
