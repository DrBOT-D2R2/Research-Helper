# Observability

## Logging

- Structured application logger with level from environment
- Log upload, parse, chunk, extraction, and graph build events
- Log parse failures with document context

## Metrics

The MVP does not introduce a full metrics stack, but it should track:

- documents ingested
- chunks created
- concepts extracted
- relationships created
- endpoint latency

## Error Handling

- API returns explicit validation and processing errors
- Ingestion failures mark document status as failed
- Search falls back gracefully when embeddings are not available

