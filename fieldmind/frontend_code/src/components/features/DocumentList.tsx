// src/components/features/DocumentList.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import type { Document } from '../../api/client';

interface DocumentListProps {
  documents: Document[];
}

export function DocumentList({ documents }: DocumentListProps) {
  return (
    <div className="document-list">
      {documents.map(doc => (
        <div key={doc.id} className="document-card">
          <h3>
            <Link to={`/documents/${doc.id}`}>{doc.title}</Link>
          </h3>
          <p className="document-preview">
            {doc.content.substring(0, 150)}...
          </p>
          <div className="document-meta">
            <span>Created: {new Date(doc.created_at).toLocaleDateString()}</span>
            <span>Updated: {new Date(doc.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
