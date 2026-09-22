// src/pages/ProjectsPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjects, useCreateProject } from '../hooks/useApi';
import { ProjectGrid } from '../components/features/ProjectGrid';
import { ProjectCreateModal } from '../components/features/ProjectCreateModal';
import { Button } from '../components/common/Button';

export function ProjectsPage() {
  const navigate = useNavigate();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { data, isLoading } = useProjects();

  const createProject = useCreateProject({
    onSuccess: (response) => {
      navigate(`/projects/${response.data.id}`);
    },
  });

  return (
    <div className="projects-page">
      <header className="page-header">
        <h1>Projects</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          Create New Project
        </Button>
      </header>

      {isLoading ? (
        <div className="loading">Loading projects...</div>
      ) : (
        <ProjectGrid projects={data?.data || []} />
      )}

      {isCreateModalOpen && (
        <ProjectCreateModal
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}
    </div>
  );
}
