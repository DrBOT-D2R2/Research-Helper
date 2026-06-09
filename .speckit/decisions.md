# Decisions

## ADR-001: SQLite as the only persistent store

Status: accepted

Reason:

- Keeps the MVP local-first and simple
- Avoids infrastructure overhead
- Works well for single-user workflows

## ADR-002: Plain module boundaries over service decomposition

Status: accepted

Reason:

- A one-week MVP benefits from an in-process architecture
- Parsing, storage, graph traversal, and search remain testable without microservices

## ADR-003: NetworkX for graph operations

Status: accepted

Reason:

- Mature traversal primitives
- Easy to bridge from SQLite rows
- Good enough for MVP graph sizes

## ADR-004: Heuristic concept extraction first

Status: accepted

Reason:

- Faster to ship than training custom extractors
- Easier to debug with local data
- Leaves room for PS-1 quality improvements

