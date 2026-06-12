import { useState } from "react";
import { apiClient } from "../api/client";
import ConceptList from "../features/concepts/ConceptList";
import { useAsync } from "../hooks/useAsync";
import PageHeader from "../components/PageHeader";
import type { Concept } from "../types/api";

export default function ConceptExplorerPage() {
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState("Concept");
  
  const { data, error, loading } = useAsync<Concept[]>(
    () => {
      const params = new URLSearchParams();
      if (query) params.append("q", query);
      if (entityType) params.append("entity_type", entityType);
      return apiClient.get(`/api/concepts?${params.toString()}`);
    },
    [query, entityType],
  );

  return (
    <section className="stack">
      <PageHeader
        title="Concept Explorer"
        description="Search and inspect concepts extracted from your local document set."
      />
      <div style={{ display: "flex", gap: "1rem" }}>
        <input
          className="search-input"
          style={{ flex: 1 }}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search concepts..."
        />
        <select 
          className="search-input"
          style={{ width: "auto" }}
          value={entityType} 
          onChange={(e) => setEntityType(e.target.value)}
        >
          <option value="All">All Types</option>
          <option value="Concept">Concept</option>
          <option value="Formula">Formula</option>
          <option value="Measurement">Measurement</option>
          <option value="Unit">Unit</option>
          <option value="Variable">Variable</option>
        </select>
      </div>
      {loading ? <p>Loading concepts...</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {data ? <ConceptList concepts={data} /> : null}
    </section>
  );
}

