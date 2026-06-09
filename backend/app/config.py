from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


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

