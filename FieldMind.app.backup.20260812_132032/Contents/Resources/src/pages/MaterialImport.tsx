import { useEffect, useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useProjectStore } from '../stores/projectStore';
import { useFileStore } from '../stores/fileStore';
import {
  Upload,
  File,
  Image,
  Video,
  Music,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader,
  Trash2,
} from 'lucide-react';

const MaterialImport = () => {
  const { currentProject } = useProjectStore();
  const { files, uploading, fetchFiles, uploadFile, deleteFile } = useFileStore();

  useEffect(() => {
    if (currentProject) {
      fetchFiles(currentProject.id);
    }
  }, [currentProject?.id]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (!currentProject) return;

      for (const file of acceptedFiles) {
        await uploadFile(currentProject.id, file);
      }
    },
    [currentProject, uploadFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const getFileIcon = (mediaType: string) => {
    switch (mediaType) {
      case 'image':
        return Image;
      case 'video':
        return Video;
      case 'audio':
        return Music;
      case 'text':
        return FileText;
      default:
        return File;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle size={18} color="#27ae60" />;
      case 'processing':
        return <Loader size={18} color="#f39c12" className="spinner" />;
      case 'pending':
        return <Clock size={18} color="#95a5a6" />;
      case 'error':
        return <AlertCircle size={18} color="#e74c3c" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      ready: '已就绪',
      processing: '处理中',
      pending: '等待中',
      error: '失败',
    };
    return statusMap[status] || status;
  };

  const handleDelete = async (fileId: string) => {
    if (confirm('确定要删除这个文件吗？')) {
      await deleteFile(fileId);
    }
  };

  return (
    <div>
      {/* 上传区域 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <div className="card-title">
            <Upload className="card-title-icon" />
            上传材料
          </div>
        </div>

        <div
          {...getRootProps()}
          style={{
            border: '2px dashed var(--border-light)',
            borderRadius: 'var(--radius-md)',
            padding: '48px',
            textAlign: 'center',
            cursor: 'pointer',
            background: isDragActive ? 'rgba(255, 107, 107, 0.05)' : 'var(--bg-light)',
            transition: 'var(--transition)',
          }}
        >
          <input {...getInputProps()} />
          <Upload
            size={48}
            style={{ color: 'var(--color-primary)', margin: '0 auto 16px' }}
          />
          {isDragActive ? (
            <p style={{ fontSize: '16px', color: 'var(--text-dark)' }}>
              松开以上传文件...
            </p>
          ) : (
            <>
              <p style={{ fontSize: '16px', color: 'var(--text-dark)', marginBottom: '8px' }}>
                拖拽文件到此处，或点击选择文件
              </p>
              <p style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                支持音频、视频、图片、文本等多种格式
              </p>
            </>
          )}
        </div>

        {uploading && (
          <div style={{ marginTop: '16px', textAlign: 'center', color: 'var(--color-primary)' }}>
            <Loader size={20} className="spinner" style={{ display: 'inline' }} />
            <span style={{ marginLeft: '8px' }}>上传中...</span>
          </div>
        )}
      </div>

      {/* 文件列表 */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <File className="card-title-icon" />
            文件列表 ({files.length})
          </div>
        </div>

        {files.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-gray)' }}>
            <FileText size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
            <p>还没有上传任何文件</p>
          </div>
        ) : (
          <div>
            {files.map((file) => {
              const FileIcon = getFileIcon(file.media_type);
              return (
                <div
                  key={file.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    padding: '16px',
                    borderBottom: '1px solid var(--border-light)',
                    transition: 'var(--transition)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--bg-light)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <FileIcon size={32} style={{ color: 'var(--color-secondary)' }} />

                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                      {file.filename}
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                      {file.media_type} • {new Date(file.created_at).toLocaleString('zh-CN')}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getStatusIcon(file.status)}
                    <span style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                      {getStatusText(file.status)}
                    </span>
                  </div>

                  <button
                    className="btn-outline"
                    style={{ padding: '6px 12px' }}
                    onClick={() => handleDelete(file.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <style>{`
        .spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default MaterialImport;
