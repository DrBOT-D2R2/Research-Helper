from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import re

import spacy
from spacy.language import Language

from ..config import settings


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


_NLP: Language | None = None


def get_nlp() -> Language:
    global _NLP
    if _NLP is None:
        try:
            _NLP = spacy.load(settings.spacy_model)
        except OSError:
            _NLP = spacy.blank("en")
            if "sentencizer" not in _NLP.pipe_names:
                _NLP.add_pipe("sentencizer")
    return _NLP


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


def fallback_candidates(text: str) -> list[str]:
    return [
        candidate.lower()
        for candidate in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", text)
        if candidate.lower() not in {"the", "and", "for", "with", "that", "this"}
    ]
