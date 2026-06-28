# Architecture

## Component Diagram

```text
[React + React Flow UI]
          |
          v
[FastAPI Routes]
          |
          v
[Ingestion Pipeline] -> [spaCy + SentenceTransformers]
          |
          v
[SQLite Store] <-> [NetworkX Graph Service]
```

## Data Flow

1. User uploads a file from the frontend.
2. FastAPI validates extension, size, and MIME hints.
3. The file is written to `data/uploads/`.
4. Parser extracts raw text.
5. Chunker splits content into bounded pieces with positional metadata.
6. Concept extractor derives concept candidates and co-occurrence relationships.
7. SQLite stores documents, chunks, concepts, and relationships.
8. Graph builder reconstructs a directed concept graph from SQLite rows.
9. Search and learning-path endpoints query the graph and return UI-ready results.

## Local-First Design

- All source files remain on disk inside the local repository data directory.
- SQLite is the sole persistent store for the MVP.
- No authentication is required because the product is single-user and offline-oriented.
- NLP and embedding models run locally; there are no hosted AI services.
- Graph traversal logic stays in-process instead of external graph infrastructure.

## Extensibility Strategy

- Parsing, chunking, extraction, storage, and traversal are separate modules.
- SQLite schema uses stable IDs so later vector indexes or annotation tables can be added without rewriting the core model.
- The API returns normalized shapes for concepts and graph nodes, making the UI resilient to backend iteration.
