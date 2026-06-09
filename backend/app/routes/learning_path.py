from __future__ import annotations

from fastapi import APIRouter, Query

from ..graph.traversal import prerequisite_path
from ..schemas import LearningPathResponse, LearningPathStep


router = APIRouter(prefix="/api", tags=["learning-path"])


@router.get("/learning-path/{concept_id}", response_model=LearningPathResponse)
def get_learning_path(
    concept_id: int,
    depth: int = Query(default=5, ge=1, le=10),
) -> LearningPathResponse:
    steps = [LearningPathStep.model_validate(step) for step in prerequisite_path(concept_id, depth)]
    return LearningPathResponse(target_concept_id=concept_id, steps=steps)
