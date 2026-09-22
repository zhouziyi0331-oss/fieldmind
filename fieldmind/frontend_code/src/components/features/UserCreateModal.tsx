// src/components/features/UserCreateModal.tsx
import React from 'react';
import { useCreateUser } from '../../hooks/useApi';
import { Modal } from '../common/Modal';
import { UserForm } from './UserForm';

interface UserCreateModalProps {
  onClose: () => void;
}

export function UserCreateModal({ onClose }: UserCreateModalProps) {
  const createUser = useCreateUser({
    onSuccess: () => {
      alert('User created successfully');
      onClose();
    },
  });

  return (
    <Modal isOpen={true} onClose={onClose} title="Create New User">
      <UserForm
        onSubmit={(data) => createUser.mutate(data)}
        submitLabel="Create User"
        showPassword={true}
      />
    </Modal>
  );
}
