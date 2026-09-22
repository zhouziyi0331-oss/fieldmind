#!/usr/bin/env python3
"""测试知识蒸馏服务"""
import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from app.core.database import SessionLocal
from app.services.distillation_service import DistillationService
from app.distillation.types import SourceKind

async def test_distillation():
    db = SessionLocal()
    try:
        service = DistillationService(db)

        # 测试文件路径
        file_path = "/Users/alwan/FieldMind/test_data_yinzhai.txt"

        print(f"测试文件: {file_path}")
        print(f"文件是否存在: {os.path.exists(file_path)}")

        # 创建蒸馏任务
        print("\n创建蒸馏任务...")
        job = await service.create_job_from_file(
            file_path=file_path,
            source_kind=SourceKind.FIELDWORK_NOTE,
            title="音寨布依族村文化全景深度报告.txt",
            author=None,
            additional_metadata={
                "project_id": 2,
                "document_id": 38,
            }
        )

        print(f"✅ 任务创建成功: {job.id}")
        print(f"   状态: {job.status}")

        # 启动蒸馏
        print("\n启动蒸馏...")
        await service.start_distillation(job.id)

        print(f"✅ 蒸馏已启动")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_distillation())
