// src/pages/UsersPage.tsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useUsers, useDeleteUser } from '../hooks/useApi';
import { UserList } from '../components/features/UserList';
import { UserCreateModal } from '../components/features/UserCreateModal';
import { Pagination } from '../components/common/Pagination';
import { SearchBar } from '../components/common/SearchBar';
import { Button } from '../components/common/Button';

export function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { data, isLoading, error } = useUsers({
    page,
    page_size: 20,
    search,
  });

  const deleteUser = useDeleteUser({
    onSuccess: () => {
      alert('User deleted successfully');
    },
  });

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      deleteUser.mutate(id);
    }
  };

  if (error) {
    return (
      <div className="error-container">
        <h2>Error loading users</h2>
        <p>{error.message}</p>
      </div>
    );
  }

  return (
    <div className="users-page">
      <header className="page-header">
        <h1>Users</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          Create New User
        </Button>
      </header>

      <div className="page-filters">
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search users..."
        />
      </div>

      {isLoading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <>
          <UserList
            users={data?.data || []}
            onDelete={handleDelete}
          />

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
        <UserCreateModal
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}
    </div>
  );
}
