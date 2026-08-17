# 贡献指南

感谢你考虑为FieldMind做出贡献！本文档提供贡献代码、报告问题和提出建议的指南。

---

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request流程](#pull-request流程)
- [问题报告](#问题报告)

---

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性别化的语言或图像，以及不受欢迎的性关注
- 挑衅、侮辱性/贬损性评论，人身攻击或政治攻击
- 公开或私下骚扰
- 未经明确许可，发布他人的私人信息
- 其他在专业环境中可能被认为不适当的行为

---

## 如何贡献

### 代码贡献

1. **Fork 项目**
2. **创建分支** (`git checkout -b feature/amazing-feature`)
3. **编写代码**
4. **编写测试**
5. **提交更改** (`git commit -m 'Add amazing feature'`)
6. **推送分支** (`git push origin feature/amazing-feature`)
7. **创建 Pull Request**

### 文档贡献

文档改进同样重要：

- 修正错别字和语法错误
- 改进说明的清晰度
- 添加缺失的信息
- 翻译文档到其他语言

### 报告Bug

发现Bug？请：

1. 检查是否已有相关Issue
2. 创建新Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 系统环境信息
   - 相关截图或日志

### 功能建议

有好想法？我们期待听到：

1. 创建Feature Request Issue
2. 描述功能用途和价值
3. 提供使用场景示例
4. 说明实现思路（可选）

---

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+ (如果开发前端)
- Docker 20.10+
- Git 2.30+

### 克隆项目

```bash
git clone https://github.com/your-org/FieldMind-Rebuild.git
cd FieldMind-Rebuild
```

### Backend开发环境

```bash
cd fieldmind-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_projects.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

### 代码检查

```bash
# 代码格式化
black app/
isort app/

# 类型检查
mypy app/

# 代码质量检查
flake8 app/
pylint app/
```

---

## 代码规范

### Python代码规范

遵循 [PEP 8](https://pep8.org/) 规范：

**命名约定**:
```python
# 类名：PascalCase
class ProjectService:
    pass

# 函数/方法：snake_case
def create_project():
    pass

# 常量：UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 100 * 1024 * 1024

# 私有成员：前缀单下划线
def _internal_method():
    pass
```

**文档字符串**:
```python
def create_project(name: str, description: str) -> Project:
    """
    创建新项目

    Args:
        name: 项目名称
        description: 项目描述

    Returns:
        Project: 创建的项目对象

    Raises:
        ValueError: 如果名称为空
    """
    pass
```

**类型注解**:
```python
from typing import List, Optional

def get_projects(
    user_id: int,
    limit: int = 20
) -> List[Project]:
    pass
```

### API设计规范

**RESTful设计**:
```python
# 资源命名使用复数
GET    /api/projects           # 获取列表
POST   /api/projects           # 创建
GET    /api/projects/{id}      # 获取单个
PUT    /api/projects/{id}      # 更新
DELETE /api/projects/{id}      # 删除

# 嵌套资源
GET    /api/projects/{id}/documents
POST   /api/projects/{id}/documents
```

**响应格式**:
```python
# 成功响应
{
  "data": {...},
  "message": "Success"
}

# 错误响应
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-08-02T10:00:00Z"
}
```

### 数据库规范

**Model定义**:
```python
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关系
    documents = relationship("Document", back_populates="project")
```

**查询优化**:
```python
# 使用 joinedload 避免 N+1 查询
projects = db.query(Project)\
    .options(joinedload(Project.documents))\
    .all()

# 使用分页
projects = db.query(Project)\
    .offset(skip)\
    .limit(limit)\
    .all()
```

---

## 提交规范

### Commit Message格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(projects): 添加项目搜索功能

- 实现基于名称的模糊搜索
- 添加项目类型筛选
- 优化查询性能

Closes #123
```

```
fix(auth): 修复token过期后无法刷新的问题

token过期时间从1小时改为30分钟，并添加自动刷新机制

Fixes #456
```

---

## Pull Request流程

### 创建PR

1. **确保代码质量**
   - 通过所有测试
   - 代码格式化
   - 无linter警告

2. **编写清晰的PR描述**
   ```markdown
   ## 变更内容
   - 添加了xxx功能
   - 修复了xxx问题
   
   ## 测试
   - [ ] 单元测试通过
   - [ ] 集成测试通过
   - [ ] 手动测试验证
   
   ## 截图（如适用）
   ![screenshot](url)
   
   ## 相关Issue
   Closes #123
   ```

3. **选择合适的标签**
   - `enhancement`: 新功能
   - `bug`: Bug修复
   - `documentation`: 文档
   - `performance`: 性能优化

### Code Review

**作为作者**:
- 响应reviewer的评论
- 根据反馈修改代码
- 保持耐心和开放心态

**作为reviewer**:
- 提供建设性反馈
- 解释"为什么"而不仅是"是什么"
- 认可好的实践
- 及时回复

### 合并要求

PR必须满足：

- [ ] 所有CI检查通过
- [ ] 至少1个approved review
- [ ] 无merge冲突
- [ ] 更新了相关文档
- [ ] 添加了必要的测试

---

## 问题报告

### Bug报告模板

```markdown
**描述问题**
清晰简洁地描述bug。

**复现步骤**
1. 访问 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

**期望行为**
应该发生什么。

**实际行为**
实际发生了什么。

**截图**
如果适用，添加截图。

**环境信息**
- OS: [e.g. macOS 13.0]
- Browser: [e.g. Chrome 120]
- Version: [e.g. 1.0.0]

**附加信息**
其他相关信息。
```

### Feature Request模板

```markdown
**功能描述**
你希望添加什么功能？

**问题背景**
这个功能解决什么问题？

**建议方案**
你希望如何实现这个功能？

**替代方案**
你考虑过哪些替代方案？

**附加信息**
其他相关信息或截图。
```

---

## 开发工作流

### 分支策略

```
main          生产分支，保护分支
├── develop   开发分支
│   ├── feature/xxx    功能分支
│   ├── bugfix/xxx     bug修复分支
│   └── hotfix/xxx     紧急修复分支
```

### 版本发布

1. 从 `develop` 创建 `release/x.x.x` 分支
2. 更新版本号
3. 更新 CHANGELOG.md
4. 测试验证
5. 合并到 `main` 和 `develop`
6. 打tag: `git tag -a v1.0.0 -m "Release 1.0.0"`

---

## 社区

### 获取帮助

- **文档**: [在线文档](https://docs.fieldmind.com)
- **GitHub Discussions**: 讨论功能和想法
- **GitHub Issues**: 报告bug
- **Email**: dev@fieldmind.example.com

### 保持联系

- GitHub: [@FieldMind](https://github.com/fieldmind)
- Twitter: [@FieldMindAI](https://twitter.com/fieldmindai)
- 博客: https://blog.fieldmind.com

---

## 许可证

贡献代码即表示你同意将代码按照项目的[MIT License](LICENSE)发布。

---

## 致谢

感谢所有贡献者让FieldMind变得更好！

---

**最后更新**: 2026-08-02
