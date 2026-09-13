import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function ProcessStepPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);

  const options = [
    { id: 1, name: 'Text Extraction', description: 'Extract text from documents', enabled: true },
    { id: 2, name: 'Data Cleaning', description: 'Remove duplicates and errors', enabled: true },
    { id: 3, name: 'Format Conversion', description: 'Convert to standard formats', enabled: false },
    { id: 4, name: 'Language Detection', description: 'Detect document language', enabled: false },
  ];

  const startProcessing = async () => {
    setProcessing(true);
    setProgress(0);

    try {
      // 使用真实的批处理 API
      const { batchService } = await import('@/services/fieldmind');

      // 创建批处理任务
      const response = await batchService.createJob(Number(projectId), [1, 2, 3]); // 示例文档 IDs
      const jobId = response?.job_id || response?.id;

      // 轮询任务状态获取真实进度
      const pollInterval = setInterval(async () => {
        try {
          const jobStatus = await batchService.getJob(jobId);
          const currentProgress = Math.round(
            (jobStatus.processed_documents / jobStatus.total_documents) * 100
          );
          setProgress(currentProgress);

          if (currentProgress >= 100 || jobStatus.status === 'completed') {
            clearInterval(pollInterval);
            setProcessing(false);
          }
        } catch (error) {
          console.error('获取任务状态失败:', error);
          clearInterval(pollInterval);
          setProcessing(false);
        }
      }, 2000); // 每2秒轮询一次

    } catch (error) {
      console.error('启动处理失败:', error);
      setProcessing(false);
    }
  };

  return (
    <div className="p-8 space-y-8">
      {/* Progress Bar */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          {['Collect', 'Process', 'Understand', 'Analyze', 'Collaborate', 'Reuse'].map((step, i) => (
            <div key={i} className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                i < 2 ? 'bg-[#27768A] text-white' : 'bg-gray-200 text-gray-400'
              }`}>
                {i + 1}
              </div>
              <span className="text-xs mt-2">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 h-1 rounded-full">
          <div className="bg-[#27768A] h-1 rounded-full" style={{ width: '33.33%' }}></div>
        </div>
      </div>

      {/* Header */}
      <div className="bg-gradient-to-r from-[#748D44] to-[#85A156] rounded-lg p-8 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm text-3xl">⚙️</div>
          <div>
            <h1 className="text-3xl font-bold">Process Data</h1>
            <p className="text-white/90">Transform and clean your data</p>
          </div>
        </div>
      </div>

      {/* Processing Options */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">Processing Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {options.map((opt) => (
            <div key={opt.id} className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${opt.enabled ? 'border-[#748D44] bg-[#748D44]/5' : 'border-gray-200 hover:border-gray-300'}`}>
              <div className="flex items-start justify-between mb-2">
                <div className="font-medium">{opt.name}</div>
                <input type="checkbox" checked={opt.enabled} className="rounded" readOnly />
              </div>
              <div className="text-sm text-gray-600">{opt.description}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Processing Status */}
      {processing && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Processing...</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Processing files...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                <div className="bg-[#748D44] h-2 transition-all duration-300" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <button onClick={() => navigate(`/projects/${projectId}/workflow/collect`)} className="px-6 py-3 border rounded-lg hover:bg-gray-50">
          ← Previous
        </button>
        <div className="flex gap-3">
          {!processing && progress === 0 && (
            <button onClick={startProcessing} className="px-6 py-3 bg-[#748D44] text-white rounded-lg hover:bg-[#5C7136]">
              Start Processing
            </button>
          )}
          {progress === 100 && (
            <button onClick={() => navigate(`/projects/${projectId}/workflow/understand`)} className="px-6 py-3 bg-[#748D44] text-white rounded-lg hover:bg-[#5C7136]">
              Next: Understand →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
