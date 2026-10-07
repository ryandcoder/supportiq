import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { monthLabel } from "../lib/format";
import { usePalette } from "./palette";

function useTooltipStyle() {
  const p = usePalette();
  return {
    contentStyle: { background: p.tooltipBg, border: `1px solid ${p.tooltipBorder}`, borderRadius: 8, fontSize: 12, color: p.ink },
    labelStyle: { color: p.ink },
    itemStyle: { color: p.ink },
  };
}

/* ---------- ticket volume over time ---------- */
export function VolumeChart({ data, height = 260 }: { data: { month: string; tickets: number; open: number }[]; height?: number }) {
  const p = usePalette();
  const tip = useTooltipStyle();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid stroke={p.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="month" tickFormatter={monthLabel} tick={{ fill: p.axis, fontSize: 11 }} stroke={p.grid} interval="preserveStartEnd" />
        <YAxis tick={{ fill: p.axis, fontSize: 11 }} stroke={p.grid} allowDecimals={false} />
        <Tooltip {...tip} labelFormatter={(m) => monthLabel(String(m))} />
        <Legend wrapperStyle={{ fontSize: 12, color: p.axis }} />
        <Line type="monotone" dataKey="tickets" name="All tickets" stroke={p.teal} strokeWidth={2.5} dot={{ r: 2.5 }} />
        <Line type="monotone" dataKey="open" name="Still open" stroke={p.amber} strokeWidth={2} strokeDasharray="5 4" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

/* ---------- horizontal bars (categories, sectors) ---------- */
interface BarDatum { name: string; value: number | null }

export function HBar({ data, format, color, height = 260, label }: {
  data: BarDatum[]; format: (v: number) => string; color?: string; height?: number; label: string;
}) {
  const p = usePalette();
  const tip = useTooltipStyle();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={p.grid} strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fill: p.axis, fontSize: 11 }} stroke={p.grid} tickFormatter={(v) => format(Number(v))} />
        <YAxis type="category" dataKey="name" width={140} tick={{ fill: p.axis, fontSize: 11 }} stroke={p.grid} />
        <Tooltip {...tip} cursor={{ fill: p.grid, opacity: 0.4 }} formatter={(v) => [format(Number(v)), label]} />
        <Bar dataKey="value" fill={color ?? p.teal} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---------- vertical bars (priority, CSAT bands) ---------- */
export function VBar({ data, format, colors, color, height = 260, label, yDomain }: {
  data: BarDatum[]; format: (v: number) => string; colors?: Record<string, string>; color?: string;
  height?: number; label: string; yDomain?: [number, number];
}) {
  const p = usePalette();
  const tip = useTooltipStyle();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
        <CartesianGrid stroke={p.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: p.axis, fontSize: 11 }} stroke={p.grid} />
        <YAxis tick={{ fill: p.axis, fontSize: 11 }} stroke={p.grid} tickFormatter={(v) => format(Number(v))} domain={yDomain} />
        <Tooltip {...tip} cursor={{ fill: p.grid, opacity: 0.4 }} formatter={(v) => [format(Number(v)), label]} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} fill={color ?? p.teal}>
          {data.map((d) => (
            <Cell key={d.name} fill={colors?.[d.name] ?? color ?? p.teal} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---------- donut with a centre label ---------- */
export function Donut({ data, centerValue, centerLabel, height = 240 }: {
  data: { name: string; value: number; color: string }[];
  centerValue: string; centerLabel: string; height?: number;
}) {
  const p = usePalette();
  const tip = useTooltipStyle();
  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius="62%" outerRadius="88%" paddingAngle={2} stroke="none">
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
          <Tooltip {...tip} />
          <Legend wrapperStyle={{ fontSize: 12, color: p.axis }} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-x-0 top-[40%] -translate-y-1/2 text-center">
        <div className="font-serif text-2xl font-semibold">{centerValue}</div>
        <div className="text-xs text-muted">{centerLabel}</div>
      </div>
    </div>
  );
}
