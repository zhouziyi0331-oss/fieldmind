# 🎯 FieldMind 应用启动指南

## 当前状态

你有**三个**不同的FieldMind应用：

### 1. WebView原生应用 (你刚才打开的)
**位置**: `/Users/alwan/FieldMind.app`
**类型**: 原生macOS应用，使用WebView加载Web界面
**状态**: ✅ 已修复 - 现在可以打开了

### 2. SwiftUI桌面应用
**位置**: `/Users/alwan/FieldMind-Rebuild/fieldmind-desktop`
**类型**: 纯SwiftUI原生应用
**状态**: ⏳ 需要编译

### 3. Web应用 (React)
**位置**: `/Users/alwan/FieldMind-Rebuild/fieldmind-web`
**类型**: React + TypeScript Web应用
**状态**: ⏳ 需要启动开发服务器

---

## 🚀 启动方案

### 方案A: 使用修复后的原生应用 (最快)

1. **启动后端** (如果还没启动):
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **打开应用**:
- 双击 `/Users/alwan/FieldMind.app`
- 应该能看到启动页面
- 点击"打开Web应用"按钮

3. **启动Web前端**:
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-web
npm run dev
```

4. **访问**:
- 浏览器会自动打开 http://localhost:5173
- 或在原生应用中点击按钮跳转

---

### 方案B: 使用SwiftUI桌面应用

1. **启动后端** (同上)

2. **编译并运行SwiftUI应用**:
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-desktop
swift build
swift run
```

或者在Xcode中打开并运行。

---

### 方案C: 纯Web浏览器使用 (推荐用于开发)

1. **启动后端** (同上)

2. **启动Web前端**:
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-web
npm install  # 首次运行
npm run dev
```

3. **打开浏览器**:
- 访问 http://localhost:5173
- 使用Chrome/Firefox等现代浏览器

---

## 📋 完整启动流程 (推荐)

### 终端1 - 启动后端:
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 -m uvicorn app.main:app --reload
```

看到这个输出说明成功:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 终端2 - 启动前端:
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-web
npm run dev
```

看到这个输出说明成功:
```
  VITE v5.3.4  ready in 500 ms

  ➜  Local:   http://localhost:5173/
```

### 浏览器:
打开 http://localhost:5173

---

## 🎨 现在可以做什么

### 1. 注册/登录
- 用户名: `test_desktop_user`
- 密码: `test123456`
- 或注册新账号

### 2. 创建项目
- 点击"新建项目"
- 填写项目名称和描述
- 提交创建

### 3. 上传文档
- 进入项目
- 点击"材料管理"或"导入资料"
- 选择本地文件
- 上传

### 4. 使用功能
- **关键词搜索**: 在文档中搜索关键词
- **文创分析**: AI分析文创机会
- **AI对话**: 基于材料的智能问答
- **知识图谱**: 可视化知识关系
- **时间线**: 事件时间线展示

---

## ⚠️ 常见问题

### Q1: FieldMind.app打不开
**解决**: 已修复！重新打开应该可以了

### Q2: 后端连接失败
**检查**:
```bash
# 测试后端是否运行
curl http://localhost:8000/health

# 如果失败，启动后端
cd fieldmind-backend
uvicorn app.main:app --reload
```

### Q3: Web前端打不开
**检查**:
```bash
# 进入前端目录
cd fieldmind-web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Q4: 上传文档没反应
**原因**: 可能后端未启动或API地址错误

**检查**:
1. 后端是否运行: `curl http://localhost:8000/health`
2. 浏览器控制台是否有错误
3. 网络请求是否发送成功

---

## 🎯 推荐使用方案

**开发/测试环境**: 
- ✅ 使用方案C (纯Web浏览器)
- 原因: 开发工具完善，调试方便

**演示/使用环境**:
- ✅ 使用方案A (原生应用)
- 原因: 看起来更专业，用户体验好

---

## 📝 下一步

1. ✅ 后端已启动 (http://localhost:8000)
2. ⏳ 启动Web前端 (http://localhost:5173)
3. ⏳ 测试上传功能
4. ⏳ 验证所有功能

现在你可以：
- 重新打开 `FieldMind.app` 看看启动页面
- 或者启动Web前端，直接在浏览器中使用

需要我帮你启动Web前端吗？
