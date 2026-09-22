// src/pages/UserDetailPage.tsx
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUser, useUpdateUser, useDeleteUser } from '../hooks/useApi';
import { UserForm } from '../components/features/UserForm';
import { Button } from '../components/common/Button';

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading } = useUser(id!);
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const handleUpdate = async (formData: any) => {
    await updateUser.mutateAsync({ id: id!, data: formData });
    alert('User updated successfully');
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      await deleteUser.mutateAsync(id!);
      navigate('/users');
    }
  };

  if (isLoading) {
    return <div className="loading">Loading user...</div>;
  }

  if (!data) {
    return <div className="error">User not found</div>;
  }

  const user = data.data;

  return (
    <div className="user-detail-page">
      <header className="page-header">
        <h1>User Details</h1>
        <div className="actions">
          <Button variant="danger" onClick={handleDelete}>
            Delete User
          </Button>
          <Button onClick={() => navigate('/users')}>
            Back to Users
          </Button>
        </div>
      </header>

      <div className="user-info">
        <div className="info-section">
          <h2>Basic Information</h2>
          <dl>
            <dt>ID:</dt>
            <dd>{user.id}</dd>
            <dt>Email:</dt>
            <dd>{user.email}</dd>
            <dt>Name:</dt>
            <dd>{user.name}</dd>
            <dt>Role:</dt>
            <dd>{user.role}</dd>
            <dt>Created:</dt>
            <dd>{new Date(user.created_at).toLocaleString()}</dd>
            <dt>Updated:</dt>
            <dd>{new Date(user.updated_at).toLocaleString()}</dd>
          </dl>
        </div>

        <div className="edit-section">
          <h2>Edit User</h2>
          <UserForm
            initialData={{
              email: user.email,
              name: user.name,
              role: user.role,
            }}
            onSubmit={handleUpdate}
            submitLabel="Update User"
          />
        </div>
      </div>
    </div>
  );
}
