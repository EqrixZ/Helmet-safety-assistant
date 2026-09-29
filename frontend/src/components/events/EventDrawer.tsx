import { Bot, Camera, Clock, Film, Gauge, HardHat, MapPin, UserX, Users, Vote } from 'lucide-react'
import type { ReactNode } from 'react'
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
import { cameraLabel, formatPercent, formatThaiDate, zoneLabel } from '@/lib/format'
import { cn } from '@/lib/utils'

export function buildEventQuestion(e: Event): string {
  return `ช่วยวิเคราะห์เหตุการณ์ ${e.event_id} (กล้อง ${e.camera} โซน${zoneLabel(e.zone)} วันที่ ${formatThaiDate(e.date, 'long')} เวลา ${e.time} น.) ว่ามีความเสี่ยงอย่างไร และควรดำเนินการอย่างไร`
}

function Meta({ icon: Icon, label, value, danger }: { icon: typeof Clock; label: string; value: ReactNode; danger?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
        <Icon className="size-3.5" /> {label}
      </div>
      <div className={cn('mt-1 truncate text-sm font-semibold text-slate-800', danger && 'text-rose-600')}>{value}</div>
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
          <SheetDescription>{e ? `${zoneLabel(e.zone)} · ${cameraLabel(e.camera)}` : 'รายละเอียดเหตุการณ์'}</SheetDescription>
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
                <FrameImage src={e.frame_url} alt={`เฟรมของ ${e.event_id}`} className="aspect-video w-full" />
                <div className="flex items-center justify-between bg-slate-900 px-3 py-2 text-[11px] text-slate-300">
                  <span>ภาพเฟรมที่มีการตรวจจับ (annotated)</span>
                  <span className="font-mono text-slate-400">{e.frame_path || '—'}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Meta icon={Clock} label="วันที่และเวลา" value={`${formatThaiDate(e.date)} ${e.time} น.`} />
                <Meta icon={MapPin} label="โซน" value={`${zoneLabel(e.zone)} (${e.zone})`} />
                <Meta icon={Camera} label="กล้อง" value={cameraLabel(e.camera)} />
                <Meta icon={Gauge} label="ความมั่นใจสูงสุด" value={formatPercent(e.max_conf)} />
                <Meta icon={HardHat} label="สวมหมวก" value={`${e.hardhat} คน`} />
                <Meta icon={UserX} label="ไม่สวมหมวก" value={`${e.no_hardhat} คน`} danger={e.no_hardhat > 0} />
                <Meta icon={Users} label="ผู้ปฏิบัติงานในเฟรม" value={`${e.total_person} คน`} />
                {e.no_hardhat_ratio !== null && (
                  <Meta
                    icon={Vote}
                    label="พบศีรษะไม่สวมหมวก (ต่อเฟรม)"
                    value={`${formatPercent(e.no_hardhat_ratio, 0)} ของเฟรม · สูงสุด ${e.no_hardhat_max} คน`}
                  />
                )}
                <Meta icon={Film} label="คลิปต้นฉบับ" value={<span className="font-mono text-xs">{e.clip}</span>} />
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
              <Bot /> ถามผู้ช่วยเกี่ยวกับเหตุการณ์นี้
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
