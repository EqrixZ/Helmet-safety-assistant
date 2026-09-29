import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { AggregateRow } from '@/api/types'
import { formatNumber, formatPercent, zoneLabel } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { AXIS_TICK, CHART } from './palette'

export function ZoneBarChart({ data }: { data: AggregateRow[] }) {
  const rows = data.map((r) => ({ ...r, label: zoneLabel(r.key) }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }} barGap={2} barCategoryGap="28%">
        <CartesianGrid horizontal={false} stroke={CHART.grid} />
        <XAxis type="number" allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} />
        <YAxis type="category" dataKey="label" width={78} tick={{ ...AXIS_TICK, fill: '#475569', fontSize: 12 }} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: '#F8FAFC' }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as (AggregateRow & { label: string }) | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={row.label}
                rows={[
                  { label: 'ละเมิด', value: formatNumber(row.violations), color: CHART.violation },
                  { label: 'เหตุการณ์ทั้งหมด', value: formatNumber(row.events), color: CHART.totalSoft },
                  { label: 'อัตราการละเมิด', value: formatPercent(row.rate) },
                ]}
              />
            )
          }}
        />
        <Bar dataKey="events" fill={CHART.totalSoft} radius={[0, 4, 4, 0]} maxBarSize={14} />
        <Bar dataKey="violations" fill={CHART.violation} radius={[0, 4, 4, 0]} maxBarSize={14} />
      </BarChart>
    </ResponsiveContainer>
  )
}
