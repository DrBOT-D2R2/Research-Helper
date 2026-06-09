from __future__ import annotations

from fastapi import APIRouter, Query

from ..schemas import SearchResult
from ..search.semantic_search import semantic_search


router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=list[SearchResult])
def search_concepts(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[SearchResult]:
    return [SearchResult.model_validate(item) for item in semantic_search(q, limit)]
