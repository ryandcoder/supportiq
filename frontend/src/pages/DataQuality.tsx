import KpiCard from "../components/KpiCard";
import PageHeader from "../components/PageHeader";
import { useApi } from "../hooks/useApi";
import { int, shortDate } from "../lib/format";
import { getDataQuality } from "../services/api";

export default function DataQuality() {
  const { data, loading, error } = useApi(getDataQuality, []);

  if (error) return <div className="card border-bad p-6 text-sm">{error}. Run <code>python scripts/clean_data.py</code> and restart the API.</div>;
  if (!data) return <p className="text-muted">{loading ? "Loading…" : ""}</p>;

  const missing = data.missing_values_raw.tickets ?? {};
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Cleaning report"
        title="Data quality"
        subtitle="Produced by the cleaning step. Every change made to the raw files is listed below; nothing is modified silently."
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard label="Tickets" value={int(data.records_raw.tickets)} />
        <KpiCard label="Merchants / agents" value={`${int(data.records_raw.merchants)} / ${int(data.records_raw.agents)}`} />
        <KpiCard label="Duplicates removed" value={int(data.duplicates_removed)} />
        <KpiCard label="Invalid records flagged" value={int(data.invalid_records_flagged)} />
      </div>
      <p className="text-sm text-muted">
        Tickets created {shortDate(data.date_range[0])} to {shortDate(data.date_range[1])}.
      </p>

      <section className="card p-4">
        <h2 className="text-lg font-semibold">Missing values (tickets)</h2>
        <p className="mb-3 text-sm italic text-muted">Blank resolution fields belong to open tickets; blank CSAT means no survey response.</p>
        <table className="w-full">
          <thead className="border-b border-line"><tr><th className="th">Column</th><th className="th text-right">Missing</th></tr></thead>
          <tbody className="divide-y divide-line">
            {Object.entries(missing).map(([col, n]) => (
              <tr key={col}><td className="td">{col}</td><td className="td text-right">{int(Number(n))}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card p-4">
        <h2 className="mb-3 text-lg font-semibold">Change log</h2>
        <table className="w-full">
          <thead className="border-b border-line">
            <tr><th className="th">Table</th><th className="th">Action</th><th className="th text-right">Rows</th></tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.change_log.map((l, i) => (
              <tr key={i}>
                <td className="td text-muted">{l.table}</td>
                <td className="td !whitespace-normal">{l.action}</td>
                <td className="td text-right">{int(l.rows_affected)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
