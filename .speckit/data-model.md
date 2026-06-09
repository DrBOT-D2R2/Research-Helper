# Data Model

## Document

- `id`: unique identifier
- `filename`: original file name
- `file_type`: `pdf`, `txt`, or `md`
- `checksum`: SHA-256 hash for deduplication
- `storage_path`: local saved file path
- `status`: ingestion lifecycle status
- `created_at`: upload timestamp

## Chunk

- `id`: unique identifier
- `document_id`: parent document
- `chunk_index`: order within the document
- `content`: normalized text chunk
- `token_estimate`: approximate token count
- `char_start`: source offset start
- `char_end`: source offset end

## Concept

- `id`: unique identifier
- `name`: canonical concept label
- `description`: optional summary or definition
- `embedding`: serialized vector for semantic search
- `frequency`: number of mentions across chunks
- `created_at`: first seen timestamp

## Relationship

- `id`: unique identifier
- `source_concept_id`: upstream concept
- `target_concept_id`: downstream concept
- `relationship_type`: `depends_on`, `related_to`, `mentioned_with`
- `weight`: confidence or frequency-derived score
- `evidence_chunk_id`: supporting chunk when available

## Design Notes

- The MVP stores one embedding per concept, not per chunk, to keep the schema lean.
- Chunk text is retained for traceability and future explanation generation.
- Relationships are directed so prerequisite traversal works from day one.

