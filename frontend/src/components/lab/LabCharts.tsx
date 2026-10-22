import { useMemo } from "react";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CTA_LABELS, chartColors, ctaSlices, type CtaKey } from "../../lib/charts";
import { useThemeStore } from "../../stores/theme";
import type { CtaStatusTotals } from "../../types";

const KEYS: CtaKey[] = ["evidenced", "in_progress", "committed", "dropped"];

function useChartColors() {
  const theme = useThemeStore((s) => s.theme);
  // chartColors() lee las variables CSS del tema activo; se recalcula al cambiar.
  return { theme, colors: useMemo(() => chartColors(), [theme]) };
}

export function CtaLegend() {
  const { colors } = useChartColors();
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
      {KEYS.map((k) => (
        <li key={k} className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-sm" style={{ background: colors[k] }} />
          {CTA_LABELS[k]}
        </li>
      ))}
    </ul>
  );
}

export function CtaDonut({ totals, evidencedPct }: { totals: CtaStatusTotals; evidencedPct: number }) {
  const { theme, colors } = useChartColors();
  const slices = ctaSlices(totals);
  const summary = slices.length === 0 ? "Sin CTAs" : slices.map((s) => `${s.label}: ${s.value}`).join(", ");
  return (
    <div key={theme} className="flex flex-col items-center gap-3">
      <div className="relative h-52 w-52" role="img" aria-label={`CTAs por estado. ${summary}`}>
        {slices.length === 0 ? (
          <svg viewBox="0 0 100 100" className="h-full w-full">
            <circle cx="50" cy="50" r="40" fill="none" strokeWidth="12" className="stroke-line" />
          </svg>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={slices} dataKey="value" nameKey="label" innerRadius="70%" outerRadius="100%" stroke="none" paddingAngle={slices.length > 1 ? 2 : 0}>
                {slices.map((s) => <Cell key={s.key} fill={colors[s.key]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle()} itemStyle={{ color: "rgb(var(--ink))" }} />
            </PieChart>
          </ResponsiveContainer>
        )}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          {slices.length === 0 ? (
            <span className="text-sm text-muted">Sin CTAs</span>
          ) : (
            <>
              <span className="font-display text-3xl font-semibold tabular-nums text-ink">{evidencedPct}%</span>
              <span className="text-xs text-muted">con evidencia</span>
            </>
          )}
        </div>
      </div>
      <CtaLegend />
    </div>
  );
}

function tooltipStyle() {
  return {
    background: "rgb(var(--surface))",
    border: "1px solid rgb(var(--line))",
    borderRadius: 8,
    color: "rgb(var(--ink))",
    fontSize: 12,
  };
}

export function CtaStackedBars({ rows }: { rows: { label: string; totals: CtaStatusTotals }[] }) {
  const { theme, colors } = useChartColors();
  if (rows.length === 0) return <p className="text-sm text-muted">Sin datos.</p>;
  const data = rows.map((r) => ({ label: r.label, ...r.totals }));
  return (
    <div key={theme}>
      <div style={{ height: 40 * rows.length + 40 }} role="img" aria-label={rows.map((r) => `${r.label}: ${r.totals.evidenced} de ${r.totals.total} con evidencia`).join("; ")}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 8, bottom: 0, left: 0 }}>
            <XAxis type="number" allowDecimals={false} stroke={colors.grid} tick={{ fill: colors.text, fontSize: 11 }} />
            <YAxis type="category" dataKey="label" width={130} stroke={colors.grid} tick={{ fill: colors.text, fontSize: 11 }} />
            <Tooltip cursor={{ fill: colors.grid, opacity: 0.4 }} contentStyle={tooltipStyle()} itemStyle={{ color: "rgb(var(--ink))" }} labelStyle={{ color: "rgb(var(--ink))" }} />
            {KEYS.map((k) => <Bar key={k} dataKey={k} name={CTA_LABELS[k]} stackId="cta" fill={colors[k]} />)}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2"><CtaLegend /></div>
    </div>
  );
}
