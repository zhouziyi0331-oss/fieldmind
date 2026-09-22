# 🎯 FieldMind 快速参考

## ✅ 项目已完成整合！

**位置**: `~/FieldMind/` (6.8GB)  
**状态**: 完整可用，前后端正常

---

## 🚀 立即使用

### 启动 FieldMind
```bash
cd ~/FieldMind
./start.sh
```

### 停止 FieldMind
```bash
cd ~/FieldMind
./stop.sh
```

### 仅启动应用
```bash
open ~/FieldMind/FieldMind.app
```

---

## 📁 项目结构

```
~/FieldMind/
├── backend/src/app/     → 后端代码
├── frontend/web/        → Web 前端
├── frontend/desktop/    → 桌面前端
├── docs/               → 163 个文档（已分类）
├── scripts/            → 所有脚本（已分类）
├── FieldMind.app       → macOS 应用（已修复）
├── start.sh            → 一键启动
└── README.md           → 使用说明
```

---

## 🧹 清理旧文件

**先测试**：确保项目正常运行
```bash
cd ~/FieldMind && ./start.sh
```

**再清理**：删除旧的重复文件
```bash
cd ~ && ./cleanup_old_files.sh
```

会删除：
- `/Users/alwan/app/` (旧后端)
- `/Users/alwan/FieldMind-Rebuild/` (重复项目)
- 110+ 散落的 .md 文件
- 散落的脚本文件
- 桌面上的 FieldMind_*.md

---

## 📖 文档位置

- **用户手册**: `~/FieldMind/docs/user-guides/`
- **API 文档**: `~/FieldMind/docs/api/`
- **架构设计**: `~/FieldMind/docs/architecture/`
- **部署指南**: `~/FieldMind/docs/deployment/`
- **完整报告**: `~/FieldMind/MERGE_COMPLETE_REPORT.md`

---

## 🆘 问题排查

### 应用打不开
```bash
~/fix_fieldmind_app.sh
```

### 后端启动失败
```bash
cd ~/FieldMind
source venv/bin/activate
cd backend/src
python -m app.main
```

### 查看日志
```bash
tail -f ~/FieldMind/data/logs/app.log
```

---

## ✅ 下一步

1. [ ] 测试应用: `cd ~/FieldMind && ./start.sh`
2. [ ] 验证功能正常
3. [ ] 清理旧文件: `~/cleanup_old_files.sh`

---

**现在你的电脑只有一个完整的 FieldMind 项目！** 🎉
