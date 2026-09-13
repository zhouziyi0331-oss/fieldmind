import React, { useState } from 'react';

export default function UploadPage() {
  const [files, setFiles] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles([...files, ...droppedFiles.map(f => ({
      file: f,
      name: f.name,
      size: formatBytes(f.size),
      progress: 0
    }))]);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const startUpload = async () => {
    setUploading(true);

    // 使用真实的上传 API
    const { documentsService } = await import('@/services/fieldmind');

    for (let i = 0; i < files.length; i++) {
      try {
        const fileObj = files[i].file; // 获取实际的 File 对象
        await documentsService.upload(1, fileObj, (progress) => {
          // 真实进度回调
          setFiles(prev => prev.map((f, idx) =>
            idx === i ? {...f, progress} : f
          ));
        });
      } catch (error) {
        console.error('上传失败:', error);
      }
    }

    setUploading(false);
  };

  return (
    <div className="p-8 space-y-8">
      <div className="page-header">
        <h1 className="page-title">Upload Documents</h1>
        <p className="page-subtitle">Add files to your knowledge base</p>
      </div>

      <div className="card p-8">
        <div onDrop={handleDrop} onDragOver={(e) => e.preventDefault()} className="border-2 border-dashed border-gray-300 rounded-lg p-16 text-center hover:border-[#27768A] transition-colors cursor-pointer">
          <div className="text-6xl mb-4">📤</div>
          <div className="text-xl font-medium mb-2">Drop files here or click to upload</div>
          <div className="text-sm text-gray-500">Supported: PDF, DOC, DOCX, TXT, CSV, Excel</div>
        </div>
      </div>

      {files.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Files ({files.length})</h3>
            {!uploading && (
              <button onClick={startUpload} className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E]">
                Upload All
              </button>
            )}
          </div>
          <div className="space-y-3">
            {files.map((file, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="w-10 h-10 bg-[#27768A]/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">{file.name}</div>
                  <div className="text-xs text-gray-500">{file.size}</div>
                  {file.progress > 0 && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 h-1 rounded-full overflow-hidden">
                        <div className="bg-[#27768A] h-1 transition-all" style={{ width: `${file.progress}%` }}></div>
                      </div>
                    </div>
                  )}
                </div>
                <button className="text-red-500 hover:text-red-700">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
