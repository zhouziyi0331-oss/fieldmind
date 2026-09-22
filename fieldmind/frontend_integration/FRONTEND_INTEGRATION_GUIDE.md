# FieldMind 前端集成指南

生成时间: 2026-09-13 15:56:17

---

## 一、前端架构概览

### 技术栈
- **框架**: React
- **状态管理**: R, e, a, c, t,  , Q, u, e, r, y,  , /,  , S, W, R
- **API 客户端**: Axios
- **表单处理**: React Hook Form
- **路由**: React Router

### 架构分层

```
┌─────────────────────────────────────────┐
│         UI Components Layer              │
│  - Pages, Layouts, Components            │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Data Hooks Layer                 │
│  - useUsers, useDocuments, etc.          │
│  - React Query / SWR                     │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         API Client Layer                 │
│  - ResourceClients (typed)               │
│  - Request/Response interceptors         │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Backend API (RESTful)            │
│  - /api/v1/users, /api/v1/documents      │
└─────────────────────────────────────────┘
```

---

## 二、快速开始

### 1. 安装依赖

```bash
# 核心依赖
npm install axios @tanstack/react-query

# TypeScript 支持
npm install -D @types/node

# 可选：表单处理
npm install react-hook-form

# 可选：UI 库
npm install antd
# 或
npm install @mui/material @emotion/react @emotion/styled
```

### 2. 配置 API 客户端

创建 `.env` 文件:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_API_TIMEOUT=30000
```

### 3. 初始化 React Query

```tsx
// src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* Your app */}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
```

### 4. 使用 API Hooks

```tsx
// src/pages/UsersList.tsx
import { useUsers, useDeleteUser } from '../hooks/useApi';

function UsersList() {
  // 获取用户列表
  const { data, isLoading, error } = useUsers({
    page: 1,
    page_size: 20,
  });

  // 删除用户
  const deleteUser = useDeleteUser({
    onSuccess: () => {
      alert('User deleted successfully');
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {data?.data.map(user => (
          <li key={user.id}>
            {user.name} ({user.email})
            <button onClick={() => deleteUser.mutate(user.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 三、API 客户端详解

### 基础使用

```typescript
import { apiClient } from './api/client';

// 登录
await apiClient.login('user@example.com', 'password');

// 获取用户列表
const users = await apiClient.users.list({ page: 1, page_size: 20 });

// 创建用户
const newUser = await apiClient.users.create({
  email: 'new@example.com',
  name: 'New User',
  password: 'password123',
});

// 更新用户
await apiClient.users.update('user-id', {
  name: 'Updated Name',
});

// 删除用户
await apiClient.users.delete('user-id');
```

### 认证流程

```typescript
// 登录
const { access_token, refresh_token } = await apiClient.login(email, password);

// Token 自动保存到 localStorage
// 后续请求自动添加 Authorization header

// 登出
await apiClient.logout();
```

### Token 自动刷新

API 客户端会自动处理 token 刷新:

1. 请求返回 401
2. 自动使用 refresh_token 刷新
3. 重试原请求
4. 如果刷新失败，跳转登录页

---

## 四、数据 Hooks 详解

### useUsers - 用户列表

```tsx
const { data, isLoading, error, refetch } = useUsers({
  page: 1,
  page_size: 20,
  sort: 'created_at:desc',
  filter: 'role:admin',
});

// 数据结构
// data.data: User[]
// data.meta: { page, page_size, total, total_pages }
```

### useUser - 单个用户

```tsx
const { data, isLoading, error } = useUser(userId, {
  enabled: !!userId, // 只在 userId 存在时请求
  refetchInterval: 30000, // 每 30 秒自动刷新
});

// 数据结构
// data.data: User
```

### useCreateUser - 创建用户

```tsx
const createUser = useCreateUser({
  onSuccess: (data) => {
    console.log('Created:', data.data);
  },
  onError: (error) => {
    console.error('Failed:', error);
  },
});

// 使用
const handleSubmit = async (formData) => {
  await createUser.mutateAsync(formData);
};

// 或
createUser.mutate(formData);
```

### useUpdateUser - 更新用户

```tsx
const updateUser = useUpdateUser();

updateUser.mutate({
  id: 'user-id',
  data: { name: 'New Name' },
});
```

### useDeleteUser - 删除用户

```tsx
const deleteUser = useDeleteUser({
  onSuccess: () => {
    // 自动 invalidate 相关查询
    alert('Deleted successfully');
  },
});

deleteUser.mutate('user-id');
```

---

## 五、完整示例

### 示例 1: 用户管理页面

```tsx
// src/pages/Users.tsx
import React, { useState } from 'react';
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
} from '../hooks/useApi';
import type { UserCreate } from '../api/client';

export function UsersPage() {
  const [page, setPage] = useState(1);
  const [isCreating, setIsCreating] = useState(false);

  // 获取用户列表
  const { data, isLoading } = useUsers({ page, page_size: 20 });

  // Mutations
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const handleCreate = async (formData: UserCreate) => {
    await createUser.mutateAsync(formData);
    setIsCreating(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure?')) {
      deleteUser.mutate(id);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Users Management</h1>

      <button onClick={() => setIsCreating(true)}>
        Create New User
      </button>

      {isCreating && (
        <UserForm onSubmit={handleCreate} onCancel={() => setIsCreating(false)} />
      )}

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.data.map(user => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <button onClick={() => handleDelete(user.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 分页 */}
      <div>
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
        >
          Previous
        </button>
        <span>Page {page} of {data?.meta.total_pages}</span>
        <button
          disabled={page === data?.meta.total_pages}
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

### 示例 2: 文档编辑器

```tsx
// src/pages/DocumentEditor.tsx
import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDocument, useUpdateDocument } from '../hooks/useApi';
import { useForm } from 'react-hook-form';
import type { DocumentUpdate } from '../api/client';

export function DocumentEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading } = useDocument(id!);
  const updateDocument = useUpdateDocument();

  const { register, handleSubmit, reset } = useForm<DocumentUpdate>();

  useEffect(() => {
    if (data?.data) {
      reset({
        title: data.data.title,
        content: data.data.content,
      });
    }
  }, [data, reset]);

  const onSubmit = async (formData: DocumentUpdate) => {
    await updateDocument.mutateAsync({ id: id!, data: formData });
    alert('Saved successfully');
  };

  if (isLoading) return <div>Loading...</div>;
  if (!data) return <div>Document not found</div>;

  return (
    <div>
      <h1>Edit Document</h1>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div>
          <label>Title</label>
          <input
            type="text"
            {...register('title', { required: true })}
          />
        </div>

        <div>
          <label>Content</label>
          <textarea
            rows={20}
            {...register('content')}
          />
        </div>

        <button type="submit" disabled={updateDocument.isPending}>
          {updateDocument.isPending ? 'Saving...' : 'Save'}
        </button>

        <button type="button" onClick={() => navigate('/documents')}>
          Cancel
        </button>
      </form>
    </div>
  );
}
```

### 示例 3: 搜索功能

```tsx
// src/components/DocumentSearch.tsx
import React, { useState, useEffect } from 'react';
import { useSearchDocuments } from '../hooks/useApi';
import { useDebounce } from '../hooks/useDebounce';

export function DocumentSearch() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);

  const { data, isLoading } = useSearchDocuments(
    debouncedQuery,
    { page_size: 10 },
    {
      enabled: debouncedQuery.length > 2, // 至少 3 个字符才搜索
    }
  );

  return (
    <div>
      <input
        type="search"
        placeholder="Search documents..."
        value={query}
        onChange={e => setQuery(e.target.value)}
      />

      {isLoading && <div>Searching...</div>}

      {data && (
        <ul>
          {data.data.map(doc => (
            <li key={doc.id}>
              <a href={`/documents/${doc.id}`}>
                {doc.title}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

## 六、错误处理

### 全局错误处理

```tsx
// src/components/ErrorBoundary.tsx
import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Query 错误处理

```tsx
const { data, error } = useUsers();

if (error) {
  // 根据错误类型显示不同消息
  if (error.message.includes('401')) {
    return <div>Please login</div>;
  }
  if (error.message.includes('403')) {
    return <div>Access denied</div>;
  }
  return <div>Error: {error.message}</div>;
}
```

### Mutation 错误处理

```tsx
const createUser = useCreateUser({
  onError: (error: any) => {
    if (error.response?.data?.errors) {
      // 显示字段级别错误
      const errors = error.response.data.errors;
      errors.forEach((err: any) => {
        console.log(`${err.field}: ${err.message}`);
      });
    } else {
      alert(error.message);
    }
  },
});
```

---

## 七、性能优化

### 1. 分页和虚拟滚动

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';

function useInfiniteUsers() {
  return useInfiniteQuery({
    queryKey: ['users', 'infinite'],
    queryFn: ({ pageParam = 1 }) =>
      apiClient.users.list({ page: pageParam, page_size: 20 }),
    getNextPageParam: (lastPage) => {
      const { page, total_pages } = lastPage.meta;
      return page < total_pages ? page + 1 : undefined;
    },
  });
}
```

### 2. 预加载数据

```tsx
import { useQueryClient } from '@tanstack/react-query';

function UserRow({ user }) {
  const queryClient = useQueryClient();

  const prefetchUser = () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.users.detail(user.id),
      queryFn: () => apiClient.users.get(user.id),
    });
  };

  return (
    <tr onMouseEnter={prefetchUser}>
      <td>{user.name}</td>
    </tr>
  );
}
```

### 3. 乐观更新

```tsx
const updateUser = useUpdateUser({
  onMutate: async ({ id, data }) => {
    // 取消正在进行的查询
    await queryClient.cancelQueries({ queryKey: queryKeys.users.detail(id) });

    // 保存当前数据
    const previousUser = queryClient.getQueryData(queryKeys.users.detail(id));

    // 乐观更新
    queryClient.setQueryData(queryKeys.users.detail(id), (old: any) => ({
      ...old,
      data: { ...old.data, ...data },
    }));

    return { previousUser };
  },
  onError: (err, variables, context) => {
    // 回滚
    if (context?.previousUser) {
      queryClient.setQueryData(
        queryKeys.users.detail(variables.id),
        context.previousUser
      );
    }
  },
});
```

---

## 八、测试

### 单元测试

```tsx
// src/hooks/__tests__/useApi.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUsers } from '../useApi';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

test('useUsers fetches users', async () => {
  const { result } = renderHook(() => useUsers(), {
    wrapper: createWrapper(),
  });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  expect(result.current.data).toBeDefined();
  expect(result.current.data?.data).toBeInstanceOf(Array);
});
```

---

## 九、部署

### 环境变量

```bash
# .env.development
REACT_APP_API_URL=http://localhost:8000/api/v1

# .env.production
REACT_APP_API_URL=https://api.fieldmind.com/api/v1
```

### 构建

```bash
npm run build
```

### Nginx 配置

```nginx
server {
  listen 80;
  server_name app.fieldmind.com;

  root /var/www/fieldmind-frontend/build;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

---

**FieldMind 前端集成项目**
Week 10-11 集成指南
Version 1.0
