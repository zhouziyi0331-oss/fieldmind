// src/pages/DocumentEditorPage.tsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDocument, useUpdateDocument, useDeleteDocument } from '../hooks/useApi';
import { Button } from '../components/common/Button';
import { TextEditor } from '../components/common/TextEditor';

export function DocumentEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const { data, isLoading } = useDocument(id!);
  const updateDocument = useUpdateDocument();
  const deleteDocument = useDeleteDocument();

  useEffect(() => {
    if (data?.data) {
      setTitle(data.data.title);
      setContent(data.data.content);
    }
  }, [data]);

  const handleSave = async () => {
    await updateDocument.mutateAsync({
      id: id!,
      data: { title, content },
    });
    setHasChanges(false);
    alert('Document saved successfully');
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      await deleteDocument.mutateAsync(id!);
      navigate('/documents');
    }
  };

  const handleChange = () => {
    setHasChanges(true);
  };

  if (isLoading) {
    return <div className="loading">Loading document...</div>;
  }

  if (!data) {
    return <div className="error">Document not found</div>;
  }

  return (
    <div className="document-editor-page">
      <header className="editor-header">
        <input
          type="text"
          className="title-input"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            handleChange();
          }}
          placeholder="Document title..."
        />

        <div className="actions">
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateDocument.isPending}
          >
            {updateDocument.isPending ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
          <Button onClick={() => navigate('/documents')}>
            Back to Documents
          </Button>
        </div>
      </header>

      <div className="editor-container">
        <TextEditor
          value={content}
          onChange={(value) => {
            setContent(value);
            handleChange();
          }}
        />
      </div>

      {hasChanges && (
        <div className="unsaved-changes-notice">
          You have unsaved changes
        </div>
      )}
    </div>
  );
}
