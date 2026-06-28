# Knowledge Vault

Knowledge Vault is a local-first knowledge operating system that converts personal documents into a navigable concept graph. The MVP is designed for a one-week build: ingest files locally, extract concepts, persist a graph in SQLite, search it, generate prerequisite paths, and explore the result visually.

## Why this project exists

Personal notes and study material usually stay trapped in folders and PDFs. Search helps locate strings, but it does not explain how ideas depend on one another. Knowledge Vault turns source material into a concept graph so a single user can ask:

- What concepts exist in my documents?
- How are they related?
- What should I learn before topic X?
- Which source documents support this concept?

## MVP Architecture

The stack is intentionally simple and local:

- Frontend: React, TypeScript, Vite, React Flow
- Backend: FastAPI, Python 3.12
- Storage: SQLite
- Graph engine: NetworkX
- Parsing: PyMuPDF for PDF, native readers for TXT and Markdown
- NLP: spaCy noun phrase and entity extraction
- Embeddings: SentenceTransformers for semantic concept search

High-level flow:

1. The user uploads PDF, TXT, or Markdown files.
2. The backend validates and stores each file locally.
3. Documents are parsed into text chunks.
4. spaCy extracts candidate concepts and sentence-level relationships.
5. The graph builder writes concepts and relationships into SQLite and materializes a NetworkX graph for traversal.
6. The frontend visualizes the graph and supports concept lookup and learning-path generation.

## Folder Structure

```text
knowledge-vault/
├── .github/
├── .speckit/
├── backend/
├── data/
├── docs/
├── frontend/
├── scripts/
├── shared/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── pyproject.toml
└── README.md
```

## Quick Start

### Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
python scripts/download_spacy_model.py
uvicorn backend.app.main:app --reload
```

The API will start on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will start on `http://localhost:5173`.

## Development Workflow

- Backend API changes live under `backend/app/`.
- Frontend UI and graph exploration live under `frontend/src/`.
- Product, architecture, and risk documents live in `.speckit/`.
- Tests live under `tests/`.

Run checks from the repository root:

```bash
ruff check .
black --check .
mypy backend
pytest
cd frontend && npm run build
```

## Repository Notes

- Local-first: all files and graph data stay on the local machine.
- Single-user: there is no authentication or multi-tenant logic.
- Extensible: the MVP keeps document parsing, concept extraction, graph traversal, and search in separate modules so PS-1 expansion can add richer ranking, annotation, and better relationship extraction without a rewrite.

## Roadmap Snapshot

- MVP: local ingestion, concept extraction, graph visualization, semantic search, learning paths
- PS-1 version: richer chunking, feedback loops for concept cleanup, graph editing, citation trails
- Future version: spaced review workflows, local vector index alternatives, import/export, plugin-style ingestion pipelines

Detailed planning lives in [.speckit/README.md](/Users/DruhinDatta1/knowledge-vault/.speckit/README.md).
