import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { AggregateRow } from '@/api/types'
import { formatNumber, formatPercent, formatThaiDate, formatThaiDayMonth } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { AXIS_TICK, CHART } from './palette'

export function DailyViolationsChart({ data }: { data: AggregateRow[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="gradViolation" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART.violation} stopOpacity={0.35} />
            <stop offset="100%" stopColor={CHART.violation} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradTotal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART.total} stopOpacity={0.18} />
            <stop offset="100%" stopColor={CHART.total} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke={CHART.grid} />
        <XAxis
          dataKey="key"
          tickFormatter={formatThaiDayMonth}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={false}
          minTickGap={24}
        />
        <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ stroke: '#CBD5E1', strokeDasharray: '4 4' }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as AggregateRow | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={formatThaiDate(row.key, 'long')}
                rows={[
                  { label: 'ละเมิด', value: formatNumber(row.violations), color: CHART.violation },
                  { label: 'เหตุการณ์ทั้งหมด', value: formatNumber(row.events), color: CHART.total },
                  { label: 'อัตราการละเมิด', value: formatPercent(row.rate) },
                ]}
              />
            )
          }}
        />
        <Area type="monotone" dataKey="events" stroke={CHART.total} strokeWidth={1.5} fill="url(#gradTotal)" />
        <Area
          type="monotone"
          dataKey="violations"
          stroke={CHART.violation}
          strokeWidth={2.25}
          fill="url(#gradViolation)"
          activeDot={{ r: 5, strokeWidth: 2, stroke: '#fff' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
