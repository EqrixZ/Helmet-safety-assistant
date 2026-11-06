import type { ReactNode } from 'react'

export type TooltipRow = { label: string; value: string; color?: string }

export function ChartTooltipBox({ title, rows }: { title: ReactNode; rows: TooltipRow[] }) {
  return (
    <div className="min-w-40 rounded-lg border border-slate-200 bg-elevated/95 px-3 py-2 text-xs shadow-lg backdrop-blur">
      <div className="mb-1.5 font-semibold text-slate-800">{title}</div>
      <div className="space-y-1">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-slate-500">
              {r.color && <span className="size-2 rounded-full" style={{ background: r.color }} />}
              {r.label}
            </span>
            <span className="font-semibold text-slate-800 tabular-nums">{r.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
