import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";
import FilterBar from "./FilterBar";
import { Icon, IconName } from "./Icons";

interface NavItem { to: string; label: string; icon: IconName }

const ANALYTICS: NavItem[] = [
  { to: "/", label: "Overview", icon: "grid" },
  { to: "/breakdowns", label: "Breakdowns", icon: "chart" },
  { to: "/insights", label: "Insights", icon: "bulb" },
  { to: "/team", label: "Team", icon: "users" },
  { to: "/tickets", label: "Tickets", icon: "list" },
];
const DATA: NavItem[] = [
  { to: "/data-quality", label: "Data quality", icon: "shield" },
  { to: "/upload", label: "Upload data", icon: "upload" },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition ${
    isActive ? "bg-teal-soft font-medium text-teal" : "text-muted hover:bg-teal-soft/60 hover:text-ink"
  }`;

function ThemeButton({ compact = false }: { compact?: boolean }) {
  const { theme, toggle } = useTheme();
  return (
    <button onClick={toggle} className="btn w-full" aria-label="Toggle light and dark mode">
      <Icon name={theme === "dark" ? "sun" : "moon"} />
      {!compact && (theme === "dark" ? "Light mode" : "Dark mode")}
    </button>
  );
}

function NavGroup({ title, items }: { title: string; items: NavItem[] }) {
  return (
    <div>
      <div className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-widest text-muted">{title}</div>
      <div className="space-y-0.5">
        {items.map((l) => (
          <NavLink key={l.to} to={l.to} end className={linkClass}>
            <Icon name={l.icon} className="h-4 w-4" /> {l.label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}

export default function Layout() {
  const { pathname } = useLocation();
  const showFilters = ANALYTICS.some((l) => l.to === pathname);

  return (
    <div className="min-h-screen lg:flex">
      {/* sidebar (desktop) */}
      <aside className="no-print sticky top-0 hidden h-screen w-60 shrink-0 flex-col gap-6 border-r border-line px-4 py-6 lg:flex">
        <div className="px-3">
          <div className="font-serif text-2xl font-semibold text-teal">SupportIQ</div>
          <div className="text-xs text-muted">IT support analytics</div>
        </div>
        <nav className="flex flex-1 flex-col gap-6 overflow-auto">
          <NavGroup title="Analytics" items={ANALYTICS} />
          <NavGroup title="Data" items={DATA} />
        </nav>
        <div className="space-y-2">
          <Link to="/report" className="btn-primary w-full">
            <Icon name="file" /> Create report
          </Link>
          <ThemeButton />
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        {/* top bar (mobile) */}
        <header className="no-print border-b border-line lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <span className="font-serif text-xl font-semibold text-teal">SupportIQ</span>
            <div className="flex items-center gap-2">
              <Link to="/report" className="btn" aria-label="Create report"><Icon name="file" /></Link>
              <div className="w-11"><ThemeButton compact /></div>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-3 pb-2">
            {[...ANALYTICS, ...DATA].map((l) => (
              <NavLink key={l.to} to={l.to} end className={(s) => `${linkClass(s)} shrink-0`}>
                <Icon name={l.icon} className="h-4 w-4" /> {l.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
          {showFilters && <FilterBar />}
          <Outlet />
        </main>
      </div>
    </div>
  );
}
