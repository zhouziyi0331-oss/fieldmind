import React, { useState, useEffect } from 'react';
import { workflowAPI } from '@/services/fieldmind-api';

interface WorkflowExecution {
  workflow_id: string;
  workflow_type: string;
  status: string;
  created_at: string;
  completed_at?: string;
  project_id?: number;
  document_id?: number;
}

interface WorkflowStats {
  total_workflows: number;
  running: number;
  completed: number;
  failed: number;
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#748D44',
  running: '#27768A',
  completed: '#2B936C',
  failed: '#C94B3F',
  cancelled: '#8B8B8B'
};

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
  const [stats, setStats] = useState<WorkflowStats | null>(null);
  const [templates, setTemplates] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
    loadTemplates();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const [workflowsData, statsData] = await Promise.all([
        workflowAPI.getWorkflows(),
        workflowAPI.getWorkflowStats()
      ]);
      setWorkflows(workflowsData);
      setStats(statsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load workflows');
      console.error('Error loading workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const templatesData = await workflowAPI.getWorkflowTemplates();
      setTemplates(templatesData);
    } catch (err) {
      console.error('Error loading templates:', err);
    }
  };

  const handleExecuteWorkflow = async (workflowType: string) => {
    try {
      await workflowAPI.executeWorkflow({
        workflow_type: workflowType,
        project_id: 1 // TODO: Get from context or user selection
      });
      loadWorkflows();
    } catch (err: any) {
      alert(`Failed to execute workflow: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#27768A] mx-auto mb-4"></div>
          <p className="text-gray-600">Loading workflows...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="card p-6 border-red-200 bg-red-50">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Workflows</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadWorkflows}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="page-title">Workflows</h1>
          <p className="page-subtitle">Manage and execute workflows</p>
        </div>
        <button
          onClick={() => handleExecuteWorkflow('document_processing')}
          className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] transition-colors"
        >
          New Workflow
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card p-6">
            <div className="text-3xl font-bold text-[#27768A]">{stats.total_workflows}</div>
            <div className="text-sm text-gray-600 mt-1">Total Workflows</div>
          </div>
          <div className="card p-6">
            <div className="text-3xl font-bold text-[#748D44]">{stats.running}</div>
            <div className="text-sm text-gray-600 mt-1">Running</div>
          </div>
          <div className="card p-6">
            <div className="text-3xl font-bold text-[#2B936C]">{stats.completed}</div>
            <div className="text-sm text-gray-600 mt-1">Completed</div>
          </div>
          <div className="card p-6">
            <div className="text-3xl font-bold text-[#C94B3F]">{stats.failed}</div>
            <div className="text-sm text-gray-600 mt-1">Failed</div>
          </div>
        </div>
      )}

      {workflows.length === 0 ? (
        <div className="card p-12 text-center">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Workflows Yet</h3>
          <p className="text-gray-600 mb-4">Create your first workflow to get started</p>
          <button
            onClick={() => handleExecuteWorkflow('document_processing')}
            className="px-6 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E] transition-colors"
          >
            Create Workflow
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((wf) => (
            <div key={wf.workflow_id} className="card p-6 hover:shadow-lg transition-all cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-12 h-12 rounded-lg flex items-center justify-center text-white"
                  style={{ backgroundColor: STATUS_COLORS[wf.status] || '#8B8B8B' }}
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2 capitalize">
                {wf.workflow_type.replace(/_/g, ' ')}
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                ID: {wf.workflow_id.substring(0, 8)}...
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">
                  {new Date(wf.created_at).toLocaleDateString()}
                </span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full capitalize ${
                  wf.status === 'completed' ? 'bg-green-100 text-green-800' :
                  wf.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  wf.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {wf.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
