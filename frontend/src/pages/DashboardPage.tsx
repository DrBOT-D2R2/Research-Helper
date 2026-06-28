import { useState } from "react";
import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";
import EmptyState from "../components/EmptyState";
import { apiClient } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Concept, GraphResponse, ResetResponse } from "../types/api";

export default function DashboardPage() {
  const [isResetting, setIsResetting] = useState(false);
  const [resetStats, setResetStats] = useState<ResetResponse | null>(null);

  const concepts = useAsync<Concept[]>(() => apiClient.get("/api/concepts"), [resetStats]);
  const graph = useAsync<GraphResponse>(() => apiClient.get("/api/graph"), [resetStats]);
  const typeStats = useAsync<Record<string, number>>(() => apiClient.get("/api/stats/types"), [resetStats]);

  const handleReset = async () => {
    const confirm = window.confirm(
      "WARNING\n\nThis action permanently deletes:\n\n* documents\n* chunks\n* concepts\n* relationships\n* graph data\n* embeddings\n\nThis cannot be undone. Proceed?"
    );

    if (!confirm) return;

    setIsResetting(true);
    try {
      const response = await apiClient.post<ResetResponse>("/api/admin/reset");
      if (response.success) {
        setResetStats(response);
        alert(
          `Knowledge Base Reset Successful\n\nDeleted:\n* ${response.deleted_documents} documents\n* ${response.deleted_chunks} chunks\n* ${response.deleted_concepts} concepts\n* ${response.deleted_relationships} relationships`
        );
      } else {
        alert(`Reset failed: ${response.error}`);
      }
    } catch (err) {
      alert(`Error during reset: ${err}`);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <section className="stack">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <PageHeader
          title="Dashboard"
          description="Inspect current graph size and verify the repository is indexed locally."
        />
        <div style={{ padding: "0 1rem" }}>
          <button
            onClick={handleReset}
            disabled={isResetting}
            style={{
              backgroundColor: isResetting ? "#ccc" : "#d9534f",
              color: "white",
              border: "none",
              padding: "0.5rem 1rem",
              borderRadius: "4px",
              cursor: isResetting ? "not-allowed" : "pointer",
              fontWeight: "bold"
            }}
          >
            {isResetting ? "Resetting..." : "Reset Knowledge Base"}
          </button>
        </div>
      </div>

      <div className="grid">
        <StatCard label="Concepts" value={concepts.data?.length ?? 0} />
        <StatCard label="Relationships" value={graph.data?.edges.length ?? 0} />
        <StatCard label="Graph Nodes" value={graph.data?.nodes.length ?? 0} />
      </div>

      {typeStats.data && Object.keys(typeStats.data).length > 0 && (
        <div className="stack" style={{ marginTop: "2rem" }}>
          <h3>Concept Types Breakdown</h3>
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))" }}>
            {Object.entries(typeStats.data).map(([type, count]) => (
              <StatCard key={type} label={type} value={count} />
            ))}
          </div>
        </div>
      )}

      {!concepts.loading && (concepts.data?.length ?? 0) === 0 ? (
        <EmptyState
          title="No concepts indexed yet"
          body="Upload a document to initialize the concept graph and start exploring."
        />
      ) : null}
    </section>
  );
}
