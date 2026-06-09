import { apiClient } from "../api/client";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { GraphResponse } from "../types/api";
import { useAsync } from "../hooks/useAsync";
import GraphCanvas from "../features/graph/GraphCanvas";

export default function GraphExplorerPage() {
  const { data, error, loading } = useAsync<GraphResponse>(() => apiClient.get("/api/graph"), []);

  return (
    <section className="stack">
      <PageHeader
        title="Graph Explorer"
        description="Visualize extracted concepts and their dependency-style relationships."
      />
      {loading ? <p>Loading graph...</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {data && data.nodes.length > 0 ? (
        <GraphCanvas graph={data} />
      ) : (
        !loading && (
          <EmptyState
            title="Graph is empty"
            body="Upload documents to produce concepts and relationships for visualization."
          />
        )
      )}
    </section>
  );
}

