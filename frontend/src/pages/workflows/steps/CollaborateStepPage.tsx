import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function CollaborateStepPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);

  const teamMembers = [
    { id: 1, name: 'John Doe', email: 'john@example.com', avatar: 'JD' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', avatar: 'JS' },
    { id: 3, name: 'Bob Wilson', email: 'bob@example.com', avatar: 'BW' },
  ];

  return (
    <div className="p-8 space-y-8">
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          {['Collect', 'Process', 'Understand', 'Analyze', 'Collaborate', 'Reuse'].map((step, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${i < 5 ? 'bg-[#27768A] text-white' : 'bg-gray-200 text-gray-400'}`}>{i + 1}</div>
              <span className="text-xs mt-2">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 h-1 rounded-full">
          <div className="bg-[#27768A] h-1 rounded-full" style={{ width: '83.33%' }}></div>
        </div>
      </div>

      <div className="bg-gradient-to-r from-[#85A156] to-[#96B266] rounded-lg p-8 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm text-3xl">👥</div>
          <div>
            <h1 className="text-3xl font-bold">Collaborate</h1>
            <p className="text-white/90">Share findings with your team</p>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">Select Team Members</h3>
        <div className="space-y-3">
          {teamMembers.map((member) => (
            <label key={member.id} className="flex items-center gap-4 p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
              <input type="checkbox" className="rounded" onChange={(e) => {
                if (e.target.checked) setSelectedMembers([...selectedMembers, member.id]);
                else setSelectedMembers(selectedMembers.filter(id => id !== member.id));
              }} />
              <div className="w-10 h-10 bg-[#85A156] rounded-full flex items-center justify-center text-white font-medium">{member.avatar}</div>
              <div className="flex-1">
                <div className="font-medium">{member.name}</div>
                <div className="text-sm text-gray-500">{member.email}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">Add Message</h3>
        <textarea className="w-full p-4 border rounded-lg" rows={4} placeholder="Add a message for your team..."></textarea>
      </div>

      {selectedMembers.length > 0 && (
        <div className="card p-6 bg-green-50 border-green-200">
          <div className="flex items-center gap-2 text-green-800">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">{selectedMembers.length} team member(s) selected</span>
          </div>
        </div>
      )}

      <div className="flex justify-between">
        <button onClick={() => navigate(`/projects/${projectId}/workflow/analyze`)} className="px-6 py-3 border rounded-lg hover:bg-gray-50">← Previous</button>
        <button onClick={() => navigate(`/projects/${projectId}/workflow/reuse`)} className="px-6 py-3 bg-[#85A156] text-white rounded-lg hover:bg-[#6A8145]">Next: Reuse →</button>
      </div>
    </div>
  );
}
