# FieldMind 管理器系统 - 完成报告

## 🎯 问题诊断

你的感觉完全正确：系统各模块是"独立的"，没有真正连接起来。

**症状**：
- 导入页上传文件 → 看板页看不见
- 看板页关键词 → 图谱页点不开
- 图谱页实体 → 聊天页问不出来
- 聊天页时间戳 → 播放器跳不过去

**根本原因**：
1. **前端状态失忆** - 页面切换时状态被重置，没有全局状态管理
2. **后端数据隔离** - 各模块查各自的数据库，没有统一快照
3. **事件不传递** - 模块间没有通信机制
4. **音频播放器孤岛** - 时间戳只是文本，没有绑定控制

---

## ✅ 已创建的解决方案

### 1. 前端全局状态管理器 (AppContext)

**文件**: `fieldmind-web/src/contexts/AppContext.tsx`

**功能**：
```typescript
// 全局状态
- currentProjectId: 当前项目ID（所有API请求必须用这个）
- refreshTrigger: 刷新触发器（任何模块更新数据后改变这个值）
- audioControl: 音频播放状态（fileId, currentTime, isPlaying）
- selectedEntity: 选中的实体（用于图谱→聊天跳转）

// 核心方法
- triggerRefresh(): 触发全局刷新
- playAudio(fileId, startTime): 播放音频
- selectEntity(name, type): 选择实体
- navigateToGraph(entityName): 跳转到图谱
- navigateToChat(question): 跳转到聊天
- navigateToDashboard(): 跳转到看板
```

**使用方式**：
```typescript
import { useAppContext, useRefreshListener } from '../contexts/AppContext';

// 任何组件都可以访问全局状态
const { currentProjectId, triggerRefresh, playAudio } = useAppContext();

// 监听刷新信号
useRefreshListener(() => {
  console.log('收到刷新信号，重新加载数据');
  loadData();
});
```

---

### 2. 后端数据聚合器 (Aggregate API)

**文件**: `fieldmind-backend/app/api/aggregate.py`

**端点**：
```
GET /api/aggregate/dashboard/{project_id}
GET /api/aggregate/quick-stats/{project_id}
```

**功能**：
- 一次性查询所有数据库（PostgreSQL + SQLite + ChromaDB + Neo4j）
- 返回统一的数据快照，确保所有模块看到的数据一致

**返回数据结构**：
```json
{
  "project": { "id": 1, "name": "...", "description": "..." },
  "summary": {
    "total_docs": 27,
    "total_facts": 5566,
    "total_vectors": 197,
    "total_entities": 84,
    "total_relations": 45
  },
  "coverage": {
    "timestamp_coverage": 33.7,
    "entity_coverage": 1.51
  },
  "documents": {
    "by_type": { "docx": 27 },
    "audio_files": [...],
    "recent_uploads": [...]
  },
  "knowledge_graph": {
    "top_entities": [
      { "name": "老王", "type": "人物", "relation_count": 14 }
    ]
  },
  "health": {
    "postgres": true,
    "sqlite": true,
    "chromadb": true,
    "neo4j": true
  }
}
```

---

### 3. 前端聚合服务 (aggregateService)

**文件**: `fieldmind-web/src/services/aggregateService.ts`

**功能**：
- 封装对后端聚合API的调用
- 提供TypeScript类型安全

**使用方式**：
```typescript
import { getDashboardAggregate, getQuickStats } from '../services/aggregateService';

const data = await getDashboardAggregate(projectId);
console.log('文档总数:', data.summary.total_docs);
console.log('实体总数:', data.summary.total_entities);
```

---

### 4. 全局音频播放器 (GlobalAudioPlayer)

**文件**: `fieldmind-web/src/components/GlobalAudioPlayer.tsx`

**功能**：
- 全局唯一的音频播放器（隐藏的`<audio>`元素）
- 监听`audioControl`状态，自动播放/暂停/跳转
- 底部显示迷你控制条（AudioControlBar）

**使用方式**：
```typescript
// 在任何页面调用
const { playAudio } = useAppContext();

<button onClick={() => playAudio(fileId, 23.5)}>
  🔊 00:23
</button>
```

**效果**：
- 点击时间戳 → 全局播放器自动跳转到该时间并播放
- 底部出现控制条，显示当前播放进度
- 任何页面都可以控制同一个播放器

---

### 5. App集成

**文件**: `fieldmind-web/src/App.tsx`

**改动**：
```typescript
<QueryClientProvider client={queryClient}>
  <Router>
    <AppProvider>  {/* 全局状态管理器 */}
      <GlobalAudioPlayer />  {/* 全局音频播放器 */}
      <AudioControlBar />    {/* 底部控制条 */}
      <Routes>...</Routes>
    </AppProvider>
  </Router>
</QueryClientProvider>
```

---

## 📋 下一步：接入现有页面

### 必须修改的5个页面（优先级排序）

#### 1. DocumentsPage - 上传后触发刷新 ⚠️ **最优先**

```typescript
// 在上传成功回调中添加
import { useAppContext } from '../contexts/AppContext';

const { triggerRefresh, setLastUploadedFileId } = useAppContext();

const handleUploadSuccess = (fileId: number) => {
  setLastUploadedFileId(fileId);
  triggerRefresh();  // 触发全局刷新
  toast.success('上传成功，数据已刷新');
};
```

#### 2. ProjectDetailPage (Dashboard) - 使用聚合API

```typescript
import { useAppContext, useRefreshListener } from '../contexts/AppContext';
import { getDashboardAggregate } from '../services/aggregateService';

const { currentProjectId } = useAppContext();
const [data, setData] = useState(null);

const loadData = async () => {
  const result = await getDashboardAggregate(currentProjectId);
  setData(result);
};

useEffect(() => { loadData(); }, [currentProjectId]);
useRefreshListener(() => { loadData(); }); // 监听刷新
```

#### 3. KnowledgeGraphPage - 节点点击跳转

```typescript
import { useAppContext } from '../contexts/AppContext';

const { navigateToChat, selectEntity } = useAppContext();

const handleNodeClick = (node: GraphNode) => {
  selectEntity(node.name, node.type);
  navigateToChat(`告诉我关于"${node.name}"的信息`);
};
```

#### 4. ChatPage - 时间戳绑定播放

```typescript
import { useAppContext } from '../contexts/AppContext';

const { playAudio, selectedEntity, clearSelectedEntity } = useAppContext();

// 渲染时间戳
<button 
  onClick={() => playAudio(msg.fileId, msg.timestamp)}
  className="text-indigo-600 hover:underline"
>
  🔊 {formatTime(msg.timestamp)}
</button>

// 处理从图谱跳转
useEffect(() => {
  if (selectedEntity) {
    sendMessage(`告诉我关于"${selectedEntity.name}"的信息`);
    clearSelectedEntity();
  }
}, [selectedEntity]);
```

#### 5. FactStatementsViewer - 时间戳按钮

```typescript
import { useAppContext } from '../contexts/AppContext';

const { playAudio } = useAppContext();

<button onClick={() => playAudio(documentId, statement.start_sec)}>
  🔊 {formatTime(statement.start_sec)}
</button>
```

---

## ✅ 验收测试（8步验证法）

完成上述5个页面的修改后，执行以下测试：

### 测试1: 上传→刷新链路
1. 打开"材料库"页面
2. 上传一个文件
3. **不刷新浏览器**，点击"项目看板"
4. ✅ 看板显示的文档数应该立即+1

### 测试2: 看板→图谱跳转
1. 在看板页面点击某个关键词（如"老王"）
2. ✅ 应该自动跳转到知识图谱页面
3. ✅ "老王"节点应该被高亮显示

### 测试3: 图谱→聊天跳转
1. 在图谱页面点击某个节点
2. ✅ 应该自动跳转到聊天页面
3. ✅ 聊天框应该自动发送相关问题

### 测试4: 聊天时间戳→音频
1. 在聊天页面找到带时间戳的消息 `[🔊 00:23]`
2. 点击时间戳
3. ✅ 页面底部应该出现音频控制条
4. ✅ 音频应该跳转到00:23并开始播放

### 测试5: 跨页面音频控制
1. 在聊天页点击时间戳，音频开始播放
2. 切换到图谱页面
3. ✅ 底部音频控制条仍在，继续播放
4. ✅ 可以在任何页面暂停/继续

### 测试6: 数据一致性
1. 打开看板页面，记下"实体总数"（假设84个）
2. 切换到图谱页面
3. ✅ 图谱应该显示84个节点
4. 切换到聊天页面，问"有多少个实体"
5. ✅ 应该回答84个

### 测试7: 刷新信号传递
1. 打开两个浏览器标签页
2. 标签页1：看板页面
3. 标签页2：材料库页面，上传文件
4. ✅ 标签页1应该自动刷新（如果实现了WebSocket）
5. 或：手动刷新标签页1，数据应该是最新的

### 测试8: 音频同步高亮
1. 打开FactStatementsViewer（陈述列表）
2. 点击某条陈述的时间戳
3. ✅ 音频跳转播放
4. ✅ 当前播放的陈述应该被高亮显示

---

## 🐛 如果测试失败

### 失败1: "看板数据没更新"

**检查点**：
- [ ] App.tsx是否包裹了`<AppProvider>`？
- [ ] DocumentsPage是否调用了`triggerRefresh()`？
- [ ] 看板页面是否使用了`useRefreshListener()`？

**调试**：
```typescript
// 在上传成功处添加
console.log('[Upload] 触发刷新');
triggerRefresh();

// 在看板页添加
useRefreshListener(() => {
  console.log('[Dashboard] 收到刷新信号');
});
```

打开浏览器控制台，应该看到两条日志。

### 失败2: "时间戳点击没反应"

**检查点**：
- [ ] 时间戳是`<button>`还是`<span>`？必须是按钮
- [ ] `onClick`是否调用了`playAudio()`？
- [ ] `GlobalAudioPlayer`是否在App.tsx中渲染？

**修复**：
```typescript
// ❌ 错误
<span>{formatTime(timestamp)}</span>

// ✅ 正确
<button onClick={() => playAudio(fileId, timestamp)}>
  🔊 {formatTime(timestamp)}
</button>
```

### 失败3: "跳转后projectId丢失"

**检查点**：
- [ ] 是否使用`navigateToGraph()`等助手方法？
- [ ] 还是手动用`navigate()`但忘记传projectId？

**修复**：
```typescript
// ❌ 错误
navigate('/projects/123/knowledge-graph');

// ✅ 正确
const { navigateToGraph } = useAppContext();
navigateToGraph('老王');
```

---

## 📊 系统架构对比

### 修复前（独立模块）

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ 导入页   │   │ 看板页   │   │ 图谱页   │   │ 聊天页   │
│         │   │         │   │         │   │         │
│查PostgreSQL │查SQLite  │查Neo4j   │查ChromaDB│
└─────────┘   └─────────┘   └─────────┘   └─────────┘
     ↓             ↓             ↓             ↓
  各查各的      数据不同步    无法跳转      时间戳失效
```

### 修复后（统一管理）

```
┌─────────────────────────────────────────────────────┐
│               AppContext (全局状态)                  │
│  - currentProjectId                                 │
│  - refreshTrigger (刷新信号)                        │
│  - audioControl (音频控制)                          │
│  - selectedEntity (选中实体)                        │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────┴───────┬───────────┬──────────┐
       ▼               ▼           ▼          ▼
   ┌─────────┐   ┌─────────┐  ┌─────────┐ ┌─────────┐
   │ 导入页   │   │ 看板页   │  │ 图谱页   │ │ 聊天页   │
   │         │   │         │  │         │ │         │
   │trigger  │   │listen   │  │navigate │ │playAudio│
   │Refresh  │   │Refresh  │  │ToChat   │ │         │
   └─────────┘   └─────────┘  └─────────┘ └─────────┘
       │               │           │          │
       └───────┬───────┴───────────┴──────────┘
               ▼
   ┌────────────────────────────────────────┐
   │   Aggregate API (统一数据快照)         │
   │   PostgreSQL + SQLite + ChromaDB + Neo4j│
   └────────────────────────────────────────┘
```

---

## 🎉 完成后的效果

✅ **上传文档** → 所有页面实时看到新文档  
✅ **点击关键词** → 自动跳转图谱并高亮  
✅ **点击图谱节点** → 自动跳转聊天并提问  
✅ **点击时间戳** → 音频自动跳转播放  
✅ **切换页面** → 音频继续播放  
✅ **所有模块** → 看到的是同一份数据快照  

**系统不再是"独立的模块"，而是一个有机整体！**

---

## 📝 文件清单

### 新增文件（5个）
1. `fieldmind-web/src/contexts/AppContext.tsx` - 全局状态管理
2. `fieldmind-web/src/services/aggregateService.ts` - 聚合服务
3. `fieldmind-web/src/components/GlobalAudioPlayer.tsx` - 全局播放器
4. `fieldmind-backend/app/api/aggregate.py` - 聚合API
5. `MANAGER_USAGE_GUIDE.md` - 使用指南

### 修改文件（2个）
1. `fieldmind-web/src/App.tsx` - 集成管理器
2. `fieldmind-backend/app/main.py` - 注册路由

### 待修改文件（5个）
1. `fieldmind-web/src/pages/DocumentsPage.tsx` - 添加刷新触发
2. `fieldmind-web/src/pages/ProjectDetailPage.tsx` - 使用聚合API
3. `fieldmind-web/src/pages/KnowledgeGraphPage.tsx` - 添加跳转
4. `fieldmind-web/src/pages/ChatPage.tsx` - 绑定时间戳
5. `fieldmind-web/src/components/FactStatementsViewer.tsx` - 绑定播放

---

## ⚡ 立即行动

1. **启动后端**: `cd fieldmind-backend && python -m app.main`
2. **启动前端**: `cd fieldmind-web && npm run dev`
3. **测试聚合API**: `curl http://localhost:8000/api/aggregate/quick-stats/1`
4. **修改5个页面**: 按照上面的代码片段修改
5. **执行8步验证**: 确保每一步都通过

**预计工作量**: 2-3小时完成5个页面的修改和测试

**验收标准**: 8步验证全部通过 ✅
