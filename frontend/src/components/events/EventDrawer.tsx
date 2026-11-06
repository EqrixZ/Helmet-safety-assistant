import { Bot, Camera, Clock, Film, Gauge, HardHat, MapPin, UserX, Users, Vote } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/endpoints'
import type { Event } from '@/api/types'
import { ErrorState } from '@/components/common/ErrorState'
import { FrameImage } from '@/components/common/FrameImage'
import { ViolationBadge } from '@/components/common/StatusBadges'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/hooks/useAsync'
import i18n from '@/i18n'
import { cameraLabel, formatDate, formatPercent, formatTime, zoneLabel } from '@/lib/format'
import { cn } from '@/lib/utils'

export function buildEventQuestion(e: Event): string {
  return i18n.t('events.drawer.question', {
    id: e.event_id,
    camera: e.camera,
    zone: zoneLabel(e.zone),
    date: formatDate(e.date, 'long'),
    time: e.time,
  })
}

function Meta({ icon: Icon, label, value, danger }: { icon: typeof Clock; label: string; value: ReactNode; danger?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
        <Icon className="size-3.5" /> {label}
      </div>
      <div className={cn('mt-1 truncate text-sm font-semibold text-slate-800', danger && 'text-red-ink')}>{value}</div>
    </div>
  )
}

export function EventDrawer({
  eventId,
  initial,
  onClose,
}: {
  eventId: string | null
  initial: Event | undefined
  onClose: () => void
}) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const fetched = useAsync((s) => api.event(eventId ?? '', s), [eventId], { enabled: Boolean(eventId) && !initial })
  const e = initial ?? fetched.data

  return (
    <Sheet open={Boolean(eventId)} onOpenChange={(o) => !o && onClose()}>
      <SheetContent>
        <SheetHeader>
          <div className="flex items-center gap-2">
            <SheetTitle>{eventId}</SheetTitle>
            {e && <ViolationBadge violation={e.violation} />}
          </div>
          <SheetDescription>{e ? `${zoneLabel(e.zone)} · ${cameraLabel(e.camera)}` : t('events.drawer.details')}</SheetDescription>
        </SheetHeader>
        <div className="scrollbar-thin flex-1 overflow-y-auto px-6 py-5">
          {fetched.error && !e ? (
            <ErrorState error={fetched.error} onRetry={fetched.reload} />
          ) : !e ? (
            <div className="space-y-4">
              <Skeleton className="aspect-video w-full rounded-xl" />
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 6 }, (_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            </div>
          ) : (
            <div className="animate-fade-in space-y-5">
              <div className="overflow-hidden rounded-xl border border-slate-200 shadow-sm">
                <FrameImage src={e.frame_url} alt={t('events.drawer.frameAlt', { id: e.event_id })} className="aspect-video w-full" />
                <div className="flex items-center justify-between bg-navy px-3 py-2 text-[11px] text-slate-300">
                  <span>{t('events.drawer.frameCaption')}</span>
                  <span className="font-mono text-slate-400">{e.frame_path || '—'}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Meta icon={Clock} label={t('events.drawer.dateTime')} value={`${formatDate(e.date)} ${formatTime(e.time)}`} />
                <Meta icon={MapPin} label={t('events.drawer.zone')} value={`${zoneLabel(e.zone)} (${e.zone})`} />
                <Meta icon={Camera} label={t('events.drawer.camera')} value={cameraLabel(e.camera)} />
                <Meta icon={Gauge} label={t('events.drawer.maxConfidence')} value={formatPercent(e.max_conf)} />
                <Meta icon={HardHat} label={t('events.drawer.hardhat')} value={t('common.persons', { count: e.hardhat })} />
                <Meta
                  icon={UserX}
                  label={t('events.drawer.noHardhat')}
                  value={t('common.persons', { count: e.no_hardhat })}
                  danger={e.no_hardhat > 0}
                />
                <Meta icon={Users} label={t('events.drawer.workers')} value={t('common.persons', { count: e.total_person })} />
                {e.no_hardhat_ratio !== null && (
                  <Meta
                    icon={Vote}
                    label={t('events.drawer.headRatio')}
                    value={t('events.drawer.headRatioValue', {
                      ratio: formatPercent(e.no_hardhat_ratio, 0),
                      count: e.no_hardhat_max,
                    })}
                  />
                )}
                <Meta icon={Film} label={t('events.drawer.clip')} value={<span className="font-mono text-xs">{e.clip}</span>} />
              </div>
            </div>
          )}
        </div>
        {e && (
          <div className="border-t bg-slate-50/80 px-6 py-4">
            <Button
              className="w-full"
              size="lg"
              onClick={() => navigate('/assistant', { state: { prefill: buildEventQuestion(e) } })}
            >
              <Bot /> {t('events.drawer.ask')}
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
