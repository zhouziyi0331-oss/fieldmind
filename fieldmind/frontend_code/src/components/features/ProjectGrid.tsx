// src/components/features/ProjectGrid.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import type { Project } from '../../api/client';

interface ProjectGridProps {
  projects: Project[];
}

export function ProjectGrid({ projects }: ProjectGridProps) {
  return (
    <div className="project-grid">
      {projects.map(project => (
        <div key={project.id} className="project-card">
          <h3>
            <Link to={`/projects/${project.id}`}>{project.name}</Link>
          </h3>
          <p>{project.description}</p>
          <div className="project-meta">
            <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
