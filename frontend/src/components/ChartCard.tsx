import { ReactNode, useState } from "react";
import { Icon } from "./Icons";

/** Editorial card: title, one data-driven sentence, then the content. The chevron hides/shows the content. */
export default function ChartCard({ title, caption, children, className = "" }: {
  title: string; caption?: string; children: ReactNode; className?: string;
}) {
  const [open, setOpen] = useState(true);
  return (
    <section className={`card p-4 ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-label={open ? `Hide ${title}` : `Show ${title}`}
          className="btn-ghost no-print -mr-1 -mt-1 shrink-0 !px-1.5"
        >
          <Icon name="chevronDown" className={`h-4 w-4 transition-transform ${open ? "" : "-rotate-90"}`} />
        </button>
      </div>
      {caption && <p className="mt-0.5 text-sm italic text-muted">{caption}</p>}
      {open && <div className="mt-3">{children}</div>}
    </section>
  );
}
