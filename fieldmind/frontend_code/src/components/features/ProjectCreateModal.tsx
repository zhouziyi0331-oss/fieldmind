// src/components/features/ProjectCreateModal.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreateProject } from '../../hooks/useApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface ProjectFormData {
  name: string;
  description: string;
}

interface ProjectCreateModalProps {
  onClose: () => void;
}

export function ProjectCreateModal({ onClose }: ProjectCreateModalProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<ProjectFormData>();

  const createProject = useCreateProject({
    onSuccess: () => {
      alert('Project created successfully');
      onClose();
    },
  });

  const onSubmit = (data: ProjectFormData) => {
    createProject.mutate(data);
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Create New Project">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="name">Project Name *</label>
          <input
            id="name"
            type="text"
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && <span className="error">{errors.name.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            rows={5}
            {...register('description')}
          />
        </div>

        <Button type="submit" disabled={createProject.isPending}>
          {createProject.isPending ? 'Creating...' : 'Create Project'}
        </Button>
      </form>
    </Modal>
  );
}
