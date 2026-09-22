"""
企业级配置管理系统

提供集中化的配置管理能力：
- 分层配置（全局、项目、用户）
- 动态配置更新
- 配置版本管理
- 配置验证
- 敏感配置加密
- 配置审计
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import json
import os
from pathlib import Path

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, Index
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from cryptography.fernet import Fernet

import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class ConfigScope(str, Enum):
    """配置作用域"""
    GLOBAL = "global"  # 全局配置
    PROJECT = "project"  # 项目级配置
    USER = "user"  # 用户级配置
    SERVICE = "service"  # 服务级配置


class ConfigType(str, Enum):
    """配置类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    SECRET = "secret"  # 敏感配置（加密）


# ==================== 数据库模型 ====================

class Configuration(Base):
    """配置表"""
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(String(128), unique=True, nullable=False, index=True)

    key = Column(String(128), nullable=False, index=True)
    value = Column(Text, nullable=False)
    encrypted_value = Column(Text)  # 加密值

    config_type = Column(String(32), nullable=False)
    config_scope = Column(String(32), nullable=False, index=True)

    scope_id = Column(String(64))  # 作用域ID（项目ID、用户ID等）

    description = Column(Text)
    default_value = Column(Text)

    is_secret = Column(Boolean, default=False)
    is_readonly = Column(Boolean, default=False)
    is_required = Column(Boolean, default=False)

    validation_rules = Column(JSON)  # 验证规则
    metadata = Column(JSON)

    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    version = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_config_scope_key", "config_scope", "scope_id", "key"),
    )


class ConfigurationHistory(Base):
    """配置变更历史表"""
    __tablename__ = "configuration_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(String(128), nullable=False, index=True)

    old_value = Column(Text)
    new_value = Column(Text)

    changed_by = Column(Integer, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

    change_reason = Column(Text)
    metadata = Column(JSON)


# ==================== 配置管理服务 ====================

class ConfigurationManager:
    """配置管理器"""

    def __init__(self, db: Session, encryption_key: Optional[str] = None):
        self.db = db
        self._cache: Dict[str, Any] = {}
        self._encryption_key = encryption_key or self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key.encode() if isinstance(self._encryption_key, str) else self._encryption_key)

    def set(
        self,
        key: str,
        value: Any,
        config_type: ConfigType = ConfigType.STRING,
        config_scope: ConfigScope = ConfigScope.GLOBAL,
        scope_id: Optional[str] = None,
        description: Optional[str] = None,
        is_secret: bool = False,
        user_id: Optional[int] = None,
        validation_rules: Optional[Dict] = None
    ) -> Configuration:
        """
        设置配置

        Args:
            key: 配置键
            value: 配置值
            config_type: 配置类型
            config_scope: 配置作用域
            scope_id: 作用域ID
            description: 描述
            is_secret: 是否为敏感配置
            user_id: 操作用户ID
            validation_rules: 验证规则

        Returns:
            Configuration 对象
        """

        # 验证配置值
        if validation_rules:
            self._validate_value(value, validation_rules)

        # 查找现有配置
        config_id = self._generate_config_id(key, config_scope, scope_id)
        existing = self.db.query(Configuration).filter(
            Configuration.config_id == config_id
        ).first()

        if existing:
            # 记录历史
            self._record_history(
                config_id=config_id,
                old_value=existing.value,
                new_value=str(value),
                changed_by=user_id
            )

            # 更新配置
            old_value = existing.value
            existing.value = str(value) if not is_secret else ""
            existing.updated_by = user_id
            existing.updated_at = datetime.utcnow()
            existing.version += 1

            if is_secret:
                existing.encrypted_value = self._encrypt(str(value))

            self.db.commit()
            self.db.refresh(existing)

            logger.info(f"✅ 配置已更新: {key} ({config_scope.value})")

            # 清除缓存
            self._invalidate_cache(key, config_scope, scope_id)

            return existing

        else:
            # 创建新配置
            config = Configuration(
                config_id=config_id,
                key=key,
                value=str(value) if not is_secret else "",
                config_type=config_type.value,
                config_scope=config_scope.value,
                scope_id=scope_id,
                description=description,
                is_secret=is_secret,
                validation_rules=validation_rules,
                created_by=user_id,
                metadata={}
            )

            if is_secret:
                config.encrypted_value = self._encrypt(str(value))

            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

            logger.info(f"✅ 配置已创建: {key} ({config_scope.value})")

            return config

    def get(
        self,
        key: str,
        config_scope: ConfigScope = ConfigScope.GLOBAL,
        scope_id: Optional[str] = None,
        default: Any = None,
        use_cache: bool = True
    ) -> Any:
        """
        获取配置

        Args:
            key: 配置键
            config_scope: 配置作用域
            scope_id: 作用域ID
            default: 默认值
            use_cache: 是否使用缓存

        Returns:
            配置值
        """

        # 检查缓存
        cache_key = self._get_cache_key(key, config_scope, scope_id)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # 查询数据库
        config_id = self._generate_config_id(key, config_scope, scope_id)
        config = self.db.query(Configuration).filter(
            Configuration.config_id == config_id
        ).first()

        if not config:
            return default

        # 解析值
        if config.is_secret:
            value = self._decrypt(config.encrypted_value)
        else:
            value = config.value

        # 类型转换
        parsed_value = self._parse_value(value, ConfigType(config.config_type))

        # 缓存
        if use_cache:
            self._cache[cache_key] = parsed_value

        return parsed_value

    def get_all(
        self,
        config_scope: Optional[ConfigScope] = None,
        scope_id: Optional[str] = None,
        include_secrets: bool = False
    ) -> Dict[str, Any]:
        """获取所有配置"""
        query = self.db.query(Configuration)

        if config_scope:
            query = query.filter(Configuration.config_scope == config_scope.value)
        if scope_id:
            query = query.filter(Configuration.scope_id == scope_id)

        configs = query.all()

        result = {}
        for config in configs:
            if config.is_secret and not include_secrets:
                result[config.key] = "***ENCRYPTED***"
            elif config.is_secret:
                result[config.key] = self._decrypt(config.encrypted_value)
            else:
                result[config.key] = self._parse_value(
                    config.value,
                    ConfigType(config.config_type)
                )

        return result

    def delete(
        self,
        key: str,
        config_scope: ConfigScope = ConfigScope.GLOBAL,
        scope_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """删除配置"""
        config_id = self._generate_config_id(key, config_scope, scope_id)
        config = self.db.query(Configuration).filter(
            Configuration.config_id == config_id
        ).first()

        if not config:
            return False

        if config.is_readonly:
            raise ValueError(f"只读配置无法删除: {key}")

        # 记录历史
        self._record_history(
            config_id=config_id,
            old_value=config.value,
            new_value=None,
            changed_by=user_id,
            change_reason="deleted"
        )

        self.db.delete(config)
        self.db.commit()

        # 清除缓存
        self._invalidate_cache(key, config_scope, scope_id)

        logger.info(f"✅ 配置已删除: {key}")
        return True

    def get_history(
        self,
        key: str,
        config_scope: ConfigScope = ConfigScope.GLOBAL,
        scope_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取配置变更历史"""
        config_id = self._generate_config_id(key, config_scope, scope_id)

        history = self.db.query(ConfigurationHistory).filter(
            ConfigurationHistory.config_id == config_id
        ).order_by(ConfigurationHistory.changed_at.desc()).limit(limit).all()

        return [
            {
                "old_value": h.old_value,
                "new_value": h.new_value,
                "changed_by": h.changed_by,
                "changed_at": h.changed_at.isoformat(),
                "reason": h.change_reason
            }
            for h in history
        ]

    def reload_from_file(self, file_path: str, config_scope: ConfigScope = ConfigScope.GLOBAL):
        """从文件重新加载配置"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            configs = json.load(f)

        for key, value in configs.items():
            self.set(
                key=key,
                value=value,
                config_scope=config_scope
            )

        logger.info(f"✅ 从文件加载配置: {file_path} ({len(configs)} 项)")

    def export_to_file(
        self,
        file_path: str,
        config_scope: Optional[ConfigScope] = None,
        scope_id: Optional[str] = None,
        include_secrets: bool = False
    ):
        """导出配置到文件"""
        configs = self.get_all(
            config_scope=config_scope,
            scope_id=scope_id,
            include_secrets=include_secrets
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 配置已导出: {file_path} ({len(configs)} 项)")

    # ==================== 辅助方法 ====================

    def _generate_config_id(
        self,
        key: str,
        config_scope: ConfigScope,
        scope_id: Optional[str]
    ) -> str:
        """生成配置ID"""
        if scope_id:
            return f"{config_scope.value}_{scope_id}_{key}"
        return f"{config_scope.value}_{key}"

    def _get_cache_key(
        self,
        key: str,
        config_scope: ConfigScope,
        scope_id: Optional[str]
    ) -> str:
        """获取缓存键"""
        return self._generate_config_id(key, config_scope, scope_id)

    def _invalidate_cache(
        self,
        key: str,
        config_scope: ConfigScope,
        scope_id: Optional[str]
    ):
        """清除缓存"""
        cache_key = self._get_cache_key(key, config_scope, scope_id)
        if cache_key in self._cache:
            del self._cache[cache_key]

    def _parse_value(self, value: str, config_type: ConfigType) -> Any:
        """解析配置值"""
        if config_type == ConfigType.STRING or config_type == ConfigType.SECRET:
            return value
        elif config_type == ConfigType.INTEGER:
            return int(value)
        elif config_type == ConfigType.FLOAT:
            return float(value)
        elif config_type == ConfigType.BOOLEAN:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif config_type == ConfigType.JSON:
            return json.loads(value)
        return value

    def _validate_value(self, value: Any, rules: Dict) -> bool:
        """验证配置值"""
        if "min" in rules and value < rules["min"]:
            raise ValueError(f"值 {value} 小于最小值 {rules['min']}")
        if "max" in rules and value > rules["max"]:
            raise ValueError(f"值 {value} 大于最大值 {rules['max']}")
        if "enum" in rules and value not in rules["enum"]:
            raise ValueError(f"值 {value} 不在允许的枚举值中: {rules['enum']}")
        if "pattern" in rules:
            import re
            if not re.match(rules["pattern"], str(value)):
                raise ValueError(f"值 {value} 不匹配模式 {rules['pattern']}")
        return True

    def _encrypt(self, value: str) -> str:
        """加密值"""
        return self._cipher.encrypt(value.encode()).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """解密值"""
        return self._cipher.decrypt(encrypted_value.encode()).decode()

    def _get_or_create_encryption_key(self) -> str:
        """获取或创建加密密钥"""
        key_file = Path.home() / ".fieldmind" / "encryption.key"

        if key_file.exists():
            return key_file.read_text().strip()

        # 生成新密钥
        key = Fernet.generate_key().decode()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(key)
        logger.info(f"✅ 已生成新的加密密钥: {key_file}")

        return key

    def _record_history(
        self,
        config_id: str,
        old_value: Optional[str],
        new_value: Optional[str],
        changed_by: Optional[int],
        change_reason: Optional[str] = None
    ):
        """记录变更历史"""
        history = ConfigurationHistory(
            config_id=config_id,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            change_reason=change_reason
        )

        self.db.add(history)
        # 注意：不在这里 commit，由调用方统一 commit


# ==================== 配置模板 ====================

class ConfigurationTemplate:
    """配置模板"""

    # Hermes 相关配置
    HERMES_CONFIGS = {
        "hermes.enable_audit": {
            "type": ConfigType.BOOLEAN,
            "default": True,
            "description": "是否启用审计日志"
        },
        "hermes.enable_lineage": {
            "type": ConfigType.BOOLEAN,
            "default": True,
            "description": "是否启用数据血缘追踪"
        },
        "hermes.enable_permission": {
            "type": ConfigType.BOOLEAN,
            "default": True,
            "description": "是否启用权限检查"
        },
        "hermes.max_workers": {
            "type": ConfigType.INTEGER,
            "default": 10,
            "validation": {"min": 1, "max": 100},
            "description": "最大工作线程数"
        }
    }

    # 故障恢复相关配置
    RECOVERY_CONFIGS = {
        "recovery.circuit_breaker.failure_threshold": {
            "type": ConfigType.INTEGER,
            "default": 5,
            "validation": {"min": 1, "max": 20},
            "description": "断路器故障阈值"
        },
        "recovery.circuit_breaker.reset_timeout": {
            "type": ConfigType.INTEGER,
            "default": 60,
            "validation": {"min": 10, "max": 600},
            "description": "断路器重置超时（秒）"
        },
        "recovery.retry.max_attempts": {
            "type": ConfigType.INTEGER,
            "default": 3,
            "validation": {"min": 1, "max": 10},
            "description": "最大重试次数"
        }
    }

    # 系统配置
    SYSTEM_CONFIGS = {
        "system.log_level": {
            "type": ConfigType.STRING,
            "default": "INFO",
            "validation": {"enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
            "description": "日志级别"
        },
        "system.cache_ttl": {
            "type": ConfigType.INTEGER,
            "default": 300,
            "validation": {"min": 60, "max": 3600},
            "description": "缓存过期时间（秒）"
        }
    }

    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict]:
        """获取所有配置模板"""
        return {
            **cls.HERMES_CONFIGS,
            **cls.RECOVERY_CONFIGS,
            **cls.SYSTEM_CONFIGS
        }

    @classmethod
    def initialize_defaults(cls, config_manager: ConfigurationManager, user_id: Optional[int] = None):
        """初始化默认配置"""
        templates = cls.get_all_templates()

        for key, template in templates.items():
            config_manager.set(
                key=key,
                value=template["default"],
                config_type=template["type"],
                description=template.get("description"),
                validation_rules=template.get("validation"),
                user_id=user_id
            )

        logger.info(f"✅ 已初始化 {len(templates)} 个默认配置")
