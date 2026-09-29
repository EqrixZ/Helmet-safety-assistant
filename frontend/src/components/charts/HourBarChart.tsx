import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { AggregateRow } from '@/api/types'
import { formatHourKey, formatHourRange, formatNumber, formatPercent } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { AXIS_TICK, CHART } from './palette'

export function HourBarChart({ data }: { data: AggregateRow[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }} barGap={2}>
        <CartesianGrid vertical={false} stroke={CHART.grid} />
        <XAxis dataKey="key" tickFormatter={formatHourKey} tick={AXIS_TICK} tickLine={false} axisLine={false} />
        <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: '#F8FAFC' }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as AggregateRow | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={formatHourRange(row.key)}
                rows={[
                  { label: 'ละเมิด', value: formatNumber(row.violations), color: CHART.violation },
                  { label: 'เหตุการณ์ทั้งหมด', value: formatNumber(row.events), color: CHART.totalSoft },
                  { label: 'อัตราการละเมิด', value: formatPercent(row.rate) },
                ]}
              />
            )
          }}
        />
        <Bar dataKey="events" fill={CHART.totalSoft} radius={[4, 4, 0, 0]} maxBarSize={18} />
        <Bar dataKey="violations" fill={CHART.violation} radius={[4, 4, 0, 0]} maxBarSize={18} />
      </BarChart>
    </ResponsiveContainer>
  )
}
