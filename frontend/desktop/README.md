# FieldMind macOS 应用

一个专为田野调查研究设计的原生 macOS 应用程序，提供完整的材料管理、知识分析和智能对话功能。

## 系统要求

- macOS 13.0 (Ventura) 或更高版本
- Apple Silicon (M1/M2/M3) 或 Intel 处理器
- Swift 5.9+
- 后端服务运行在 `http://localhost:8000`

## 功能特性

### 1. 用户认证
- **登录/登出系统**
- 演示账号: `demo` / `demo123`
- 基于 Token 的身份验证
- 用户状态持久化

### 2. 项目管理
- 创建、查看、编辑、删除项目
- 项目统计信息（文档数、脉络数）
- 卡片式项目展示
- 项目快速切换

### 3. 知识脉络（三层结构）
- **树状层级展示**
  - 第一层：大脉络
  - 第二层：子脉络
  - 第三层：细分脉络
- **脉络详情**
  - 关键词标签
  - 描述段落
  - 相关报告（三层报告）
- 可视化脉络树
- 点击展开/折叠

### 4. 材料导入
- **多格式支持**
  - PDF、Word、TXT、Excel
- **状态管理**
  - 待处理、处理中、已完成、失败
- **过滤器**
  - 按状态快速筛选
- **确认对话框**
  - 上传前确认
  - 失败提示
- 文件拖拽上传
- 批量处理

### 5. 智能对话
- **多会话管理**
  - 独立对话会话
  - 会话历史保存
- **数据源选择**
  - 基于文档的 RAG 对话
  - 多文档联合查询
- **分析框架集成**
  - 费孝通理论（差序格局、礼治秩序、熟人社会）
  - SOP 标准流程
  - 自定义框架
- **消息展示**
  - 用户/助手区分
  - 数据来源标注
  - 实时流式输出

### 6. 村落编年史
- **时间线可视化**
  - 按年份组织
  - 事件卡片展示
- **自动生成**
  - 从文档中提取时间信息
  - AI 智能整理
- 年份导航
- 事件详情查看

### 7. 知识关系图谱
- **图形化展示**
  - 节点（人物、地点、事件、概念）
  - 关系边（带权重）
- **交互操作**
  - 缩放、拖拽
  - 点击查看详情
- **节点详情**
  - 属性信息
  - 关联关系
- **统计信息**
  - 节点数、边数
  - 密度、平均度

### 8. 思维模型/技能
- **Python 脚本管理**
  - 上传 .py 文件
  - 技能启用/禁用
- **确认对话框**
  - 安装确认
  - 启用确认
  - 删除确认
- **技能分类**
  - 按类别组织
  - 卡片式展示
- **执行集成**
  - 在分析中自动应用

### 9. 二度分析框架
- **费孝通理论框架**
  - 差序格局：社会关系网络结构
  - 礼治秩序：传统礼俗维护
  - 熟人社会：信任与声誉机制
- **SOP 框架**
  - 标准调研流程
  - 前期准备、田野工作、资料分析
- **框架组件**
  - 分析维度
  - 引导问题
  - 使用说明

### 10. 概览仪表板
- **统计卡片**
  - 项目、文档、脉络、会话总数
- **最近活动**
  - 操作历史记录
- **快速操作**
  - 常用功能入口

## 技术架构

### 前端技术栈
- **SwiftUI**: 原生 UI 框架
- **Alamofire**: HTTP 网络请求
- **Combine**: 响应式编程
- **Codable**: JSON 序列化

### 项目结构
```
FieldMindApp/
├── Package.swift                 # Swift Package 配置
├── Sources/
│   └── FieldMind/
│       ├── main.swift           # 应用入口
│       ├── Models/              # 数据模型
│       │   ├── User.swift
│       │   ├── Project.swift
│       │   ├── Document.swift
│       │   ├── Context.swift
│       │   ├── Chat.swift
│       │   ├── Timeline.swift
│       │   ├── Graph.swift
│       │   ├── Skill.swift
│       │   └── Framework.swift
│       ├── Views/               # 视图组件
│       │   ├── LoginView.swift
│       │   ├── MainAppView.swift
│       │   ├── DashboardView.swift
│       │   ├── ProjectsView.swift
│       │   ├── ContextsView.swift
│       │   ├── DocumentsView.swift
│       │   ├── ChatView.swift
│       │   ├── TimelineView.swift
│       │   ├── GraphView.swift
│       │   ├── SkillsView.swift
│       │   └── FrameworksView.swift
│       ├── Services/            # 服务层
│       │   └── APIService.swift
│       └── Utils/               # 工具类
│           └── AppState.swift
└── README.md
```

### API 集成

应用通过 RESTful API 与后端通信：

- **认证**: `/api/v1/auth/login`, `/api/v1/auth/logout`
- **项目**: `/api/v1/projects/`
- **文档**: `/api/v1/documents/`
- **脉络**: `/api/v1/contexts/`
- **对话**: `/api/v1/chat/`
- **时间线**: `/api/v1/timeline/`
- **图谱**: `/api/v1/graph/`
- **技能**: `/api/v1/skills/`

## 编译和运行

### 1. 安装依赖

确保已安装 Xcode Command Line Tools:
```bash
xcode-select --install
```

### 2. 编译应用

```bash
cd ~/Desktop/FieldMindApp
swift build -c release
```

### 3. 运行应用

```bash
swift run
```

或者使用 Xcode 打开项目：
```bash
open Package.swift
```

### 4. 创建 .app 包

使用 Xcode 构建并导出应用程序包，或使用以下命令：
```bash
swift build -c release
# 应用程序位于 .build/release/FieldMind
```

## 配置

### API 地址配置

默认连接到 `http://localhost:8000`，可以在应用设置中修改。

### 后端启动

在运行 macOS 应用前，确保后端服务已启动：

```bash
cd ~/FieldMind-Rebuild  # 或您的后端目录
./quick_start.sh
```

## 使用流程

### 首次使用

1. **启动后端服务**
   ```bash
   cd ~/FieldMind-Rebuild
   ./quick_start.sh
   ```

2. **运行 macOS 应用**
   ```bash
   cd ~/Desktop/FieldMindApp
   swift run
   ```

3. **登录系统**
   - 用户名: `demo`
   - 密码: `demo123`

### 典型工作流

1. **创建项目**
   - 进入"项目管理"页面
   - 点击"新建项目"
   - 输入项目名称和描述

2. **导入材料**
   - 选择项目
   - 进入"材料导入"页面
   - 点击"导入材料"
   - 选择文档文件
   - 确认上传
   - 等待处理完成

3. **构建知识脉络**
   - 进入"知识脉络"页面
   - 查看自动生成的三层脉络树
   - 点击脉络查看详情
   - 查看关键词和相关报告

4. **开始智能对话**
   - 进入"智能对话"页面
   - 点击创建新会话
   - 选择数据源（已处理的文档）
   - 可选择分析框架（费孝通理论或 SOP）
   - 输入问题开始对话

5. **生成编年史**
   - 进入"编年史"页面
   - 点击"生成编年史"
   - 查看按年份组织的事件时间线

6. **查看关系图谱**
   - 进入"关系图谱"页面
   - 点击"构建图谱"
   - 交互式探索知识网络

7. **管理思维模型**
   - 进入"思维模型"页面
   - 上传 Python 技能文件
   - 启用/禁用技能
   - 技能将自动应用于分析

## UI/UX 特性

### 设计风格
- **原生 macOS 体验**
  - 遵循 Apple Human Interface Guidelines
  - 系统原生组件
  - 流畅的动画过渡

### 颜色主题
- 主色调: `#667eea` (紫蓝色)
- 成功色: `#48bb78` (绿色)
- 警告色: `#ed8936` (橙色)
- 错误色: `#f56565` (红色)

### 交互特性
- **键盘快捷键支持**
  - `⌘N`: 新建项目/会话
  - `⌘W`: 关闭对话框
  - `⌘Enter`: 确认操作
  - `Esc`: 取消操作

- **手势支持**
  - 双指滚动
  - 缩放手势（图谱视图）
  - 拖拽操作

- **状态反馈**
  - 加载指示器
  - 操作确认对话框
  - 成功/失败提示

## 性能优化

- **懒加载**: 使用 `LazyVStack` 和 `LazyVGrid` 优化列表渲染
- **异步加载**: 所有网络请求使用 async/await
- **状态管理**: 使用 `@Published` 和 `@State` 管理响应式状态
- **内存管理**: ARC 自动内存管理
- **缓存策略**: Token 和用户信息持久化到 UserDefaults

## 调试

### 日志输出

应用会在控制台输出详细的调试信息：
```bash
swift run 2>&1 | grep "Error"
```

### 常见问题

1. **无法连接到后端**
   - 检查后端是否运行在 `localhost:8000`
   - 检查防火墙设置

2. **登录失败**
   - 确认使用正确的演示账号
   - 检查网络连接

3. **文档上传失败**
   - 检查文件格式是否支持
   - 检查文件大小限制

## 后续开发计划

### v1.1 计划功能
- [ ] 报告生成器
- [ ] 批量导出功能
- [ ] 高级搜索
- [ ] 标签系统
- [ ] 团队协作功能

### v1.2 计划功能
- [ ] 离线模式
- [ ] 云端同步
- [ ] 移动端应用（iOS）
- [ ] 数据备份/恢复
- [ ] 更多分析框架

## 开源协议

MIT License

## 联系方式

- 项目地址: https://github.com/yourusername/fieldmind
- 问题反馈: https://github.com/yourusername/fieldmind/issues

## 致谢

感谢所有为 FieldMind 项目做出贡献的开发者和研究者。
