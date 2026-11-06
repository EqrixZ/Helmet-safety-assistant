import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import type { AggregateRow } from '@/api/types'
import { formatNumber, formatPercent, formatDate, formatDayMonth } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { useChartTheme } from './palette'

export function DailyViolationsChart({ data }: { data: AggregateRow[] }) {
  const c = useChartTheme()
  const { t } = useTranslation()
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="gradViolation" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c.violation} stopOpacity={0.22} />
            <stop offset="100%" stopColor={c.violation} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid {...c.gridProps} />
        <XAxis
          dataKey="key"
          tickFormatter={formatDayMonth}
          tick={c.axisTick}
          tickLine={false}
          axisLine={false}
          minTickGap={24}
        />
        <YAxis allowDecimals={false} tick={c.axisTick} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ stroke: c.total, strokeDasharray: '4 4' }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as AggregateRow | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={formatDate(row.key, 'long')}
                rows={[
                  { label: t('charts.violations'), value: formatNumber(row.violations), color: c.violation },
                  { label: t('charts.totalEvents'), value: formatNumber(row.events), color: c.total },
                  { label: t('charts.rate'), value: formatPercent(row.rate) },
                ]}
              />
            )
          }}
        />
        <Area type="monotone" dataKey="events" stroke={c.total} strokeWidth={1.5} strokeDasharray="4 4" fill="none" />
        <Area
          type="monotone"
          dataKey="violations"
          stroke={c.violation}
          strokeWidth={2}
          fill="url(#gradViolation)"
          activeDot={{ r: 5, strokeWidth: 2, stroke: c.surface }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
