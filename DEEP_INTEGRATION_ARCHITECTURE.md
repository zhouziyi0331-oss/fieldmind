# FieldMind深度集成架构设计 - Obsidian生态完整融合

## 🎯 深度集成目标

将Obsidian releases和obsidian-skills的**完整功能**融入FieldMind，而不是简单的导出工具。

---

## 📦 第一阶段：Obsidian Releases深度集成

### 1.1 Obsidian插件系统核心

**来源**: https://github.com/obsidianmd/obsidian-releases

**核心能力**:
- 插件生命周期管理
- 数据持久化机制
- 视图渲染系统
- 命令注册和快捷键
- 设置面板
- 事件系统

**深度集成方案**:

#### 1.1.1 FieldMind插件引擎
**新建**: `backend/src/app/core/plugin_engine.py`

```python
"""
FieldMind插件引擎 - 完全兼容Obsidian插件规范

不是简单导出，而是在FieldMind内部实现完整的插件系统：
- 运行时加载用户自定义插件
- 插件间通信
- 数据共享
- 视图扩展
"""

class FieldMindPluginEngine:
    def __init__(self):
        self.plugins = {}
        self.commands = {}
        self.views = {}
        
    def load_plugin(self, plugin_path: str):
        """动态加载插件（支持Python和JavaScript）"""
        pass
        
    def register_command(self, command_id: str, handler):
        """注册命令"""
        pass
        
    def register_view(self, view_type: str, component):
        """注册自定义视图"""
        pass
```

#### 1.1.2 数据存储兼容层
**新建**: `backend/src/app/core/obsidian_compat.py`

```python
"""
Obsidian数据格式完全兼容

FieldMind内部使用Obsidian的数据结构：
- Markdown文件作为第一公民
- Frontmatter元数据
- 双向链接 [[]]
- 标签系统 #tag
- 块引用 ^blockid
"""

class ObsidianDataStore:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        
    def create_note(self, title: str, content: str, metadata: dict):
        """创建Obsidian兼容的笔记"""
        pass
        
    def parse_wikilinks(self, content: str) -> List[str]:
        """解析双向链接"""
        pass
        
    def resolve_block_ref(self, block_id: str):
        """解析块引用"""
        pass
```

#### 1.1.3 实时同步引擎
**新建**: `backend/src/app/core/obsidian_sync.py`

```python
"""
FieldMind ⟷ Obsidian 双向实时同步

不是单向导出，而是：
- 实时监听Obsidian vault变化
- 自动同步到FieldMind数据库
- FieldMind修改实时推送到Obsidian
- 冲突解决机制
"""

class ObsidianSyncEngine:
    def __init__(self, vault_path: Path, db: Session):
        self.vault_path = vault_path
        self.db = db
        self.watcher = None
        
    def start_watch(self):
        """开始监听vault变化"""
        pass
        
    def sync_to_obsidian(self, item_id: int):
        """将FieldMind数据同步到Obsidian"""
        pass
        
    def sync_from_obsidian(self, file_path: Path):
        """将Obsidian文件同步到FieldMind"""
        pass
```

---

## 📚 第二阶段：Obsidian Skills深度集成

### 2.1 Skills插件核心功能

**来源**: https://github.com/kepano/obsidian-skills

**核心能力**:
- 技能追踪系统
- 技能树可视化
- 技能关系网络
- 进度追踪
- 技能标签
- 技能搜索

**深度集成方案**:

#### 2.1.1 技能系统原生化
**更新**: `backend/src/app/models/skill.py`

```python
"""
将obsidian-skills的数据模型完全融入FieldMind

不是导出到Obsidian，而是FieldMind本身就是技能管理系统
"""

class SkillNode(Base):
    """技能节点 - 兼容obsidian-skills格式"""
    __tablename__ = "skill_nodes"
    
    id = Column(Integer, primary_key=True)
    skill_id = Column(String, unique=True)  # 对应SBPACK的skill_id
    
    # obsidian-skills兼容字段
    name = Column(String, nullable=False)
    category = Column(String)  # 技能分类
    level = Column(Integer, default=0)  # 技能等级
    xp = Column(Integer, default=0)  # 经验值
    prerequisites = Column(JSON)  # 前置技能
    
    # 可视化数据
    position_x = Column(Float)  # 技能树位置
    position_y = Column(Float)
    color = Column(String)  # 节点颜色
    icon = Column(String)  # 图标
    
    # 关系
    parent_skills = relationship("SkillRelation", foreign_keys="SkillRelation.target_id")
    child_skills = relationship("SkillRelation", foreign_keys="SkillRelation.source_id")


class SkillRelation(Base):
    """技能关系 - 构建技能树"""
    __tablename__ = "skill_relations"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("skill_nodes.id"))
    target_id = Column(Integer, ForeignKey("skill_nodes.id"))
    relation_type = Column(String)  # prerequisite, related, unlocks
    strength = Column(Float)


class SkillProgress(Base):
    """技能进度追踪"""
    __tablename__ = "skill_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_id = Column(Integer, ForeignKey("skill_nodes.id"))
    
    status = Column(String)  # locked, available, in_progress, mastered
    progress_percentage = Column(Float, default=0)
    last_practiced = Column(DateTime)
    mastery_level = Column(Integer, default=0)
```

#### 2.1.2 技能树可视化引擎
**新建**: `backend/src/app/services/skill_tree_builder.py`

```python
"""
技能树自动构建和可视化

从SBPACK技能轨自动生成技能树：
- 基于技能关系自动布局
- 前置技能识别
- 技能等级分层
- 学习路径推荐
"""

class SkillTreeBuilder:
    def __init__(self, db: Session):
        self.db = db
        
    def build_from_sbpack(self, package_id: int) -> Dict[str, Any]:
        """从SBPACK构建技能树"""
        # 1. 加载所有技能
        skills = self.load_skills(package_id)
        
        # 2. 分析技能关系
        relations = self.analyze_relations(skills)
        
        # 3. 构建层级结构
        tree = self.build_hierarchy(skills, relations)
        
        # 4. 自动布局
        layout = self.auto_layout(tree)
        
        return layout
        
    def analyze_relations(self, skills: List[SkillItem]) -> List[SkillRelation]:
        """分析技能间关系"""
        # 基于RIA++的B字段（boundaries）和I字段（interpretation）
        # 自动识别前置关系
        pass
        
    def recommend_path(self, target_skill_id: int, user_id: int) -> List[int]:
        """推荐学习路径"""
        pass
```

#### 2.1.3 技能进度系统
**新建**: `backend/src/app/services/skill_progress_tracker.py`

```python
"""
技能进度追踪和游戏化

将技能学习游戏化：
- XP系统
- 成就系统
- 技能解锁机制
- 练习提醒
"""

class SkillProgressTracker:
    def __init__(self, db: Session):
        self.db = db
        
    def practice_skill(self, user_id: int, skill_id: int, result: Dict):
        """记录技能练习"""
        # 更新XP
        # 检查是否升级
        # 解锁新技能
        pass
        
    def check_unlocks(self, user_id: int) -> List[int]:
        """检查可解锁的技能"""
        pass
        
    def get_recommendations(self, user_id: int) -> List[Dict]:
        """获取推荐练习的技能"""
        pass
```

---

## 🔗 第三阶段：完整融合架构

### 3.1 统一数据模型

**核心思想**: FieldMind内部数据结构**就是**Obsidian格式

```
FieldMind数据库
    ↕ (实时同步)
Obsidian Vault文件
    ↕ (插件扩展)
用户自定义功能
```

### 3.2 新的架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     FieldMind Core                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Obsidian   │    │    SBPACK    │    │    Skills    │ │
│  │   Compat     │◄──►│   Engine     │◄──►│    Engine    │ │
│  │   Layer      │    │              │    │              │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         ▲                    ▲                    ▲         │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            PostgreSQL Database                        │  │
│  │  - Markdown原生存储                                   │  │
│  │  - 双向链接图                                         │  │
│  │  - 技能树结构                                         │  │
│  │  - 进度追踪                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     同步层                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   File       │    │   Real-time  │    │   Conflict   │ │
│  │   Watcher    │◄──►│   Sync       │◄──►│   Resolver   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         ▲                                         │         │
│         └─────────────────────────────────────────┘         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   Obsidian Vault                            │
│              (本地文件系统 或 云同步)                          │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 完整的数据流

```
1. 用户上传PDF
   ↓
2. 蒸馏提取（知识轨+技能轨）
   ↓
3. 存储为Markdown格式（在数据库中）
   ↓
4. 自动同步到Obsidian vault
   ↓
5. 用户在Obsidian中编辑
   ↓
6. 实时同步回FieldMind
   ↓
7. 触发技能树更新
   ↓
8. 更新进度追踪
```

---

## 📋 完整的新增模块列表

### 核心引擎层
1. `backend/src/app/core/plugin_engine.py` - 插件引擎
2. `backend/src/app/core/obsidian_compat.py` - Obsidian兼容层
3. `backend/src/app/core/obsidian_sync.py` - 实时同步引擎
4. `backend/src/app/core/markdown_parser.py` - Markdown完整解析器
5. `backend/src/app/core/wikilink_resolver.py` - 双向链接解析器

### 技能系统层
6. `backend/src/app/models/skill_node.py` - 技能节点模型
7. `backend/src/app/models/skill_progress.py` - 进度追踪模型
8. `backend/src/app/services/skill_tree_builder.py` - 技能树构建器
9. `backend/src/app/services/skill_progress_tracker.py` - 进度追踪服务
10. `backend/src/app/services/skill_relation_analyzer.py` - 关系分析器

### API层
11. `backend/src/app/api/obsidian_sync.py` - 同步API
12. `backend/src/app/api/skill_tree.py` - 技能树API
13. `backend/src/app/api/skill_progress.py` - 进度追踪API
14. `backend/src/app/api/plugins.py` - 插件管理API

### 前端组件
15. `frontend/src/components/SkillTreeViewer.tsx` - 技能树可视化
16. `frontend/src/components/SkillProgressPanel.tsx` - 进度面板
17. `frontend/src/components/ObsidianSyncPanel.tsx` - 同步控制面板
18. `frontend/src/components/WikiLinkEditor.tsx` - 双向链接编辑器
19. `frontend/src/components/MarkdownEditor.tsx` - Markdown原生编辑器

### 工具层
20. `backend/src/app/utils/obsidian_plugin_loader.py` - 插件加载器
21. `backend/src/app/utils/skill_tree_layout.py` - 技能树布局算法
22. `backend/src/app/utils/markdown_renderer.py` - Markdown渲染器

---

## 🎯 深度集成的关键特性

### 1. Markdown作为第一公民
- 数据库直接存储Markdown内容
- 保留完整的frontmatter
- 支持所有Obsidian语法

### 2. 双向链接原生支持
- `[[note name]]` 自动解析和跳转
- 反向链接自动维护
- 链接图谱可视化

### 3. 实时双向同步
- FieldMind编辑 → 自动推送到Obsidian
- Obsidian编辑 → 自动同步到FieldMind
- 冲突自动检测和解决

### 4. 插件系统完全兼容
- 支持加载Obsidian社区插件
- 用户可以自定义扩展
- 插件间通信机制

### 5. 技能树原生功能
- 不是导出，而是内置功能
- 自动构建技能树
- 游戏化学习路径
- 进度追踪和推荐

---

## 📊 实施优先级

### P0 - 基础设施（第一周）
1. Obsidian兼容层
2. Markdown解析器
3. 双向链接解析器
4. 技能节点数据模型

### P1 - 核心功能（第二周）
5. 实时同步引擎
6. 技能树构建器
7. 进度追踪系统
8. 前端可视化组件

### P2 - 高级功能（第三周）
9. 插件引擎
10. 技能关系分析
11. 学习路径推荐
12. 冲突解决机制

---

## 🎓 与现有系统的整合

### 整合点1: SBPACK → 技能树
```python
# 从SBPACK自动生成技能树
builder = SkillTreeBuilder(db)
tree = builder.build_from_sbpack(package_id)

# 存储为技能节点
for skill in tree:
    node = SkillNode(
        skill_id=skill.skill_id,
        name=skill.name,
        prerequisites=skill.extract_prerequisites(),  # 从B字段提取
        position_x=skill.layout_x,
        position_y=skill.layout_y
    )
    db.add(node)
```

### 整合点2: 知识点 → Obsidian笔记
```python
# 知识点自动转换为Markdown笔记
for knowledge in knowledge_items:
    markdown = f"""---
type: knowledge
knowledge_type: {knowledge.knowledge_type}
tags: [知识点, {knowledge.knowledge_type}]
---

# {knowledge.title}

{knowledge.statement}

## 相关技能
{generate_skill_links(knowledge.id)}
"""
    sync_engine.create_note(knowledge.title, markdown)
```

### 整合点3: 蒸馏 → 实时同步
```python
# 蒸馏完成后自动同步到Obsidian
@event.listens_for(KnowledgeItem, 'after_insert')
def sync_new_knowledge(mapper, connection, target):
    sync_engine.sync_to_obsidian(target.id, 'knowledge')

@event.listens_for(SkillItem, 'after_insert')
def sync_new_skill(mapper, connection, target):
    sync_engine.sync_to_obsidian(target.id, 'skill')
    tree_builder.update_tree(target.package_id)
```

---

## 🚀 最终效果

用户体验：
1. 在FieldMind上传书籍 → 自动蒸馏
2. 蒸馏结果**自动出现在Obsidian vault中**
3. 在Obsidian编辑笔记 → **实时同步回FieldMind**
4. FieldMind自动构建技能树
5. 用户在FieldMind查看技能树和学习进度
6. 在Obsidian使用所有社区插件增强体验
7. 一切数据双向同步，无缝集成

这才是**真正的深度集成**！
