import type { Concept } from "../../types/api";

type ConceptListProps = {
  concepts: Concept[];
};

export default function ConceptList({ concepts }: ConceptListProps) {
  return (
    <div className="stack">
      {concepts.map((concept) => (
        <article key={concept.id} className="card">
          <div className="row between">
            <div>
              <h3>{concept.name}</h3>
              <p className="muted">{concept.description ?? "No description yet."}</p>
            </div>
            <strong>{concept.frequency} mentions</strong>
          </div>
        </article>
      ))}
    </div>
  );
}

