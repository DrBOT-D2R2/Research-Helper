from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True)
class Document:
    id: int
    filename: str
    file_type: str
    checksum: str
    storage_path: str
    status: str
    created_at: datetime

@dataclass(slots=True)
class Chunk:
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_estimate: int
    char_start: int
    char_end: int

@dataclass(slots=True)
class Concept:
    id: int
    name: str
    description: str | None
    embedding: str | None
    frequency: int
    created_at: datetime

@dataclass(slots=True)
class ConceptRelationship:
    id: int
    source_concept_id: int
    target_concept_id: int
    relationship_type: str
    weight: float
    evidence_chunk_id: int | None
