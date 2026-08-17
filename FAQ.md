# 常见问题解答 (FAQ)

本文档收集FieldMind使用过程中的常见问题及解决方案。

---

## 目录

- [一般问题](#一般问题)
- [安装和部署](#安装和部署)
- [使用问题](#使用问题)
- [性能问题](#性能问题)
- [故障排查](#故障排查)
- [开发问题](#开发问题)

---

## 一般问题

### Q1: FieldMind是什么？

**A**: FieldMind是一个智能化的田野调查知识管理系统，专为文化研究、民俗调查、社会学研究等领域设计。系统通过AI技术帮助研究者高效管理调研数据、挖掘文化价值、生成专业报告。

### Q2: FieldMind适合哪些人使用？

**A**: 
- 文化研究者和人类学家
- 民俗学者和社会学研究者
- 文旅规划和文创开发人员
- 政府文化部门工作人员
- 高校师生（文化、社会学等专业）

### Q3: 需要什么技术背景才能使用？

**A**: 不需要编程背景。系统提供友好的用户界面，只需基本的计算机操作能力即可。如需自行部署，建议有基础的Linux和Docker知识。

### Q4: FieldMind是开源的吗？

**A**: 是的，FieldMind采用MIT许可证开源。你可以自由使用、修改和分发。

### Q5: 支持哪些语言？

**A**: 目前主要支持中文，英文支持正在开发中。系统的分词和语义分析针对中文优化。

### Q6: 数据安全吗？

**A**: 
- 所有数据本地存储，不上传云端
- 支持加密存储
- 用户权限严格控制
- 定期自动备份
- 支持私有部署

---

## 安装和部署

### Q7: 支持哪些操作系统？

**A**: 
- **后端**: Linux (Ubuntu 20.04+推荐), macOS 12+, Windows 10+
- **前端**: 任何支持现代浏览器的系统
- **推荐**: Linux服务器用于生产部署

### Q8: 最低硬件要求是什么？

**A**:
- **最低**: 2核CPU, 4GB内存, 20GB磁盘
- **推荐**: 4核CPU, 8GB内存, 100GB SSD
- **生产**: 8核CPU, 16GB内存, 500GB SSD

### Q9: 如何快速开始？

**A**:
```bash
# 克隆项目
git clone https://github.com/your-org/FieldMind-Rebuild.git
cd FieldMind-Rebuild

# 使用Docker快速启动
./deploy.sh development

# 访问
http://localhost:8000/docs
```

详见 [部署指南](DEPLOYMENT_GUIDE.md)

### Q10: Docker部署失败怎么办？

**A**: 常见原因和解决方法：

1. **端口被占用**
   ```bash
   # 检查端口
   lsof -i :8000
   # 修改端口或停止占用进程
   ```

2. **权限不足**
   ```bash
   # 添加当前用户到docker组
   sudo usermod -aG docker $USER
   # 重新登录
   ```

3. **磁盘空间不足**
   ```bash
   # 清理Docker缓存
   docker system prune -a
   ```

### Q11: 如何配置生产环境？

**A**: 
1. 复制环境配置：`cp .env.example .env.production`
2. 修改关键配置：
   - `SECRET_KEY` - 使用随机32字符
   - `DATABASE_URL` - 配置PostgreSQL
   - `CORS_ORIGINS` - 设置允许的域名
3. 使用生产部署脚本：`./deploy.sh production`

详见 [部署指南](DEPLOYMENT_GUIDE.md)

### Q12: 如何升级到新版本？

**A**:
```bash
# 1. 备份数据
cp data/fieldmind.db backups/

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
pip install -r requirements.txt

# 4. 运行数据库迁移
alembic upgrade head

# 5. 重启服务
docker-compose restart
```

---

## 使用问题

### Q13: 支持哪些文档格式？

**A**:
- **文本**: PDF, DOC, DOCX, TXT, MD
- **表格**: XLS, XLSX, CSV
- **音频**: MP3, WAV, M4A (需转录)
- **视频**: MP4, AVI, MOV (需转录)

### Q14: 单个文件大小限制是多少？

**A**: 默认100MB。可以在配置文件中修改：
```python
# app/config.py
MAX_UPLOAD_SIZE_MB = 200  # 修改为200MB
```

### Q15: 文档处理需要多长时间？

**A**: 取决于文档大小：
- 小文档 (<5MB): 10-30秒
- 中等文档 (5-20MB): 30秒-2分钟
- 大文档 (20-100MB): 2-5分钟

处理包括文本提取、切分、向量化和索引建立。

### Q16: 为什么搜索结果不准确？

**A**: 可能原因：
1. **文档数量太少** - 建议至少上传5个相关文档
2. **关键词太宽泛** - 使用更具体的2-4字词
3. **文档未处理完成** - 等待所有文档处理完成

改进方法：
- 上传更多高质量文档
- 使用更精确的关键词
- 查看"相关词推荐"

### Q17: 分析结果为什么没有来源？

**A**: 可能原因：
1. AI推理得出的结论（非直接引用）
2. 文档向量化未完成
3. 相关度阈值设置过高

解决方法：
- 等待所有文档处理完成
- 重新运行分析
- 上传更多相关文档

### Q18: 如何提高文创分析质量？

**A**:
1. **上传高质量文档** - 调研笔记、访谈记录、文献资料
2. **具体的问题描述** - "如何开发山歌文创？" 比 "文创建议？" 更好
3. **多角度分析** - 从不同角度提问，综合结果
4. **利用对话功能** - 连续提问深入探讨

### Q19: 提案生成需要多长时间？

**A**:
- 小项目 (<10文档): 30秒-1分钟
- 中项目 (10-50文档): 1-2分钟  
- 大项目 (50+文档): 2-5分钟

时间取决于项目规模和分析结果数量。

### Q20: 提案内容不满意怎么办？

**A**:
1. **在线编辑** - 点击"编辑"按钮修改内容
2. **重新生成** - 选择不同的提案类型
3. **手动调整** - 导出后使用Word/Pages编辑
4. **补充文档** - 上传更多相关材料后重新生成

---

## 性能问题

### Q21: 系统响应很慢怎么办？

**A**: 检查以下方面：

1. **系统资源**
   ```bash
   # 查看资源使用
   docker stats
   
   # 查看日志
   docker logs fieldmind-backend
   ```

2. **数据库优化**
   ```bash
   # SQLite vacuum
   sqlite3 data/fieldmind.db "VACUUM;"
   ```

3. **缓存配置**
   ```python
   # 启用Redis缓存
   CACHE_BACKEND=redis
   REDIS_HOST=redis
   ```

### Q22: 如何优化搜索性能？

**A**:
1. **启用缓存** - 配置Redis缓存
2. **定期清理** - 删除无用文档和分析结果
3. **数据库索引** - 系统自动创建，无需手动操作
4. **增加硬件** - 提升CPU和内存

### Q23: 大量文档上传时系统卡顿？

**A**:
1. **分批上传** - 每批10-20个文档
2. **错峰处理** - 避免高峰时段
3. **增加workers** - 修改配置增加处理worker数量
4. **使用队列** - 启用Celery异步处理（高级功能）

### Q24: 如何监控系统性能？

**A**:
```bash
# 启动监控栈
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# 访问监控面板
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

详见 [监控指南](MONITORING_GUIDE.md)

---

## 故障排查

### Q25: 登录后显示403错误？

**A**: 权限不足。检查：
1. 用户角色是否正确
2. 是否有访问该资源的权限
3. Token是否过期

解决：
```bash
# 重新登录获取新token
# 或联系管理员分配权限
```

### Q26: 文档上传后状态一直是"处理中"？

**A**: 可能原因：
1. 文件格式不支持
2. 文件损坏
3. 处理进程崩溃

排查：
```bash
# 查看日志
docker logs fieldmind-backend | grep ERROR

# 重启服务
docker-compose restart backend
```

### Q27: 数据库连接错误？

**A**:
```bash
# 检查数据库文件
ls -lh data/fieldmind.db

# 检查权限
chmod 644 data/fieldmind.db

# 测试连接
sqlite3 data/fieldmind.db "SELECT 1"
```

### Q28: API返回500错误？

**A**:
1. **查看日志**
   ```bash
   docker logs fieldmind-backend --tail=100
   ```

2. **检查配置**
   ```bash
   cat .env | grep -v "^#"
   ```

3. **重启服务**
   ```bash
   docker-compose restart
   ```

4. **如果持续出现，提交Issue**

### Q29: 忘记管理员密码？

**A**:
```bash
# 使用管理脚本重置
python reset_admin_password.py

# 或直接修改数据库（需要bcrypt hash）
sqlite3 data/fieldmind.db
UPDATE users SET password_hash='...' WHERE username='admin';
```

### Q30: 如何清理所有数据重新开始？

**A**:
```bash
# ⚠️ 警告：此操作不可恢复

# 停止服务
docker-compose down

# 删除数据库
rm data/fieldmind.db

# 重新初始化
alembic upgrade head

# 启动服务
docker-compose up -d
```

---

## 开发问题

### Q31: 如何添加新的API端点？

**A**:
```python
# 1. 创建路由文件
# app/api/my_module.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-module", tags=["我的模块"])

@router.get("/")
async def get_items():
    return {"items": []}

# 2. 注册路由
# app/main.py
from app.api import my_module
app.include_router(my_module.router, prefix="/api")
```

### Q32: 如何添加数据库表？

**A**:
```python
# 1. 定义Model
# app/models/my_model.py
class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

# 2. 生成迁移
alembic revision --autogenerate -m "add my_table"

# 3. 应用迁移
alembic upgrade head
```

### Q33: 如何运行测试？

**A**:
```bash
# 所有测试
pytest tests/ -v

# 特定测试
pytest tests/test_projects.py::test_create_project -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Q34: 如何调试代码？

**A**:
```python
# 1. 添加断点
import pdb; pdb.set_trace()

# 2. 或使用logging
from app.core.logging import logger
logger.debug(f"Variable value: {variable}")

# 3. 查看日志
tail -f /tmp/fieldmind_logs/fieldmind_$(date +%Y-%m-%d).log
```

### Q35: 如何贡献代码？

**A**: 
1. Fork项目
2. 创建分支：`git checkout -b feature/my-feature`
3. 编写代码和测试
4. 提交：`git commit -m 'feat: add my feature'`
5. 推送：`git push origin feature/my-feature`
6. 创建Pull Request

详见 [贡献指南](CONTRIBUTING.md)

---

## 更多资源

### 📚 文档

- [用户手册](USER_MANUAL.md)
- [API参考](API_REFERENCE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [监控指南](MONITORING_GUIDE.md)

### 🔗 链接

- **GitHub**: https://github.com/your-org/FieldMind-Rebuild
- **文档站**: https://docs.fieldmind.com
- **在线Demo**: https://demo.fieldmind.com

### 💬 获取帮助

- **GitHub Issues**: 报告Bug和功能建议
- **GitHub Discussions**: 提问和讨论
- **Email**: support@fieldmind.example.com

### 🤝 社区

- **Twitter**: [@FieldMindAI](https://twitter.com/fieldmindai)
- **博客**: https://blog.fieldmind.com
- **Newsletter**: 订阅最新动态

---

**文档版本**: 1.0.0  
**最后更新**: 2026-08-02  

如果你的问题未在此列出，请访问 [GitHub Issues](https://github.com/your-org/FieldMind-Rebuild/issues) 提问。
