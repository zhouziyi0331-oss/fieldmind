// src/pages/DocumentsPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocuments, useCreateDocument } from '../hooks/useApi';
import { DocumentList } from '../components/features/DocumentList';
import { DocumentCreateModal } from '../components/features/DocumentCreateModal';
import { SearchBar } from '../components/common/SearchBar';
import { Button } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';

export function DocumentsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { data, isLoading } = useDocuments({
    page,
    page_size: 20,
    search,
  });

  const createDocument = useCreateDocument({
    onSuccess: (response) => {
      navigate(`/documents/${response.data.id}`);
    },
  });

  return (
    <div className="documents-page">
      <header className="page-header">
        <h1>Documents</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          Create New Document
        </Button>
      </header>

      <div className="page-filters">
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search documents..."
        />
      </div>

      {isLoading ? (
        <div className="loading">Loading documents...</div>
      ) : (
        <>
          <DocumentList documents={data?.data || []} />

          {data?.meta && (
            <Pagination
              currentPage={page}
              totalPages={data.meta.total_pages}
              onPageChange={setPage}
            />
          )}
        </>
      )}

      {isCreateModalOpen && (
        <DocumentCreateModal
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}
    </div>
  );
}
