# Risks

## Technical Risks

### spaCy concept extraction is too noisy

Mitigation:

- Start with noun chunks and named entities only
- Filter stopword-heavy and short concepts
- Add manual review affordances in the PS-1 phase

### SentenceTransformer model load is heavy for local MVP

Mitigation:

- Lazy-load the embedder
- Fallback to lexical scoring if embeddings are unavailable

### Relationship direction may be weak

Mitigation:

- Use simple sentence heuristics for MVP
- Mark uncertain links as `related_to`
- Improve with richer dependency parsing later

### Large PDFs may slow ingestion

Mitigation:

- Bound upload size
- Process per page
- Surface ingestion progress in later iterations
