# FieldMind 文件整理方案

## 当前问题

1. **110+ 个 .md 文档**散落在根目录 `/Users/alwan/`
2. **实际项目代码**分散在多个位置
3. **FieldMind.app** 存在但无法启动
4. **文件结构混乱**，难以管理和维护

## 当前结构分析

```
/Users/alwan/
├── app/                          # ✅ 核心代码目录（Python 后端）
├── fieldmind-backend/            # ❓ 重复的后端代码？
├── fieldmind-web/                # ✅ Web 前端
├── fieldmind-desktop/            # ✅ 桌面应用
├── FieldMind-Rebuild/            # ❓ 重建版本？
├── FieldMind.app/                # ❌ 应用程序（需修复）
├── 110+ .md 文件                 # ❌ 文档散落
├── 各种测试脚本                  # ❌ 脚本混乱
└── 其他杂项文件                  # ❌ 需整理
```

## 整理目标

创建规范的项目结构：

```
/Users/alwan/FieldMind/           # 主项目目录
├── backend/                      # 后端代码（整合 app/ 和 fieldmind-backend/）
│   ├── app/                      # Python 应用核心
│   ├── tests/                    # 后端测试
│   ├── requirements.txt          
│   └── README.md
├── frontend/                     # 前端代码
│   ├── web/                      # Web 版本（fieldmind-web）
│   ├── desktop/                  # 桌面版本（fieldmind-desktop）
│   └── README.md
├── docs/                         # 所有文档
│   ├── architecture/             # 架构文档
│   ├── api/                      # API 文档
│   ├── deployment/               # 部署文档
│   ├── development/              # 开发文档
│   ├── user-guides/              # 用户指南
│   └── reports/                  # 各种报告
├── scripts/                      # 所有脚本
│   ├── install/                  # 安装脚本
│   ├── deploy/                   # 部署脚本
│   ├── test/                     # 测试脚本
│   └── maintenance/              # 维护脚本
├── external-libs/                # 外部集成库
│   ├── AutoRAG/
│   ├── KAG/
│   └── ...
├── config/                       # 配置文件
│   ├── docker-compose.yml
│   ├── .env.example
│   └── k8s/
├── data/                         # 数据目录
│   ├── uploads/
│   ├── chroma_db/
│   └── logs/
├── FieldMind.app/                # macOS 应用程序
├── README.md                     # 主 README
└── .gitignore
```

## 整理步骤

### 1️⃣ 创建新的项目结构（不移动原文件）
```bash
mkdir -p ~/FieldMind/{backend,frontend,docs,scripts,config,data,external-libs}
mkdir -p ~/FieldMind/docs/{architecture,api,deployment,development,user-guides,reports,phases}
mkdir -p ~/FieldMind/scripts/{install,deploy,test,maintenance}
mkdir -p ~/FieldMind/frontend/{web,desktop}
```

### 2️⃣ 整理文档文件
按类型分类所有 .md 文件：
- **架构文档** → `docs/architecture/`
  - ARCHITECTURE.md, AI_SYSTEM_ARCHITECTURE.md, WORKFLOW_DESIGN.md
- **API 文档** → `docs/api/`
  - API_*.md 系列
- **部署文档** → `docs/deployment/`
  - DEPLOYMENT_*.md, DOCKER.md, K8S_*.md
- **开发文档** → `docs/development/`
  - CONTRIBUTING.md, CODE_QUALITY_*.md
- **用户指南** → `docs/user-guides/`
  - USER_MANUAL.md, USAGE_GUIDE.md, QUICK_START*.md
- **报告文档** → `docs/reports/`
  - *_REPORT.md, *_COMPLETE.md, *_SUMMARY.md
- **阶段文档** → `docs/phases/`
  - PHASE_*.md, CHAIN_*.md, FUNCTION_*.md

### 3️⃣ 整理代码
- 保留 `/Users/alwan/app/` 作为后端核心
- 创建符号链接到新结构
- 逐步迁移到 `~/FieldMind/backend/app/`

### 4️⃣ 整理脚本
- `install*.sh` → `scripts/install/`
- `deploy*.sh` → `scripts/deploy/`
- `test*.sh`, `test*.py` → `scripts/test/`
- `cleanup*.sh`, `monitor.sh` → `scripts/maintenance/`

### 5️⃣ 修复 FieldMind.app
- 检查应用程序包结构
- 重新构建或修复启动配置
- 移动到新项目目录

## 实施方案

### 方案 A：渐进式整理（推荐）✅
1. 创建新结构，不删除原文件
2. 复制文件到新位置
3. 验证新结构可用
4. 逐步切换到新目录
5. 最后清理旧文件

### 方案 B：直接移动（风险较高）⚠️
1. 直接移动所有文件
2. 更新所有路径引用
3. 一次性切换

## 需要确认的问题

1. **FieldMind-Rebuild/** 是什么？是否需要保留？
2. **fieldmind-backend/** vs **app/** 有什么区别？
3. 是否需要保留所有历史文档？
4. 当前工作目录是哪个？（避免中断正在进行的工作）

## 下一步行动

请选择：

**选项 1**：自动执行整理方案 A（我会创建脚本自动整理）
**选项 2**：手动选择要保留的文档（我帮你分类，你决定保留哪些）
**选项 3**：先修复 FieldMind.app 启动问题
**选项 4**：保持现状，只创建文档索引

---

## 关于 FieldMind.app 无法启动

可能原因：
1. 应用程序包不完整
2. 代码签名问题
3. 启动配置错误
4. 依赖路径变更

需要检查：
- `FieldMind.app/Contents/MacOS/` 中的可执行文件
- `Info.plist` 配置
- 启动日志

我可以帮你诊断和修复这个问题。
