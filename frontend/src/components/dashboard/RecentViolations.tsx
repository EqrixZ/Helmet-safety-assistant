import { ChevronRight, ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { api } from '@/api/endpoints'
import type { DateRange } from '@/api/types'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { FrameImage } from '@/components/common/FrameImage'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/hooks/useAsync'
import { cameraLabel, formatDate, formatTime, zoneWithName } from '@/lib/format'

export function RecentViolations({ range }: { range: DateRange }) {
  const { t } = useTranslation()
  const { data, loading, error, reload } = useAsync(
    (signal) => api.events({ ...range, violation: true, size: 6, sort: 'datetime', order: 'desc' }, signal),
    [range.from, range.to],
  )

  return (
    <Card className="card-hover flex flex-col">
      <CardHeader>
        <div>
          <CardTitle>{t('dashboard.recent.title')}</CardTitle>
          <CardDescription>{t('dashboard.recent.description')}</CardDescription>
        </div>
        <Button asChild variant="outline" size="sm" className="shrink-0">
          <Link to="/events?violation=true">{t('common.viewAll')}</Link>
        </Button>
      </CardHeader>
      <CardContent className="flex-1">
        {loading && !data ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="size-11 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3.5 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={reload} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState icon={ShieldCheck} title={t('dashboard.recent.emptyTitle')}
            description={t('dashboard.recent.emptyDescription')} />
        ) : (
          <ul className="-mx-2 space-y-1">
            {data.items.map((e) => (
              <li key={e.event_id}>
                <Link
                  to={`/events?event=${e.event_id}`}
                  className="group flex items-center gap-3 rounded-lg p-2 transition hover:bg-slate-50"
                >
                  <FrameImage src={e.frame_url} alt={e.event_id} compact className="size-11 shrink-0 rounded-full" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-semibold text-navy">{zoneWithName(e.zone)}</span>
                      <Badge variant="danger" className="px-1.5 py-0 text-[10px]">
                        {t('common.persons', { count: e.no_hardhat })}
                      </Badge>
                    </div>
                    <div className="truncate text-xs text-caption">
                      {e.event_id} · {cameraLabel(e.camera)} · {formatDate(e.date)} {formatTime(e.time)}
                    </div>
                  </div>
                  <ChevronRight className="size-4 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-slate-500" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
