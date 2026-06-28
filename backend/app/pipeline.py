from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from math import sqrt
from pathlib import Path
from typing import Any, cast

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
    entity_type: str = "Concept"


@dataclass(slots=True)
class ExtractedRelationship:
    source: str
    target: str
    relationship_type: str
    weight: float


_NLP = None


def get_nlp() -> Any:
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


GENERIC_ACADEMIC_WORDS = {
    "model",
    "method",
    "result",
    "paper",
    "study",
    "data",
    "image",
    "approach",
    "system",
    "analysis",
    "performance",
    "experiment",
    "process",
    "framework",
    "technique",
    "evaluation",
    "application",
    "concept",
    "feature",
    "example",
    "table",
    "figure",
    "point",
    "solution",
    "second",
    "direction",
    "length",
    "case",
    "value",
    "term",
    "part",
    "problem",
    "question",
    "answer",
    "time",
    "number",
    "way",
    "object",
    "step",
    "fact",
    "idea",
    "sense",
    "reason",
    "change",
    "area",
    "type",
    "form",
    "level",
    "order",
    "group",
    "set",
    "end",
    "start",
    "side",
    "line",
    "work",
    "state",
    "mind",
    "life",
    "name",
    "thing",
    "hand",
    "eye",
    "word",
    "place",
    "man",
    "woman",
    "child",
    "world",
    "school",
    "family",
    "student",
    "country",
    "week",
    "company",
    "program",
    "government",
    "night",
    "mr",
    "mrs",
    "ms",
    "dr",
    "st",
    "ave",
    "rd",
    "blvd",
    "equation",
    "expression",
    "variable",
    "constant",
    "function",
    "graph",
    "difference",
    "total",
    "sum",
    "average",
    "ratio",
    "percentage",
    "rate",
    "unit",
    "quantity",
    "measurement",
    "scale",
    "range",
    "limit",
    "period",
    "particle",
    "wire",
    "velocity",
    "speed",
    "string",
    "wave",
    "medium",
    "minute",
    "hour",
    "day",
}

# Simple map for abbreviation merging (could be expanded or made dynamic)
CONCEPT_ALIAS_MAP = {
    "convolutional neural network": "cnn",
    "convolutional neural networks": "cnn",
    "magnetic resonance imaging": "mri",
    "recurrent neural network": "rnn",
    "recurrent neural networks": "rnn",
    "generative adversarial network": "gan",
    "generative adversarial networks": "gan",
    "large language model": "llm",
    "large language models": "llm",
    "natural language processing": "nlp",
    "artificial intelligence": "ai",
    "machine learning": "ml",
    "deep learning": "dl",
    "stationary wave": "standing wave",
    "stationary waves": "standing wave",
    "standing waves": "standing wave",
    "transverse waves": "transverse wave",
    "longitudinal waves": "longitudinal wave",
    "wave velocity": "wave speed",
    "wave velocities": "wave speed",
    "phase difference": "phase",
    "path difference": "phase",
    "superposition principle": "superposition",
}


def normalize_concept(name: str) -> str:
    # 1. Canonical lowercase
    name = name.lower().strip()

    # 2. Remove possessives specifically before stripping punctuation
    name = re.sub(r"'s\b", "", name)

    # 3. Remove punctuation like ( ) and leading/trailing whitespace
    name = re.sub(r"[\(\)\"']", "", name)
    name = name.replace("\n", " ")

    # 4. Remove leading articles: a, an, the
    name = re.sub(r"^(a|an|the)\s+", "", name)

    # 5. Simple plural stripping (optional but helps merging "waves" -> "wave")
    # Only if it ends in 's' and is at least 4 chars to avoid 'as', 'is', etc.
    if len(name) > 3 and name.endswith("s") and not name.endswith("ss"):
        # Very crude singularization, but effective for many technical terms
        name = name[:-1]

    # 6. Final strip
    name = name.strip()

    # 7. Alias mapping
    return CONCEPT_ALIAS_MAP.get(name, name)


def is_valid_concept(name: str, count: int, is_ner: bool) -> bool:
    # 0. Basic sanity
    if not name or len(name) < 2:
        return False

    etype = classify_entity(name)

    # If it's a specific technical type, we generally want to keep it
    if etype in {"Measurement", "Formula", "Unit", "Variable"}:
        # Still reject purely numeric strings that aren't variables or formulas
        return not (etype == "Measurement" and re.match(r"^[0-9.]+$", name))

    # Rule: Must start with a letter or number (avoid math symbols like =, +, etc.)
    if not re.match(r"^[a-z0-9]", name):
        return False

    # Rule 3: Filter generic words
    if name in GENERIC_ACADEMIC_WORDS:
        return False

    # NEW: Numeric / Junk filtering
    # Reject purely numeric or punctuation
    if re.match(r"^[0-9. ,;:-]+$", name):
        return False

    # Split into words to check composition
    words = name.split()
    if not words:
        return False

    junk_words = 0
    for w in words:
        # Numeric fragments (10, 2a, 3.14)
        if re.match(r"^[0-9.]+[a-z]?$|^[a-z][0-9.]+$", w) or (
            len(w) == 1 and w not in {"a", "i"} and w not in CONCEPT_ALIAS_MAP.values()
        ):
            junk_words += 1

    # Reject if more than 50% of the phrase is junk
    if junk_words / len(words) > 0.5:
        return False

    # Rule 5: Discard concepts appearing only once unless they are named entities or multi-word
    if count < 2 and not is_ner and " " not in name:
        return False
    # Rule 2: Prefer multi-word concepts (len > 3 for single words to avoid junk)
    if " " not in name and len(name) <= 3 and not is_ner and name not in CONCEPT_ALIAS_MAP.values():
        # Keep short single words only if they are common abbreviations (like CNN, MRI)
        return False
    # Filter out junk
    return not len(name) < 2


def classify_entity(name: str) -> str:
    # 1. Measurement: numbers followed by unit (1 cm, 10 cm, 40 cm)
    if re.search(
        r"\d+\s*(cm|m|mm|kg|g|s|Hz|hz|rad|deg|degree|meter|kilogram|second|n\b)",
        name,
        re.IGNORECASE,
    ):
        return "Measurement"

    # 2. Unit: single or common units (m, cm, kg, Hz)
    units = {"m", "cm", "mm", "kg", "g", "s", "hz", "rad", "deg", "meter", "kg/m", "n/m", "n"}
    if name in units:
        return "Unit"

    # 3. Formula: contains math operators or common math functions
    if any(op in name for op in ["=", "+", "×", "*", "/", "λ", "π", "θ", "ω", "σ", "ρ", "√"]):
        return "Formula"
    if re.search(r"\b(sin|cos|tan|log|exp|ln)\b", name, re.IGNORECASE):
        return "Formula"
    if re.search(r"\d+[a-zπθλω]", name):  # e.g., 2π, 2f
        return "Formula"

    # 4. Variable: very short, often single letter, but not a common word
    if len(name) <= 2 and name not in {"a", "i", "to", "in", "on", "of", "at"}:
        return "Variable"

    # Default
    return "Concept"


def extract_concepts(
    text: str, top_n: int = 50, sim_threshold: float = 0.4
) -> tuple[list[ExtractedConcept], list[ExtractedRelationship]]:
    nlp = get_nlp()
    doc = nlp(text)

    # Rule 1: Extract noun phrases rather than individual nouns
    candidate_counts: Counter[str] = Counter()
    ner_names: set[str] = set()

    # We need to map the normalized name back to some "original" variants for text searching later
    normalized_to_variants: dict[str, set[str]] = {}

    def add_candidate(original: str, is_ner: bool = False) -> None:
        norm = normalize_concept(original)
        if len(norm) < 2:
            return
        candidate_counts[norm] += 1
        if is_ner:
            ner_names.add(norm)
        if norm not in normalized_to_variants:
            normalized_to_variants[norm] = set()
        normalized_to_variants[norm].add(original.strip().lower())

    # Track entities
    for ent in doc.ents:
        add_candidate(ent.text, is_ner=True)

    # Track noun chunks (Rule 1)
    if doc.has_annotation("DEP"):
        for chunk in doc.noun_chunks:
            if not chunk.root.is_stop:
                add_candidate(chunk.text)

    # Report: rejected examples for inspection
    rejected = []
    filtered_candidates = {}
    for name, count in candidate_counts.items():
        if is_valid_concept(name, count, name in ner_names):
            filtered_candidates[name] = count
        else:
            rejected.append(name)

    print("--- Rejected Concept Examples ---")
    print(rejected[:15])  # Show first 15 rejected items
    print("---------------------------------")

    # Rule 6: Limit graph generation to top N concepts
    top_candidates = sorted(filtered_candidates.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_names = {name for name, count in top_candidates}

    concepts = [
        ExtractedConcept(
            name=name, description=f"Observed {count} time(s).", entity_type=classify_entity(name)
        )
        for name, count in top_candidates
    ]

    # Pre-calculate embeddings for top concepts for semantic similarity filtering
    model = get_model()
    concept_list = [c.name for c in concepts]
    if concept_list:
        embeddings = model.encode(concept_list)
        concept_to_emb = {name: emb for name, emb in zip(concept_list, embeddings, strict=True)}
    else:
        concept_to_emb = {}

    relationships_map: dict[tuple[str, str], dict[str, Any]] = {}
    dependency_keywords = {
        "before",
        "follows",
        "requires",
        "prerequisite",
        "depends",
        "using",
        "via",
    }

    for sentence in doc.sents:
        sentence_text = sentence.text.lower()

        # Which top concepts are in this sentence?
        present = []
        for name in top_names:
            # Check normalized name itself
            if name in sentence_text:
                present.append(name)
                continue
            # Check any of the original variants that were normalized to this name
            variants = normalized_to_variants.get(name, set())
            if any(v in sentence_text for v in variants):
                present.append(name)

        # Sort to ensure consistent source/target order
        present = sorted(list(set(present)))

        # Strict relationship creation:
        # 1. Same sentence (looping through present)
        for i, source in enumerate(present):
            for target in present[i + 1 :]:
                # 2. Semantic Similarity check
                sim = cosine_similarity(
                    concept_to_emb[source].tolist(), concept_to_emb[target].tolist()
                )

                # 3. Dependency detection (keyword heuristic)
                has_dep = any(kw in sentence_text for kw in dependency_keywords)

                # Only create if sufficiently similar OR explicitly linked by dependency keywords
                if sim > sim_threshold or has_dep:
                    rel_key = (source, target) if source < target else (target, source)
                    relationship_type = "depends_on" if has_dep else "related_to"

                    if rel_key not in relationships_map:
                        relationships_map[rel_key] = {
                            "source": source,
                            "target": target,
                            "type": relationship_type,
                            "weight": 0.0,
                            "max_sim": sim,
                        }
                    # Aggregate weights
                    relationships_map[rel_key]["weight"] += 1.0
                    # Preserve highest similarity
                    if sim > relationships_map[rel_key]["max_sim"]:
                        relationships_map[rel_key]["max_sim"] = sim

    [
        ExtractedRelationship(
            source=str(rel_v["source"]),
            target=str(rel_v["target"]),
            relationship_type=str(rel_v["type"]),
            weight=float(rel_v["weight"]),
        )
        for rel_v in relationships_map.values()
    ]

    # --- Relationship Scoring & Capping ---
    max_relationships_per_node = 5
    scored_rels: list[dict[str, Any]] = []
    for _rel_key, rel_val in relationships_map.items():
        # Score = Frequency * (1 + similarity) + Dependency Bonus
        score = rel_val["weight"] * (1 + rel_val["max_sim"])
        if rel_val["type"] == "depends_on":
            score += 2.0
        rel_val["score"] = score
        scored_rels.append(rel_val)

    # Cap relationships per node to keep only the strongest connections
    from collections import defaultdict

    node_connections: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scored_r in scored_rels:
        node_connections[scored_r["source"]].append(scored_r)
        node_connections[scored_r["target"]].append(scored_r)

    final_rel_keys: set[tuple[str, str]] = set()
    for _node, rels in node_connections.items():
        # Sort by score descending
        rels.sort(key=lambda x: float(x["score"]), reverse=True)
        for limit_r in rels[:max_relationships_per_node]:
            s_node = str(limit_r["source"])
            t_node = str(limit_r["target"])
            key = (s_node, t_node) if s_node < t_node else (t_node, s_node)
            final_rel_keys.add(key)

    final_relationships = [
        ExtractedRelationship(
            source=relationships_map[k]["source"],
            target=relationships_map[k]["target"],
            relationship_type=relationships_map[k]["type"],
            weight=relationships_map[k]["score"],  # Use score as weight for visualization
        )
        for k in final_rel_keys
    ]

    # Sort final relationships by weight (score) for reporting
    final_relationships.sort(key=lambda x: x.weight, reverse=True)

    # Calculate metrics
    node_count = len(concepts)
    edge_count = len(final_relationships)
    possible_edges = (node_count * (node_count - 1)) / 2 if node_count > 1 else 1
    avg_degree = (2 * edge_count / node_count) if node_count > 0 else 0
    density = edge_count / possible_edges if node_count > 1 else 0

    print("--- Final Extraction Metrics ---")
    print(f"Concept count: {node_count}")
    print(f"Relationship count: {edge_count}")
    print(f"Average degree: {avg_degree:.2f}")
    print(f"Graph density: {density:.4f}")
    print("--------------------------------")

    if final_relationships:
        print("--- Top 20 Strongest Relationships ---")
        for final_r in final_relationships[:20]:
            print(
                f"{final_r.source} <-({final_r.relationship_type})-> {final_r.target} "
                f"[Score: {final_r.weight:.2f}]"
            )
        print("---------------------------------------")

    return concepts, final_relationships


def serialize_embedding(vector: list[float]) -> str:
    return json.dumps(vector)


# -- Search --
@lru_cache(maxsize=1)
def get_model() -> Any:
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
        scored: list[dict[str, float | int | str]] = [
            {
                "concept_id": int(row["id"]),
                "name": str(row["name"]),
                "score": float(cosine_similarity(query_vector, vector)),
                "frequency": int(row["frequency"]),
            }
            for row, vector in zip(concepts, concept_vectors, strict=False)
        ]
        scored.sort(key=lambda item: float(cast(float, item["score"])), reverse=True)
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty files are not allowed."
        )

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
