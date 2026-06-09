type StatCardProps = {
  label: string;
  value: string | number;
};

export default function StatCard({ label, value }: StatCardProps) {
  return (
    <article className="card stat-card">
      <span className="muted">{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

