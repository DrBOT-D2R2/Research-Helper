import { useState } from "react";
import { apiClient } from "../api/client";
import ConceptList from "../features/concepts/ConceptList";
import { useAsync } from "../hooks/useAsync";
import PageHeader from "../components/PageHeader";
import type { Concept } from "../types/api";

export default function ConceptExplorerPage() {
  const [query, setQuery] = useState("");
  const { data, error, loading } = useAsync<Concept[]>(
    () => apiClient.get(`/api/concepts${query ? `?q=${encodeURIComponent(query)}` : ""}`),
    [query],
  );

  return (
    <section className="stack">
      <PageHeader
        title="Concept Explorer"
        description="Search and inspect concepts extracted from your local document set."
      />
      <input
        className="search-input"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Filter concepts..."
      />
      {loading ? <p>Loading concepts...</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {data ? <ConceptList concepts={data} /> : null}
    </section>
  );
}

