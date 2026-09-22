# FieldMind Backend 测试文档

## 测试概述

本项目使用 pytest 作为测试框架，包含了完整的 API 单元测试套件。

## 测试结构

```
tests/
├── conftest.py          # pytest 配置和全局 fixtures
├── api/
│   ├── test_auth.py      # 认证 API 测试 (12个测试)
│   ├── test_projects.py  # 项目 API 测试 (9个测试)
│   ├── test_documents.py # 文档 API 测试 (11个测试)
│   └── test_chat.py      # 聊天 API 测试 (14个测试)
└── README.md            # 本文档
```

## 运行测试

### 运行所有测试
```bash
python3 -m pytest tests/ -v
```

### 运行特定测试文件
```bash
python3 -m pytest tests/api/test_auth.py -v
python3 -m pytest tests/api/test_projects.py -v
python3 -m pytest tests/api/test_documents.py -v
python3 -m pytest tests/api/test_chat.py -v
```

### 运行特定测试
```bash
python3 -m pytest tests/api/test_auth.py::TestAuthAPI::test_login_success -v
```

### 查看详细输出
```bash
python3 -m pytest tests/ -v -s
```

### 显示代码覆盖率
```bash
python3 -m pytest tests/ --cov=app --cov-report=html
```

## 测试覆盖

### 认证 API (test_auth.py) - 12个测试

#### 用户注册
- ✅ `test_register_user_success` - 成功注册用户
- ✅ `test_register_duplicate_email` - 重复邮箱注册失败
- ✅ `test_register_duplicate_username` - 重复用户名注册失败
- ✅ `test_register_invalid_email` - 无效邮箱格式
- ✅ `test_register_short_password` - 密码过短

#### 用户登录
- ✅ `test_login_success` - 成功登录
- ✅ `test_login_wrong_password` - 错误密码登录失败
- ✅ `test_login_nonexistent_user` - 不存在的用户登录失败

#### Token 管理
- ✅ `test_refresh_token` - 刷新 access token

#### 用户信息
- ✅ `test_get_current_user` - 获取当前用户信息
- ✅ `test_get_current_user_no_token` - 无 token 获取用户信息失败
- ✅ `test_get_current_user_invalid_token` - 无效 token

### 项目 API (test_projects.py) - 9个测试

#### 项目创建
- ✅ `test_create_project_success` - 成功创建项目
- ✅ `test_create_project_no_auth` - 未认证创建项目失败
- ✅ `test_create_project_missing_name` - 缺少项目名称

#### 项目查询
- ✅ `test_list_projects` - 获取项目列表
- ✅ `test_get_project_by_id` - 根据ID获取项目
- ✅ `test_get_project_not_found` - 获取不存在的项目

#### 项目更新和删除
- ✅ `test_update_project` - 更新项目
- ✅ `test_delete_project` - 删除项目
- ✅ `test_delete_project_not_found` - 删除不存在的项目

### 文档 API (test_documents.py) - 11个测试

#### 文档上传
- ✅ `test_upload_document_success` - 成功上传文档
- ✅ `test_upload_document_without_auth` - 未认证上传文档
- ✅ `test_upload_document_project_not_found` - 上传到不存在的项目
- ✅ `test_upload_different_file_types` - 上传不同类型的文件 (PDF, DOCX, MD等)

#### 文档查询
- ✅ `test_list_project_documents` - 获取项目文档列表
- ✅ `test_list_documents_with_status_filter` - 使用状态过滤文档列表
- ✅ `test_list_documents_pagination` - 文档列表分页
- ✅ `test_get_document_by_id` - 根据ID获取文档详情
- ✅ `test_get_document_not_found` - 获取不存在的文档

#### 文档删除
- ✅ `test_delete_document` - 删除文档
- ✅ `test_delete_document_not_found` - 删除不存在的文档

### 聊天 API (test_chat.py) - 14个测试

#### 会话管理
- ✅ `test_create_chat_session_success` - 成功创建对话会话
- ✅ `test_create_chat_session_project_not_found` - 创建会话时项目不存在
- ✅ `test_get_chat_session` - 获取会话详情
- ✅ `test_get_chat_session_not_found` - 获取不存在的会话
- ✅ `test_list_project_sessions` - 获取项目的对话会话列表
- ✅ `test_session_pagination` - 会话列表分页
- ✅ `test_session_with_config` - 创建带配置的会话
- ✅ `test_delete_session` - 删除对话会话
- ✅ `test_delete_session_not_found` - 删除不存在的会话

#### 消息管理
- ✅ `test_send_message_success` - 发送消息并获取AI响应
- ✅ `test_send_message_session_not_found` - 向不存在的会话发送消息
- ✅ `test_get_session_messages` - 获取会话的所有消息
- ✅ `test_get_messages_session_not_found` - 获取不存在会话的消息
- ✅ `test_message_pagination` - 消息列表分页

## 测试配置 (conftest.py)

### 测试数据库
测试使用独立的 SQLite 临时文件数据库，每个测试函数运行时：
1. 创建新的数据库表
2. 运行测试
3. 清理并删除所有表

### 全局 Fixtures

#### `client`
创建 FastAPI TestClient，用于模拟 HTTP 请求

#### `test_user`
通过 API 注册一个测试用户
- 邮箱: test@example.com
- 用户名: testuser
- 密码: testpassword123

#### `auth_token`
获取 test_user 的 JWT access token

#### `auth_headers`
返回包含 Bearer token 的请求头字典

## 依赖包

测试需要以下依赖：
```bash
pip3 install pytest pytest-asyncio httpx
```

## 已知问题

### Pydantic 弃用警告
当前版本使用 Pydantic v2，但代码中还有一些 v1 的语法，会产生弃用警告。这些不影响功能，但需要在未来版本中迁移到 Pydantic v2 语法。

### FastAPI 事件弃用
`@app.on_event` 已被弃用，建议迁移到 lifespan 事件处理器。

## 测试统计

**总计: 46个测试全部通过 ✅**
- 认证 API: 12个测试
- 项目 API: 9个测试
- 文档 API: 11个测试
- 聊天 API: 14个测试

## 下一步

待添加的测试：
- [ ] 知识图谱 API 测试
- [ ] 时间线 API 测试
- [ ] 集成测试
- [ ] 性能测试

## 测试最佳实践

1. **隔离性**: 每个测试独立运行，不依赖其他测试
2. **幂等性**: 测试可以重复运行，结果一致
3. **清理**: 测试结束后自动清理数据
4. **命名**: 测试函数名清晰描述测试内容
5. **断言**: 使用明确的断言消息

## 持续集成

可以将测试集成到 CI/CD 流程：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
      - name: Run tests
        run: pytest tests/ -v
```
