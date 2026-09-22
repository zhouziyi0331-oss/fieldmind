# 前端集成指南 - FieldMind后端API
**更新时间**: 2024-01-XX  
**后端版本**: v3.1-unified

---

## 📋 目录
1. [API基础配置](#api基础配置)
2. [认证集成](#认证集成)
3. [知识流水线API](#知识流水线api)
4. [文档规范化API](#文档规范化api)
5. [知识查询API](#知识查询api)
6. [Reader生成API](#reader生成api)
7. [WebSocket实时通信](#websocket实时通信)
8. [错误处理](#错误处理)
9. [示例代码](#示例代码)

---

## API基础配置

### 后端地址
```javascript
const API_BASE_URL = 'http://localhost:8000'
```

### 通用响应格式
```typescript
interface ApiResponse<T> {
  code: number;        // 状态码：200成功，401未认证，500错误
  message: string;     // 消息描述
  data: T | null;      // 响应数据
}
```

### 请求拦截器配置
```javascript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 未认证，跳转登录
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 认证集成

### 1. 用户登录
```javascript
// POST /api/v1/auth/login
async function login(email, password) {
  const response = await apiClient.post('/api/v1/auth/login', {
    email,
    password
  });
  
  // 保存token
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('user_id', response.data.user.id);
  
  return response.data;
}
```

### 2. 获取当前用户
```javascript
// GET /api/v1/auth/me
async function getCurrentUser() {
  return await apiClient.get('/api/v1/auth/me');
}
```

### 3. 刷新Token
```javascript
// POST /api/v1/auth/refresh
async function refreshToken() {
  const response = await apiClient.post('/api/v1/auth/refresh');
  localStorage.setItem('access_token', response.data.access_token);
  return response.data;
}
```

---

## 知识流水线API

### 1. 启动知识流水线
```javascript
// POST /knowledge-pipeline/start
async function startKnowledgePipeline(documentId, projectId, options = {}) {
  return await apiClient.post('/knowledge-pipeline/start', {
    document_id: documentId,
    project_id: projectId,
    enable_statistical_cleaning: options.statisticalCleaning ?? true,
    enable_llm_cleaning: options.llmCleaning ?? false,
    use_workflow_engine: options.useWorkflowEngine ?? true  // 🔥 新增
  });
}

// 响应示例
{
  "code": 200,
  "message": "知识流水线已启动",
  "data": {
    "execution_id": "exec_12345_1234567890",
    "status": "running",
    "document_id": "12345",
    "project_id": "67890"
  }
}
```

### 2. 查询流水线状态
```javascript
// GET /knowledge-pipeline/status/{execution_id}
async function getPipelineStatus(executionId) {
  return await apiClient.get(`/knowledge-pipeline/status/${executionId}`);
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "execution_id": "exec_12345_1234567890",
    "status": "running",  // pending | running | completed | failed
    "current_step": "entity",
    "progress": 45,  // 百分比
    "results": {
      "cleaning": { "success": true, "duration": 2.5 },
      "structure": { "success": true, "duration": 1.8 }
    }
  }
}
```

### 3. 获取流水线结果
```javascript
// GET /knowledge-pipeline/results/{execution_id}
async function getPipelineResults(executionId) {
  return await apiClient.get(`/knowledge-pipeline/results/${executionId}`);
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "execution_id": "exec_12345_1234567890",
    "status": "completed",
    "duration": 125.6,
    "results": {
      "cleaning": { "cleaned_text_length": 5000 },
      "entity": { "entities_count": 45 },
      "event": { "events_count": 23 },
      "relation": { "relations_count": 67 },
      "knowledge": { "knowledge_units_count": 89 }
    }
  }
}
```

### 4. 取消流水线执行
```javascript
// POST /knowledge-pipeline/cancel/{execution_id}
async function cancelPipeline(executionId) {
  return await apiClient.post(`/knowledge-pipeline/cancel/${executionId}`);
}
```

### 5. 获取流水线列表
```javascript
// GET /knowledge-pipeline/list
async function getPipelineList(params = {}) {
  return await apiClient.get('/knowledge-pipeline/list', {
    params: {
      project_id: params.projectId,
      status: params.status,
      limit: params.limit || 20,
      offset: params.offset || 0
    }
  });
}
```

---

## 文档规范化API

### 1. 触发文档规范化
```javascript
// POST /api/v1/files/{file_id}/normalize
async function normalizeDocument(fileId) {
  return await apiClient.post(`/api/v1/files/${fileId}/normalize`);
}

// 响应示例
{
  "code": 200,
  "message": "文档规范化已启动",
  "data": {
    "file_id": 123,
    "status": "processing"
  }
}
```

### 2. 查询规范化进度
```javascript
// GET /api/v1/files/{file_id}/normalization-progress
async function getNormalizationProgress(fileId) {
  return await apiClient.get(`/api/v1/files/${fileId}/normalization-progress`);
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "file_id": 123,
    "status": "completed",  // pending | processing | completed | failed
    "progress": 100,
    "normalized_text_length": 8500,
    "warnings": [],
    "errors": []
  }
}
```

### 3. 获取规范化内容
```javascript
// GET /api/v1/files/{file_id}/normalized-content
async function getNormalizedContent(fileId) {
  return await apiClient.get(`/api/v1/files/${fileId}/normalized-content`);
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "file_id": 123,
    "normalized_text": "规范化后的文本内容...",
    "metadata": {
      "original_length": 10000,
      "normalized_length": 8500,
      "removed_chars": 1500
    }
  }
}
```

### 4. 获取脏数据报告
```javascript
// GET /api/v1/files/{file_id}/dirty-data-report
async function getDirtyDataReport(fileId) {
  return await apiClient.get(`/api/v1/files/${fileId}/dirty-data-report`);
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "file_id": 123,
    "file_type": "pdf",
    "dirty_data_items": [
      {
        "severity": "warning",
        "message": "检测到重复内容",
        "location": "第3页"
      },
      {
        "severity": "error",
        "message": "OCR识别错误",
        "location": "第5页"
      }
    ]
  }
}
```

---

## 知识查询API

### 1. 查询实体列表
```javascript
// GET /knowledge/entities
async function getEntities(params = {}) {
  return await apiClient.get('/knowledge/entities', {
    params: {
      project_id: params.projectId,
      entity_type: params.entityType,  // person | location | organization | concept
      search: params.search,
      limit: params.limit || 20,
      offset: params.offset || 0
    }
  });
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 145,
    "entities": [
      {
        "id": 1,
        "name": "张三",
        "entity_type": "person",
        "confidence": 0.95,
        "attributes": {
          "age": "35",
          "occupation": "工程师"
        },
        "mention_count": 12
      }
    ]
  }
}
```

### 2. 获取实体详情
```javascript
// GET /knowledge/entities/{entity_id}
async function getEntityDetail(entityId) {
  return await apiClient.get(`/knowledge/entities/${entityId}`);
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "张三",
    "entity_type": "person",
    "attributes": { ... },
    "relations": [
      {
        "relation_type": "works_at",
        "target_entity": "ABC公司",
        "confidence": 0.9
      }
    ],
    "mentions": [
      {
        "document_id": 123,
        "context": "...张三在公司工作...",
        "position": 45
      }
    ]
  }
}
```

### 3. 查询事件列表
```javascript
// GET /knowledge/events
async function getEvents(params = {}) {
  return await apiClient.get('/knowledge/events', {
    params: {
      project_id: params.projectId,
      event_type: params.eventType,
      time_range: params.timeRange,  // "2023-01-01,2023-12-31"
      limit: params.limit || 20,
      offset: params.offset || 0
    }
  });
}

// 响应示例
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 78,
    "events": [
      {
        "id": 1,
        "event_type": "meeting",
        "who": ["张三", "李四"],
        "what": "讨论项目进展",
        "when": "2023-06-15",
        "where": "会议室A",
        "confidence": 0.88
      }
    ]
  }
}
```

### 4. 查询关系
```javascript
// GET /knowledge/relations
async function getRelations(params = {}) {
  return await apiClient.get('/knowledge/relations', {
    params: {
      source_entity_id: params.sourceEntityId,
      target_entity_id: params.targetEntityId,
      relation_type: params.relationType
    }
  });
}
```

---

## Reader生成API

### 1. 生成时间线Reader
```javascript
// POST /reader/timeline/{document_id}
async function generateTimelineReader(documentId) {
  return await apiClient.post(`/reader/timeline/${documentId}`);
}

// 响应示例
{
  "code": 200,
  "message": "时间线Reader生成成功",
  "data": {
    "reader_id": "timeline_123",
    "document_id": 123,
    "timeline": [
      {
        "date": "2023-01-15",
        "events": [
          { "time": "09:00", "description": "项目启动会议" },
          { "time": "14:00", "description": "需求讨论" }
        ]
      }
    ]
  }
}
```

### 2. 生成网络关系Reader
```javascript
// POST /reader/network/{document_id}
async function generateNetworkReader(documentId) {
  return await apiClient.post(`/reader/network/${documentId}`);
}

// 响应示例
{
  "code": 200,
  "message": "网络关系Reader生成成功",
  "data": {
    "reader_id": "network_123",
    "nodes": [
      { "id": 1, "name": "张三", "type": "person" },
      { "id": 2, "name": "ABC公司", "type": "organization" }
    ],
    "edges": [
      { "source": 1, "target": 2, "relation": "works_at" }
    ]
  }
}
```

### 3. 生成主题Reader
```javascript
// POST /reader/topics/{document_id}
async function generateTopicsReader(documentId) {
  return await apiClient.post(`/reader/topics/${documentId}`);
}

// 响应示例
{
  "code": 200,
  "message": "主题Reader生成成功",
  "data": {
    "reader_id": "topics_123",
    "topics": [
      {
        "topic": "技术讨论",
        "keywords": ["架构", "设计", "优化"],
        "weight": 0.35,
        "segments": [...]
      }
    ]
  }
}
```

### 4. 生成Wiki Reader
```javascript
// POST /reader/wiki/{document_id}
async function generateWikiReader(documentId, options = {}) {
  return await apiClient.post(`/reader/wiki/${documentId}`, {
    include_toc: options.includeToc ?? true,
    max_depth: options.maxDepth ?? 3
  });
}

// 响应示例
{
  "code": 200,
  "message": "Wiki Reader生成成功",
  "data": {
    "reader_id": "wiki_123",
    "pages": [
      {
        "page_id": 1,
        "title": "项目概述",
        "content": "...",
        "children": [...]
      }
    ],
    "toc": [...]
  }
}
```

---

## WebSocket实时通信

### 连接配置
```javascript
const WS_URL = 'ws://localhost:8000/ws';

class WebSocketClient {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.listeners = {};
  }

  connect() {
    this.ws = new WebSocket(`${WS_URL}?token=${this.token}`);
    
    this.ws.onopen = () => {
      console.log('WebSocket连接已建立');
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket连接已关闭');
      // 自动重连
      setTimeout(() => this.connect(), 5000);
    };
  }

  handleMessage(message) {
    const { type, data } = message;
    
    if (this.listeners[type]) {
      this.listeners[type].forEach(callback => callback(data));
    }
  }

  on(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
  }

  send(type, data) {
    this.ws.send(JSON.stringify({ type, data }));
  }
}

// 使用示例
const wsClient = new WebSocketClient(localStorage.getItem('access_token'));
wsClient.connect();

// 监听流水线进度更新
wsClient.on('pipeline_progress', (data) => {
  console.log(`流水线进度: ${data.progress}%`);
  updateProgressBar(data.progress);
});

// 监听文档处理完成
wsClient.on('document_completed', (data) => {
  console.log(`文档 ${data.document_id} 处理完成`);
  showNotification('文档处理完成');
});
```

---

## 错误处理

### 错误码对照表
```typescript
enum ErrorCode {
  SUCCESS = 200,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  INTERNAL_ERROR = 500,
  SERVICE_UNAVAILABLE = 503
}
```

### 统一错误处理
```javascript
function handleApiError(error) {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        showError('请求参数错误: ' + data.message);
        break;
      case 401:
        showError('未登录或登录已过期');
        redirectToLogin();
        break;
      case 403:
        showError('没有权限访问此资源');
        break;
      case 404:
        showError('请求的资源不存在');
        break;
      case 500:
        showError('服务器内部错误: ' + data.message);
        break;
      default:
        showError('未知错误: ' + data.message);
    }
  } else if (error.request) {
    showError('网络请求失败，请检查网络连接');
  } else {
    showError('请求配置错误: ' + error.message);
  }
}
```

---

## 示例代码

### React组件示例：文档处理进度

```typescript
import React, { useState, useEffect } from 'react';
import apiClient from './apiClient';

function DocumentProcessing({ documentId, projectId }) {
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [executionId, setExecutionId] = useState(null);
  const [results, setResults] = useState(null);

  // 启动处理
  const startProcessing = async () => {
    try {
      const response = await apiClient.post('/knowledge-pipeline/start', {
        document_id: documentId,
        project_id: projectId,
        use_workflow_engine: true  // 🔥 使用WorkflowEngine
      });
      
      setExecutionId(response.data.execution_id);
      setStatus('running');
      
      // 开始轮询状态
      pollStatus(response.data.execution_id);
    } catch (error) {
      console.error('启动失败:', error);
      setStatus('failed');
    }
  };

  // 轮询状态
  const pollStatus = async (execId) => {
    const interval = setInterval(async () => {
      try {
        const response = await apiClient.get(`/knowledge-pipeline/status/${execId}`);
        const { status: execStatus, progress: execProgress } = response.data;
        
        setStatus(execStatus);
        setProgress(execProgress);
        
        if (execStatus === 'completed' || execStatus === 'failed') {
          clearInterval(interval);
          
          if (execStatus === 'completed') {
            // 获取结果
            const resultsResponse = await apiClient.get(`/knowledge-pipeline/results/${execId}`);
            setResults(resultsResponse.data);
          }
        }
      } catch (error) {
        console.error('查询状态失败:', error);
        clearInterval(interval);
      }
    }, 2000);  // 每2秒查询一次
  };

  return (
    <div className="document-processing">
      <h3>文档处理</h3>
      
      {status === 'idle' && (
        <button onClick={startProcessing}>开始处理</button>
      )}
      
      {status === 'running' && (
        <div className="progress">
          <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          <span>{progress}%</span>
        </div>
      )}
      
      {status === 'completed' && results && (
        <div className="results">
          <h4>处理完成</h4>
          <ul>
            <li>实体数量: {results.results.entity?.entities_count || 0}</li>
            <li>事件数量: {results.results.event?.events_count || 0}</li>
            <li>关系数量: {results.results.relation?.relations_count || 0}</li>
            <li>耗时: {results.duration.toFixed(2)}秒</li>
          </ul>
        </div>
      )}
      
      {status === 'failed' && (
        <div className="error">处理失败，请重试</div>
      )}
    </div>
  );
}

export default DocumentProcessing;
```

### Vue组件示例：知识实体查询

```vue
<template>
  <div class="entity-list">
    <h3>知识实体</h3>
    
    <!-- 搜索和过滤 -->
    <div class="filters">
      <input 
        v-model="searchText" 
        placeholder="搜索实体..." 
        @input="searchEntities"
      />
      <select v-model="selectedType" @change="filterByType">
        <option value="">所有类型</option>
        <option value="person">人物</option>
        <option value="location">地点</option>
        <option value="organization">组织</option>
        <option value="concept">概念</option>
      </select>
    </div>
    
    <!-- 实体列表 -->
    <div class="entity-items">
      <div 
        v-for="entity in entities" 
        :key="entity.id"
        class="entity-item"
        @click="viewEntityDetail(entity.id)"
      >
        <span class="entity-name">{{ entity.name }}</span>
        <span class="entity-type">{{ entity.entity_type }}</span>
        <span class="mention-count">提及 {{ entity.mention_count }} 次</span>
      </div>
    </div>
    
    <!-- 分页 -->
    <div class="pagination">
      <button @click="prevPage" :disabled="currentPage === 1">上一页</button>
      <span>第 {{ currentPage }} 页</span>
      <button @click="nextPage" :disabled="!hasMore">下一页</button>
    </div>
  </div>
</template>

<script>
import apiClient from '@/services/apiClient';

export default {
  name: 'EntityList',
  props: {
    projectId: String
  },
  data() {
    return {
      entities: [],
      searchText: '',
      selectedType: '',
      currentPage: 1,
      pageSize: 20,
      hasMore: true
    };
  },
  mounted() {
    this.loadEntities();
  },
  methods: {
    async loadEntities() {
      try {
        const response = await apiClient.get('/knowledge/entities', {
          params: {
            project_id: this.projectId,
            search: this.searchText,
            entity_type: this.selectedType,
            limit: this.pageSize,
            offset: (this.currentPage - 1) * this.pageSize
          }
        });
        
        this.entities = response.data.entities;
        this.hasMore = response.data.total > this.currentPage * this.pageSize;
      } catch (error) {
        console.error('加载实体失败:', error);
      }
    },
    
    searchEntities() {
      this.currentPage = 1;
      this.loadEntities();
    },
    
    filterByType() {
      this.currentPage = 1;
      this.loadEntities();
    },
    
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.loadEntities();
      }
    },
    
    nextPage() {
      if (this.hasMore) {
        this.currentPage++;
        this.loadEntities();
      }
    },
    
    viewEntityDetail(entityId) {
      this.$router.push(`/entity/${entityId}`);
    }
  }
};
</script>
```

---

## 🔧 开发建议

### 1. 环境变量配置
```javascript
// .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

// .env.production
VITE_API_BASE_URL=https://api.fieldmind.com
VITE_WS_URL=wss://api.fieldmind.com/ws
```

### 2. TypeScript类型定义
```typescript
// types/api.ts
export interface Entity {
  id: number;
  name: string;
  entity_type: 'person' | 'location' | 'organization' | 'concept';
  confidence: number;
  attributes: Record<string, any>;
  mention_count: number;
}

export interface PipelineExecution {
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_step?: string;
  results?: Record<string, any>;
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}
```

### 3. 性能优化
- 使用防抖(debounce)处理搜索输入
- 实现虚拟滚动显示大量数据
- 缓存常用查询结果
- 使用WebSocket代替轮询获取实时更新

---

## 📞 技术支持

如有问题，请联系：
- 后端API文档: http://localhost:8000/docs
- 问题反馈: [GitHub Issues]

---

**更新记录**:
- 2024-01-XX: 初始版本，包含知识流水线、文档规范化、知识查询、Reader生成API
