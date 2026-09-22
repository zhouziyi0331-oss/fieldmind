import React from 'react';
import { assetAPI } from '@/services/fieldmind-api';

const assets = [
  { id: 1, name: 'Analysis Template', description: 'Data analysis template', type: 'Template', downloads: 342, color: '#27768A' },
  { id: 2, name: 'ML Model v3', description: 'Machine learning model', type: 'Model', downloads: 156, color: '#748D44' },
  { id: 3, name: 'Training Dataset', description: 'Curated dataset', type: 'Dataset', downloads: 89, color: '#F8B042' },
];

export default function AssetsPage() {
  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="page-title">Asset Library</h1>
          <p className="page-subtitle">Manage reusable knowledge assets</p>
        </div>
        <button className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] transition-colors">
          Upload Asset
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {assets.map((asset) => (
          <div key={asset.id} className="card overflow-hidden hover:shadow-lg transition-all cursor-pointer">
            <div className="h-40 flex items-center justify-center text-white" style={{ backgroundColor: asset.color }}>
              <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-2">{asset.name}</h3>
              <p className="text-sm text-gray-600 mb-4">{asset.description}</p>
              <div className="flex items-center justify-between">
                <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                  {asset.type}
                </span>
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {asset.downloads}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
