# Ingestion Pipeline

The MVP ingestion pipeline is intentionally deterministic:

1. Validate uploaded file type and size.
2. Save the file under `data/uploads/`.
3. Parse raw text from PDF, TXT, or Markdown.
4. Chunk text into bounded slices with source offsets.
5. Extract concepts and sentence-level relationships.
6. Persist chunks, concepts, and graph edges.

This keeps the first implementation explainable and testable while leaving space for stronger extraction later.

