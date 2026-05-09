type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
  tone?: "neutral" | "good" | "warn" | "bad";
};

export function MetricCard({ label, value, hint, tone = "neutral" }: MetricCardProps) {
  return (
    <section className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <p>{hint}</p> : null}
    </section>
  );
}
