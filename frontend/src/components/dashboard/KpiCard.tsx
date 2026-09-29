import { ArrowDownRight, ArrowUpRight, Minus, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import type { Trend } from '@/api/types'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

type Polarity = 'up-good' | 'up-bad' | 'neutral'

function TrendChip({ trend, polarity }: { trend: Trend; polarity: Polarity }) {
  const pct = trend.change_pct
  if (pct === null) {
    return <span className="text-[11px] text-slate-400">ไม่มีข้อมูลช่วงก่อนหน้า</span>
  }
  const up = pct > 0
  const flat = pct === 0
  const bad = !flat && ((polarity === 'up-bad' && up) || (polarity === 'up-good' && !up))
  const good = !flat && !bad && polarity !== 'neutral'
  const Icon = flat ? Minus : up ? ArrowUpRight : ArrowDownRight
  return (
    <span className="flex items-center gap-1.5">
      <span
        className={cn(
          'inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums',
          bad && 'bg-rose-50 text-rose-600',
          good && 'bg-emerald-50 text-emerald-600',
          !bad && !good && 'bg-slate-100 text-slate-500',
        )}
      >
        <Icon className="size-3.5" />
        {Math.abs(pct).toFixed(1)}%
      </span>
      <span className="text-[11px] text-slate-400">เทียบช่วงก่อนหน้า</span>
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
  accent: 'orange' | 'rose' | 'slate' | 'amber'
  trend?: Trend
  polarity?: Polarity
  loading: boolean
  delay?: number
}) {
  const accents = {
    orange: 'bg-primary/10 text-primary',
    rose: 'bg-rose-50 text-rose-500',
    slate: 'bg-slate-100 text-slate-600',
    amber: 'bg-amber-50 text-amber-600',
  }
  return (
    <Card className="card-hover relative overflow-hidden p-5" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-start justify-between">
        <div className="text-[13px] font-medium text-slate-500">{label}</div>
        <div className={cn('grid size-9 place-items-center rounded-lg', accents[accent])}>
          <Icon className="size-[18px]" />
        </div>
      </div>
      {loading ? (
        <div className="mt-2 space-y-2.5">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-36" />
        </div>
      ) : (
        <>
          <div className="mt-1 truncate text-[28px] leading-tight font-bold tracking-tight text-slate-900 tabular-nums">{value}</div>
          <div className="mt-2 flex min-h-5 items-center">
            {trend ? <TrendChip trend={trend} polarity={polarity} /> : <span className="truncate text-[11px] text-slate-400">{sub}</span>}
          </div>
        </>
      )}
    </Card>
  )
}
