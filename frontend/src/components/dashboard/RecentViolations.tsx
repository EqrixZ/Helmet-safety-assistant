import { ChevronRight, ShieldCheck, Siren } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '@/api/endpoints'
import type { DateRange } from '@/api/types'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { FrameImage } from '@/components/common/FrameImage'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/hooks/useAsync'
import { cameraLabel, formatThaiDate, zoneLabel } from '@/lib/format'

export function RecentViolations({ range }: { range: DateRange }) {
  const { data, loading, error, reload } = useAsync(
    (signal) => api.events({ ...range, violation: true, size: 6, sort: 'datetime', order: 'desc' }, signal),
    [range.from, range.to],
  )

  return (
    <Card className="card-hover flex flex-col">
      <CardHeader>
        <div className="flex items-start gap-3">
          <div className="grid size-8 place-items-center rounded-lg bg-rose-50 text-rose-500">
            <Siren className="size-4" />
          </div>
          <div>
            <CardTitle>เหตุการณ์ละเมิดล่าสุด</CardTitle>
            <CardDescription>ตรวจพบผู้ไม่สวมหมวกนิรภัย</CardDescription>
          </div>
        </div>
        <Link to="/events?violation=true" className="flex items-center text-xs font-medium text-primary hover:underline">
          ดูทั้งหมด <ChevronRight className="size-3.5" />
        </Link>
      </CardHeader>
      <CardContent className="flex-1">
        {loading && !data ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-11 w-16 rounded-lg" />
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
          <EmptyState icon={ShieldCheck} title="ไม่พบการละเมิด" description="ยอดเยี่ยม! ไม่มีผู้ไม่สวมหมวกนิรภัยในช่วงเวลานี้" />
        ) : (
          <ul className="-mx-2 space-y-1">
            {data.items.map((e) => (
              <li key={e.event_id}>
                <Link
                  to={`/events?event=${e.event_id}`}
                  className="group flex items-center gap-3 rounded-lg p-2 transition hover:bg-slate-50"
                >
                  <FrameImage src={e.frame_url} alt={e.event_id} compact className="h-11 w-16 shrink-0 rounded-lg" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-slate-800">{zoneLabel(e.zone)}</span>
                      <Badge variant="danger" className="px-1.5 py-0 text-[10px]">
                        {e.no_hardhat} คน
                      </Badge>
                    </div>
                    <div className="truncate text-xs text-slate-500">
                      {e.event_id} · {cameraLabel(e.camera)} · {formatThaiDate(e.date)} {e.time} น.
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
