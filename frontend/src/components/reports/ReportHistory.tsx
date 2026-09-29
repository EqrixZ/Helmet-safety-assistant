import { FileClock, FileText } from 'lucide-react'
import type { ReportMeta } from '@/api/types'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatBytes, formatThaiDate, formatThaiDateTime } from '@/lib/format'
import { cn } from '@/lib/utils'

export function ReportHistory({
  items,
  loading,
  error,
  onRetry,
  activeName,
  onOpen,
}: {
  items: ReportMeta[] | undefined
  loading: boolean
  error: unknown
  onRetry: () => void
  activeName: string | undefined
  onOpen: (name: string) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>รายงานที่เคยสร้าง</CardTitle>
        {items && <span className="text-xs text-slate-400">{items.length} ฉบับ</span>}
      </CardHeader>
      <CardContent className="px-3">
        {loading && !items ? (
          <div className="space-y-2 px-2">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={onRetry} className="py-6" />
        ) : !items || items.length === 0 ? (
          <EmptyState icon={FileClock} title="ยังไม่มีรายงาน" description="รายงานที่สร้างจะถูกบันทึกและแสดงที่นี่" className="py-8" />
        ) : (
          <ul className="scrollbar-thin max-h-80 space-y-1 overflow-y-auto">
            {items.map((r) => (
              <li key={r.name}>
                <button
                  type="button"
                  onClick={() => onOpen(r.name)}
                  className={cn(
                    'flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left transition hover:bg-slate-50',
                    activeName === r.name && 'bg-orange-50 ring-1 ring-primary/20',
                  )}
                >
                  <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500">
                    <FileText className="size-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-slate-800">{formatThaiDate(r.date)}</span>
                      <Badge variant={r.type === 'daily' ? 'info' : 'default'} className="px-1.5 py-0 text-[10px]">
                        {r.type === 'daily' ? 'รายวัน' : 'รายสัปดาห์'}
                      </Badge>
                    </div>
                    <div className="truncate text-[11px] text-slate-400">
                      สร้างเมื่อ {formatThaiDateTime(r.created_at)} · {formatBytes(r.size)}
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
