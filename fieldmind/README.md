# FieldMind - 智能知识管理系统

## 📁 项目结构

```
FieldMind/
├── backend/                # 后端服务
│   └── src/               # Python 后端代码
│       └── app/           # 应用核心
├── frontend/              # 前端应用
│   ├── web/              # Web 版本
│   ├── desktop/          # 桌面版本
│   └── ios/              # iOS 版本
├── docs/                  # 项目文档
│   ├── architecture/     # 架构设计
│   ├── api/             # API 文档
│   ├── deployment/      # 部署指南
│   ├── development/     # 开发文档
│   ├── user-guides/     # 用户指南
│   ├── reports/         # 项目报告
│   ├── phases/          # 开发阶段文档
│   └── daily/           # 每日工作记录
├── scripts/              # 工具脚本
│   ├── install/         # 安装脚本
│   ├── deploy/          # 部署脚本
│   ├── test/            # 测试脚本
│   └── maintenance/     # 维护脚本
├── config/               # 配置文件
├── data/                 # 数据目录
├── external-libs/        # 外部集成库
├── FieldMind.app         # macOS 桌面应用
└── venv/                 # Python 虚拟环境

## 🚀 快速启动

### 1. 启动后端服务

```bash
cd ~/FieldMind
source venv/bin/activate
cd backend/src
python -m app.main
```

后端将在 `http://127.0.0.1:8000` 运行

### 2. 启动 Web 前端

```bash
cd ~/FieldMind/frontend/web
npm install
npm run dev
```

Web 前端将在 `http://localhost:3000` 运行

### 3. 启动桌面应用

```bash
open ~/FieldMind/FieldMind.app
```

或直接双击 `FieldMind.app`

## 📚 文档

- **用户手册**: [docs/user-guides/](docs/user-guides/)
- **API 文档**: [docs/api/](docs/api/)
- **部署指南**: [docs/deployment/](docs/deployment/)
- **开发文档**: [docs/development/](docs/development/)
- **系统架构**: [docs/architecture/](docs/architecture/)

## 🔧 开发

### 安装依赖

```bash
# Python 后端
cd backend/src
pip install -r requirements.txt

# Web 前端
cd frontend/web
npm install

# 桌面应用
cd frontend/desktop
npm install
```

### 运行测试

```bash
# 后端测试
cd backend/src
pytest

# 前端测试
cd frontend/web
npm test
```

## 📦 部署

详见 [docs/deployment/](docs/deployment/)

## 🆘 问题排查

### 后端无法启动
```bash
# 检查日志
tail -f data/logs/app.log

# 检查服务状态
curl http://127.0.0.1:8000/health
```

### 应用无法打开
```bash
# 重新签名
codesign --force --deep --sign - FieldMind.app

# 查看日志
log show --predicate 'process == "FieldMind"' --last 5m
```

## 📞 联系方式

项目文档: ~/FieldMind/docs/
