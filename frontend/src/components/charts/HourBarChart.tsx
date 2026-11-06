import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import type { AggregateRow } from '@/api/types'
import { formatHourKey, formatHourRange, formatNumber, formatPercent } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { useChartTheme } from './palette'

export function HourBarChart({ data }: { data: AggregateRow[] }) {
  const c = useChartTheme()
  const { t } = useTranslation()
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }} barGap={2}>
        <CartesianGrid {...c.gridProps} />
        <XAxis dataKey="key" tickFormatter={formatHourKey} tick={c.axisTick} tickLine={false} axisLine={false} />
        <YAxis allowDecimals={false} tick={c.axisTick} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: c.violationSoft, opacity: 0.5 }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as AggregateRow | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={formatHourRange(row.key)}
                rows={[
                  { label: t('charts.violations'), value: formatNumber(row.violations), color: c.violation },
                  { label: t('charts.totalEvents'), value: formatNumber(row.events), color: c.totalSoft },
                  { label: t('charts.rate'), value: formatPercent(row.rate) },
                ]}
              />
            )
          }}
        />
        <Bar dataKey="events" fill={c.totalSoft} radius={[6, 6, 0, 0]} maxBarSize={14} />
        <Bar dataKey="violations" fill={c.violation} radius={[6, 6, 0, 0]} maxBarSize={14} />
      </BarChart>
    </ResponsiveContainer>
  )
}
