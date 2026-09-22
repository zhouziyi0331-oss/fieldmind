"""
FieldMind 对象存储服务
支持MinIO和S3的统一接口
"""
import os
import io
from typing import Optional, BinaryIO
from datetime import timedelta
from pathlib import Path

try:
    from minio import Minio
    from minio.error import S3Error
except Exception:
    Minio = None
    S3Error = Exception

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:
    boto3 = None
    ClientError = Exception


class StorageBackend:
    """存储后端抽象基类"""

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        raise NotImplementedError

    def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> bool:
        """上传数据"""
        raise NotImplementedError

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        raise NotImplementedError

    def download_data(self, bucket: str, object_name: str) -> Optional[bytes]:
        """下载数据"""
        raise NotImplementedError

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        raise NotImplementedError

    def file_exists(self, bucket: str, object_name: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """获取预签名URL"""
        raise NotImplementedError

    def create_bucket(self, bucket: str) -> bool:
        """创建存储桶"""
        raise NotImplementedError

    def bucket_exists(self, bucket: str) -> bool:
        """检查存储桶是否存在"""
        raise NotImplementedError


class MinIOBackend(StorageBackend):
    """MinIO存储后端"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        print(f"✅ MinIO客户端初始化成功: {endpoint}")

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)

            # 上传文件
            self.client.fput_object(
                bucket,
                object_name,
                file_path
            )
            print(f"✅ 文件上传成功: {object_name} ({file_size} bytes)")
            return True
        except S3Error as e:
            print(f"❌ 上传失败: {e}")
            return False

    def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> bool:
        """上传数据"""
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type or "application/octet-stream"
            )
            print(f"✅ 数据上传成功: {object_name} ({len(data)} bytes)")
            return True
        except S3Error as e:
            print(f"❌ 上传失败: {e}")
            return False

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            print(f"✅ 文件下载成功: {object_name} -> {file_path}")
            return True
        except S3Error as e:
            print(f"❌ 下载失败: {e}")
            return False

    def download_data(self, bucket: str, object_name: str) -> Optional[bytes]:
        """下载数据"""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            print(f"✅ 数据下载成功: {object_name} ({len(data)} bytes)")
            return data
        except S3Error as e:
            print(f"❌ 下载失败: {e}")
            return None

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(bucket, object_name)
            print(f"✅ 文件删除成功: {object_name}")
            return True
        except S3Error as e:
            print(f"❌ 删除失败: {e}")
            return False

    def file_exists(self, bucket: str, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """获取预签名URL"""
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(seconds=expires)
            )
            print(f"✅ 生成预签名URL: {object_name}")
            return url
        except S3Error as e:
            print(f"❌ 生成URL失败: {e}")
            return None

    def create_bucket(self, bucket: str) -> bool:
        """创建存储桶"""
        try:
            if not self.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                print(f"✅ 存储桶创建成功: {bucket}")
            else:
                print(f"ℹ️  存储桶已存在: {bucket}")
            return True
        except S3Error as e:
            print(f"❌ 创建存储桶失败: {e}")
            return False

    def bucket_exists(self, bucket: str) -> bool:
        """检查存储桶是否存在"""
        try:
            return self.client.bucket_exists(bucket)
        except S3Error:
            return False


class S3Backend(StorageBackend):
    """AWS S3存储后端"""

    def __init__(self, access_key: str, secret_key: str, region: str = "us-east-1"):
        self.client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        print(f"✅ S3客户端初始化成功: {region}")

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """上传文件"""
        try:
            self.client.upload_file(file_path, bucket, object_name)
            file_size = os.path.getsize(file_path)
            print(f"✅ 文件上传成功: {object_name} ({file_size} bytes)")
            return True
        except ClientError as e:
            print(f"❌ 上传失败: {e}")
            return False

    def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> bool:
        """上传数据"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            self.client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=data,
                **extra_args
            )
            print(f"✅ 数据上传成功: {object_name} ({len(data)} bytes)")
            return True
        except ClientError as e:
            print(f"❌ 上传失败: {e}")
            return False

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """下载文件"""
        try:
            self.client.download_file(bucket, object_name, file_path)
            print(f"✅ 文件下载成功: {object_name} -> {file_path}")
            return True
        except ClientError as e:
            print(f"❌ 下载失败: {e}")
            return False

    def download_data(self, bucket: str, object_name: str) -> Optional[bytes]:
        """下载数据"""
        try:
            response = self.client.get_object(Bucket=bucket, Key=object_name)
            data = response['Body'].read()
            print(f"✅ 数据下载成功: {object_name} ({len(data)} bytes)")
            return data
        except ClientError as e:
            print(f"❌ 下载失败: {e}")
            return None

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.delete_object(Bucket=bucket, Key=object_name)
            print(f"✅ 文件删除成功: {object_name}")
            return True
        except ClientError as e:
            print(f"❌ 删除失败: {e}")
            return False

    def file_exists(self, bucket: str, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=bucket, Key=object_name)
            return True
        except ClientError:
            return False

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """获取预签名URL"""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_name},
                ExpiresIn=expires
            )
            print(f"✅ 生成预签名URL: {object_name}")
            return url
        except ClientError as e:
            print(f"❌ 生成URL失败: {e}")
            return None

    def create_bucket(self, bucket: str) -> bool:
        """创建存储桶"""
        try:
            if not self.bucket_exists(bucket):
                self.client.create_bucket(Bucket=bucket)
                print(f"✅ 存储桶创建成功: {bucket}")
            else:
                print(f"ℹ️  存储桶已存在: {bucket}")
            return True
        except ClientError as e:
            print(f"❌ 创建存储桶失败: {e}")
            return False

    def bucket_exists(self, bucket: str) -> bool:
        """检查存储桶是否存在"""
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except ClientError:
            return False


class LocalBackend(StorageBackend):
    """本地文件系统后端，供桌面端和测试环境使用。"""

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(
            root_dir or os.getenv("LOCAL_STORAGE_DIR", "./data/object_storage")
        ).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, bucket: str, object_name: str) -> Path:
        path = self.root_dir / bucket / object_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        try:
            self._path(bucket, object_name).write_bytes(Path(file_path).read_bytes())
            return True
        except Exception:
            return False

    def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> bool:
        try:
            self._path(bucket, object_name).write_bytes(data)
            return True
        except Exception:
            return False

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        try:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self._path(bucket, object_name).read_bytes())
            return True
        except Exception:
            return False

    def download_data(self, bucket: str, object_name: str) -> Optional[bytes]:
        try:
            return self._path(bucket, object_name).read_bytes()
        except Exception:
            return None

    def delete_file(self, bucket: str, object_name: str) -> bool:
        try:
            path = self._path(bucket, object_name)
            if path.exists():
                path.unlink()
            return True
        except Exception:
            return False

    def file_exists(self, bucket: str, object_name: str) -> bool:
        return self._path(bucket, object_name).exists()

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        path = self._path(bucket, object_name)
        return path.as_uri() if path.exists() else None

    def create_bucket(self, bucket: str) -> bool:
        (self.root_dir / bucket).mkdir(parents=True, exist_ok=True)
        return True

    def bucket_exists(self, bucket: str) -> bool:
        return (self.root_dir / bucket).exists()


class ObjectStorage:
    """统一的对象存储服务"""

    def __init__(self):
        storage_type = os.getenv("STORAGE_TYPE", "minio").lower()

        if storage_type == "minio" and Minio is not None:
            endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
            secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
            secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

            self.backend = MinIOBackend(endpoint, access_key, secret_key, secure)

        elif storage_type == "s3" and boto3 is not None:
            access_key = os.getenv("AWS_ACCESS_KEY_ID")
            secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            region = os.getenv("AWS_REGION", "us-east-1")

            if not access_key or not secret_key:
                raise ValueError("AWS credentials not found in environment")

            self.backend = S3Backend(access_key, secret_key, region)

        else:
            self.backend = LocalBackend()

        # 初始化默认存储桶
        self._init_default_buckets()

    def _init_default_buckets(self):
        """初始化默认存储桶"""
        default_buckets = [
            "documents",   # 文档文件
            "images",      # 图片文件
            "audio",       # 音频文件
            "video",       # 视频文件
            "tables",      # 表格文件
            "temp",        # 临时文件
        ]

        for bucket in default_buckets:
            self.backend.create_bucket(bucket)

    # 代理所有backend方法
    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        return self.backend.upload_file(bucket, object_name, file_path)

    def upload_data(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> bool:
        return self.backend.upload_data(bucket, object_name, data, content_type)

    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        return self.backend.download_file(bucket, object_name, file_path)

    def download_data(self, bucket: str, object_name: str) -> Optional[bytes]:
        return self.backend.download_data(bucket, object_name)

    def delete_file(self, bucket: str, object_name: str) -> bool:
        return self.backend.delete_file(bucket, object_name)

    def file_exists(self, bucket: str, object_name: str) -> bool:
        return self.backend.file_exists(bucket, object_name)

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        return self.backend.get_presigned_url(bucket, object_name, expires)

    def create_bucket(self, bucket: str) -> bool:
        return self.backend.create_bucket(bucket)

    def bucket_exists(self, bucket: str) -> bool:
        return self.backend.bucket_exists(bucket)


# 全局单例
_storage_instance: Optional[ObjectStorage] = None


def get_storage() -> ObjectStorage:
    """获取对象存储实例（单例模式）"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ObjectStorage()
    return _storage_instance


if __name__ == "__main__":
    # 简单测试
    storage = get_storage()
    print("\n对象存储服务初始化完成")
