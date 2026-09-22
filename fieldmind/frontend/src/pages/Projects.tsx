import React from 'react';
import { projectAPI } from '@/services/fieldmind-api';
import { useNavigate } from 'react-router-dom';

const projects = [
  { id: 1, name: 'Data Analysis Project', description: 'Comprehensive data analysis workflow', status: 'Active', color: '#27768A', members: 5, tasks: 24, updated: '2 hours ago' },
  { id: 2, name: 'ML Pipeline', description: 'Machine learning data pipeline', status: 'In Progress', color: '#748D44', members: 3, tasks: 18, updated: '5 hours ago' },
  { id: 3, name: 'Research Documentation', description: 'Research knowledge base', status: 'Active', color: '#F8B042', members: 7, tasks: 32, updated: '1 day ago' },
];

export default function ProjectsPage() {
  const navigate = useNavigate();

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-subtitle">Manage your knowledge projects</p>
        </div>
        <button className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] transition-colors flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <div
            key={project.id}
            onClick={() => navigate(`/projects/${project.id}`)}
            className="card p-6 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center text-white" style={{ backgroundColor: project.color }}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                {project.status}
              </span>
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-2">{project.name}</h3>
            <p className="text-sm text-gray-600 mb-4">{project.description}</p>

            <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  {project.members}
                </span>
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  {project.tasks}
                </span>
              </div>
              <span className="text-xs">{project.updated}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
