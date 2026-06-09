from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from ..config import settings
from ..db import (
    fetch_document,
    insert_chunk,
    insert_document,
    insert_relationship,
    update_document_status,
    upsert_concept,
)
from ..ingestion.chunker import chunk_text
from ..ingestion.concept_extractor import extract_concepts
from ..ingestion.parser import parse_document
from ..schemas import DocumentRead, UploadResult
from ..security.file_validation import compute_checksum, sanitize_filename, validate_upload


router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResult)
async def upload_document(file: UploadFile = File(...)) -> UploadResult:
    payload = await validate_upload(file)
    checksum = compute_checksum(payload)
    safe_name = sanitize_filename(file.filename or "document.txt")
    output_path = settings.data_dir / "uploads" / safe_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)

    document_id = insert_document(
        filename=safe_name,
        file_type=Path(safe_name).suffix.lstrip("."),
        checksum=checksum,
        storage_path=str(output_path),
        status="processing",
    )

    try:
        text = parse_document(output_path)
        chunks = chunk_text(text)
        chunk_ids: list[int] = []
        for chunk in chunks:
            chunk_ids.append(
                insert_chunk(
                    document_id=document_id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    token_estimate=chunk.token_estimate,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                )
            )

        concepts, relationships = extract_concepts(text)
        concept_ids = {
            concept.name: upsert_concept(
                name=concept.name,
                description=concept.description,
                embedding=concept.embedding,
            )
            for concept in concepts
        }

        for relationship in relationships:
            source_id = concept_ids.get(relationship.source)
            target_id = concept_ids.get(relationship.target)
            if source_id and target_id and source_id != target_id:
                insert_relationship(
                    source_concept_id=source_id,
                    target_concept_id=target_id,
                    relationship_type=relationship.relationship_type,
                    weight=relationship.weight,
                    evidence_chunk_id=chunk_ids[0] if chunk_ids else None,
                )

        update_document_status(document_id, "ready")
        row = fetch_document(document_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document not found after ingestion.")

        return UploadResult(
            document=DocumentRead.model_validate(dict(row)),
            chunk_count=len(chunks),
            concept_count=len(concept_ids),
            relationship_count=len(relationships),
        )
    except Exception as exc:
        update_document_status(document_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc

