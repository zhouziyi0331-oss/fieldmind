"""统一项目文档数据流的幂等迁移脚本。

执行内容：
- project_documents 增加 file_hash、mime_type
- 创建 project_document_assets、project_document_tags
- document_chunks 从旧字段回填到统一字段
- 同项目同 SHA256 的 project_documents 去重，只保留最早主记录
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "src" / "data" / "fieldmind.db"


def db_path_from_env() -> Path:
    url = os.getenv("DATABASE_URL")
    if url and url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", "", 1))
    return DEFAULT_DB


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def add_column(conn: sqlite3.Connection, table: str, name: str, ddl: str) -> None:
    if name not in columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def resolve_file(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    candidates = []
    raw = Path(path_value)
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend([
            ROOT / path_value,
            ROOT / "src" / path_value,
            ROOT.parent / path_value,
        ])
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def migrate_project_documents(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "project_documents"):
        return

    add_column(conn, "project_documents", "file_hash", "file_hash VARCHAR(64)")
    add_column(conn, "project_documents", "mime_type", "mime_type VARCHAR(150)")

    rows = conn.execute(
        "SELECT id, file_path, original_filename FROM project_documents"
    ).fetchall()
    for row_id, file_path, original_filename in rows:
        path = resolve_file(file_path)
        if path:
            file_hash = sha256_file(path)
            mime_type = "text/plain" if path.suffix.lower() in {".txt", ".md"} else None
            conn.execute(
                """
                UPDATE project_documents
                SET file_hash = COALESCE(file_hash, ?),
                    mime_type = COALESCE(mime_type, ?)
                WHERE id = ?
                """,
                (file_hash, mime_type, row_id),
            )

    duplicate_rows = conn.execute(
        """
        SELECT project_id, file_hash, MIN(id) AS keep_id
        FROM project_documents
        WHERE file_hash IS NOT NULL AND file_hash != ''
        GROUP BY project_id, file_hash
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    removed = 0
    for project_id, file_hash, keep_id in duplicate_rows:
        removed += conn.execute(
            """
            DELETE FROM project_documents
            WHERE project_id = ? AND file_hash = ? AND id != ?
            """,
            (project_id, file_hash, keep_id),
        ).rowcount

    if table_exists(conn, "projects"):
        conn.execute(
            """
            UPDATE projects
            SET document_count = (
                SELECT COUNT(*) FROM project_documents
                WHERE project_documents.project_id = projects.id
            )
            """
        )

    print(f"project_documents migrated, duplicate rows removed: {removed}")


def migrate_assets_and_tags(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS project_document_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            asset_type VARCHAR(50) NOT NULL,
            content TEXT,
            storage_path VARCHAR(1000),
            asset_metadata JSON,
            status VARCHAR(30) NOT NULL DEFAULT 'completed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(document_id) REFERENCES project_documents(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS project_document_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'auto',
            source VARCHAR(50) NOT NULL DEFAULT 'keyword',
            confidence INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY(document_id) REFERENCES project_documents(id) ON DELETE CASCADE
        )
        """
    )


def migrate_chunks(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "document_chunks"):
        return

    for name, ddl in [
        ("chunk_id", "chunk_id VARCHAR(100)"),
        ("text", "text TEXT"),
        ("text_length", "text_length INTEGER"),
        ("total_chunks", "total_chunks INTEGER"),
        ("token_count", "token_count INTEGER"),
        ("start_pos", "start_pos INTEGER"),
        ("end_pos", "end_pos INTEGER"),
        ("page_number", "page_number INTEGER"),
        ("speaker", "speaker VARCHAR(100)"),
        ("timestamp_start", "timestamp_start INTEGER"),
        ("timestamp_end", "timestamp_end INTEGER"),
        ("embedding", "embedding JSON"),
        ("chunk_metadata", "chunk_metadata JSON"),
        ("prev_chunk_id", "prev_chunk_id VARCHAR(100)"),
        ("next_chunk_id", "next_chunk_id VARCHAR(100)"),
        ("vectorized_at", "vectorized_at DATETIME"),
        ("metadata", "metadata JSON"),
    ]:
        add_column(conn, "document_chunks", name, ddl)

    colset = columns(conn, "document_chunks")
    if "chunk_text" in colset:
        conn.execute("UPDATE document_chunks SET text = COALESCE(text, chunk_text)")
    if "chunk_size" in colset:
        conn.execute("UPDATE document_chunks SET text_length = COALESCE(text_length, chunk_size)")
    if "embedding_vector" in colset:
        conn.execute("UPDATE document_chunks SET embedding = COALESCE(embedding, embedding_vector)")
    if "extra_metadata" in colset:
        conn.execute("UPDATE document_chunks SET metadata = COALESCE(metadata, extra_metadata)")
        conn.execute("UPDATE document_chunks SET chunk_metadata = COALESCE(chunk_metadata, extra_metadata)")

    conn.execute(
        """
        UPDATE document_chunks
        SET chunk_id = COALESCE(chunk_id, 'chunk_' || id),
            text_length = COALESCE(text_length, LENGTH(text)),
            total_chunks = COALESCE(total_chunks, (
                SELECT COUNT(*) FROM document_chunks AS c2
                WHERE c2.document_id = document_chunks.document_id
            ))
        """
    )
    print("document_chunks migrated")


def main() -> None:
    db_path = db_path_from_env()
    print(f"migrating sqlite database: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        migrate_project_documents(conn)
        migrate_assets_and_tags(conn)
        migrate_chunks(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
