import type { LearningPathResponse } from "../../types/api";

type LearningPathViewProps = {
  path: LearningPathResponse;
};

export default function LearningPathView({ path }: LearningPathViewProps) {
  return (
    <div className="stack">
      {path.steps.map((step) => (
        <article className="card" key={`${step.concept_id}-${step.depth}`}>
          <div className="row between">
            <div>
              <h3>{step.name}</h3>
              <p className="muted">Concept ID {step.concept_id}</p>
            </div>
            <strong>Depth {step.depth}</strong>
          </div>
        </article>
      ))}
    </div>
  );
}
