from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
import sqlite3
import os
from typing import Any, Iterator

@dataclass(slots=True)
class Settings:
    env: str = os.getenv("KNOWLEDGE_VAULT_ENV", "development")
    host: str = os.getenv("KNOWLEDGE_VAULT_HOST", "0.0.0.0")
    port: int = int(os.getenv("KNOWLEDGE_VAULT_PORT", "8000"))
    data_dir: Path = Path(os.getenv("KNOWLEDGE_VAULT_DATA_DIR", "./data"))
    database_url: Path = Path(
        os.getenv("KNOWLEDGE_VAULT_DATABASE_URL", "./data/sqlite/knowledge_vault.db")
    )
    log_level: str = os.getenv("KNOWLEDGE_VAULT_LOG_LEVEL", "INFO")
    embedding_model: str = os.getenv(
        "KNOWLEDGE_VAULT_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    spacy_model: str = os.getenv("KNOWLEDGE_VAULT_SPACY_MODEL", "en_core_web_sm")
    max_upload_size_bytes: int = 10 * 1024 * 1024

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.database_url.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    checksum TEXT NOT NULL UNIQUE,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_estimate INTEGER NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding TEXT,
    frequency INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concept_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_concept_id INTEGER NOT NULL,
    target_concept_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,
    weight REAL NOT NULL,
    evidence_chunk_id INTEGER,
    UNIQUE(source_concept_id, target_concept_id, relationship_type, evidence_chunk_id),
    FOREIGN KEY(source_concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    FOREIGN KEY(target_concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    FOREIGN KEY(evidence_chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);
"""

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.database_url)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection

@contextmanager
def db_cursor() -> Iterator[sqlite3.Cursor]:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def init_db() -> None:
    Path(settings.database_url).parent.mkdir(parents=True, exist_ok=True)
    with db_cursor() as cursor:
        cursor.executescript(SCHEMA_SQL)

def utc_now() -> str:
    return datetime.now(UTC).isoformat()

def insert_document(filename: str, file_type: str, checksum: str, storage_path: str, status: str) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO documents (filename, file_type, checksum, storage_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (filename, file_type, checksum, storage_path, status, utc_now()),
        )
        return int(cursor.lastrowid)

def update_document_status(document_id: int, status: str) -> None:
    with db_cursor() as cursor:
        cursor.execute("UPDATE documents SET status = ? WHERE id = ?", (status, document_id))

def fetch_document(document_id: int) -> sqlite3.Row | None:
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        return cursor.fetchone()

def insert_chunk(document_id: int, chunk_index: int, content: str, token_estimate: int, char_start: int, char_end: int) -> int:
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, content, token_estimate, char_start, char_end)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, chunk_index, content, token_estimate, char_start, char_end),
        )
        return int(cursor.lastrowid)

def upsert_concept(name: str, description: str | None = None, embedding: str | None = None) -> int:
    with db_cursor() as cursor:
        cursor.execute("SELECT id, frequency FROM concepts WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "UPDATE concepts SET frequency = ?, description = COALESCE(?, description) WHERE id = ?",
                (int(row["frequency"]) + 1, description, int(row["id"])),
            )
            return int(row["id"])

        cursor.execute(
            """
            INSERT INTO concepts (name, description, embedding, frequency, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, description, embedding, 1, utc_now()),
        )
        return int(cursor.lastrowid)

def insert_relationship(source_concept_id: int, target_concept_id: int, relationship_type: str, weight: float, evidence_chunk_id: int | None) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT OR IGNORE INTO concept_relationships (
                source_concept_id, target_concept_id, relationship_type, weight, evidence_chunk_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_concept_id, target_concept_id, relationship_type, weight, evidence_chunk_id),
        )

def reset_knowledge_base() -> None:
    # 1. Print counts before deletion
    with db_cursor() as cursor:
        cursor.execute("SELECT count(*) as count FROM documents")
        doc_count = cursor.fetchone()["count"]
        cursor.execute("SELECT count(*) as count FROM chunks")
        chunk_count = cursor.fetchone()["count"]
        cursor.execute("SELECT count(*) as count FROM concepts")
        concept_count = cursor.fetchone()["count"]
        cursor.execute("SELECT count(*) as count FROM concept_relationships")
        rel_count = cursor.fetchone()["count"]

    print("--- Before Reset ---")
    print(f"Documents: {doc_count}")
    print(f"Chunks: {chunk_count}")
    print(f"Concepts: {concept_count}")
    print(f"Relationships: {rel_count}")

    # 2. Delete all existing data
    with db_cursor() as cursor:
        # Tables are linked by foreign keys with ON DELETE CASCADE
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM concepts")
    
    # 2.5 Vacuum to clear any remaining storage (must be outside transaction)
    conn = get_connection()
    try:
        conn.execute("VACUUM")
    finally:
        conn.close()

    # 3. Clear uploaded files
    upload_dir = settings.data_dir / "uploads"
    if upload_dir.exists():
        import shutil
        for item in upload_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    
    # 4. Print counts after deletion
    with db_cursor() as cursor:
        cursor.execute("SELECT count(*) as count FROM documents")
        doc_count = cursor.fetchone()["count"]
        cursor.execute("SELECT count(*) as count FROM concepts")
        concept_count = cursor.fetchone()["count"]

    print("--- After Reset ---")
    print(f"Documents: {doc_count}")
    print(f"Concepts: {concept_count}")
    print("Knowledge base has been fully reset.")

def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    with db_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()

def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    with db_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()
