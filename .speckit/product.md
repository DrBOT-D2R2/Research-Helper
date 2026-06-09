# Product

## Problem Statement

Students and self-learners collect PDFs, notes, and Markdown documents, but those materials remain difficult to navigate as a coherent knowledge system. Search can locate terms, yet it rarely reveals the prerequisite structure between ideas.

## Target Users

- A single student managing class notes and reference material
- A self-learner building a concept map for a subject
- A project owner organizing technical documents for structured review

## MVP Features

- Upload PDF, TXT, and Markdown documents
- Parse documents locally and store metadata in SQLite
- Split text into chunks for downstream processing
- Extract concepts with spaCy-based heuristics
- Build a concept dependency graph with NetworkX and persist relationships
- Search concepts semantically
- Generate prerequisite paths for a target concept
- Visualize the graph in an interactive frontend

## Future Vision

Knowledge Vault becomes a personal knowledge operating system:

- Editable concepts and relationships
- Source-linked explanations and citations
- Learning plans across multiple documents and subjects
- Incremental re-indexing and background ingestion
- Exportable graph packages for presentations or coursework

