from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from math import sqrt
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile, status

from .database import fetch_all, settings

# -- Chunking --
@dataclass(slots=True)
class TextChunk:
    index: int
    content: str
    char_start: int
    char_end: int
    token_estimate: int

def chunk_text(text: str, max_chars: int = 500) -> list[TextChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            split_at = normalized.rfind(" ", start, end)
            if split_at > start:
                end = split_at
        content = normalized[start:end].strip()
        if content:
            chunks.append(
                TextChunk(
                    index=index,
                    content=content,
                    char_start=start,
                    char_end=end,
                    token_estimate=max(1, len(content.split())),
                )
            )
            index += 1
        start = max(end + 1, start + 1)
    return chunks

# -- Parsing --
def parse_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported file type: {suffix}")

def parse_pdf(file_path: Path) -> str:
    document = fitz.open(file_path)
    pages = [page.get_text("text") for page in document]
    document.close()
    return "\n".join(page.strip() for page in pages if page.strip())

# -- Concept Extraction --
@dataclass(slots=True)
class ExtractedConcept:
    name: str
    description: str | None = None
    embedding: str | None = None

@dataclass(slots=True)
class ExtractedRelationship:
    source: str
    target: str
    relationship_type: str
    weight: float

_NLP = None

def get_nlp():
    global _NLP
    if _NLP is None:
        import spacy
        try:
            _NLP = spacy.load(settings.spacy_model)
        except OSError:
            _NLP = spacy.blank("en")
            if "sentencizer" not in _NLP.pipe_names:
                _NLP.add_pipe("sentencizer")
    return _NLP

def fallback_candidates(text: str) -> list[str]:
    return [
        candidate.lower()
        for candidate in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", text)
        if candidate.lower() not in {"the", "and", "for", "with", "that", "this"}
    ]

def extract_concepts(text: str) -> tuple[list[ExtractedConcept], list[ExtractedRelationship]]:
    nlp = get_nlp()
    doc = nlp(text)

    if doc.has_annotation("DEP"):
        candidates = [
            chunk.text.strip().lower()
            for chunk in doc.noun_chunks
            if len(chunk.text.strip()) > 2 and not chunk.root.is_stop
        ]
    else:
        candidates = fallback_candidates(text)

    candidates.extend(ent.text.strip().lower() for ent in doc.ents if len(ent.text.strip()) > 2)

    frequency = Counter(candidate for candidate in candidates if candidate.isascii())
    concepts = [
        ExtractedConcept(name=name, description=f"Observed {count} time(s) in source text.")
        for name, count in frequency.items()
    ]

    relationships: list[ExtractedRelationship] = []
    for sentence in doc.sents:
        if doc.has_annotation("POS"):
            sentence_concepts = sorted(
                {
                    token.text.strip().lower()
                    for token in sentence
                    if token.pos_ in {"NOUN", "PROPN"} and len(token.text.strip()) > 2
                }
            )
        else:
            sentence_concepts = sorted(set(fallback_candidates(sentence.text)))
        for index, source in enumerate(sentence_concepts):
            for target in sentence_concepts[index + 1 :]:
                relationship_type = "depends_on" if "before" in sentence.text.lower() else "related_to"
                relationships.append(
                    ExtractedRelationship(
                        source=source,
                        target=target,
                        relationship_type=relationship_type,
                        weight=1.0,
                    )
                )

    return concepts, relationships

def serialize_embedding(vector: list[float]) -> str:
    return json.dumps(vector)

# -- Search --
@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
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

# -- File Validation / Security --
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

async def validate_upload(file: UploadFile) -> bytes:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty files are not allowed.")

    if len(payload) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB MVP upload limit.",
        )

    return payload

def sanitize_filename(filename: str) -> str:
    stem = SAFE_FILENAME_RE.sub("-", Path(filename).stem).strip("-") or "document"
    return f"{stem}{Path(filename).suffix.lower()}"

def compute_checksum(payload: bytes) -> str:
    return sha256(payload).hexdigest()
