from __future__ import annotations

from functools import lru_cache
from math import sqrt

from sentence_transformers import SentenceTransformer

from ..config import settings
from ..db import fetch_all


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def cosine_similarity(lhs: list[float], rhs: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(lhs, rhs, strict=False))
    lhs_norm = sqrt(sum(a * a for a in lhs))
    rhs_norm = sqrt(sum(b * b for b in rhs))
    if lhs_norm == 0 or rhs_norm == 0:
        return 0.0
    return numerator / (lhs_norm * rhs_norm)


def lexical_search(query: str, limit: int = 10) -> list[dict[str, float | int | str]]:
    rows = fetch_all(
        """
        SELECT id, name, frequency
        FROM concepts
        WHERE name LIKE ?
        ORDER BY frequency DESC, name ASC
        LIMIT ?
        """,
        (f"%{query.lower()}%", limit),
    )
    return [
        {
            "concept_id": int(row["id"]),
            "name": str(row["name"]),
            "score": 1.0,
            "frequency": int(row["frequency"]),
        }
        for row in rows
    ]


def semantic_search(query: str, limit: int = 10) -> list[dict[str, float | int | str]]:
    concepts = fetch_all("SELECT id, name, frequency FROM concepts")
    if not concepts:
        return []

    try:
        model = get_model()
        query_vector = model.encode(query).tolist()
        concept_vectors = model.encode([str(row["name"]) for row in concepts]).tolist()
        scored = [
            {
                "concept_id": int(row["id"]),
                "name": str(row["name"]),
                "score": cosine_similarity(query_vector, vector),
                "frequency": int(row["frequency"]),
            }
            for row, vector in zip(concepts, concept_vectors, strict=False)
        ]
        scored.sort(key=lambda item: float(item["score"]), reverse=True)
        return scored[:limit]
    except Exception:
        return lexical_search(query, limit)

