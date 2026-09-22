// src/components/features/UserList.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import type { User } from '../../api/client';
import { Button } from '../common/Button';

interface UserListProps {
  users: User[];
  onDelete: (id: string) => void;
}

export function UserList({ users, onDelete }: UserListProps) {
  return (
    <div className="user-list">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>
                <Link to={`/users/${user.id}`}>{user.name}</Link>
              </td>
              <td>{user.email}</td>
              <td><span className="badge">{user.role}</span></td>
              <td>{new Date(user.created_at).toLocaleDateString()}</td>
              <td>
                <Button
                  size="small"
                  variant="danger"
                  onClick={() => onDelete(user.id)}
                >
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
