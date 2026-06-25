from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .database import (
    fetch_all,
    fetch_document,
    fetch_one,
    init_db,
    insert_chunk,
    insert_document,
    insert_relationship,
    settings,
    update_document_status,
    upsert_concept,
)
from .graph import build_concept_graph, prerequisite_path
from .pipeline import (
    chunk_text,
    compute_checksum,
    extract_concepts,
    parse_document,
    sanitize_filename,
    semantic_search,
    validate_upload,
)
from .schemas import (
    ConceptDetail,
    ConceptRead,
    DocumentRead,
    GraphEdge,
    GraphNode,
    GraphResponse,
    LearningPathResponse,
    LearningPathStep,
    ResetResponse,
    SearchResult,
    UploadResult,
)

def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

def create_app() -> FastAPI:
    configure_logging()
    
    if os.getenv("KNOWLEDGE_VAULT_RESET") == "true":
        from .database import reset_knowledge_base
        reset_knowledge_base()

    init_db()

    app = FastAPI(
        title="Knowledge Vault API",
        description="Local-first API for document ingestion and concept graph exploration.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.env,
            "database": str(settings.database_url),
        }

    @app.post("/api/admin/reset", response_model=ResetResponse, tags=["admin"])
    async def admin_reset() -> ResetResponse:
        try:
            from .database import reset_knowledge_base
            stats = reset_knowledge_base()
            logging.info(f"Knowledge base reset successful: {stats}")
            return ResetResponse(success=True, **stats)
        except Exception as e:
            logging.error(f"Knowledge base reset failed: {e}")
            return ResetResponse(
                success=False,
                deleted_documents=0,
                deleted_chunks=0,
                deleted_concepts=0,
                deleted_relationships=0,
                error=str(e)
            )

    @app.post("/api/upload", response_model=UploadResult, tags=["upload"])
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
            
            # Map concepts to their first seen character position
            # This is a bit complex as extract_concepts doesn't return positions yet
            # Let's adjust extract_concepts signature or handle it here
            concept_ids = {}
            for concept in concepts:
                # Find first occurrence in text
                first_pos = text.lower().find(concept.name.lower())
                first_pos = first_pos if first_pos != -1 else 0
                
                concept_ids[concept.name] = upsert_concept(
                    name=concept.name,
                    description=concept.description,
                    embedding=concept.embedding,
                    entity_type=concept.entity_type,
                    first_seen_index=first_pos
                )

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

    @app.get("/api/graph", response_model=GraphResponse, tags=["graph"])
    def get_graph() -> GraphResponse:
        graph_obj = build_concept_graph()
        nodes = [
            GraphNode(id=node_id, label=str(attrs["label"]), frequency=int(attrs["frequency"]))
            for node_id, attrs in graph_obj.nodes(data=True)
        ]
        edges = [
            GraphEdge(
                id=str(attrs["id"]),
                source=str(source),
                target=str(target),
                relationship_type=str(attrs["relationship_type"]),
                weight=float(attrs["weight"]),
            )
            for source, target, attrs in graph_obj.edges(data=True)
        ]
        return GraphResponse(nodes=nodes, edges=edges)

    @app.get("/api/search", response_model=list[SearchResult], tags=["search"])
    def search_concepts(
        q: str = Query(..., min_length=2),
        limit: int = Query(default=10, ge=1, le=50),
    ) -> list[SearchResult]:
        return [SearchResult.model_validate(item) for item in semantic_search(q, limit)]

    @app.get("/api/learning-path/{concept_id}", response_model=LearningPathResponse, tags=["learning-path"])
    def get_learning_path(
        concept_id: int,
        depth: int = Query(default=5, ge=1, le=10),
    ) -> LearningPathResponse:
        steps = [LearningPathStep.model_validate(step) for step in prerequisite_path(concept_id, depth)]
        return LearningPathResponse(target_concept_id=concept_id, steps=steps)

    @app.get("/api/concepts", response_model=list[ConceptRead], tags=["concepts"])
    def list_concepts(
        q: str | None = Query(default=None),
        entity_type: str | None = Query(default=None)
    ) -> list[ConceptRead]:
        sql = "SELECT * FROM concepts"
        params: list[Any] = []
        where_clauses: list[str] = []

        if q:
            where_clauses.append("name LIKE ?")
            params.append(f"%{q.lower()}%")
        
        if entity_type and entity_type != "All":
            where_clauses.append("entity_type = ?")
            params.append(entity_type)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        sql += " ORDER BY frequency DESC, name ASC"
        
        rows = fetch_all(sql, tuple(params))
        return [ConceptRead.model_validate(dict(row)) for row in rows]

    @app.get("/api/concepts/{concept_id}", response_model=ConceptDetail, tags=["concepts"])
    def get_concept(concept_id: int) -> ConceptDetail:
        concept = fetch_one("SELECT * FROM concepts WHERE id = ?", (concept_id,))
        if concept is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found.")

        related_rows = fetch_all(
            """
            SELECT DISTINCT c.*
            FROM concepts c
            JOIN concept_relationships r
                ON c.id = r.source_concept_id OR c.id = r.target_concept_id
            WHERE (r.source_concept_id = ? OR r.target_concept_id = ?)
              AND c.id != ?
            ORDER BY c.frequency DESC, c.name ASC
            LIMIT 12
            """,
            (concept_id, concept_id, concept_id),
        )

        return ConceptDetail(
            concept=ConceptRead.model_validate(dict(concept)),
            related=[ConceptRead.model_validate(dict(row)) for row in related_rows],
        )

    @app.get("/api/stats/types", tags=["admin"])
    def get_type_stats() -> dict[str, int]:
        rows = fetch_all("SELECT entity_type, count(*) as count FROM concepts GROUP BY entity_type")
        return {str(row["entity_type"]): int(row["count"]) for row in rows}

    return app

app = create_app()
