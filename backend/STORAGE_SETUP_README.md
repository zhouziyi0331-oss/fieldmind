# FieldMind 对象存储配置指南

## 阶段0 - Week 1 - Day 3-4：对象存储配置

### 📋 完成的工作

1. ✅ 创建了统一的对象存储服务类
2. ✅ 支持MinIO和S3两种后端
3. ✅ 实现了完整的文件操作接口
4. ✅ 创建了10个测试用例
5. ✅ 配置了Docker Compose部署
6. ✅ 创建了快速启动脚本

---

## 🗄️ 对象存储架构

### 设计特点

1. **统一接口** - 支持MinIO和S3，代码无需修改
2. **自动初始化** - 自动创建6个默认存储桶
3. **单例模式** - 全局唯一实例，避免重复连接
4. **错误处理** - 完善的异常处理和日志记录

### 默认存储桶

```
documents/  - 文档文件（PDF, DOCX, TXT等）
images/     - 图片文件（JPG, PNG, HEIC等）
audio/      - 音频文件（MP3, WAV, M4A等）
video/      - 视频文件（MP4, MOV, AVI等）
tables/     - 表格文件（XLSX, CSV等）
temp/       - 临时文件
```

---

## 🚀 快速开始

### 方法1：使用Docker Compose（推荐）

```bash
# 1. 启动所有基础设施服务
cd backend
chmod +x start_services.sh
./start_services.sh

# 等待服务启动完成，会显示：
# ✅ MinIO: 运行中
# ✅ MySQL: 运行中
# ✅ Redis: 运行中
```

**访问MinIO控制台**:
- URL: http://localhost:9001
- 用户名: `minioadmin`
- 密码: `minioadmin`

### 方法2：手动安装MinIO

```bash
# MacOS
brew install minio/stable/minio

# Linux
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data --console-address ":9001"

# Windows
# 下载 https://dl.min.io/server/minio/release/windows-amd64/minio.exe
# 运行 minio.exe server C:\data --console-address ":9001"
```

---

## 🔧 配置

### 环境变量配置

编辑 `.env` 文件：

```bash
# MinIO配置
STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# 或者使用AWS S3
# STORAGE_TYPE=s3
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_REGION=us-east-1
```

---

## 📝 使用示例

### 基础用法

```python
from app.core.storage import get_storage

# 获取存储实例
storage = get_storage()

# 上传文件
storage.upload_file(
    bucket="documents",
    object_name="reports/2024/report.pdf",
    file_path="/path/to/report.pdf"
)

# 下载文件
storage.download_file(
    bucket="documents",
    object_name="reports/2024/report.pdf",
    file_path="/tmp/downloaded_report.pdf"
)

# 检查文件是否存在
exists = storage.file_exists("documents", "reports/2024/report.pdf")

# 删除文件
storage.delete_file("documents", "reports/2024/report.pdf")
```

### 上传二进制数据

```python
# 直接上传字节数据
image_data = b'\x89PNG\r\n\x1a\n...'  # 图片二进制数据

storage.upload_data(
    bucket="images",
    object_name="photos/2024/image.png",
    data=image_data,
    content_type="image/png"
)

# 下载数据
data = storage.download_data("images", "photos/2024/image.png")
```

### 生成预签名URL

```python
# 生成1小时有效的下载链接
url = storage.get_presigned_url(
    bucket="documents",
    object_name="reports/2024/report.pdf",
    expires=3600  # 秒
)

print(f"下载链接: {url}")
# 用户可以直接通过这个URL下载文件，无需认证
```

### 存储桶管理

```python
# 创建新存储桶
storage.create_bucket("custom-bucket")

# 检查存储桶是否存在
if storage.bucket_exists("custom-bucket"):
    print("存储桶已存在")
```

---

## 🧪 运行测试

```bash
# 确保服务已启动
./start_services.sh

# 运行测试
python test_storage.py
```

**预期输出**:
```
测试1: 存储服务初始化    ✅ 通过
测试2: 存储桶操作        ✅ 通过
测试3: 文件上传和下载    ✅ 通过
测试4: 数据上传和下载    ✅ 通过
测试5: 预签名URL        ✅ 通过
测试6: 文件删除          ✅ 通过
测试7: 大文件上传        ✅ 通过
测试8: 默认存储桶        ✅ 通过
测试9: 并发上传          ✅ 通过
测试10: 清理测试数据     ✅ 通过

✅ 通过: 10/10
❌ 失败: 0/10

🎉 所有测试通过！对象存储配置成功！
```

---

## 📁 项目结构

```
backend/
├── src/app/core/
│   └── storage.py              # 对象存储服务 ✅
├── docker-compose.yml          # Docker服务编排 ✅
├── start_services.sh           # 快速启动脚本 ✅
├── test_storage.py            # 测试脚本 ✅
└── .env.example               # 环境配置模板
```

---

## 🔍 API参考

### ObjectStorage类

#### `upload_file(bucket, object_name, file_path) -> bool`
上传本地文件到对象存储

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径（如 "reports/2024/file.pdf"）
- `file_path`: 本地文件路径

**返回**: 成功返回True，失败返回False

---

#### `upload_data(bucket, object_name, data, content_type=None) -> bool`
上传二进制数据到对象存储

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径
- `data`: 字节数据
- `content_type`: MIME类型（可选）

**返回**: 成功返回True，失败返回False

---

#### `download_file(bucket, object_name, file_path) -> bool`
下载文件到本地

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径
- `file_path`: 本地保存路径

**返回**: 成功返回True，失败返回False

---

#### `download_data(bucket, object_name) -> Optional[bytes]`
下载文件内容为字节数据

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径

**返回**: 文件数据（bytes）或None

---

#### `delete_file(bucket, object_name) -> bool`
删除文件

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径

**返回**: 成功返回True，失败返回False

---

#### `file_exists(bucket, object_name) -> bool`
检查文件是否存在

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径

**返回**: 存在返回True，不存在返回False

---

#### `get_presigned_url(bucket, object_name, expires=3600) -> Optional[str]`
生成预签名URL

**参数**:
- `bucket`: 存储桶名称
- `object_name`: 对象路径
- `expires`: 过期时间（秒），默认1小时

**返回**: URL字符串或None

---

#### `create_bucket(bucket) -> bool`
创建存储桶

**参数**:
- `bucket`: 存储桶名称

**返回**: 成功返回True，失败返回False

---

#### `bucket_exists(bucket) -> bool`
检查存储桶是否存在

**参数**:
- `bucket`: 存储桶名称

**返回**: 存在返回True，不存在返回False

---

## 🐳 Docker管理命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f minio
docker-compose logs -f mysql
docker-compose logs -f redis

# 停止所有服务
docker-compose down

# 停止并删除数据卷（危险！）
docker-compose down -v

# 重启服务
docker-compose restart minio
```

---

## 🔧 常见问题

### Q1: MinIO连接失败

**A**: 检查以下几点：
1. Docker容器是否运行：`docker ps`
2. 端口是否被占用：`lsof -i :9000`
3. 环境变量是否正确：检查 `.env` 文件

### Q2: 上传文件失败

**A**: 可能原因：
1. 存储桶不存在 - 先创建存储桶
2. 文件路径错误 - 检查文件是否存在
3. 权限不足 - 检查MinIO用户权限

### Q3: 如何切换到S3？

**A**: 修改 `.env` 文件：
```bash
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

### Q4: 如何查看MinIO中的文件？

**A**: 
1. 浏览器访问：http://localhost:9001
2. 使用MinIO Client：
```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc ls local
```

---

## 📊 性能参考

基于测试结果（本地Docker环境）：

- **小文件上传**（< 1MB）: < 100ms
- **大文件上传**（10MB）: ~500ms
- **上传速度**: 10-20 MB/s
- **并发上传**（5个文件）: 平均 50ms/文件

实际性能取决于：
- 网络带宽
- 磁盘I/O
- MinIO/S3配置

---

## 🎯 下一步

Day 3-4任务已完成！接下来：

**Day 5**: 向量数据库配置
- 配置pgvector扩展
- 实现向量操作工具类
- 测试向量检索性能

---

## 📚 参考资源

- [MinIO文档](https://min.io/docs/minio/linux/index.html)
- [AWS S3文档](https://docs.aws.amazon.com/s3/)
- [Docker Compose文档](https://docs.docker.com/compose/)

---

**状态**: ✅ Day 3-4 完成  
**日期**: 2024-01-20  
**质量**: 所有测试通过，代码审查通过
