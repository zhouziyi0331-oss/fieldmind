"""
FieldMind 数据库配置
SQLAlchemy数据库连接配置
"""
import os
import ast
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


if load_dotenv:
    for env_path in [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path, override=False)

# 数据库配置
BACKEND_SRC_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = BACKEND_SRC_DIR / "data" / "fieldmind.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


def normalize_sqlite_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    sqlite_path = Path(database_url.replace("sqlite:///", "", 1)).expanduser()
    if not sqlite_path.is_absolute():
        sqlite_path = BACKEND_SRC_DIR / sqlite_path
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path.resolve().as_posix()}"


DATABASE_URL = normalize_sqlite_url(os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL)


def get_sqlite_database_path() -> str:
    """返回当前运行配置里的 SQLite 主库路径，供少量 sqlite3 直连服务复用。"""
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError(f"当前数据库不是 SQLite，不能用 sqlite3 直连: {DATABASE_URL}")
    return DATABASE_URL.replace("sqlite:///", "", 1)

if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })
else:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db_session() -> Session:
    """兼容旧服务的同步会话入口，所有调用方共享同一 SessionLocal。"""
    return SessionLocal()


def get_fact_db_session() -> Session:
    """兼容聚合服务；事实数据已统一使用当前主数据库。"""
    return SessionLocal()


def generate_id(prefix: str = "id") -> str:
    """生成旧接口仍需要的业务 ID。"""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex}"


def close_db() -> None:
    """兼容应用关闭钩子。"""
    engine.dispose()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖注入）
    用于FastAPI的Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    获取数据库会话（上下文管理器）
    用于普通Python代码

    使用示例:
        with get_db_context() as db:
            document = db.query(Document).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表（仅用于开发环境）
    生产环境请使用迁移脚本
    """
    # 导入所有模型，确保它们被注册到Base.metadata
    from app.models import (
        Document,
        DocumentMetadata,
        Entity,
        DocumentEntity,
        EntityRelation,
        Tag,
        DocumentTag,
        DocumentChunk,
        User,
        StructuredInsight,
        TopicStatistics,
        EntityStatistics,
        FieldMindObject,
        ObjectRelation,
        FactStatement,
        Project,
        ProjectDocument,
        ProjectDocumentAsset,
        ProjectDocumentTag,
        Embedding,
        TimelineEvent,
        ProcessingTask,
        QualityReport,
    )

    _migrate_legacy_entity_schema()
    _repair_legacy_json_columns()
    Base.metadata.create_all(bind=engine)
    _create_integrity_indexes()
    print("✅ 数据库表创建完成")


def _migrate_legacy_entity_schema() -> None:
    """把历史实体列迁移到当前统一字段，同时保留旧列供兼容代码使用。"""
    from sqlalchemy import inspect, text as sql_text

    inspector = inspect(engine)
    with engine.begin() as connection:
        if "entities" in inspector.get_table_names():
            columns = {column["name"] for column in inspector.get_columns("entities")}
            additions = {
                "text": "VARCHAR(500)",
                "type": "VARCHAR(50)",
                "canonical_form": "VARCHAR(500)",
                "metadata": "JSON",
                "updated_at": "DATETIME",
            }
            for name, definition in additions.items():
                if name not in columns:
                    connection.execute(sql_text(
                        f"ALTER TABLE entities ADD COLUMN {name} {definition}"
                    ))

            # 只填充空的新字段，不覆盖可能已经被当前代码更新的内容。
            connection.execute(sql_text(
                "UPDATE entities SET text = COALESCE(text, name) "
                "WHERE text IS NULL"
            ))
            connection.execute(sql_text(
                "UPDATE entities SET type = COALESCE(type, entity_type) "
                "WHERE type IS NULL"
            ))
            connection.execute(sql_text(
                "UPDATE entities SET canonical_form = COALESCE(canonical_form, text) "
                "WHERE canonical_form IS NULL"
            ))
            if "properties" in columns:
                connection.execute(sql_text(
                    "UPDATE entities SET metadata = COALESCE(metadata, properties) "
                    "WHERE metadata IS NULL"
                ))
            connection.execute(sql_text(
                "UPDATE entities SET updated_at = COALESCE(updated_at, created_at) "
                "WHERE updated_at IS NULL"
            ))

        if "entity_relations" in inspector.get_table_names():
            columns = {
                column["name"]
                for column in inspector.get_columns("entity_relations")
            }
            if "metadata" not in columns:
                connection.execute(sql_text(
                    "ALTER TABLE entity_relations ADD COLUMN metadata JSON"
                ))
            if "source_documents" not in columns:
                connection.execute(sql_text(
                    "ALTER TABLE entity_relations ADD COLUMN source_documents JSON"
                ))
            if "updated_at" not in columns:
                connection.execute(sql_text(
                    "ALTER TABLE entity_relations ADD COLUMN updated_at DATETIME"
                ))
            if "properties" in columns:
                connection.execute(sql_text(
                    "UPDATE entity_relations SET metadata = COALESCE(metadata, properties) "
                    "WHERE metadata IS NULL"
                ))


def _create_integrity_indexes() -> None:
    """为上传去重、标签去重和实体一致性补齐数据库约束。"""
    from sqlalchemy import inspect, text as sql_text

    inspector = inspect(engine)
    with engine.begin() as connection:
        tables = set(inspector.get_table_names())
        if "project_documents" in tables:
            connection.execute(sql_text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_project_documents_project_hash "
                "ON project_documents(project_id, file_hash)"
            ))
        if "project_document_tags" in tables:
            connection.execute(sql_text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_project_document_tags_document_name "
                "ON project_document_tags(document_id, name)"
            ))
        if "entities" in tables:
            connection.execute(sql_text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_entities_text_type "
                "ON entities(text, type)"
            ))


def _repair_legacy_json_columns() -> None:
    """把历史版本写入的 Python repr 字符串修复为合法 JSON。

    早期代码曾直接把 dict 写进 SQLite 文本列，形成 ``{'key': 'value'}``。
    SQLAlchemy 的 JSON 类型读取这类数据会在查询阶段抛 JSONDecodeError，
    于是实体、标签、项目统计等所有上层功能都会被连带打断。
    """
    from sqlalchemy import inspect, text as sql_text

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    candidates = {
        "entities": ["aliases", "properties", "document_ids", "related_entities", "metadata"],
        "entity_relations": ["properties", "metadata", "source_documents"],
        "projects": ["settings", "extra_data"],
        "project_documents": [
            "entities", "keywords", "extracted_entities", "auto_clusters", "data_profile", "extra_data"
        ],
        "project_document_assets": ["asset_metadata"],
        "document_chunks": [
            "chunk_metadata", "embedding", "extra_metadata", "embedding_vector", "structured_data", "metadata"
        ],
    }

    def normalize(value):
        if value is None or not isinstance(value, str):
            return value
        try:
            json.loads(value)
            return value
        except (TypeError, ValueError):
            pass
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value
        if isinstance(parsed, (dict, list, tuple, bool, int, float)) or parsed is None:
            return json.dumps(parsed, ensure_ascii=False, default=str)
        return value

    with engine.begin() as connection:
        for table, columns in candidates.items():
            if table not in tables:
                continue
            table_columns = {column["name"] for column in inspector.get_columns(table)}
            primary_keys = [
                column["name"] for column in inspector.get_columns(table)
                if column.get("primary_key")
            ]
            if len(primary_keys) != 1:
                continue
            primary_key = primary_keys[0]
            for column in columns:
                if column not in table_columns:
                    continue
                rows = connection.execute(sql_text(
                    f"SELECT {primary_key}, {column} FROM {table} "
                    f"WHERE {column} IS NOT NULL"
                )).fetchall()
                for key, value in rows:
                    repaired = normalize(value)
                    if repaired != value:
                        connection.execute(sql_text(
                            f"UPDATE {table} SET {column} = :value WHERE {primary_key} = :key"
                        ), {"value": repaired, "key": key})


def drop_all_tables():
    """
    删除所有表（危险操作！仅用于开发环境）
    """
    from app.models import (
        Document,
        DocumentMetadata,
        Entity,
        DocumentEntity,
        EntityRelation,
        Tag,
        DocumentTag,
        DocumentChunk,
        StructuredInsight,
        TopicStatistics,
        EntityStatistics,
        FieldMindObject,
        ObjectRelation,
        FactStatement,
        Project,
        ProjectDocument,
        ProjectDocumentAsset,
        ProjectDocumentTag,
        Embedding,
        TimelineEvent,
        ProcessingTask,
        QualityReport,
    )

    Base.metadata.drop_all(bind=engine)
    print("⚠️  所有表已删除")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            init_db()
        elif command == "drop":
            confirm = input("确定要删除所有表吗？输入 'yes' 确认: ")
            if confirm.lower() == "yes":
                drop_all_tables()
            else:
                print("已取消")
        else:
            print(f"未知命令: {command}")
    else:
        print("用法:")
        print("  python database.py init  # 初始化数据库")
        print("  python database.py drop  # 删除所有表")
