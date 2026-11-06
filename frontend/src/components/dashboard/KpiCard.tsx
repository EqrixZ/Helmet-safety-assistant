import { ArrowDownRight, ArrowUpRight, Minus, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { Trend } from '@/api/types'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

type Polarity = 'up-good' | 'up-bad' | 'neutral'

function TrendChip({ trend, polarity }: { trend: Trend; polarity: Polarity }) {
  const { t } = useTranslation()
  const pct = trend.change_pct
  if (pct === null) {
    return <span className="text-[11px] text-slate-400">{t('dashboard.kpi.noPrevious')}</span>
  }
  const up = pct > 0
  const flat = pct === 0
  const bad = !flat && ((polarity === 'up-bad' && up) || (polarity === 'up-good' && !up))
  const good = !flat && !bad && polarity !== 'neutral'
  const Icon = flat ? Minus : up ? ArrowUpRight : ArrowDownRight
  return (
    <span className="flex min-w-0 items-center gap-1.5">
      <span
        className={cn(
          'inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums',
          bad && 'bg-red-soft text-red-ink',
          good && 'bg-green-soft text-green-ink',
          !bad && !good && 'bg-slate-100 text-slate-500',
        )}
      >
        <Icon className="size-3.5" />
        {Math.abs(pct).toFixed(1)}%
      </span>
      <span className="truncate text-[11px] whitespace-nowrap text-caption">{t('dashboard.kpi.vsPrevious')}</span>
    </span>
  )
}

export function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  accent,
  trend,
  polarity = 'neutral',
  loading,
  delay = 0,
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
  icon: LucideIcon
  accent: 'blue' | 'green' | 'orange' | 'red'
  trend?: Trend
  polarity?: Polarity
  loading: boolean
  delay?: number
}) {
  const accents = {
    blue: 'bg-tile-blue',
    green: 'bg-tile-green',
    orange: 'bg-tile-orange',
    red: 'bg-tile-red',
  }
  return (
    <Card className="card-hover relative overflow-hidden p-6" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="truncate text-[13px] text-caption">{label}</div>
          {loading ? (
            <div className="mt-2 space-y-2.5">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-4 w-36" />
            </div>
          ) : (
            <>
              <div className="mt-1 truncate text-[28px] leading-tight font-bold tracking-tight text-navy tabular-nums">{value}</div>
              <div className="mt-2 flex min-h-5 items-center">
                {trend ? <TrendChip trend={trend} polarity={polarity} /> : <span className="truncate text-[11px] text-caption">{sub}</span>}
              </div>
            </>
          )}
        </div>
        <div className={cn('grid size-14 shrink-0 place-items-center rounded-2xl text-white', accents[accent])}>
          <Icon className="size-6" strokeWidth={2.2} />
        </div>
      </div>
    </Card>
  )
}
