/*
import { DragEvent, useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "../components/Icons";
import KpiCard from "../components/KpiCard";
import PageHeader from "../components/PageHeader";
import { useApi } from "../hooks/useApi";
import { int } from "../lib/format";
import { errorMessages, getUploadStatus, uploadFiles } from "../services/api";
import type { UploadResult } from "../types";

const FIELDS = [
  { key: "agents", label: "agents.csv", cols: "agent_id, agent_name, tier, primary_category, shift_region, efficiency_multiplier" },
  { key: "merchants", label: "merchants.csv", cols: "merchant_id, merchant_name, sector, tier, region" },
  {
    key: "tickets",
    label: "tickets.csv",
    cols: "ticket_id, merchant_id, category, sub_category, priority (P1-P4), created_at, is_legacy, assigned_agent_id, category_mismatch, first_response_at, closed_at, ttfr_hours, resolution_hours, response_breached, resolution_breached, is_reopened, is_reopen_child, is_incident_ticket, csat_score",
  },
] as const;
type Key = (typeof FIELDS)[number]["key"];

const kb = (n: number) => (n < 1024 * 1024 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`);

function DropZone({ label, cols, file, onFile }: { label: string; cols: string; file?: File; onFile: (f?: File) => void }) {
  const [over, setOver] = useState(false);
  const drop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  };
  return (
    <div>
      <label
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={drop}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-4 py-6 text-center transition ${
          file ? "border-good bg-good/5" : over ? "border-teal bg-teal-soft" : "border-line hover:border-teal hover:bg-teal-soft/50"
        }`}
      >
        <span className={`grid h-10 w-10 place-items-center rounded-full ${file ? "bg-good/15 text-good" : "bg-teal-soft text-teal"}`}>
          <Icon name={file ? "check" : "file"} className="h-5 w-5" />
        </span>
        <span className="text-sm font-semibold">{label}</span>
        {file ? (
          <span className="text-xs text-muted">{file.name} · {kb(file.size)}</span>
        ) : (
          <span className="text-xs text-muted">Drop the file here or click to choose</span>
        )}
        <input type="file" accept=".csv,text/csv" className="sr-only" onChange={(e) => onFile(e.target.files?.[0])} />
      </label>
      <div className="mt-1.5 flex items-start justify-between gap-2">
        <details className="text-xs text-muted">
          <summary className="cursor-pointer">Required columns</summary>
          <p className="mt-1">{cols}</p>
        </details>
        {file && (
          <button type="button" className="btn-ghost !px-1.5 !py-0.5 text-xs" onClick={() => onFile(undefined)}>
            <Icon name="x" className="h-3 w-3" /> Remove
          </button>
        )}
      </div>
    </div>
  );
}

function Step({ n, label, done, current }: { n: number; label: string; done: boolean; current: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`grid h-6 w-6 place-items-center rounded-full text-xs font-semibold ${done ? "bg-good text-paper" : current ? "bg-teal text-paper" : "bg-line text-muted"}`}>
        {done ? <Icon name="check" className="h-3.5 w-3.5" /> : n}
      </span>
      <span className={`text-sm ${current || done ? "font-medium" : "text-muted"}`}>{label}</span>
    </div>
  );
}

export default function Upload() {
  const status = useApi(getUploadStatus, []);
  const [files, setFiles] = useState<Partial<Record<Key, File>>>({});
  const [checked, setChecked] = useState<UploadResult | null>(null);
  const [done, setDone] = useState<UploadResult | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  const ready = Boolean(files.agents && files.merchants && files.tickets);
  const picked = Object.values(files).filter(Boolean).length;

  const pick = (key: Key, file?: File) => {
    setFiles({ ...files, [key]: file });
    setChecked(null); // a changed file must be checked again
    setDone(null);
    setErrors([]);
  };

  const run = async (dryRun: boolean) => {
    if (!files.agents || !files.merchants || !files.tickets) return;
    if (!dryRun && !window.confirm("This replaces ALL agents, merchants and tickets in the database. Continue?")) return;
    setBusy(true);
    setErrors([]);
    try {
      const result = await uploadFiles({ agents: files.agents, merchants: files.merchants, tickets: files.tickets }, dryRun);
      if (dryRun) setChecked(result);
      else {
        setDone(result);
        setChecked(null);
      }
    } catch (e) {
      setErrors(errorMessages(e));
      setChecked(null);
    } finally {
      setBusy(false);
    }
  };

  if (status.data && !status.data.enabled) {
    return (
      <>
        <PageHeader eyebrow="Your data" title="Upload data" />
        <div className="card p-6">
          <h2 className="text-xl font-semibold">Uploads are disabled</h2>
          <p className="mt-2 text-sm text-muted">
            Set <code>ALLOW_UPLOAD=true</code> in <code>.env</code> and restart the API. Keep it off on a public deployment, because there is no login.
          </p>
        </div>
      </>
    );
  }

  const shown = done ?? checked;
  const r = shown?.report;

  return (
    <>
      <PageHeader
        eyebrow="Your data"
        title="Upload data"
        subtitle="Choose the three CSV files. They go through the same cleaning as the command-line script. Check first (nothing changes), then replace the data. Your original files are never modified."
      />

      <section className="card space-y-5 p-5">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <Step n={1} label="Choose 3 files" done={ready} current={!ready} />
          <Step n={2} label="Check" done={Boolean(checked || done)} current={ready && !checked && !done} />
          <Step n={3} label="Replace data" done={Boolean(done)} current={Boolean(checked) && !done} />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {FIELDS.map((f) => (
            <DropZone key={f.key} label={f.label} cols={f.cols} file={files[f.key]} onFile={(file) => pick(f.key, file)} />
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 border-t border-line pt-4">
          <button className="btn" disabled={!ready || busy} onClick={() => run(true)}>
            <Icon name="check" /> {busy && !checked ? "Working…" : "Check files"}
          </button>
          <button className="btn-primary" disabled={!checked || busy} onClick={() => run(false)}>
            <Icon name="upload" /> Replace data
          </button>
          <span className="text-xs text-muted">{picked}/3 files chosen · max {status.data?.max_mb ?? 10} MB each · extra columns are ignored</span>
        </div>
      </section>

      {errors.length > 0 && (
        <section className="card border-bad p-4">
          <h2 className="text-lg font-semibold text-bad">Nothing was changed</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {errors.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </section>
      )}

      {done && (
        <section className="card border-good p-4">
          <h2 className="text-lg font-semibold text-good">Data replaced</h2>
          <p className="mt-1 text-sm">
            Loaded {int(done.loaded?.tickets)} tickets, {int(done.loaded?.merchants)} merchants and {int(done.loaded?.agents)} agents.{" "}
            <Link to="/" className="text-teal underline">Open the overview</Link>
          </p>
        </section>
      )}

      {r && (
        <>
          <p className="text-sm text-muted">{done ? "Cleaning report for the loaded data:" : "Check passed. This is what replacing the data would do:"}</p>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <KpiCard label="Tickets kept" value={`${int(r.records_clean.tickets)} / ${int(r.records_raw.tickets)}`} />
            <KpiCard label="Rows dropped" value={int(r.dropped_records)} />
            <KpiCard label="Duplicates removed" value={int(r.duplicates_removed)} />
            <KpiCard label="Invalid values fixed" value={int(r.invalid_records_flagged)} />
          </div>
          <section className="card p-4">
            <h2 className="mb-3 text-lg font-semibold">What the cleaning changed</h2>
            <table className="w-full">
              <thead className="border-b border-line"><tr><th className="th">Table</th><th className="th">Action</th><th className="th text-right">Rows</th></tr></thead>
              <tbody className="divide-y divide-line">
                {r.change_log.filter((l) => l.rows_affected > 0).map((l, i) => (
                  <tr key={i}>
                    <td className="td text-muted">{l.table}</td>
                    <td className="td !whitespace-normal">{l.action}</td>
                    <td className="td text-right">{int(l.rows_affected)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </>
  );
}
*/