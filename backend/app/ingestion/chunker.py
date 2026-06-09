from __future__ import annotations

from dataclasses import dataclass


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

