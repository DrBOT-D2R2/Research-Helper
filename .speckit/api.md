# API

## `GET /health`

Returns service health and storage path information.

## `POST /api/upload`

Uploads one document and triggers local ingestion.

Request:

- Multipart form field `file`

Response:

- Stored document metadata
- Ingestion counts for chunks, concepts, and relationships

## `GET /api/concepts`

Returns all concepts, optionally filtered by search text.

Query params:

- `q`: optional name filter

## `GET /api/concepts/{concept_id}`

Returns concept details plus related concepts.

## `GET /api/graph`

Returns graph nodes and edges for visualization.

## `GET /api/search`

Performs concept search.

Query params:

- `q`: required query string
- `limit`: result count

## `GET /api/learning-path/{concept_id}`

Returns a prerequisite path for the requested concept.

Query params:

- `depth`: optional maximum traversal depth

