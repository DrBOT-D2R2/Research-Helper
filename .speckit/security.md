# Security

## Local Data Handling

- All uploaded files are stored on local disk under `data/uploads/`.
- No file contents are transmitted to third-party services.
- SQLite stays local under `data/sqlite/`.

## File Validation Strategy

- Allow only `.pdf`, `.txt`, and `.md`
- Enforce maximum upload size before writing to disk
- Normalize filenames to avoid path traversal
- Hash file bytes for deduplication and traceability
- Reject empty files

## Future Hardening

- Magic-byte sniffing for PDF validation
- File quarantine for parse failures
- Optional encryption at rest for stored documents and database

