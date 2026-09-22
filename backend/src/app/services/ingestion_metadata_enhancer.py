"""
Ingestion Metadata Enhancer - 采集元数据增强器

职责：
1. 为 IngestionAgent 捕获的文件增加12个治理元数据字段
2. 自动检测和分类文件属性
3. 生成治理标签
4. 评估初始质量得分

12个元数据字段：
1. source_system - 来源系统
2. business_owner - 业务负责人
3. data_classification - 数据分类（public/internal/confidential/restricted）
4. retention_period - 保留期限（天）
5. last_accessed_at - 最后访问时间
6. access_count - 访问次数
7. quality_score - 质量得分（0-100）
8. processing_status - 处理状态
9. error_message - 错误消息
10. retry_count - 重试次数
11. metadata_version - 元数据版本
12. governance_tags - 治理标签（JSON）
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    """数据分类级别"""
    PUBLIC = "public"              # 公开数据
    INTERNAL = "internal"          # 内部数据
    CONFIDENTIAL = "confidential"  # 机密数据
    RESTRICTED = "restricted"      # 受限数据


class ProcessingStatus(str, Enum):
    """处理状态"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败


class IngestionMetadataEnhancer:
    """
    采集元数据增强器

    功能：
    1. 检测来源系统
    2. 识别业务负责人
    3. 分类数据敏感度
    4. 计算保留期限
    5. 评估初始质量
    6. 生成治理标签
    """

    # 敏感关键词（用于数据分类）
    CONFIDENTIAL_KEYWORDS = {
        'zh': ['密码', '身份证', '银行卡', '手机号', '邮箱', '地址', '工资', '薪资', '合同', '协议'],
        'en': ['password', 'ssn', 'credit card', 'phone', 'email', 'address', 'salary', 'contract']
    }

    RESTRICTED_KEYWORDS = {
        'zh': ['绝密', '机密', '私密', '保密', '秘密'],
        'en': ['top secret', 'classified', 'confidential', 'restricted', 'private']
    }

    def __init__(self, use_workflow_engine: bool = True):
        """初始化元数据增强器"""



        self.use_workflow_engine = use_workflow_engine



        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.metadata_version = "2.0"
        logger.info("IngestionMetadataEnhancer initialized (metadata_version=2.0)")

    def enhance_metadata(
        self,
        file_path: str,
        file_type: str,
        raw_content: str,
        existing_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增强元数据 - 添加12个治理字段

        Args:
            file_path: 文件路径
            file_type: 文件类型
            raw_content: 文件内容
            existing_metadata: 已有的元数据

        Returns:
            Dict: 增强后的元数据（包含12个新字段）
        """
        logger.info(f"Enhancing metadata for: {file_path}")

        enhanced = existing_metadata.copy()

        # 1. source_system - 来源系统检测
        enhanced['source_system'] = self._detect_source_system(file_path, existing_metadata)

        # 2. business_owner - 业务负责人识别
        enhanced['business_owner'] = self._identify_business_owner(file_path, existing_metadata)

        # 3. data_classification - 数据分类
        enhanced['data_classification'] = self._classify_data_sensitivity(
            raw_content, file_path, file_type
        )

        # 4. retention_period - 保留期限（天）
        enhanced['retention_period'] = self._calculate_retention_period(
            file_type, enhanced['data_classification']
        )

        # 5. last_accessed_at - 最后访问时间（初始为现在）
        enhanced['last_accessed_at'] = datetime.utcnow().isoformat()

        # 6. access_count - 访问次数（初始为1）
        enhanced['access_count'] = 1

        # 7. quality_score - 初始质量评估
        enhanced['quality_score'] = self._assess_initial_quality(
            raw_content, file_type, existing_metadata
        )

        # 8. processing_status - 处理状态
        enhanced['processing_status'] = ProcessingStatus.PROCESSING.value

        # 9. error_message - 错误消息（初始为空）
        enhanced['error_message'] = None

        # 10. retry_count - 重试次数（初始为0）
        enhanced['retry_count'] = 0

        # 11. metadata_version - 元数据版本
        enhanced['metadata_version'] = self.metadata_version

        # 12. governance_tags - 治理标签
        enhanced['governance_tags'] = self._generate_governance_tags(
            file_path, file_type, raw_content, enhanced
        )

        logger.info(f"✅ Metadata enhanced: classification={enhanced['data_classification']}, "
                   f"quality={enhanced['quality_score']}, tags={len(enhanced['governance_tags'])}")

        return enhanced

    def _detect_source_system(
        self,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        检测来源系统

        识别规则：
        1. 从文件路径中提取（如包含系统名称）
        2. 从元数据中提取（如有 source 字段）
        3. 默认为 'local_upload'
        """
        path_lower = file_path.lower()

        # 常见系统标识
        system_patterns = {
            'sharepoint': ['sharepoint', 'office365'],
            'google_drive': ['google_drive', 'drive.google', 'gdrive'],
            'dropbox': ['dropbox'],
            'onedrive': ['onedrive'],
            'nas': ['nas', 'network'],
            'email': ['email', 'outlook', 'gmail'],
            'scanner': ['scan', 'scanned'],
            'mobile': ['mobile', 'phone', 'iphone', 'android'],
            'web': ['download', 'web', 'http']
        }

        for system_name, patterns in system_patterns.items():
            if any(pattern in path_lower for pattern in patterns):
                return system_name

        # 从元数据检测
        if 'source' in metadata:
            return metadata['source']

        # 默认
        return 'local_upload'

    def _identify_business_owner(
        self,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        识别业务负责人

        识别规则：
        1. 从文件路径提取用户名（如 /users/john/...）
        2. 从元数据中提取（author、creator等）
        3. 默认为 None
        """
        # 从文件路径提取
        path_parts = Path(file_path).parts
        for i, part in enumerate(path_parts):
            if part.lower() in ['users', 'user', 'home']:
                if i + 1 < len(path_parts):
                    return path_parts[i + 1]

        # 从元数据提取
        owner_fields = ['author', 'creator', 'owner', 'user', 'uploaded_by']
        for field in owner_fields:
            if field in metadata and metadata[field]:
                return str(metadata[field])

        # 默认
        return None

    def _classify_data_sensitivity(
        self,
        content: str,
        file_path: str,
        file_type: str
    ) -> str:
        """
        数据分类 - 基于内容和文件名

        分类规则：
        1. RESTRICTED - 包含受限关键词
        2. CONFIDENTIAL - 包含机密关键词
        3. INTERNAL - 内部文档（默认）
        4. PUBLIC - 明确标记为公开的
        """
        content_lower = content[:5000].lower()  # 只检查前5000字符
        filename_lower = Path(file_path).name.lower()

        # 检查 RESTRICTED 级别
        for keyword in self.RESTRICTED_KEYWORDS['zh'] + self.RESTRICTED_KEYWORDS['en']:
            if keyword in content_lower or keyword in filename_lower:
                return DataClassification.RESTRICTED.value

        # 检查 CONFIDENTIAL 级别
        for keyword in self.CONFIDENTIAL_KEYWORDS['zh'] + self.CONFIDENTIAL_KEYWORDS['en']:
            if keyword in content_lower or keyword in filename_lower:
                return DataClassification.CONFIDENTIAL.value

        # 检查 PUBLIC 标记
        public_markers = ['public', '公开', 'open', '开放']
        if any(marker in filename_lower or marker in content_lower for marker in public_markers):
            return DataClassification.PUBLIC.value

        # 默认为 INTERNAL
        return DataClassification.INTERNAL.value

    def _calculate_retention_period(
        self,
        file_type: str,
        classification: str
    ) -> int:
        """
        计算保留期限（天）

        规则：
        - RESTRICTED: 2555天（7年）
        - CONFIDENTIAL: 1825天（5年）
        - INTERNAL: 1095天（3年）
        - PUBLIC: 730天（2年）
        """
        retention_map = {
            DataClassification.RESTRICTED.value: 2555,    # 7年
            DataClassification.CONFIDENTIAL.value: 1825,  # 5年
            DataClassification.INTERNAL.value: 1095,      # 3年
            DataClassification.PUBLIC.value: 730          # 2年
        }

        return retention_map.get(classification, 1095)  # 默认3年

    def _assess_initial_quality(
        self,
        content: str,
        file_type: str,
        metadata: Dict[str, Any]
    ) -> float:
        """
        初始质量评估（0-100）

        评估维度：
        1. 内容完整性（40%）
        2. 格式规范性（30%）
        3. 元数据完整性（30%）
        """
        score = 0.0

        # 1. 内容完整性（40分）
        content_score = 0.0
        if content and len(content) > 0:
            content_score += 10  # 有内容
            if len(content) > 100:
                content_score += 10  # 内容足够长
            if len(content) > 1000:
                content_score += 10  # 内容丰富
            # 检查是否有乱码
            if self._check_no_garbled(content):
                content_score += 10  # 无乱码

        score += content_score

        # 2. 格式规范性（30分）
        format_score = 0.0
        # 检查是否有明确的段落结构
        if '\n\n' in content or '\n' in content:
            format_score += 10
        # 检查是否有标点符号（说明格式良好）
        if any(p in content for p in ['。', '，', '.', ',']):
            format_score += 10
        # 检查是否有标题或结构
        if any(marker in content for marker in ['#', '标题', 'Title', '章节']):
            format_score += 10

        score += format_score

        # 3. 元数据完整性（30分）
        metadata_score = 0.0
        essential_fields = ['file_name', 'file_size', 'created_at']
        present_fields = sum(1 for field in essential_fields if field in metadata and metadata[field])
        metadata_score = (present_fields / len(essential_fields)) * 30

        score += metadata_score

        # 确保在0-100范围内
        return round(min(max(score, 0.0), 100.0), 2)

    def _check_no_garbled(self, content: str) -> bool:
        """检查是否有乱码"""
        # 简单检查：如果乱码字符比例过高，返回False
        sample = content[:1000]  # 检查前1000字符
        if not sample:
            return True

        # 检查不可打印字符的比例
        printable_count = sum(1 for c in sample if c.isprintable() or c in '\n\t')
        ratio = printable_count / len(sample)

        return ratio > 0.9  # 90%以上是可打印字符

    def _generate_governance_tags(
        self,
        file_path: str,
        file_type: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        生成治理标签

        标签类型：
        1. 文件类型标签
        2. 敏感度标签
        3. 来源标签
        4. 内容特征标签
        """
        tags = []

        # 1. 文件类型标签
        tags.append(f"type:{file_type}")

        # 2. 敏感度标签
        classification = metadata.get('data_classification', 'internal')
        tags.append(f"classification:{classification}")

        # 3. 来源标签
        source_system = metadata.get('source_system', 'unknown')
        tags.append(f"source:{source_system}")

        # 4. 大小标签
        file_size = metadata.get('file_size', 0)
        if file_size < 1024 * 100:  # < 100KB
            tags.append("size:small")
        elif file_size < 1024 * 1024 * 10:  # < 10MB
            tags.append("size:medium")
        else:
            tags.append("size:large")

        # 5. 语言标签
        if metadata.get('translated'):
            tags.append("lang:translated")
            original_lang = metadata.get('original_language', 'unknown')
            tags.append(f"original_lang:{original_lang}")
        else:
            tags.append("lang:original")

        # 6. 质量标签
        quality_score = metadata.get('quality_score', 0)
        if quality_score >= 80:
            tags.append("quality:high")
        elif quality_score >= 50:
            tags.append("quality:medium")
        else:
            tags.append("quality:low")

        # 7. 内容特征标签
        if len(content) > 10000:
            tags.append("content:long")
        if metadata.get('source_count', 0) > 0:
            tags.append("feature:traceable")
        if file_type in ['audio', 'video']:
            tags.append("feature:multimedia")
        if file_type in ['excel', 'csv']:
            tags.append("feature:structured")

        return tags


def create_metadata_enhancer() -> IngestionMetadataEnhancer:
    """
    工厂方法：创建元数据增强器实例

    Returns:
        IngestionMetadataEnhancer: 元数据增强器实例
    """
    return IngestionMetadataEnhancer()
