import { useState } from "react";
import { apiClient } from "../api/client";
import PageHeader from "../components/PageHeader";
import LearningPathView from "../features/learning-path/LearningPathView";
import type { LearningPathResponse } from "../types/api";

export default function LearningPathPage() {
  const [conceptId, setConceptId] = useState("1");
  const [path, setPath] = useState<LearningPathResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadPath = async () => {
    setError(null);
    try {
      const response = await apiClient.get<LearningPathResponse>(
        `/api/learning-path/${conceptId}`,
      );
      setPath(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load learning path.");
    }
  };

  return (
    <section className="stack">
      <PageHeader
        title="Learning Path"
        description="Generate a prerequisite path for a target concept ID."
      />
      <div className="row gap">
        <input
          className="search-input"
          value={conceptId}
          onChange={(event) => setConceptId(event.target.value)}
          placeholder="Enter concept ID"
        />
        <button className="button" onClick={loadPath}>
          Generate
        </button>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {path ? <LearningPathView path={path} /> : null}
    </section>
  );
}

