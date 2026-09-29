import { ArrowRight, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ZoneSummary } from '@/api/types'
import { Sparkline } from '@/components/charts/Sparkline'
import { Card } from '@/components/ui/card'
import { formatNumber, formatPercent, riskLevel, zoneLabel } from '@/lib/format'
import { cn } from '@/lib/utils'

const RISK_STYLES = {
  high: { chip: 'bg-rose-50 text-rose-700 ring-rose-200', bar: 'bg-rose-500', spark: '#E11D48', stripe: 'from-rose-500' },
  medium: { chip: 'bg-amber-50 text-amber-700 ring-amber-200', bar: 'bg-amber-500', spark: '#F28C28', stripe: 'from-amber-400' },
  low: { chip: 'bg-emerald-50 text-emerald-700 ring-emerald-200', bar: 'bg-emerald-500', spark: '#10B981', stripe: 'from-emerald-400' },
} as const

export function ZoneCard({ zone, index }: { zone: ZoneSummary; index: number }) {
  const risk = riskLevel(zone.rate)
  const s = RISK_STYLES[risk.tone]
  return (
    <Link to={`/events?zone=${encodeURIComponent(zone.key)}`} className="group block outline-none">
      <Card
        className="card-hover relative h-full overflow-hidden p-5 group-focus-visible:ring-[3px] group-focus-visible:ring-primary/30"
        style={{ animationDelay: `${index * 60}ms` }}
      >
        <div className={cn('absolute inset-x-0 top-0 h-1 bg-gradient-to-r to-transparent', s.stripe)} />
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-slate-100 text-slate-600">
              <MapPin className="size-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">{zoneLabel(zone.key)}</h3>
              <div className="font-mono text-[11px] text-slate-400">{zone.key}</div>
            </div>
          </div>
          <span className={cn('rounded-full px-2.5 py-1 text-xs font-semibold ring-1', s.chip)}>ความเสี่ยง{risk.label}</span>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <div>
            <div className="text-[11px] text-slate-500">เหตุการณ์</div>
            <div className="text-lg font-bold text-slate-900 tabular-nums">{formatNumber(zone.events)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-500">ละเมิด</div>
            <div className="text-lg font-bold text-rose-600 tabular-nums">{formatNumber(zone.violations)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-500">อัตรา</div>
            <div className="text-lg font-bold text-slate-900 tabular-nums">{formatPercent(zone.rate, 0)}</div>
          </div>
        </div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div className={cn('h-full rounded-full transition-all duration-700', s.bar)} style={{ width: `${Math.min(100, zone.rate * 100)}%` }} />
        </div>

        <div className="mt-4">
          <div className="mb-1 text-[11px] text-slate-400">การละเมิดรายวัน 14 วันล่าสุด</div>
          <div className="h-14">
            <Sparkline values={zone.sparkline} color={s.spark} id={zone.key} />
          </div>
        </div>
        <div className="mt-3 flex items-center justify-end gap-1 text-xs font-medium text-slate-400 transition group-hover:text-primary">
          ดูเหตุการณ์ในโซนนี้ <ArrowRight className="size-3.5 transition group-hover:translate-x-0.5" />
        </div>
      </Card>
    </Link>
  )
}
