import { useState, type ChangeEvent } from "react";
import { apiClient } from "../../api/client";
import type { UploadResult } from "../../types/api";

export default function UploadPanel() {
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.postForm<UploadResult>("/api/upload", formData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card stack">
      <label className="upload-dropzone">
        <input type="file" accept=".pdf,.txt,.md" onChange={onChange} hidden />
        <span>Select a PDF, TXT, or Markdown file</span>
        <small className="muted">Files are parsed locally by the FastAPI backend.</small>
      </label>
      {loading ? <p>Ingesting document...</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {result ? (
        <div className="stack">
          <h3>Last upload</h3>
          <p>
            <strong>{result.document.filename}</strong> processed with status{" "}
            <strong>{result.document.status}</strong>.
          </p>
          <div className="grid">
            <div className="card inset">
              <span className="muted">Chunks</span>
              <strong>{result.chunk_count}</strong>
            </div>
            <div className="card inset">
              <span className="muted">Concepts</span>
              <strong>{result.concept_count}</strong>
            </div>
            <div className="card inset">
              <span className="muted">Relationships</span>
              <strong>{result.relationship_count}</strong>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
