import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";
import EmptyState from "../components/EmptyState";
import { apiClient } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Concept, GraphResponse } from "../types/api";

export default function DashboardPage() {
  const concepts = useAsync<Concept[]>(() => apiClient.get("/api/concepts"), []);
  const graph = useAsync<GraphResponse>(() => apiClient.get("/api/graph"), []);

  return (
    <section className="stack">
      <PageHeader
        title="Dashboard"
        description="Inspect current graph size and verify the repository is indexed locally."
      />
      <div className="grid">
        <StatCard label="Concepts" value={concepts.data?.length ?? 0} />
        <StatCard label="Relationships" value={graph.data?.edges.length ?? 0} />
        <StatCard label="Graph Nodes" value={graph.data?.nodes.length ?? 0} />
      </div>
      {!concepts.loading && (concepts.data?.length ?? 0) === 0 ? (
        <EmptyState
          title="No concepts indexed yet"
          body="Upload a document to initialize the concept graph and start exploring."
        />
      ) : null}
    </section>
  );
}

