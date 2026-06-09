from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentRead(BaseModel):
    id: int
    filename: str
    file_type: str
    checksum: str
    storage_path: str
    status: str
    created_at: datetime


class ChunkRead(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_estimate: int
    char_start: int
    char_end: int


class ConceptRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    frequency: int
    created_at: datetime


class RelationshipRead(BaseModel):
    id: int
    source_concept_id: int
    target_concept_id: int
    relationship_type: str
    weight: float
    evidence_chunk_id: int | None = None


class UploadResult(BaseModel):
    document: DocumentRead
    chunk_count: int
    concept_count: int
    relationship_count: int


class GraphNode(BaseModel):
    id: str
    label: str
    frequency: int = 1


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    weight: float


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ConceptDetail(BaseModel):
    concept: ConceptRead
    related: list[ConceptRead] = Field(default_factory=list)


class SearchResult(BaseModel):
    concept_id: int
    name: str
    score: float
    frequency: int


class LearningPathStep(BaseModel):
    concept_id: int
    name: str
    depth: int


class LearningPathResponse(BaseModel):
    target_concept_id: int
    steps: list[LearningPathStep]

