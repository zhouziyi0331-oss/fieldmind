"""
Photos API - 图片管理（带EXIF元数据支持）
扩展DocumentService以支持照片特定功能
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json

from app.core.database import get_db
from app.models.document import Document
from app.models.project import ProjectDocument
from app.config import settings
from app.core.exceptions import ResourceNotFoundException, ValidationException, FileException

router = APIRouter(tags=["photos"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class PhotoExifMetadata(BaseModel):
    """EXIF元数据"""
    width: int
    height: int
    taken_at: Optional[str] = None  # ISO format datetime
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    location_name: Optional[str] = None
    device_make: Optional[str] = None
    device_model: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[str] = None


class PhotoResponse(BaseModel):
    """照片响应"""
    id: str
    filename: str
    file_size: int
    file_path: str
    format: str
    width: int
    height: int
    taken_at: Optional[datetime] = None
    location: Optional[str] = None
    device: Optional[str] = None
    project_id: int
    tags: List[str] = []
    uploaded_at: datetime

    class Config:
        from_attributes = True


class PhotoListResponse(BaseModel):
    """照片列表响应"""
    photos: List[PhotoResponse]
    total: int
    page: int
    page_size: int


class PhotoStatsResponse(BaseModel):
    """照片统计响应"""
    total_photos: int
    total_size: int
    by_device: dict  # {device: count}
    by_location: dict  # {location: count}
    by_format: dict  # {format: count}
    recent_uploads: int


# ==================== Helper Functions ====================

def extract_exif(image_path: str) -> Optional[PhotoExifMetadata]:
    """从图片提取EXIF元数据"""
    try:
        image = Image.open(image_path)

        # 获取基本尺寸
        width, height = image.size
        format_name = image.format or "UNKNOWN"

        # 尝试获取EXIF数据
        exif_data = {}
        if hasattr(image, '_getexif') and image._getexif():
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

        # 提取关键字段
        taken_at = None
        if 'DateTime' in exif_data:
            try:
                taken_at = datetime.strptime(str(exif_data['DateTime']), '%Y:%m:%d %H:%M:%S').isoformat()
            except:
                pass
        elif 'DateTimeOriginal' in exif_data:
            try:
                taken_at = datetime.strptime(str(exif_data['DateTimeOriginal']), '%Y:%m:%d %H:%M:%S').isoformat()
            except:
                pass

        # GPS信息
        gps_latitude = None
        gps_longitude = None
        if 'GPSInfo' in exif_data:
            gps_info = exif_data['GPSInfo']
            if gps_info:
                gps_data = {}
                for key in gps_info.keys():
                    decode = GPSTAGS.get(key, key)
                    gps_data[decode] = gps_info[key]

                # 解析GPS坐标
                if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                    lat = gps_data['GPSLatitude']
                    lon = gps_data['GPSLongitude']

                    # 转换为十进制度数
                    if lat and lon:
                        try:
                            gps_latitude = float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600
                            gps_longitude = float(lon[0]) + float(lon[1])/60 + float(lon[2])/3600

                            if gps_data.get('GPSLatitudeRef') == 'S':
                                gps_latitude = -gps_latitude
                            if gps_data.get('GPSLongitudeRef') == 'W':
                                gps_longitude = -gps_longitude
                        except:
                            pass

        # 设备信息
        device_make = exif_data.get('Make')
        device_model = exif_data.get('Model')

        # 相机设置
        iso = exif_data.get('ISOSpeedRatings')
        aperture = exif_data.get('FNumber')
        shutter_speed = exif_data.get('ExposureTime')
        focal_length = exif_data.get('FocalLength')

        return PhotoExifMetadata(
            width=width,
            height=height,
            taken_at=taken_at,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            device_make=str(device_make) if device_make else None,
            device_model=str(device_model) if device_model else None,
            iso=int(iso) if iso else None,
            aperture=str(aperture) if aperture else None,
            shutter_speed=str(shutter_speed) if shutter_speed else None,
            focal_length=str(focal_length) if focal_length else None
        )

    except Exception as e:
        logger.warning(f"⚠️ EXIF提取失败: {e}")
        # 至少返回基本尺寸
        try:
            image = Image.open(image_path)
            width, height = image.size
            return PhotoExifMetadata(width=width, height=height)
        except:
            return None


# ==================== API接口 ====================

@router.post("/photos/upload")
async def upload_photo(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),  # 逗号分隔
    location_name: Optional[str] = Form(None),  # 手动指定位置
    db: Session = Depends(get_db)
):
    """上传照片并提取EXIF元数据"""
    try:
        # 验证文件类型
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.raw', '.tiff', '.gif'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationException(
                message="不支持的图片格式",
                field="file",
                details={"file_extension": file_ext, "allowed": list(allowed_extensions)}
            )

        # 保存文件
        upload_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}", "photos")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 提取EXIF
        exif = extract_exif(file_path)

        # 构建exif_metadata JSON
        exif_json = None
        if exif:
            exif_json = {
                "width": exif.width,
                "height": exif.height,
                "taken_at": exif.taken_at,
                "gps_latitude": exif.gps_latitude,
                "gps_longitude": exif.gps_longitude,
                "location_name": location_name or exif.location_name,
                "device_make": exif.device_make,
                "device_model": exif.device_model,
                "camera_settings": {
                    "iso": exif.iso,
                    "aperture": exif.aperture,
                    "shutter_speed": exif.shutter_speed,
                    "focal_length": exif.focal_length
                }
            }

        # 解析tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]

        # 创建文档记录
        doc = ProjectDocument(
            project_id=project_id,
            filename=file.filename,
            original_filename=file.filename,
            file_type="image",
            file_path=file_path,
            file_size=len(content),
            status="completed",
            exif_metadata=exif_json
        )

        # 添加tags到doc_metadata
        if tag_list:
            doc.doc_metadata = {"tags": tag_list}

        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"✅ 上传照片: {file.filename}, EXIF已提取")
        return {
            "status": "success",
            "document_id": doc.id,
            "filename": file.filename,
            "exif": exif_json
        }

    except (ValidationException, FileException):
        raise
    except Exception as e:
        logger.error(f"❌ 上传照片失败: {e}")
        raise FileException(
            message="上传照片失败",
            operation="upload",
            details={"error": str(e)}
        )


@router.get("/photos", response_model=PhotoListResponse)
async def list_photos(
    project_id: int = Query(...),
    search: Optional[str] = Query(None),
    date_filter: Optional[str] = Query(None, description="all/today/week/month/year"),
    sort_by: str = Query("created_at", description="created_at/filename/size"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取照片列表（带EXIF元数据）"""
    try:
        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.file_type == "image"
        )

        # 搜索
        if search:
            query = query.filter(ProjectDocument.filename.ilike(f"%{search}%"))

        # 日期筛选
        if date_filter and date_filter != "all":
            now = datetime.utcnow()
            if date_filter == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_filter == "week":
                start_date = now - timedelta(days=7)
            elif date_filter == "month":
                start_date = now - timedelta(days=30)
            elif date_filter == "year":
                start_date = now - timedelta(days=365)
            else:
                start_date = None

            if start_date:
                query = query.filter(ProjectDocument.created_at >= start_date)

        # 总数
        total = query.count()

        # 排序
        if sort_by == "filename":
            order_col = ProjectDocument.filename
        elif sort_by == "size":
            order_col = ProjectDocument.file_size
        else:
            order_col = ProjectDocument.created_at

        if sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # 分页
        docs = query.offset((page - 1) * page_size).limit(page_size).all()

        # 构建响应
        photos = []
        for doc in docs:
            exif = doc.exif_metadata or {}
            tags = []
            if doc.doc_metadata and 'tags' in doc.doc_metadata:
                tags = doc.doc_metadata['tags']

            # 构建device字符串
            device = None
            if exif.get('device_make') or exif.get('device_model'):
                parts = []
                if exif.get('device_make'):
                    parts.append(exif['device_make'])
                if exif.get('device_model'):
                    parts.append(exif['device_model'])
                device = ' '.join(parts)

            # 解析taken_at
            taken_at = None
            if exif.get('taken_at'):
                try:
                    taken_at = datetime.fromisoformat(exif['taken_at'])
                except:
                    pass

            photo = PhotoResponse(
                id=str(doc.id),
                filename=doc.filename,
                file_size=doc.file_size or 0,
                file_path=doc.file_path,
                format=os.path.splitext(doc.filename)[1].upper().replace('.', ''),
                width=exif.get('width', 0),
                height=exif.get('height', 0),
                taken_at=taken_at,
                location=exif.get('location_name'),
                device=device,
                project_id=doc.project_id,
                tags=tags,
                uploaded_at=doc.created_at
            )
            photos.append(photo)

        return PhotoListResponse(
            photos=photos,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"❌ 获取照片列表失败: {e}")
        raise FileException(
            message="获取照片列表失败",
            operation="list",
            details={"error": str(e)}
        )


@router.get("/photos/stats/{project_id}", response_model=PhotoStatsResponse)
async def get_photo_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取照片统计"""
    try:
        docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.file_type == "image"
        ).all()

        total = len(docs)
        total_size = sum(doc.file_size or 0 for doc in docs)

        # 按设备统计
        by_device = {}
        by_location = {}
        by_format = {}

        for doc in docs:
            exif = doc.exif_metadata or {}

            # 设备
            device = None
            if exif.get('device_make') or exif.get('device_model'):
                parts = []
                if exif.get('device_make'):
                    parts.append(exif['device_make'])
                if exif.get('device_model'):
                    parts.append(exif['device_model'])
                device = ' '.join(parts)

            if device:
                by_device[device] = by_device.get(device, 0) + 1
            else:
                by_device['未知设备'] = by_device.get('未知设备', 0) + 1

            # 位置
            location = exif.get('location_name') or '未知位置'
            by_location[location] = by_location.get(location, 0) + 1

            # 格式
            fmt = os.path.splitext(doc.filename)[1].upper().replace('.', '') or 'UNKNOWN'
            by_format[fmt] = by_format.get(fmt, 0) + 1

        # 最近7天
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.file_type == "image",
            ProjectDocument.created_at >= seven_days_ago
        ).scalar() or 0

        return PhotoStatsResponse(
            total_photos=total,
            total_size=total_size,
            by_device=by_device,
            by_location=by_location,
            by_format=by_format,
            recent_uploads=recent
        )

    except Exception as e:
        logger.error(f"❌ 获取照片统计失败: {e}")
        raise FileException(
            message="获取照片统计失败",
            operation="stats",
            details={"error": str(e)}
        )


@router.delete("/photos/{photo_id}")
async def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db)
):
    """删除照片"""
    try:
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == photo_id).first()
        if not doc:
            raise ResourceNotFoundException(resource_type="Photo", resource_id=photo_id)

        # 删除文件
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        # 删除记录
        db.delete(doc)
        db.commit()

        logger.info(f"✅ 删除照片: {doc.filename}")
        return {"status": "success", "message": "照片已删除"}

    except (ResourceNotFoundException, FileException):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 删除照片失败: {e}")
        raise FileException(
            message="删除照片失败",
            operation="delete",
            details={"error": str(e), "photo_id": photo_id}
        )
