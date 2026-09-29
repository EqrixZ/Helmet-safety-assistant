import { Area, AreaChart, ResponsiveContainer, Tooltip } from 'recharts'
import { ChartTooltipBox } from './ChartTooltip'

export function Sparkline({ values, color, id }: { values: number[]; color: string; id: string }) {
  const data = values.map((v, i) => ({ i, v, ago: values.length - 1 - i }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 4, right: 2, left: 2, bottom: 0 }}>
        <defs>
          <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Tooltip
          cursor={{ stroke: '#CBD5E1' }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as { v: number; ago: number } | undefined
            if (!active || !row) return null
            return (
              <ChartTooltipBox
                title={row.ago === 0 ? 'วันล่าสุด' : `${row.ago} วันก่อน`}
                rows={[{ label: 'ละเมิด', value: String(row.v), color }]}
              />
            )
          }}
        />
        <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#spark-${id})`} dot={false} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
