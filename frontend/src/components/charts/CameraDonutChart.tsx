import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { AggregateRow } from '@/api/types'
import { cameraLabel, formatNumber, formatPercent } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { categoricalColor } from './palette'

export function CameraDonutChart({ data }: { data: AggregateRow[] }) {
  // Stable colour per camera (by sorted key), not by rank.
  const keys = [...data.map((d) => d.key)].sort()
  const colorOf = (k: string) => categoricalColor(keys.indexOf(k))
  const rows = data.filter((d) => d.violations > 0)
  const total = data.reduce((s, d) => s + d.violations, 0)

  return (
    <div className="flex h-full flex-col gap-3 sm:flex-row sm:items-center">
      <div className="relative h-full min-h-40 flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip
              content={({ active, payload }) => {
                const row = payload?.[0]?.payload as AggregateRow | undefined
                if (!active || !row) return null
                return (
                  <ChartTooltipBox
                    title={cameraLabel(row.key)}
                    rows={[
                      { label: 'ละเมิด', value: formatNumber(row.violations), color: colorOf(row.key) },
                      { label: 'สัดส่วน', value: formatPercent(total ? row.violations / total : 0) },
                      { label: 'เหตุการณ์ทั้งหมด', value: formatNumber(row.events) },
                    ]}
                  />
                )
              }}
            />
            <Pie
              data={rows}
              dataKey="violations"
              nameKey="key"
              innerRadius="64%"
              outerRadius="92%"
              paddingAngle={2}
              cornerRadius={4}
              stroke="#fff"
              strokeWidth={2}
            >
              {rows.map((r) => (
                <Cell key={r.key} fill={colorOf(r.key)} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-bold text-slate-900 tabular-nums">{formatNumber(total)}</div>
          <div className="text-[11px] text-slate-500">ครั้งที่ละเมิด</div>
        </div>
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-2 sm:w-40 sm:grid-cols-1">
        {[...data].sort((a, b) => a.key.localeCompare(b.key)).map((d) => (
          <li key={d.key} className="flex items-center justify-between gap-2 text-xs">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="size-2.5 rounded-sm" style={{ background: colorOf(d.key) }} />
              {cameraLabel(d.key)}
            </span>
            <span className="font-semibold text-slate-800 tabular-nums">{d.violations}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
