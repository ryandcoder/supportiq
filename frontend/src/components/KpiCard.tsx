export default function KpiCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 font-serif text-3xl font-semibold leading-tight">{value}</div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}
