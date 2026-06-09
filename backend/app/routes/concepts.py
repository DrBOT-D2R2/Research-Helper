from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..db import fetch_all, fetch_one
from ..schemas import ConceptDetail, ConceptRead


router = APIRouter(prefix="/api", tags=["concepts"])


@router.get("/concepts", response_model=list[ConceptRead])
def list_concepts(q: str | None = Query(default=None)) -> list[ConceptRead]:
    if q:
        rows = fetch_all(
            "SELECT * FROM concepts WHERE name LIKE ? ORDER BY frequency DESC, name ASC",
            (f"%{q.lower()}%",),
        )
    else:
        rows = fetch_all("SELECT * FROM concepts ORDER BY frequency DESC, name ASC")
    return [ConceptRead.model_validate(dict(row)) for row in rows]


@router.get("/concepts/{concept_id}", response_model=ConceptDetail)
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

