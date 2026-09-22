# FieldMind 程序统一整合方案

## 📊 当前状态分析

### 三个独立程序
1. **FieldMind Backend** (`/Users/alwan/FieldMind/backend/`)
   - Python FastAPI 后端服务
   - 知识蒸馏系统（11 阶段流水线）
   - SQLite 数据库
   - REST API 接口

2. **FieldMind Swift App** (`/Users/alwan/FieldMind/fieldmind/`)
   - Xcode 项目（Bundle ID: `-122.fieldmind`）
   - 基础 SwiftUI 界面
   - 已集成蒸馏服务和界面

3. **FieldMind Native** (`/Users/alwan/FieldMind/frontend/fieldmind-native/`)
   - Swift Package Manager 项目
   - 完整的功能模块（47 个页面）
   - Services、ViewModels、Components 完整架构

## 🎯 统一目标

**创建一个完整的原生 macOS 程序**，包含：
- 原生 Swift/SwiftUI 界面（单一 Xcode 项目）
- 内嵌 Python 后端服务（自动启动/停止）
- 集成 Obsidian 知识库功能
- 知识蒸馏系统
- 所有现有功能模块

## 🔄 整合策略

### 第一步：合并 Swift 项目
- 将 `fieldmind-native` 的所有模块迁移到主 Xcode 项目
- 保留完整的 Pages、Services、ViewModels、Components
- 统一 Bundle ID 和构建配置

### 第二步：内嵌后端服务
- 在 macOS app bundle 中包含 Python 后端
- 创建自动启动/停止机制
- 使用 LaunchAgent 管理后端生命周期

### 第三步：集成 Obsidian
- Clone Obsidian releases 仓库
- 提取核心功能（Markdown 渲染、插件系统、Graph View）
- 原生 Swift 实现或通过 WebView 集成

### 第四步：统一数据层
- 共享 SQLite 数据库
- 统一配置文件
- 统一日志系统

## 📦 最终结构

```
FieldMind.app/
├── Contents/
│   ├── MacOS/
│   │   └── FieldMind (Swift 主程序)
│   ├── Resources/
│   │   ├── backend/ (Python 后端)
│   │   │   ├── venv/
│   │   │   ├── app/
│   │   │   └── requirements.txt
│   │   ├── obsidian/ (Obsidian 核心)
│   │   └── data/
│   │       └── fieldmind.db
│   └── Info.plist
```

## 🚀 实施步骤

1. ✅ 分析现有三个项目结构
2. ⏳ 迁移 fieldmind-native 模块到主 Xcode 项目
3. ⏳ 配置后端自动启动机制
4. ⏳ Clone 并集成 Obsidian
5. ⏳ 统一测试和打包
6. ⏳ 创建单一启动入口

## 📝 下一步操作

继续执行整合...
