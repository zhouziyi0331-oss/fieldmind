// src/pages/HomePage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useCurrentUser } from '../hooks/useApi';

export function HomePage() {
  const { data: currentUser } = useCurrentUser();

  return (
    <div className="home-page">
      <header className="hero">
        <h1>Welcome to FieldMind</h1>
        {currentUser ? (
          <p>Hello, {currentUser.data.name}!</p>
        ) : (
          <p>Your knowledge management platform</p>
        )}
      </header>

      <section className="features">
        <h2>Features</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>📚 Documents</h3>
            <p>Manage and organize your documents</p>
            <Link to="/documents">Browse Documents</Link>
          </div>

          <div className="feature-card">
            <h3>👥 Users</h3>
            <p>Collaborate with your team</p>
            <Link to="/users">View Users</Link>
          </div>

          <div className="feature-card">
            <h3>📊 Projects</h3>
            <p>Track your projects</p>
            <Link to="/projects">View Projects</Link>
          </div>

          <div className="feature-card">
            <h3>🔍 Search</h3>
            <p>Find anything quickly</p>
            <Link to="/search">Search</Link>
          </div>
        </div>
      </section>

      <section className="quick-stats">
        <h2>Quick Stats</h2>
        {/* Add stats here */}
      </section>
    </div>
  );
}
