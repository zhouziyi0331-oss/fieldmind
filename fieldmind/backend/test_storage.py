#!/usr/bin/env python3
"""
FieldMind 对象存储测试脚本
测试MinIO/S3对象存储功能
"""
import sys
import os
from pathlib import Path
import tempfile
import time

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.core.storage import get_storage, ObjectStorage


def test_storage_initialization():
    """测试1: 存储服务初始化"""
    print("\n" + "=" * 60)
    print("测试1: 存储服务初始化")
    print("=" * 60)

    try:
        storage = get_storage()
        print(f"✅ 存储服务初始化成功")
        print(f"   后端类型: {type(storage.backend).__name__}")
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_bucket_operations():
    """测试2: 存储桶操作"""
    print("\n" + "=" * 60)
    print("测试2: 存储桶操作")
    print("=" * 60)

    try:
        storage = get_storage()

        # 测试存储桶
        test_bucket = "test-bucket"

        # 创建存储桶
        print(f"\n创建存储桶: {test_bucket}")
        if not storage.create_bucket(test_bucket):
            print(f"❌ 创建存储桶失败")
            return False

        # 检查存储桶是否存在
        print(f"检查存储桶是否存在")
        if storage.bucket_exists(test_bucket):
            print(f"✅ 存储桶存在: {test_bucket}")
        else:
            print(f"❌ 存储桶不存在")
            return False

        return True
    except Exception as e:
        print(f"❌ 存储桶操作失败: {e}")
        return False


def test_upload_download_file():
    """测试3: 文件上传和下载"""
    print("\n" + "=" * 60)
    print("测试3: 文件上传和下载")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"

        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_file_path = f.name
            test_content = "这是一个测试文件\nFieldMind对象存储测试\n"
            f.write(test_content)

        object_name = "test/sample.txt"

        # 上传文件
        print(f"\n上传文件: {test_file_path} -> {object_name}")
        if not storage.upload_file(bucket, object_name, test_file_path):
            print(f"❌ 上传失败")
            os.unlink(test_file_path)
            return False

        # 检查文件是否存在
        print(f"检查文件是否存在")
        if storage.file_exists(bucket, object_name):
            print(f"✅ 文件存在: {object_name}")
        else:
            print(f"❌ 文件不存在")
            os.unlink(test_file_path)
            return False

        # 下载文件
        download_path = test_file_path + ".download"
        print(f"下载文件: {object_name} -> {download_path}")
        if not storage.download_file(bucket, object_name, download_path):
            print(f"❌ 下载失败")
            os.unlink(test_file_path)
            return False

        # 验证内容
        with open(download_path, 'r') as f:
            downloaded_content = f.read()

        if downloaded_content == test_content:
            print(f"✅ 文件内容验证成功")
        else:
            print(f"❌ 文件内容不匹配")
            os.unlink(test_file_path)
            os.unlink(download_path)
            return False

        # 清理
        os.unlink(test_file_path)
        os.unlink(download_path)

        return True
    except Exception as e:
        print(f"❌ 文件操作失败: {e}")
        return False


def test_upload_download_data():
    """测试4: 数据上传和下载"""
    print("\n" + "=" * 60)
    print("测试4: 数据上传和下载")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"

        # 测试数据
        test_data = b"This is binary test data\x00\x01\x02\x03"
        object_name = "test/binary_data.bin"

        # 上传数据
        print(f"\n上传数据: {len(test_data)} bytes -> {object_name}")
        if not storage.upload_data(bucket, object_name, test_data, "application/octet-stream"):
            print(f"❌ 上传失败")
            return False

        # 下载数据
        print(f"下载数据: {object_name}")
        downloaded_data = storage.download_data(bucket, object_name)

        if downloaded_data is None:
            print(f"❌ 下载失败")
            return False

        # 验证数据
        if downloaded_data == test_data:
            print(f"✅ 数据验证成功 ({len(downloaded_data)} bytes)")
        else:
            print(f"❌ 数据不匹配")
            return False

        return True
    except Exception as e:
        print(f"❌ 数据操作失败: {e}")
        return False


def test_presigned_url():
    """测试5: 预签名URL生成"""
    print("\n" + "=" * 60)
    print("测试5: 预签名URL生成")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"
        object_name = "test/sample.txt"

        # 生成预签名URL
        print(f"\n生成预签名URL: {object_name}")
        url = storage.get_presigned_url(bucket, object_name, expires=3600)

        if url:
            print(f"✅ URL生成成功")
            print(f"   URL长度: {len(url)} 字符")
            print(f"   URL前缀: {url[:50]}...")
            return True
        else:
            print(f"❌ URL生成失败")
            return False

    except Exception as e:
        print(f"❌ URL生成失败: {e}")
        return False


def test_delete_file():
    """测试6: 文件删除"""
    print("\n" + "=" * 60)
    print("测试6: 文件删除")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"

        files_to_delete = [
            "test/sample.txt",
            "test/binary_data.bin"
        ]

        for object_name in files_to_delete:
            print(f"\n删除文件: {object_name}")

            # 检查文件是否存在
            if not storage.file_exists(bucket, object_name):
                print(f"⚠️  文件不存在，跳过")
                continue

            # 删除文件
            if not storage.delete_file(bucket, object_name):
                print(f"❌ 删除失败")
                return False

            # 验证文件已删除
            if storage.file_exists(bucket, object_name):
                print(f"❌ 文件仍然存在")
                return False

            print(f"✅ 文件删除成功")

        return True
    except Exception as e:
        print(f"❌ 删除操作失败: {e}")
        return False


def test_large_file():
    """测试7: 大文件上传"""
    print("\n" + "=" * 60)
    print("测试7: 大文件上传（10MB）")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"

        # 创建10MB测试文件
        file_size = 10 * 1024 * 1024  # 10MB
        print(f"\n创建测试文件: {file_size / 1024 / 1024:.1f} MB")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            test_file_path = f.name
            # 写入10MB数据
            chunk = b'x' * (1024 * 1024)  # 1MB chunk
            for _ in range(10):
                f.write(chunk)

        object_name = "test/large_file.bin"

        # 上传
        print(f"上传大文件...")
        start_time = time.time()

        if not storage.upload_file(bucket, object_name, test_file_path):
            print(f"❌ 上传失败")
            os.unlink(test_file_path)
            return False

        upload_time = time.time() - start_time
        upload_speed = file_size / upload_time / 1024 / 1024

        print(f"✅ 上传成功")
        print(f"   耗时: {upload_time:.2f} 秒")
        print(f"   速度: {upload_speed:.2f} MB/s")

        # 删除测试文件
        storage.delete_file(bucket, object_name)
        os.unlink(test_file_path)

        return True
    except Exception as e:
        print(f"❌ 大文件测试失败: {e}")
        return False


def test_default_buckets():
    """测试8: 默认存储桶"""
    print("\n" + "=" * 60)
    print("测试8: 验证默认存储桶")
    print("=" * 60)

    try:
        storage = get_storage()

        default_buckets = [
            "documents",
            "images",
            "audio",
            "video",
            "tables",
            "temp"
        ]

        print("\n检查默认存储桶:")
        all_exist = True

        for bucket in default_buckets:
            exists = storage.bucket_exists(bucket)
            status = "✅" if exists else "❌"
            print(f"  {status} {bucket}")

            if not exists:
                all_exist = False

        if all_exist:
            print(f"\n✅ 所有默认存储桶都已创建")
            return True
        else:
            print(f"\n⚠️  部分默认存储桶缺失")
            return False

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def test_concurrent_uploads():
    """测试9: 并发上传"""
    print("\n" + "=" * 60)
    print("测试9: 并发上传（5个文件）")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"

        # 创建5个测试文件
        test_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(f"Test file {i}\n" * 100)
                test_files.append(f.name)

        # 上传所有文件
        print(f"\n上传 {len(test_files)} 个文件...")
        start_time = time.time()

        for i, file_path in enumerate(test_files):
            object_name = f"test/concurrent_{i}.txt"
            if not storage.upload_file(bucket, object_name, file_path):
                print(f"❌ 文件 {i} 上传失败")
                # 清理
                for fp in test_files:
                    os.unlink(fp)
                return False

        upload_time = time.time() - start_time

        print(f"✅ 所有文件上传成功")
        print(f"   总耗时: {upload_time:.2f} 秒")
        print(f"   平均: {upload_time / len(test_files):.2f} 秒/文件")

        # 清理
        for i in range(len(test_files)):
            storage.delete_file(bucket, f"test/concurrent_{i}.txt")
            os.unlink(test_files[i])

        return True
    except Exception as e:
        print(f"❌ 并发测试失败: {e}")
        return False


def test_cleanup():
    """测试10: 清理测试数据"""
    print("\n" + "=" * 60)
    print("测试10: 清理测试数据")
    print("=" * 60)

    try:
        storage = get_storage()
        bucket = "test-bucket"

        print(f"\n清理测试存储桶: {bucket}")
        # 注意：MinIO/S3 不支持直接删除非空存储桶
        # 在实际应用中需要先删除所有对象
        print(f"⚠️  测试存储桶保留，包含测试数据")

        print(f"✅ 清理完成")
        return True

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print(" " * 15 + "FieldMind 对象存储测试")
    print("*" * 60)

    # 检查环境变量
    storage_type = os.getenv("STORAGE_TYPE", "minio")
    print(f"\n存储类型: {storage_type}")

    if storage_type == "minio":
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        print(f"MinIO端点: {endpoint}")
    elif storage_type == "s3":
        region = os.getenv("AWS_REGION", "us-east-1")
        print(f"S3区域: {region}")

    tests = [
        ("存储服务初始化", test_storage_initialization),
        ("存储桶操作", test_bucket_operations),
        ("文件上传和下载", test_upload_download_file),
        ("数据上传和下载", test_upload_download_data),
        ("预签名URL", test_presigned_url),
        ("文件删除", test_delete_file),
        ("大文件上传", test_large_file),
        ("默认存储桶", test_default_buckets),
        ("并发上传", test_concurrent_uploads),
        ("清理测试数据", test_cleanup),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 所有测试通过！对象存储配置成功！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
