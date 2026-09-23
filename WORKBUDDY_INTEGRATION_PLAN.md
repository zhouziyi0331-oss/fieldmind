# FieldMind完整集成计划 - WorkBuddy蒸馏系统 + Second Brain Installer

## 📋 集成目标

将以下两个完整系统集成到FieldMind中：

1. **WorkBuddy蒸馏交付包 (1.4.4版)** - SBPACK 2.0双轨蒸馏系统
2. **Second Brain Installer (1.7.2版)** - 第二大脑安装助手

---

## 📦 待集成内容清单

### 一、WorkBuddy蒸馏系统

#### 1.1 核心规范文档 (14个MD)
```
/Users/alwan/Downloads/直接给WorkBuddy-开始蒸馏-中文表达1.4.4-交付/

核心文档：
✅ 01-给WorkBuddy的最终提示词.md (17KB) - 已部分转换为Skills
□ 02-输入材料与元信息.md
□ 03-知识点轨生产规范.md
□ 04-仓颉技能轨生产规范.md
□ 05-SBPACK-2.0封装与验收清单.md
□ 06-当前兼容性与失败处理.md
□ 07-网页视频直接蒸馏.md
□ 08-双轨冻结与封装权限矩阵.md
□ 09-生产者真实快照与产物登记.md
□ 10-技能充分提取与质量标准.md
□ 11-生产审计与验收.md
□ 12-技能中文表达规范.md
□ 00-先读我.md
□ 00-自动入口.md
```

#### 1.2 工具脚本 (10个文件)
```
工具/
□ 构建-SBPACK-2.0.cjs (12KB) - SBPACK打包器
□ 验收-SBPACK-2.0.cjs (4KB) - SBPACK验收
□ 校验生产审计.cjs (5KB) - 审计校验
□ 校验阅读章节.cjs (1.5KB)
□ 登记-生产者快照.cjs (4KB)
□ 刷新交接包清单.cjs (2KB)
□ 检查交接包完整性.cjs (2KB)
□ v2-preflight/ - 预检工具集
```

#### 1.3 配置和元数据
```
□ 交接包清单.json (33KB)
□ 版本锁定.json
□ 交接包验收报告.md
□ 交付说明.md
```

#### 1.4 示例和规范
```
示例/
规范/
第三方许可/
```

---

### 二、Second Brain Installer

#### 2.1 核心Skill
```
/Users/alwan/Downloads/second-brain-installer/

□ SKILL.md (8.5KB) - Obsidian插件安装Skill
```

#### 2.2 安装脚本 (8个)
```
scripts/
□ second-brain-installer.ps1 (Windows安装)
□ second-brain-installer-macos.sh (macOS安装)
□ second-brain-update-windows.ps1 (Windows升级)
□ second-brain-update-macos.sh (macOS升级)
□ install-starter-library.ps1 (Windows种子库)
□ install-starter-library-macos.sh (macOS种子库)
□ preserve-plugin-files.ps1
□ macos-json-helper.js
```

#### 2.3 参考文档 (4个)
```
references/
□ windows.md - Windows执行流程
□ macos.md - macOS执行流程
□ api_reference.md - API参考
□ automatic-startup.md - 自动启动逻辑
```

#### 2.4 资源包
```
assets/
□ second-brain-mode-1.7.2-founder-beta.zip
□ shared-program.zip
□ plugin-release.json
□ starter-library/manifest.json
□ update-bootstrap/
```

#### 2.5 测试数据
```
□ test-prompts.json
```

---

## 🎯 集成策略

### Phase 1: SBPACK 2.0双轨蒸馏核心 (优先级: 最高)

#### 任务1.1: 知识轨生产系统
**来源**: `03-知识点轨生产规范.md`

**转换为**:
- `backend/src/app/skills/sbpack/extract_knowledge_track.py`
- 独立判断的概念、主张、原理提取
- 8个必须字段完整实现
- 质量门禁和验证

**集成点**: 
- 增强现有的 `extract_knowledge_points.py`
- 添加完整的SBPACK 2.0验证逻辑

#### 任务1.2: 技能轨生产系统（仓颉v2.0.0）
**来源**: `04-仓颉技能轨生产规范.md` + `10-技能充分提取与质量标准.md` + `12-技能中文表达规范.md`

**转换为**:
- `backend/src/app/skills/sbpack/extract_skill_track.py`
- 完整RIA++结构实现
- 压力测试设计器
- 三项验证（V1/V2/V3）

**集成点**:
- 增强现有的 `extract_cangjie_skills.py`
- 添加仓颉官方标准的完整实现

#### 任务1.3: SBPACK 2.0打包系统
**来源**: `工具/构建-SBPACK-2.0.cjs` + `05-SBPACK-2.0封装与验收清单.md`

**转换为**:
- `backend/src/app/services/sbpack_builder.py`
- SBPACK文件格式生成器
- 元数据封装
- SHA-256校验
- 双轨冻结逻辑

**新增API**:
```python
POST /api/sbpack/build/{project_id}  # 构建SBPACK
GET  /api/sbpack/packages            # 列出SBPACK包
GET  /api/sbpack/packages/{id}       # 获取SBPACK详情
POST /api/sbpack/verify/{id}         # 验收SBPACK
```

#### 任务1.4: SBPACK验收系统
**来源**: `工具/验收-SBPACK-2.0.cjs` + `11-生产审计与验收.md`

**转换为**:
- `backend/src/app/services/sbpack_validator.py`
- 完整性检查
- 证据追溯验证
- 压力测试执行
- 生产审计

---

### Phase 2: 输入处理系统

#### 任务2.1: 多格式输入支持
**来源**: `02-输入材料与元信息.md` + `07-网页视频直接蒸馏.md`

**转换为**:
- `backend/src/app/services/input_processor.py`
- 支持格式：PDF, DOCX, TXT, MD, MOBI, EPUB, 网页URL, 视频URL
- 元信息提取（YAML格式）
- 字幕/音频转写集成

**新增API**:
```python
POST /api/input/upload              # 上传文件
POST /api/input/from_url            # 从URL提取
POST /api/input/extract_metadata    # 提取元信息
GET  /api/input/formats             # 支持的格式列表
```

#### 任务2.2: 章节规范化
**来源**: `工具/校验阅读章节.cjs`

**转换为**:
- `backend/src/app/services/chapter_normalizer.py`
- 章节识别和标准化
- 层级结构构建
- 章节校验

---

### Phase 3: 生产者快照与审计系统

#### 任务3.1: 生产者快照
**来源**: `09-生产者真实快照与产物登记.md` + `工具/登记-生产者快照.cjs`

**转换为**:
- `backend/src/app/models/producer_snapshot.py` (数据模型)
- `backend/src/app/services/producer_registry.py` (服务)
- 记录每个生产角色的真实运行快照
- SHA-256哈希验证

**数据库表**:
```sql
CREATE TABLE producer_snapshots (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    role VARCHAR(50),  -- 'knowledge_track', 'skill_track', 'adapter'
    input_snapshot TEXT,
    output_snapshot TEXT,
    trace_snapshot TEXT,
    snapshot_hash VARCHAR(64),
    created_at TIMESTAMP
);
```

#### 任务3.2: 生产审计
**来源**: `工具/校验生产审计.cjs`

**转换为**:
- `backend/src/app/services/production_auditor.py`
- 审计生产过程
- 验证快照完整性
- 生成审计报告

---

### Phase 4: 关系与冻结系统

#### 任务4.1: 双轨冻结机制
**来源**: `08-双轨冻结与封装权限矩阵.md`

**转换为**:
- `backend/src/app/services/track_freezer.py`
- 知识轨冻结
- 技能轨冻结
- 权限矩阵控制
- 冻结后不可修改

**数据库表**:
```sql
CREATE TABLE track_freezes (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    track_type VARCHAR(20),  -- 'knowledge', 'skill'
    frozen_at TIMESTAMP,
    frozen_by VARCHAR(100),
    freeze_hash VARCHAR(64),
    is_frozen BOOLEAN DEFAULT false
);
```

#### 任务4.2: 知识-技能关系建立
**来源**: `01-给WorkBuddy的最终提示词.md` (关系部分)

**转换为**:
- `backend/src/app/services/knowledge_skill_linker.py`
- 自动关系推断
- 关系验证
- 关系可视化数据生成

---

### Phase 5: Second Brain Installer集成

#### 任务5.1: Obsidian插件导出
**来源**: `second-brain-installer/SKILL.md`

**转换为**:
- `backend/src/app/skills/obsidian_exporter.py`
- 导出为Obsidian插件格式
- 自动打包和签名
- 版本管理

**功能**:
- 将FieldMind的蒸馏结果导出为Obsidian可用格式
- 生成`.sbpack`文件
- 创建Obsidian插件包

#### 任务5.2: 安装器脚本适配
**来源**: `scripts/` 目录所有脚本

**转换为**:
- `backend/src/app/services/installer_generator.py`
- 生成Windows/macOS安装脚本
- 自动检测和配置
- 一键部署到Obsidian

---

### Phase 6: 前端界面

#### 任务6.1: SBPACK管理界面
**新建**: `frontend/src/pages/SBPACKManager.tsx`

**功能**:
- SBPACK列表
- 构建SBPACK
- 验收和审计
- 导出和分享

#### 任务6.2: 双轨生产界面
**新建**: `frontend/src/pages/DualTrackProduction.tsx`

**功能**:
- 知识轨编辑器
- 技能轨编辑器
- 双轨状态显示
- 冻结控制

#### 任务6.3: 生产者快照查看
**新建**: `frontend/src/components/ProducerSnapshot.tsx`

**功能**:
- 快照列表
- 快照详情
- 审计报告查看

---

## 🗂️ 新增目录结构

```
backend/
├── src/app/
│   ├── skills/
│   │   ├── sbpack/
│   │   │   ├── __init__.py
│   │   │   ├── extract_knowledge_track.py
│   │   │   ├── extract_skill_track.py
│   │   │   └── skill_validator.py
│   │   ├── obsidian_exporter.py
│   │   └── ... (现有skills)
│   ├── services/
│   │   ├── sbpack_builder.py
│   │   ├── sbpack_validator.py
│   │   ├── input_processor.py
│   │   ├── chapter_normalizer.py
│   │   ├── producer_registry.py
│   │   ├── production_auditor.py
│   │   ├── track_freezer.py
│   │   ├── knowledge_skill_linker.py
│   │   └── installer_generator.py
│   ├── models/
│   │   ├── sbpack.py
│   │   ├── producer_snapshot.py
│   │   └── track_freeze.py
│   └── api/
│       ├── sbpack.py
│       └── input.py
├── tools/
│   ├── workbuddy/  # WorkBuddy工具集
│   │   ├── build_sbpack.js
│   │   ├── verify_sbpack.js
│   │   └── audit_production.js
│   └── installer/  # 安装器脚本
│       ├── windows/
│       └── macos/
└── docs/
    ├── sbpack/  # SBPACK规范文档
    │   ├── knowledge_track.md
    │   ├── skill_track.md
    │   └── packaging.md
    └── references/  # 参考文档
        └── workbuddy_original/

frontend/
├── src/
│   ├── pages/
│   │   ├── SBPACKManager.tsx
│   │   ├── DualTrackProduction.tsx
│   │   └── ProductionAudit.tsx
│   └── components/
│       ├── KnowledgeTrackEditor.tsx
│       ├── SkillTrackEditor.tsx
│       ├── ProducerSnapshot.tsx
│       └── SBPACKVerifier.tsx
```

---

## 📊 优先级排序

### P0 - 立即开始（核心功能）
1. ✅ Skills系统基础架构（已完成）
2. □ SBPACK 2.0双轨蒸馏核心（Phase 1）
3. □ 多格式输入支持（Phase 2）

### P1 - 第二优先（完整性）
4. □ 生产者快照与审计（Phase 3）
5. □ 双轨冻结与关系（Phase 4）
6. □ SBPACK管理界面（Phase 6.1-6.2）

### P2 - 第三优先（扩展功能）
7. □ Obsidian导出（Phase 5）
8. □ 生产审计界面（Phase 6.3）

---

## 🔧 技术栈

### 后端
- **语言**: Python 3.9+
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **验证**: Pydantic
- **脚本工具**: Node.js (复用WorkBuddy的.cjs工具)

### 前端
- **框架**: React + TypeScript
- **UI**: Ant Design
- **状态管理**: React Query
- **编辑器**: Monaco Editor (代码编辑)

### 工具
- **打包**: 复用WorkBuddy的构建工具
- **校验**: SHA-256哈希
- **测试**: pytest + Jest

---

## 📝 实施步骤

### 第一步：文档迁移
1. 将14个MD规范文档复制到 `backend/docs/sbpack/`
2. 将installer文档复制到 `backend/docs/references/`
3. 创建索引文档 `SBPACK_INTEGRATION_INDEX.md`

### 第二步：工具迁移
1. 复制所有.cjs工具到 `backend/tools/workbuddy/`
2. 复制installer脚本到 `backend/tools/installer/`
3. 创建Python wrapper调用这些工具

### 第三步：数据模型
1. 创建SBPACK相关数据模型
2. 创建生产者快照模型
3. 创建轨道冻结模型
4. 运行数据库迁移

### 第四步：核心服务
1. 实现知识轨提取
2. 实现技能轨提取
3. 实现SBPACK构建器
4. 实现SBPACK验收器

### 第五步：API开发
1. SBPACK管理API
2. 输入处理API
3. 生产审计API

### 第六步：前端开发
1. SBPACK管理界面
2. 双轨生产界面
3. 审计查看界面

### 第七步：集成测试
1. 端到端蒸馏流程测试
2. SBPACK打包和验收测试
3. 多格式输入测试

---

## 🎯 预期成果

### 功能完整性
- ✅ 现有6类知识单元提取（已完成）
- □ SBPACK 2.0完整双轨蒸馏
- □ 多格式输入支持（PDF/DOCX/网页/视频）
- □ 生产审计和快照系统
- □ Obsidian插件导出

### 质量保证
- □ 遵循SBPACK 2.0协议
- □ 遵循仓颉v2.0.0标准
- □ 完整的验收清单
- □ SHA-256文件校验
- □ 生产者快照追溯

### 用户体验
- □ 一键蒸馏
- □ 可视化双轨编辑
- □ 自动审计报告
- □ 一键导出到Obsidian

---

## 📅 时间估算

| Phase | 任务数 | 预估工时 | 优先级 |
|-------|--------|----------|--------|
| Phase 1 | 4 | 40小时 | P0 |
| Phase 2 | 2 | 20小时 | P0 |
| Phase 3 | 2 | 16小时 | P1 |
| Phase 4 | 2 | 16小时 | P1 |
| Phase 5 | 2 | 12小时 | P2 |
| Phase 6 | 3 | 24小时 | P1-P2 |
| **总计** | **15** | **128小时** | - |

---

## 🚀 下一步行动

您希望我从哪个Phase开始？建议顺序：

1. **Phase 1.1** - 知识轨生产系统（增强现有extract_knowledge_points.py）
2. **Phase 1.2** - 技能轨生产系统（增强现有extract_cangjie_skills.py）
3. **Phase 1.3** - SBPACK打包系统（新建sbpack_builder.py）
4. **Phase 2.1** - 多格式输入支持（新建input_processor.py）

请告诉我从哪里开始？
