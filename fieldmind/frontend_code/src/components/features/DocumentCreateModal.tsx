// src/components/features/DocumentCreateModal.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreateDocument } from '../../hooks/useApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface DocumentFormData {
  title: string;
  content: string;
  project_id: string;
}

interface DocumentCreateModalProps {
  onClose: () => void;
}

export function DocumentCreateModal({ onClose }: DocumentCreateModalProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<DocumentFormData>();

  const createDocument = useCreateDocument({
    onSuccess: () => {
      alert('Document created successfully');
      onClose();
    },
  });

  const onSubmit = (data: DocumentFormData) => {
    createDocument.mutate(data);
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Create New Document">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            type="text"
            {...register('title', { required: 'Title is required' })}
          />
          {errors.title && <span className="error">{errors.title.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="content">Content</label>
          <textarea
            id="content"
            rows={10}
            {...register('content')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="project_id">Project ID</label>
          <input
            id="project_id"
            type="text"
            {...register('project_id', { required: 'Project ID is required' })}
          />
          {errors.project_id && <span className="error">{errors.project_id.message}</span>}
        </div>

        <Button type="submit" disabled={createDocument.isPending}>
          {createDocument.isPending ? 'Creating...' : 'Create Document'}
        </Button>
      </form>
    </Modal>
  );
}
