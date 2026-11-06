import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import type { AggregateRow } from '@/api/types'
import { formatNumber, formatPercent, zoneLabel } from '@/lib/format'
import { ChartTooltipBox } from './ChartTooltip'
import { useChartTheme } from './palette'

export function ZoneBarChart({ data }: { data: AggregateRow[] }) {
  const c = useChartTheme()
  const { t } = useTranslation()
  const rows = data.map((r) => ({ ...r, label: zoneLabel(r.key) }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }} barGap={2} barCategoryGap="28%">
        <XAxis type="number" allowDecimals={false} tick={c.axisTick} tickLine={false} axisLine={false} />
        <YAxis type="category" dataKey="label" width={78} tick={{ ...c.axisTick, fill: c.label, fontSize: 12 }} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: c.violationSoft, opacity: 0.5 }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as (AggregateRow & { label: string }) | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={row.label}
                rows={[
                  { label: t('charts.violations'), value: formatNumber(row.violations), color: c.violation },
                  { label: t('charts.totalEvents'), value: formatNumber(row.events), color: c.totalSoft },
                  { label: t('charts.rate'), value: formatPercent(row.rate) },
                ]}
              />
            )
          }}
        />
        <Bar dataKey="events" fill={c.totalSoft} radius={[0, 6, 6, 0]} maxBarSize={12} />
        <Bar dataKey="violations" fill={c.violation} radius={[0, 6, 6, 0]} maxBarSize={12} />
      </BarChart>
    </ResponsiveContainer>
  )
}
