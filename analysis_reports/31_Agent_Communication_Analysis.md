# Agent Communication Protocols 深度分析报告

**插件名称**: Agent Communication Protocols  
**类别**: 多Agent通信系统  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
Agent通信协议定义了多个AI Agent之间如何交互、协作和协调。这是构建多Agent系统的基础，涵盖消息传递、任务分配、状态同步等。

### 核心特点
- **消息传递**: 异步/同步通信
- **协议标准**: ACL、KQML等
- **发布订阅**: 事件驱动架构
- **任务分配**: 协调和调度
- **共识机制**: 多Agent决策
- **故障恢复**: 容错和重试

### 架构设计
```
Agent Communication
├── Message Passing (消息传递)
│   ├── Point-to-Point
│   ├── Broadcast
│   ├── Multicast
│   └── Request-Reply
├── Message Protocols (协议)
│   ├── ACL (Agent Communication Language)
│   ├── FIPA Standards
│   ├── Custom Protocols
│   └── Message Format
├── Event System (事件系统)
│   ├── Publish-Subscribe
│   ├── Event Bus
│   ├── Event Handlers
│   └── Event Filtering
├── Coordination (协调)
│   ├── Task Allocation
│   ├── Resource Management
│   ├── Negotiation
│   └── Consensus
└── Reliability (可靠性)
    ├── Message Queue
    ├── Retry Logic
    ├── Dead Letter Queue
    └── Circuit Breaker
```

---

## 2. 核心概念

### 2.1 基础消息结构

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime
import uuid

class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    INFORM = "inform"
    QUERY = "query"
    COMMAND = "command"
    EVENT = "event"

@dataclass
class Message:
    """标准消息结构"""
    
    # 消息头
    id: str
    type: MessageType
    sender: str
    receiver: str
    timestamp: datetime
    
    # 消息体
    content: Any
    metadata: Dict[str, Any]
    
    # 关联
    reply_to: Optional[str] = None
    conversation_id: Optional[str] = None
    
    # 配置
    ttl: Optional[int] = None  # 生存时间（秒）
    priority: int = 5  # 优先级 1-10
    
    @classmethod
    def create(
        cls,
        msg_type: MessageType,
        sender: str,
        receiver: str,
        content: Any,
        **kwargs
    ):
        """创建消息"""
        return cls(
            id=str(uuid.uuid4()),
            type=msg_type,
            sender=sender,
            receiver=receiver,
            timestamp=datetime.utcnow(),
            content=content,
            metadata={},
            **kwargs
        )
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "metadata": self.metadata,
            "reply_to": self.reply_to,
            "conversation_id": self.conversation_id,
            "ttl": self.ttl,
            "priority": self.priority
        }
```

### 2.2 消息总线

```python
from collections import defaultdict
from queue import PriorityQueue
import threading

class MessageBus:
    """消息总线 - 中央通信枢纽"""
    
    def __init__(self):
        # 订阅者注册表
        self.subscribers = defaultdict(list)
        
        # 消息队列（每个Agent一个）
        self.queues = {}
        
        # 锁
        self.lock = threading.Lock()
    
    def register_agent(self, agent_id: str):
        """注册Agent"""
        with self.lock:
            if agent_id not in self.queues:
                self.queues[agent_id] = PriorityQueue()
    
    def subscribe(self, agent_id: str, topic: str):
        """订阅主题"""
        with self.lock:
            if agent_id not in self.subscribers[topic]:
                self.subscribers[topic].append(agent_id)
    
    def unsubscribe(self, agent_id: str, topic: str):
        """取消订阅"""
        with self.lock:
            if agent_id in self.subscribers[topic]:
                self.subscribers[topic].remove(agent_id)
    
    def send(self, message: Message):
        """发送消息（点对点）"""
        receiver = message.receiver
        
        if receiver not in self.queues:
            raise ValueError(f"Agent {receiver} not registered")
        
        # 优先级队列：priority越小越优先
        priority = -message.priority  # 反转使得大priority先出队
        self.queues[receiver].put((priority, message))
    
    def publish(self, topic: str, message: Message):
        """发布消息（发布-订阅）"""
        subscribers = self.subscribers.get(topic, [])
        
        for subscriber in subscribers:
            # 创建副本发送给每个订阅者
            msg_copy = Message(
                id=str(uuid.uuid4()),
                type=message.type,
                sender=message.sender,
                receiver=subscriber,
                timestamp=datetime.utcnow(),
                content=message.content,
                metadata={**message.metadata, 'topic': topic},
                conversation_id=message.conversation_id
            )
            
            self.send(msg_copy)
    
    def receive(self, agent_id: str, timeout: float = None) -> Optional[Message]:
        """接收消息"""
        if agent_id not in self.queues:
            raise ValueError(f"Agent {agent_id} not registered")
        
        try:
            if timeout:
                priority, message = self.queues[agent_id].get(timeout=timeout)
            else:
                priority, message = self.queues[agent_id].get(block=False)
            
            # 检查TTL
            if message.ttl:
                age = (datetime.utcnow() - message.timestamp).total_seconds()
                if age > message.ttl:
                    return None  # 消息过期
            
            return message
        
        except:
            return None
```

### 2.3 Agent基类

```python
from abc import ABC, abstractmethod
import threading

class Agent(ABC):
    """Agent基类"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.id = agent_id
        self.bus = message_bus
        self.running = False
        self.thread = None
        
        # 注册到消息总线
        self.bus.register_agent(self.id)
    
    def start(self):
        """启动Agent"""
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.start()
    
    def stop(self):
        """停止Agent"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run_loop(self):
        """运行循环"""
        while self.running:
            # 接收消息
            message = self.bus.receive(self.id, timeout=0.1)
            
            if message:
                self.handle_message(message)
    
    @abstractmethod
    def handle_message(self, message: Message):
        """处理消息（子类实现）"""
        pass
    
    def send(self, receiver: str, msg_type: MessageType, content: Any, **kwargs):
        """发送消息"""
        message = Message.create(
            msg_type=msg_type,
            sender=self.id,
            receiver=receiver,
            content=content,
            **kwargs
        )
        
        self.bus.send(message)
    
    def publish(self, topic: str, msg_type: MessageType, content: Any, **kwargs):
        """发布消息"""
        message = Message.create(
            msg_type=msg_type,
            sender=self.id,
            receiver="*",  # 广播
            content=content,
            **kwargs
        )
        
        self.bus.publish(topic, message)
    
    def subscribe(self, topic: str):
        """订阅主题"""
        self.bus.subscribe(self.id, topic)
```

### 2.4 协调器Agent

```python
class CoordinatorAgent(Agent):
    """协调器Agent - 管理任务分配"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        super().__init__(agent_id, message_bus)
        self.workers = []
        self.tasks = []
        self.task_assignments = {}
    
    def register_worker(self, worker_id: str):
        """注册工作Agent"""
        self.workers.append(worker_id)
    
    def assign_task(self, task: Dict):
        """分配任务"""
        # 选择最空闲的worker
        worker = self._select_worker()
        
        if worker:
            # 发送任务
            self.send(
                receiver=worker,
                msg_type=MessageType.COMMAND,
                content={
                    "action": "execute_task",
                    "task": task
                }
            )
            
            self.task_assignments[task['id']] = worker
    
    def _select_worker(self) -> Optional[str]:
        """选择worker（简单轮询）"""
        if not self.workers:
            return None
        
        # 轮询
        worker = self.workers[0]
        self.workers = self.workers[1:] + [worker]
        
        return worker
    
    def handle_message(self, message: Message):
        """处理消息"""
        if message.type == MessageType.RESPONSE:
            # 任务完成
            task_id = message.content.get('task_id')
            result = message.content.get('result')
            
            print(f"任务 {task_id} 完成，结果: {result}")
        
        elif message.type == MessageType.REQUEST:
            # 新任务请求
            task = message.content.get('task')
            self.assign_task(task)
```

### 2.5 工作Agent

```python
class WorkerAgent(Agent):
    """工作Agent - 执行任务"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        super().__init__(agent_id, message_bus)
        self.current_task = None
    
    def handle_message(self, message: Message):
        """处理消息"""
        if message.type == MessageType.COMMAND:
            action = message.content.get('action')
            
            if action == 'execute_task':
                task = message.content.get('task')
                self.execute_task(task, message.sender)
    
    def execute_task(self, task: Dict, coordinator: str):
        """执行任务"""
        self.current_task = task
        
        # 模拟任务执行
        result = self._do_work(task)
        
        # 返回结果
        self.send(
            receiver=coordinator,
            msg_type=MessageType.RESPONSE,
            content={
                "task_id": task['id'],
                "result": result
            }
        )
        
        self.current_task = None
    
    def _do_work(self, task: Dict) -> Any:
        """实际工作逻辑"""
        # 子类实现
        return {"status": "completed"}
```

---

## 3. 核心算法

### 3.1 请求-响应模式

```python
import time

def request_response_pattern(
    requester: Agent,
    responder_id: str,
    request_content: Any,
    timeout: float = 5.0
) -> Optional[Any]:
    """
    请求-响应模式
    
    同步通信：发送请求，等待响应
    """
    # 生成会话ID
    conversation_id = str(uuid.uuid4())
    
    # 发送请求
    requester.send(
        receiver=responder_id,
        msg_type=MessageType.REQUEST,
        content=request_content,
        conversation_id=conversation_id
    )
    
    # 等待响应
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        message = requester.bus.receive(requester.id, timeout=0.1)
        
        if message and message.conversation_id == conversation_id:
            if message.type == MessageType.RESPONSE:
                return message.content
        
        time.sleep(0.1)
    
    # 超时
    return None

# 时间复杂度: O(1) 平均
# 注意：这是简化实现，生产环境需要更健壮的实现
```

### 3.2 合约网协议（Contract Net Protocol）

```python
def contract_net_protocol(
    manager: Agent,
    task: Dict,
    potential_contractors: List[str],
    deadline: float = 10.0
) -> Optional[str]:
    """
    合约网协议
    
    流程:
    1. 管理者发布任务公告
    2. 承包者提交报价
    3. 管理者选择最佳承包者
    4. 授予合约
    """
    conversation_id = str(uuid.uuid4())
    
    # 1. 发布任务公告（Call for Proposals）
    for contractor in potential_contractors:
        manager.send(
            receiver=contractor,
            msg_type=MessageType.QUERY,
            content={
                "action": "call_for_proposal",
                "task": task
            },
            conversation_id=conversation_id
        )
    
    # 2. 收集报价（Proposals）
    proposals = []
    start_time = time.time()
    
    while time.time() - start_time < deadline:
        message = manager.bus.receive(manager.id, timeout=0.1)
        
        if message and message.conversation_id == conversation_id:
            if message.type == MessageType.RESPONSE:
                proposal = message.content
                proposals.append({
                    "contractor": message.sender,
                    "bid": proposal.get("bid"),
                    "capability": proposal.get("capability")
                })
        
        # 如果所有人都回复了，提前结束
        if len(proposals) == len(potential_contractors):
            break
    
    if not proposals:
        return None
    
    # 3. 选择最佳承包者
    best_proposal = min(proposals, key=lambda p: p['bid'])
    winner = best_proposal['contractor']
    
    # 4. 授予合约
    manager.send(
        receiver=winner,
        msg_type=MessageType.COMMAND,
        content={
            "action": "award_contract",
            "task": task
        },
        conversation_id=conversation_id
    )
    
    # 通知失败者
    for proposal in proposals:
        if proposal['contractor'] != winner:
            manager.send(
                receiver=proposal['contractor'],
                msg_type=MessageType.INFORM,
                content={"action": "contract_rejected"},
                conversation_id=conversation_id
            )
    
    return winner

# 时间复杂度: O(n) - n为承包者数量
```

### 3.3 共识算法（简化版Raft）

```python
class ConsensusAgent(Agent):
    """共识Agent"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, peers: List[str]):
        super().__init__(agent_id, message_bus)
        self.peers = peers
        self.state = "follower"  # follower, candidate, leader
        self.current_term = 0
        self.voted_for = None
        self.log = []
    
    def propose_value(self, value: Any) -> bool:
        """提议值（需要共识）"""
        if self.state != "leader":
            # 不是leader，不能提议
            return False
        
        # 追加到日志
        entry = {
            "term": self.current_term,
            "value": value,
            "index": len(self.log)
        }
        self.log.append(entry)
        
        # 复制到多数节点
        conversation_id = str(uuid.uuid4())
        acks = 0
        
        # 发送给所有peer
        for peer in self.peers:
            self.send(
                receiver=peer,
                msg_type=MessageType.COMMAND,
                content={
                    "action": "append_entries",
                    "entry": entry
                },
                conversation_id=conversation_id
            )
        
        # 等待多数确认
        majority = len(self.peers) // 2 + 1
        timeout = 5.0
        start_time = time.time()
        
        while acks < majority and time.time() - start_time < timeout:
            message = self.bus.receive(self.id, timeout=0.1)
            
            if message and message.conversation_id == conversation_id:
                if message.type == MessageType.RESPONSE:
                    if message.content.get('success'):
                        acks += 1
        
        # 检查是否达到多数
        return acks >= majority
    
    def handle_message(self, message: Message):
        """处理消息"""
        if message.type == MessageType.COMMAND:
            action = message.content.get('action')
            
            if action == 'append_entries':
                # 追加日志
                entry = message.content.get('entry')
                self.log.append(entry)
                
                # 确认
                self.send(
                    receiver=message.sender,
                    msg_type=MessageType.RESPONSE,
                    content={"success": True},
                    conversation_id=message.conversation_id
                )

# 时间复杂度: O(n) - n为节点数
# 注意：这是极度简化的版本，完整Raft要复杂得多
```

### 3.4 消息路由算法

```python
def route_message(
    message: Message,
    routing_table: Dict[str, str],
    topology: Dict[str, List[str]]
) -> List[str]:
    """
    消息路由算法
    
    找到从sender到receiver的路径
    
    使用Dijkstra算法
    """
    sender = message.sender
    receiver = message.receiver
    
    # 如果是直连，直接返回
    if receiver in topology.get(sender, []):
        return [sender, receiver]
    
    # Dijkstra
    import heapq
    
    distances = {node: float('inf') for node in topology}
    distances[sender] = 0
    
    previous = {}
    pq = [(0, sender)]
    visited = set()
    
    while pq:
        dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        
        visited.add(current)
        
        if current == receiver:
            break
        
        for neighbor in topology.get(current, []):
            if neighbor in visited:
                continue
            
            new_dist = dist + 1  # 假设每条边权重为1
            
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))
    
    # 重建路径
    if receiver not in previous:
        return []  # 无法到达
    
    path = []
    current = receiver
    
    while current in previous:
        path.append(current)
        current = previous[current]
    
    path.append(sender)
    path.reverse()
    
    return path

# 时间复杂度: O(E log V) - E为边数，V为节点数
```

### 3.5 死锁检测算法

```python
def detect_deadlock(
    waiting_for: Dict[str, str]
) -> Optional[List[str]]:
    """
    检测死锁
    
    waiting_for: {agent_id: waiting_for_agent_id}
    
    使用DFS检测环
    """
    def dfs(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # 访问邻居
        if node in waiting_for:
            neighbor = waiting_for[node]
            
            if neighbor not in visited:
                result = dfs(neighbor, visited, rec_stack, path)
                if result:
                    return result
            
            elif neighbor in rec_stack:
                # 找到环
                cycle_start = path.index(neighbor)
                return path[cycle_start:]
        
        rec_stack.remove(node)
        path.pop()
        return None
    
    visited = set()
    
    for agent in waiting_for:
        if agent not in visited:
            rec_stack = set()
            path = []
            
            cycle = dfs(agent, visited, rec_stack, path)
            
            if cycle:
                return cycle
    
    return None

# 时间复杂度: O(V + E) - V为Agent数，E为等待关系数
```

---

## 4. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Message Bus | 消息总线 | ⭐⭐⭐⭐⭐ |
| Message Structure | 标准消息格式 | ⭐⭐⭐⭐⭐ |
| Agent Base Class | Agent基类 | ⭐⭐⭐⭐⭐ |
| Coordinator | 协调器Agent | ⭐⭐⭐⭐⭐ |
| Worker | 工作Agent | ⭐⭐⭐⭐⭐ |
| Request-Response | 请求响应模式 | ⭐⭐⭐⭐⭐ |
| Contract Net | 合约网协议 | ⭐⭐⭐⭐ |
| Consensus | 共识算法 | ⭐⭐⭐⭐ |
| Message Routing | 消息路由 | ⭐⭐⭐⭐ |
| Deadlock Detection | 死锁检测 | ⭐⭐⭐⭐ |

---

## 5. 核心学习

### 关键概念
1. **消息总线** - 中央通信枢纽
2. **发布订阅** - 解耦通信
3. **协调模式** - 任务分配和管理
4. **共识机制** - 多Agent决策
5. **容错机制** - 重试和恢复

### 核心算法
1. 消息路由（Dijkstra）
2. 合约网协议
3. 共识算法（Raft简化）
4. 死锁检测（DFS环检测）
5. 优先级队列调度

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 消息总线架构
- ⭐⭐⭐⭐⭐ Agent协调模式
- ⭐⭐⭐⭐ 合约网协议
- ⭐⭐⭐⭐ 共识机制
- ⭐⭐⭐⭐ 死锁检测

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 31/40 (77.5%)  
**剩余**: 9个插件
