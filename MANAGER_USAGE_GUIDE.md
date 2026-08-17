# FieldMind 管理器系统使用指南

## 🎯 目标

解决系统"模块独立、数据不同步"的问题，通过3个管理器+1个事件总线，让所有模块连接起来。

---

## 📦 已创建的管理器

### 1. 前端状态管理器 (AppContext)

**位置**: `fieldmind-web/src/contexts/AppContext.tsx`

**职责**: 
- 管理全局状态（当前项目ID、会话ID、音频播放状态）
- 提供跨页面导航方法
- 触发全局数据刷新

**核心API**:
```typescript
const {
  // 状态
  currentProjectId,
  refreshTrigger,
  audioControl,
  selectedEntity,

  // 方法
  triggerRefresh,              // 触发全局刷新
  playAudio(fileId, startTime), // 播放音频
  selectEntity(name, type),     // 选择实体
  navigateToGraph(entityName),  // 跳转到图谱
  navigateToChat(question),     // 跳转到聊天
} = useAppContext();
```

### 2. 后端数据聚合器 (AggregateAPI)

**位置**: `fieldmind-backend/app/api/aggregate.py`

**职责**:
- 一次性查询所有数据库（PostgreSQL、SQLite、ChromaDB、Neo4j）
- 返回统一的数据快照
- 避免各模块重复查询导致数据不一致

**端点**:
```
GET /api/aggregate/dashboard/{project_id}
GET /api/aggregate/quick-stats/{project_id}
```

### 3. 前端聚合服务 (aggregateService)

**位置**: `fieldmind-web/src/services/aggregateService.ts`

**职责**:
- 封装对后端聚合API的调用
- 提供类型安全的接口

### 4. 全局音频播放器 (GlobalAudioPlayer)

**位置**: `fieldmind-web/src/components/GlobalAudioPlayer.tsx`

**职责**:
- 全局唯一的音频播放器
- 任何页面都可以通过 `playAudio()` 控制它
- 自动显示底部控制条

---

## 🔧 如何在页面中使用管理器

### 示例1: 文档上传后自动刷新看板

**场景**: 在"材料库"页面上传文件后，"看板"页面应该立即显示新文件

```typescript
// DocumentsPage.tsx
import { useAppContext } from '../contexts/AppContext';

const DocumentsPage = () => {
  const { triggerRefresh, setLastUploadedFileId } = useAppContext();

  const handleUploadSuccess = (fileId: number) => {
    console.log('文件上传成功:', fileId);
    
    // 1. 记录上传的文件ID
    setLastUploadedFileId(fileId);
    
    // 2. 触发全局刷新
    triggerRefresh();
    
    // 3. 可选：跳转到看板
    // navigateToDashboard();
  };

  return (
    <div>
      <FileUploader onSuccess={handleUploadSuccess} />
    </div>
  );
};
```

### 示例2: 看板页监听刷新信号

```typescript
// DashboardPage.tsx
import { useAppContext, useRefreshListener } from '../contexts/AppContext';
import { getDashboardAggregate } from '../services/aggregateService';

const DashboardPage = () => {
  const { currentProjectId } = useAppContext();
  const [data, setData] = useState(null);

  // 加载数据
  const loadData = async () => {
    if (!currentProjectId) return;
    const result = await getDashboardAggregate(currentProjectId);
    setData(result);
  };

  // 初始加载
  useEffect(() => {
    loadData();
  }, [currentProjectId]);

  // 监听全局刷新信号
  useRefreshListener(() => {
    console.log('检测到刷新信号，重新加载数据');
    loadData();
  });

  return (
    <div>
      <h1>文档总数: {data?.summary.total_docs}</h1>
      <h1>陈述总数: {data?.summary.total_facts}</h1>
      <h1>实体总数: {data?.summary.total_entities}</h1>
    </div>
  );
};
```

### 示例3: 时间戳点击跳转音频

```typescript
// ChatPage.tsx
import { useAppContext } from '../contexts/AppContext';

const ChatMessage = ({ message }) => {
  const { playAudio } = useAppContext();

  const handleTimestampClick = (fileId: number, startSec: number) => {
    // 直接调用全局播放器
    playAudio(fileId, startSec);
  };

  return (
    <div>
      <p>{message.text}</p>
      {message.timestamp && (
        <button
          onClick={() => handleTimestampClick(message.fileId, message.timestamp)}
          className="text-indigo-600 hover:underline"
        >
          🔊 {formatTime(message.timestamp)}
        </button>
      )}
    </div>
  );
};
```

### 示例4: 图谱节点跳转到聊天

```typescript
// KnowledgeGraphPage.tsx
import { useAppContext } from '../contexts/AppContext';

const KnowledgeGraphPage = () => {
  const { navigateToChat, selectEntity } = useAppContext();

  const handleNodeClick = (nodeName: string, nodeType: string) => {
    // 1. 标记选中的实体
    selectEntity(nodeName, nodeType);
    
    // 2. 跳转到聊天页，并传入问题
    navigateToChat(`告诉我关于"${nodeName}"的信息`);
  };

  return (
    <div>
      <GraphVisualization onNodeClick={handleNodeClick} />
    </div>
  );
};
```

### 示例5: 聊天页读取选中实体

```typescript
// ChatPage.tsx
import { useAppContext } from '../contexts/AppContext';

const ChatPage = () => {
  const { selectedEntity, clearSelectedEntity } = useAppContext();

  useEffect(() => {
    // 检查是否从图谱跳转过来
    if (selectedEntity) {
      console.log('从图谱跳转，选中实体:', selectedEntity);
      
      // 自动发送问题
      sendMessage(`告诉我关于"${selectedEntity.name}"的信息`);
      
      // 清除选中状态
      clearSelectedEntity();
    }

    // 检查是否有待发送的问题（从sessionStorage读取）
    const pendingQuestion = sessionStorage.getItem('pendingQuestion');
    if (pendingQuestion) {
      sendMessage(pendingQuestion);
      sessionStorage.removeItem('pendingQuestion');
    }
  }, [selectedEntity]);

  return <div>...</div>;
};
```

---

## ✅ 验收测试流程

按照这个顺序测试，每一步都应该成功：

### 测试1: 上传文档→看板更新

1. 打开"材料库"页面
2. 上传一个文件（假设ID=28）
3. **不刷新页面**，直接点击左侧导航"项目看板"
4. 看板上的"文档总数"应该从27变成28 ✅

### 测试2: 看板关键词→图谱高亮

1. 在看板页面，点击某个关键词（如"老王"）
2. 页面应该自动跳转到"知识图谱"
3. 图谱中的"老王"节点应该被高亮 ✅

### 测试3: 图谱节点→聊天提问

1. 在图谱页面，点击某个节点（如"老王"）
2. 页面应该自动跳转到"AI对话"
3. 聊天框应该自动发送"告诉我关于'老王'的信息" ✅

### 测试4: 聊天时间戳→音频跳转

1. 在聊天页面，看到一条带时间戳的消息 `[🔊 00:23]`
2. 点击时间戳
3. 页面底部应该出现音频控制条
4. 音频应该跳转到00:23并开始播放 ✅

---

## 🐛 常见问题排查

### 问题1: "看板数据没有更新"

**可能原因**:
- 上传页面没有调用 `triggerRefresh()`
- 看板页面没有使用 `useRefreshListener()`

**检查方法**:
```typescript
// 在上传成功后添加日志
console.log('[Upload] 触发刷新');
triggerRefresh();

// 在看板页添加日志
useRefreshListener(() => {
  console.log('[Dashboard] 收到刷新信号');
});
```

### 问题2: "时间戳点击没反应"

**可能原因**:
- 时间戳不是 `<button>` 而是纯文本
- `onClick` 没有调用 `playAudio()`

**修复方法**:
```typescript
// ❌ 错误写法
<span>{formatTime(timestamp)}</span>

// ✅ 正确写法
<button onClick={() => playAudio(fileId, timestamp)}>
  🔊 {formatTime(timestamp)}
</button>
```

### 问题3: "跨页面跳转丢失projectId"

**可能原因**:
- 没有使用 `navigateToGraph()` 等助手方法
- 手动使用 `navigate()` 时忘记传递 `?project_id=xxx`

**修复方法**:
```typescript
// ❌ 错误写法
navigate('/projects/123/knowledge-graph');

// ✅ 正确写法（推荐）
navigateToGraph('老王');

// ✅ 正确写法（手动）
const { currentProjectId } = useAppContext();
navigate(`/projects/${currentProjectId}/knowledge-graph`);
```

---

## 📝 下一步工作

### 立即修改的页面（按优先级）

1. **DocumentsPage** - 上传成功后调用 `triggerRefresh()`
2. **ProjectDetailPage (Dashboard)** - 使用聚合API和 `useRefreshListener()`
3. **KnowledgeGraphPage** - 节点点击调用 `navigateToChat()`
4. **ChatPage** - 时间戳绑定 `playAudio()`
5. **FactStatementsViewer** - 时间戳按钮绑定 `playAudio()`

### 需要创建的组件

1. **EntityCard** - 统一的实体卡片，带"查看图谱"和"提问"按钮
2. **TimestampButton** - 统一的时间戳按钮组件
3. **ProjectStatsBar** - 顶部状态栏，显示快速统计

---

## 🎉 完成后的效果

当所有管理器接入后：

✅ 上传文档→看板实时更新→图谱实时更新  
✅ 点击看板关键词→图谱自动跳转并高亮  
✅ 点击图谱节点→聊天自动提问  
✅ 点击聊天时间戳→音频自动跳转播放  
✅ 所有页面看到的数据都是一致的快照  
✅ 不再有"独立模块"的感觉，整个系统像一个整体  

**系统真正"连接"起来了！**
