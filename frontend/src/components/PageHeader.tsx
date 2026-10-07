import { ReactNode } from "react";

export default function PageHeader({ eyebrow, title, subtitle, actions }: {
  eyebrow?: string; title: string; subtitle?: string; actions?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div>
        {eyebrow && <p className="text-xs font-medium uppercase tracking-widest text-teal">{eyebrow}</p>}
        <h1 className="mt-1 text-3xl font-semibold sm:text-4xl">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="no-print flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
