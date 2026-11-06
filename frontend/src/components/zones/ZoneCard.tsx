import { ArrowRight, MapPin } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import type { ZoneSummary } from '@/api/types'
import { useChartTheme } from '@/components/charts/palette'
import { Sparkline } from '@/components/charts/Sparkline'
import { Card } from '@/components/ui/card'
import { formatNumber, formatPercent, riskLevel, zoneLabel } from '@/lib/format'
import { cn } from '@/lib/utils'

const RISK_STYLES = {
  high: { chip: 'bg-red-soft text-red-ink', bar: 'bg-tile-red', tile: 'bg-tile-red' },
  medium: { chip: 'bg-orange-soft text-orange-ink', bar: 'bg-tile-orange', tile: 'bg-tile-orange' },
  low: { chip: 'bg-green-soft text-green-ink', bar: 'bg-tile-green', tile: 'bg-tile-green' },
} as const

export function ZoneCard({ zone, index }: { zone: ZoneSummary; index: number }) {
  const chart = useChartTheme()
  const { t } = useTranslation()
  const risk = riskLevel(zone.rate)
  const s = RISK_STYLES[risk.tone]
  return (
    <Link to={`/events?zone=${encodeURIComponent(zone.key)}`} className="group block outline-none">
      <Card
        className="card-hover relative h-full overflow-hidden p-6 group-focus-visible:ring-[3px] group-focus-visible:ring-primary/30"
        style={{ animationDelay: `${index * 60}ms` }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={cn('grid size-11 place-items-center rounded-xl text-white', s.tile)}>
              <MapPin className="size-5" />
            </div>
            <div>
              <h3 className="font-semibold text-navy">{zoneLabel(zone.key)}</h3>
              <div className="font-mono text-[11px] text-slate-400">{zone.key}</div>
            </div>
          </div>
          <span className={cn('rounded-full px-2.5 py-1 text-xs font-semibold', s.chip)}>
            {t('risk.label', { level: risk.label })}
          </span>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <div>
            <div className="text-[11px] text-slate-500">{t('zones.card.events')}</div>
            <div className="text-lg font-bold text-slate-900 tabular-nums">{formatNumber(zone.events)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-500">{t('zones.card.violations')}</div>
            <div className="text-lg font-bold text-red-ink tabular-nums">{formatNumber(zone.violations)}</div>
          </div>
          <div>
            <div className="text-[11px] text-slate-500">{t('zones.card.rate')}</div>
            <div className="text-lg font-bold text-slate-900 tabular-nums">{formatPercent(zone.rate, 0)}</div>
          </div>
        </div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div className={cn('h-full rounded-full transition-all duration-700', s.bar)} style={{ width: `${Math.min(100, zone.rate * 100)}%` }} />
        </div>

        <div className="mt-4">
          <div className="mb-1 text-[11px] text-caption">{t('zones.card.sparkTitle')}</div>
          <div className="h-14">
            <Sparkline values={zone.sparkline} color={chart.violation} id={zone.key} />
          </div>
        </div>
        <div className="mt-3 flex items-center justify-end gap-1 text-xs font-medium text-slate-400 transition group-hover:text-primary">
          {t('zones.card.viewEvents')} <ArrowRight className="size-3.5 transition group-hover:translate-x-0.5" />
        </div>
      </Card>
    </Link>
  )
}
