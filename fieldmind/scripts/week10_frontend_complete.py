#!/usr/bin/env python3
"""
Week 10-11 Day 2-5: 前端完整实现

功能：
1. 生成示例页面组件
2. 生成可复用 UI 组件
3. 实现状态管理（Redux/Zustand）
4. 配置路由系统
5. 创建完整的前端应用结构
"""

import os
import json
from datetime import datetime


class FrontendImplementationGenerator:
    """前端完整实现生成器"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.frontend_code_dir = f"{output_dir}/frontend_code"

        # 创建目录结构
        self._create_directory_structure()

    def _create_directory_structure(self):
        """创建目录结构"""
        dirs = [
            f"{self.frontend_code_dir}/src/pages",
            f"{self.frontend_code_dir}/src/components/common",
            f"{self.frontend_code_dir}/src/components/features",
            f"{self.frontend_code_dir}/src/hooks",
            f"{self.frontend_code_dir}/src/store",
            f"{self.frontend_code_dir}/src/routes",
            f"{self.frontend_code_dir}/src/utils",
            f"{self.frontend_code_dir}/src/types",
            f"{self.frontend_code_dir}/src/styles",
        ]

        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)

    def generate_pages(self):
        """生成示例页面"""
        print("📄 生成示例页面...")

        pages = {
            'HomePage': self._generate_home_page(),
            'UsersPage': self._generate_users_page(),
            'UserDetailPage': self._generate_user_detail_page(),
            'DocumentsPage': self._generate_documents_page(),
            'DocumentEditorPage': self._generate_document_editor_page(),
            'ProjectsPage': self._generate_projects_page(),
            'LoginPage': self._generate_login_page(),
            'DashboardPage': self._generate_dashboard_page(),
        }

        for page_name, code in pages.items():
            file_path = f"{self.frontend_code_dir}/src/pages/{page_name}.tsx"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

        print(f"   ✓ 生成了 {len(pages)} 个页面组件")

    def _generate_home_page(self) -> str:
        return """// src/pages/HomePage.tsx
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
"""

    def _generate_users_page(self) -> str:
        return """// src/pages/UsersPage.tsx
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
"""

    def _generate_user_detail_page(self) -> str:
        return """// src/pages/UserDetailPage.tsx
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
"""

    def _generate_documents_page(self) -> str:
        return """// src/pages/DocumentsPage.tsx
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
"""

    def _generate_document_editor_page(self) -> str:
        return """// src/pages/DocumentEditorPage.tsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDocument, useUpdateDocument, useDeleteDocument } from '../hooks/useApi';
import { Button } from '../components/common/Button';
import { TextEditor } from '../components/common/TextEditor';

export function DocumentEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const { data, isLoading } = useDocument(id!);
  const updateDocument = useUpdateDocument();
  const deleteDocument = useDeleteDocument();

  useEffect(() => {
    if (data?.data) {
      setTitle(data.data.title);
      setContent(data.data.content);
    }
  }, [data]);

  const handleSave = async () => {
    await updateDocument.mutateAsync({
      id: id!,
      data: { title, content },
    });
    setHasChanges(false);
    alert('Document saved successfully');
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      await deleteDocument.mutateAsync(id!);
      navigate('/documents');
    }
  };

  const handleChange = () => {
    setHasChanges(true);
  };

  if (isLoading) {
    return <div className="loading">Loading document...</div>;
  }

  if (!data) {
    return <div className="error">Document not found</div>;
  }

  return (
    <div className="document-editor-page">
      <header className="editor-header">
        <input
          type="text"
          className="title-input"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            handleChange();
          }}
          placeholder="Document title..."
        />

        <div className="actions">
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateDocument.isPending}
          >
            {updateDocument.isPending ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
          <Button onClick={() => navigate('/documents')}>
            Back to Documents
          </Button>
        </div>
      </header>

      <div className="editor-container">
        <TextEditor
          value={content}
          onChange={(value) => {
            setContent(value);
            handleChange();
          }}
        />
      </div>

      {hasChanges && (
        <div className="unsaved-changes-notice">
          You have unsaved changes
        </div>
      )}
    </div>
  );
}
"""

    def _generate_projects_page(self) -> str:
        return """// src/pages/ProjectsPage.tsx
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
"""

    def _generate_login_page(self) -> str:
        return """// src/pages/LoginPage.tsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { apiClient } from '../api/client';
import { Button } from '../components/common/Button';

interface LoginForm {
  email: string;
  password: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    setError('');

    try {
      await apiClient.login(data.email, data.password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>FieldMind</h1>
        <h2>Sign In</h2>

        {error && (
          <div className="error-message">{error}</div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}$/i,
                  message: 'Invalid email address',
                },
              })}
            />
            {errors.email && (
              <span className="error">{errors.email.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 6,
                  message: 'Password must be at least 6 characters',
                },
              })}
            />
            {errors.password && (
              <span className="error">{errors.password.message}</span>
            )}
          </div>

          <Button type="submit" fullWidth disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <div className="login-footer">
          <p>
            Don't have an account? <Link to="/register">Sign Up</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
"""

    def _generate_dashboard_page(self) -> str:
        return """// src/pages/DashboardPage.tsx
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
"""

    def generate_components(self):
        """生成可复用组件"""
        print("\n🧩 生成可复用组件...")

        # 通用组件
        common_components = {
            'Button': self._generate_button_component(),
            'SearchBar': self._generate_searchbar_component(),
            'Pagination': self._generate_pagination_component(),
            'Modal': self._generate_modal_component(),
            'TextEditor': self._generate_text_editor_component(),
            'LoadingSpinner': self._generate_loading_spinner_component(),
        }

        for name, code in common_components.items():
            file_path = f"{self.frontend_code_dir}/src/components/common/{name}.tsx"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

        # 功能组件
        feature_components = {
            'UserList': self._generate_user_list_component(),
            'UserForm': self._generate_user_form_component(),
            'UserCreateModal': self._generate_user_create_modal_component(),
            'DocumentList': self._generate_document_list_component(),
            'DocumentCreateModal': self._generate_document_create_modal_component(),
            'ProjectGrid': self._generate_project_grid_component(),
            'ProjectCreateModal': self._generate_project_create_modal_component(),
        }

        for name, code in feature_components.items():
            file_path = f"{self.frontend_code_dir}/src/components/features/{name}.tsx"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

        print(f"   ✓ 生成了 {len(common_components)} 个通用组件")
        print(f"   ✓ 生成了 {len(feature_components)} 个功能组件")

    def _generate_button_component(self) -> str:
        return """// src/components/common/Button.tsx
import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
}

export function Button({
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  className = '',
  children,
  ...props
}: ButtonProps) {
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth && 'btn-full-width',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
"""

    def _generate_searchbar_component(self) -> str:
        return """// src/components/common/SearchBar.tsx
import React from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchBar({ value, onChange, placeholder = 'Search...' }: SearchBarProps) {
  return (
    <div className="search-bar">
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="search-input"
      />
      <span className="search-icon">🔍</span>
    </div>
  );
}
"""

    def _generate_pagination_component(self) -> str:
        return """// src/components/common/Pagination.tsx
import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="pagination-button"
      >
        Previous
      </button>

      <div className="pagination-pages">
        {pages.map(page => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={page === currentPage ? 'active' : ''}
          >
            {page}
          </button>
        ))}
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="pagination-button"
      >
        Next
      </button>

      <span className="pagination-info">
        Page {currentPage} of {totalPages}
      </span>
    </div>
  );
}
"""

    def _generate_modal_component(self) -> str:
        return """// src/components/common/Modal.tsx
import React, { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          {title && <h2>{title}</h2>}
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
}
"""

    def _generate_text_editor_component(self) -> str:
        return """// src/components/common/TextEditor.tsx
import React from 'react';

interface TextEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function TextEditor({ value, onChange, placeholder }: TextEditorProps) {
  return (
    <textarea
      className="text-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
}
"""

    def _generate_loading_spinner_component(self) -> str:
        return """// src/components/common/LoadingSpinner.tsx
import React from 'react';

export function LoadingSpinner() {
  return (
    <div className="loading-spinner">
      <div className="spinner"></div>
      <p>Loading...</p>
    </div>
  );
}
"""

    def _generate_user_list_component(self) -> str:
        return """// src/components/features/UserList.tsx
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
"""

    def _generate_user_form_component(self) -> str:
        return """// src/components/features/UserForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '../common/Button';

interface UserFormData {
  email: string;
  name: string;
  role?: string;
  password?: string;
}

interface UserFormProps {
  initialData?: Partial<UserFormData>;
  onSubmit: (data: UserFormData) => void;
  submitLabel?: string;
  showPassword?: boolean;
}

export function UserForm({
  initialData = {},
  onSubmit,
  submitLabel = 'Submit',
  showPassword = false,
}: UserFormProps) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<UserFormData>({
    defaultValues: initialData,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="user-form">
      <div className="form-group">
        <label htmlFor="email">Email *</label>
        <input
          id="email"
          type="email"
          {...register('email', { required: 'Email is required' })}
        />
        {errors.email && <span className="error">{errors.email.message}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="name">Name *</label>
        <input
          id="name"
          type="text"
          {...register('name', { required: 'Name is required' })}
        />
        {errors.name && <span className="error">{errors.name.message}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="role">Role</label>
        <select id="role" {...register('role')}>
          <option value="user">User</option>
          <option value="admin">Admin</option>
          <option value="editor">Editor</option>
        </select>
      </div>

      {showPassword && (
        <div className="form-group">
          <label htmlFor="password">Password *</label>
          <input
            id="password"
            type="password"
            {...register('password', {
              required: showPassword && 'Password is required',
              minLength: {
                value: 6,
                message: 'Password must be at least 6 characters',
              },
            })}
          />
          {errors.password && <span className="error">{errors.password.message}</span>}
        </div>
      )}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : submitLabel}
      </Button>
    </form>
  );
}
"""

    def _generate_user_create_modal_component(self) -> str:
        return """// src/components/features/UserCreateModal.tsx
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
"""

    def _generate_document_list_component(self) -> str:
        return """// src/components/features/DocumentList.tsx
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
"""

    def _generate_document_create_modal_component(self) -> str:
        return """// src/components/features/DocumentCreateModal.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreateDocument } from '../../hooks/useApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface DocumentFormData {
  title: string;
  content: string;
  project_id: string;
}

interface DocumentCreateModalProps {
  onClose: () => void;
}

export function DocumentCreateModal({ onClose }: DocumentCreateModalProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<DocumentFormData>();

  const createDocument = useCreateDocument({
    onSuccess: () => {
      alert('Document created successfully');
      onClose();
    },
  });

  const onSubmit = (data: DocumentFormData) => {
    createDocument.mutate(data);
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Create New Document">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            type="text"
            {...register('title', { required: 'Title is required' })}
          />
          {errors.title && <span className="error">{errors.title.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="content">Content</label>
          <textarea
            id="content"
            rows={10}
            {...register('content')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="project_id">Project ID</label>
          <input
            id="project_id"
            type="text"
            {...register('project_id', { required: 'Project ID is required' })}
          />
          {errors.project_id && <span className="error">{errors.project_id.message}</span>}
        </div>

        <Button type="submit" disabled={createDocument.isPending}>
          {createDocument.isPending ? 'Creating...' : 'Create Document'}
        </Button>
      </form>
    </Modal>
  );
}
"""

    def _generate_project_grid_component(self) -> str:
        return """// src/components/features/ProjectGrid.tsx
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
"""

    def _generate_project_create_modal_component(self) -> str:
        return """// src/components/features/ProjectCreateModal.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { useCreateProject } from '../../hooks/useApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface ProjectFormData {
  name: string;
  description: string;
}

interface ProjectCreateModalProps {
  onClose: () => void;
}

export function ProjectCreateModal({ onClose }: ProjectCreateModalProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<ProjectFormData>();

  const createProject = useCreateProject({
    onSuccess: () => {
      alert('Project created successfully');
      onClose();
    },
  });

  const onSubmit = (data: ProjectFormData) => {
    createProject.mutate(data);
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Create New Project">
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="name">Project Name *</label>
          <input
            id="name"
            type="text"
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && <span className="error">{errors.name.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            rows={5}
            {...register('description')}
          />
        </div>

        <Button type="submit" disabled={createProject.isPending}>
          {createProject.isPending ? 'Creating...' : 'Create Project'}
        </Button>
      </form>
    </Modal>
  );
}
"""

    def generate_state_management(self):
        """生成状态管理代码"""
        print("\n🔄 生成状态管理代码...")

        # Zustand 状态管理示例
        auth_store = """// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
"""

        ui_store = """// src/store/uiStore.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));
"""

        # 保存状态管理文件
        with open(f"{self.frontend_code_dir}/src/store/authStore.ts", 'w') as f:
            f.write(auth_store)

        with open(f"{self.frontend_code_dir}/src/store/uiStore.ts", 'w') as f:
            f.write(ui_store)

        print(f"   ✓ 生成了状态管理代码（Zustand）")

    def generate_routing(self):
        """生成路由配置"""
        print("\n🗺️  生成路由配置...")

        router_code = """// src/routes/index.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { ProtectedRoute } from '../components/ProtectedRoute';

// Pages
import { HomePage } from '../pages/HomePage';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { UsersPage } from '../pages/UsersPage';
import { UserDetailPage } from '../pages/UserDetailPage';
import { DocumentsPage } from '../pages/DocumentsPage';
import { DocumentEditorPage } from '../pages/DocumentEditorPage';
import { ProjectsPage } from '../pages/ProjectsPage';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            <Route path="/users" element={<UsersPage />} />
            <Route path="/users/:id" element={<UserDetailPage />} />

            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/:id" element={<DocumentEditorPage />} />

            <Route path="/projects" element={<ProjectsPage />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<div>404 - Page Not Found</div>} />
      </Routes>
    </BrowserRouter>
  );
}
"""

        protected_route = """// src/components/ProtectedRoute.tsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
"""

        layout = """// src/components/Layout.tsx
import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useUIStore } from '../store/uiStore';

export function Layout() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);

  return (
    <div className={`app-layout ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      <header className="app-header">
        <div className="header-left">
          <button onClick={toggleSidebar} className="sidebar-toggle">
            ☰
          </button>
          <h1>FieldMind</h1>
        </div>
        <div className="header-right">
          <span>Welcome, {user?.name}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      <aside className="app-sidebar">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/users">Users</Link>
          <Link to="/documents">Documents</Link>
          <Link to="/projects">Projects</Link>
        </nav>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
"""

        # 保存路由文件
        with open(f"{self.frontend_code_dir}/src/routes/index.tsx", 'w') as f:
            f.write(router_code)

        with open(f"{self.frontend_code_dir}/src/components/ProtectedRoute.tsx", 'w') as f:
            f.write(protected_route)

        with open(f"{self.frontend_code_dir}/src/components/Layout.tsx", 'w') as f:
            f.write(layout)

        print(f"   ✓ 生成了路由配置")

    def generate_app_entry(self):
        """生成应用入口文件"""
        print("\n🚀 生成应用入口文件...")

        app_tsx = """// src/App.tsx
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { AppRouter } from './routes';
import './styles/main.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRouter />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
"""

        index_tsx = """// src/index.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

        # 保存入口文件
        with open(f"{self.frontend_code_dir}/src/App.tsx", 'w') as f:
            f.write(app_tsx)

        with open(f"{self.frontend_code_dir}/src/index.tsx", 'w') as f:
            f.write(index_tsx)

        print(f"   ✓ 生成了应用入口文件")

    def generate_styles(self):
        """生成样式文件"""
        print("\n🎨 生成样式文件...")

        main_css = """/* src/styles/main.css */
:root {
  --primary-color: #1890ff;
  --danger-color: #ff4d4f;
  --success-color: #52c41a;
  --text-color: #333;
  --border-color: #d9d9d9;
  --bg-color: #f0f2f5;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-color);
  background: var(--bg-color);
}

/* Layout */
.app-layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main";
  grid-template-columns: 250px 1fr;
  grid-template-rows: 60px 1fr;
  height: 100vh;
}

.app-header {
  grid-area: header;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: white;
  border-bottom: 1px solid var(--border-color);
}

.app-sidebar {
  grid-area: sidebar;
  background: white;
  border-right: 1px solid var(--border-color);
  padding: 20px;
}

.app-sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.app-sidebar nav a {
  padding: 10px;
  border-radius: 4px;
  text-decoration: none;
  color: var(--text-color);
}

.app-sidebar nav a:hover {
  background: var(--bg-color);
}

.app-main {
  grid-area: main;
  padding: 20px;
  overflow-y: auto;
}

/* Button */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.btn-secondary {
  background: white;
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Form */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.form-group .error {
  color: var(--danger-color);
  font-size: 12px;
  margin-top: 4px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-close {
  font-size: 24px;
  border: none;
  background: none;
  cursor: pointer;
}

/* Table */
table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

th {
  font-weight: 600;
  background: var(--bg-color);
}

/* Loading */
.loading {
  text-align: center;
  padding: 40px;
}

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  background: white;
  cursor: pointer;
  border-radius: 4px;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button.active {
  background: var(--primary-color);
  color: white;
}
"""

        with open(f"{self.frontend_code_dir}/src/styles/main.css", 'w') as f:
            f.write(main_css)

        print(f"   ✓ 生成了样式文件")

    def generate_package_json(self):
        """生成 package.json"""
        print("\n📦 生成 package.json...")

        package_json = {
            "name": "fieldmind-frontend",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "react-hook-form": "^7.48.0",
                "@tanstack/react-query": "^5.13.0",
                "axios": "^1.6.0",
                "zustand": "^4.4.0",
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@types/node": "^20.10.0",
                "@tanstack/react-query-devtools": "^5.13.0",
                "typescript": "^5.3.0",
                "vite": "^5.0.0",
                "@vitejs/plugin-react": "^4.2.0",
            },
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
                "lint": "eslint src --ext ts,tsx",
            }
        }

        with open(f"{self.frontend_code_dir}/package.json", 'w') as f:
            json.dump(package_json, f, indent=2)

        print(f"   ✓ 生成了 package.json")

    def generate_readme(self):
        """生成 README"""
        print("\n📖 生成 README...")

        readme = f"""# FieldMind Frontend

React + TypeScript 前端应用

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 技术栈

- **框架**: React 18
- **语言**: TypeScript
- **构建工具**: Vite
- **路由**: React Router v6
- **数据获取**: React Query (TanStack Query)
- **状态管理**: Zustand
- **表单**: React Hook Form
- **HTTP 客户端**: Axios

## 项目结构

```
src/
├── api/                  # API 客户端
│   └── client.ts
├── hooks/                # 自定义 Hooks
│   └── useApi.ts
├── components/           # React 组件
│   ├── common/          # 通用组件
│   │   ├── Button.tsx
│   │   ├── Modal.tsx
│   │   ├── Pagination.tsx
│   │   └── SearchBar.tsx
│   └── features/        # 功能组件
│       ├── UserList.tsx
│       ├── DocumentList.tsx
│       └── ProjectGrid.tsx
├── pages/                # 页面组件
│   ├── HomePage.tsx
│   ├── LoginPage.tsx
│   ├── UsersPage.tsx
│   ├── DocumentsPage.tsx
│   └── ProjectsPage.tsx
├── store/                # 状态管理
│   ├── authStore.ts
│   └── uiStore.ts
├── routes/               # 路由配置
│   └── index.tsx
├── styles/               # 样式文件
│   └── main.css
├── types/                # TypeScript 类型
├── utils/                # 工具函数
├── App.tsx               # 应用根组件
└── index.tsx             # 应用入口
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 配置环境变量

创建 `.env` 文件:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:5173 启动

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 核心功能

### 1. 认证系统

- JWT Token 认证
- 自动 Token 刷新
- 受保护的路由

### 2. 用户管理

- 用户列表（分页、搜索）
- 创建用户
- 编辑用户
- 删除用户

### 3. 文档管理

- 文档列表
- 文档编辑器
- 搜索文档
- 导出文档

### 4. 项目管理

- 项目列表
- 创建项目
- 项目详情

## API 客户端使用

```typescript
import { apiClient } from './api/client';

// 登录
await apiClient.login('user@example.com', 'password');

// 获取用户列表
const users = await apiClient.users.list({{ page: 1, page_size: 20 }});

// 创建用户
const newUser = await apiClient.users.create({{
  email: 'new@example.com',
  name: 'New User',
  password: 'password123',
}});
```

## React Query Hooks

```typescript
import {{ useUsers, useCreateUser }} from './hooks/useApi';

function UsersPage() {{
  // 获取用户列表
  const {{ data, isLoading }} = useUsers({{ page: 1 }});

  // 创建用户
  const createUser = useCreateUser({{
    onSuccess: () => alert('Created!'),
  }});

  // ...
}}
```

## 状态管理

```typescript
import {{ useAuthStore }} from './store/authStore';

function Header() {{
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <div>
      Welcome, {{user?.name}}
      <button onClick={{logout}}>Logout</button>
    </div>
  );
}}
```

## 部署

### Nginx 配置

```nginx
server {{
  listen 80;
  server_name app.fieldmind.com;

  root /var/www/fieldmind-frontend/dist;
  index index.html;

  location / {{
    try_files $uri $uri/ /index.html;
  }}

  location /api {{
    proxy_pass http://backend:8000;
  }}
}}
```

## 开发规范

### 命名约定

- 组件: PascalCase (UserList.tsx)
- Hooks: camelCase, 以 use 开头 (useUser.ts)
- 工具函数: camelCase (formatDate.ts)
- 常量: UPPER_SNAKE_CASE

### 组件结构

```typescript
// 1. Imports
import React from 'react';
import {{ useXxx }} from '../hooks';

// 2. Types
interface XxxProps {{
  ...
}}

// 3. Component
export function Xxx({{ ...props }}: XxxProps) {{
  // 3.1 Hooks
  const {{ data }} = useXxx();

  // 3.2 Handlers
  const handleClick = () => {{...}};

  // 3.3 Render
  return (...);
}}
```

## 故障排查

### 常见问题

**Q: API 请求失败**
- 检查 `.env` 中的 API URL
- 确认后端服务已启动
- 检查浏览器控制台的网络请求

**Q: 登录后立即跳转回登录页**
- 检查 localStorage 中的 token
- 确认 token 格式正确
- 检查后端 JWT 配置

**Q: 页面刷新后状态丢失**
- 确认使用了 persist middleware (Zustand)
- 检查 localStorage 权限

## License

MIT

---

**FieldMind Frontend Application**
Week 10-11 Complete Implementation
"""

        with open(f"{self.frontend_code_dir}/README.md", 'w') as f:
            f.write(readme)

        print(f"   ✓ 生成了 README.md")

    def run(self):
        """执行完整生成流程"""
        print("=" * 70)
        print("Week 10-11 Day 2-5: 前端完整实现")
        print("=" * 70)

        # Day 2-3: 页面和组件
        self.generate_pages()
        self.generate_components()

        # Day 4: 状态管理
        self.generate_state_management()

        # Day 5: 路由和入口
        self.generate_routing()
        self.generate_app_entry()
        self.generate_styles()
        self.generate_package_json()
        self.generate_readme()

        print("\n" + "=" * 70)
        print("前端完整实现生成完成")
        print("=" * 70)

        print(f"\n📊 生成统计:")
        print(f"  8 个页面组件")
        print(f"  6 个通用组件")
        print(f"  7 个功能组件")
        print(f"  2 个状态管理 Store")
        print(f"  完整路由配置")
        print(f"  样式文件")
        print(f"  package.json")
        print(f"  README.md")

        print(f"\n📁 输出目录:")
        print(f"  {self.frontend_code_dir}/")

        print(f"\n🚀 下一步:")
        print(f"  1. cd {self.frontend_code_dir}")
        print(f"  2. npm install")
        print(f"  3. npm run dev")


def main():
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind"

    generator = FrontendImplementationGenerator(output_dir)
    generator.run()

    print("\n✅ 前端完整实现生成完成！")


if __name__ == "__main__":
    main()
