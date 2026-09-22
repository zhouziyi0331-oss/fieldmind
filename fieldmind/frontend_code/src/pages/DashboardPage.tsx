// src/pages/DashboardPage.tsx
import React from 'react';
import { useCurrentUser, useDocuments, useProjects } from '../hooks/useApi';
import { Link } from 'react-router-dom';

export function DashboardPage() {
  const { data: currentUser } = useCurrentUser();
  const { data: recentDocs } = useDocuments({ page_size: 5 });
  const { data: recentProjects } = useProjects({ page_size: 5 });

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Welcome back, {currentUser?.data.name}!</p>
      </header>

      <div className="dashboard-grid">
        <section className="dashboard-card">
          <h2>Recent Documents</h2>
          {recentDocs?.data.length ? (
            <ul className="recent-list">
              {recentDocs.data.map(doc => (
                <li key={doc.id}>
                  <Link to={`/documents/${doc.id}`}>{doc.title}</Link>
                </li>
              ))}
            </ul>
          ) : (
            <p>No recent documents</p>
          )}
          <Link to="/documents" className="view-all">View all documents →</Link>
        </section>

        <section className="dashboard-card">
          <h2>Recent Projects</h2>
          {recentProjects?.data.length ? (
            <ul className="recent-list">
              {recentProjects.data.map(project => (
                <li key={project.id}>
                  <Link to={`/projects/${project.id}`}>{project.name}</Link>
                </li>
              ))}
            </ul>
          ) : (
            <p>No recent projects</p>
          )}
          <Link to="/projects" className="view-all">View all projects →</Link>
        </section>

        <section className="dashboard-card">
          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <Link to="/documents/new" className="action-button">
              📝 New Document
            </Link>
            <Link to="/projects/new" className="action-button">
              📊 New Project
            </Link>
            <Link to="/search" className="action-button">
              🔍 Search
            </Link>
          </div>
        </section>

        <section className="dashboard-card">
          <h2>Activity</h2>
          {/* Add activity feed here */}
          <p>Recent activity will appear here</p>
        </section>
      </div>
    </div>
  );
}
