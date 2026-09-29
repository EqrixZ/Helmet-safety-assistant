import { ArrowDown, ArrowUp, ArrowUpDown, SearchX } from 'lucide-react'
import type { Event, EventQuery } from '@/api/types'
import { EmptyState } from '@/components/common/EmptyState'
import { FrameImage } from '@/components/common/FrameImage'
import { ViolationBadge } from '@/components/common/StatusBadges'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cameraLabel, formatThaiDate, zoneLabel } from '@/lib/format'
import { cn } from '@/lib/utils'
import { ConfidenceBar } from './ConfidenceBar'

type Column = { key: string; label: string; sortable: boolean; align?: 'right' | 'center'; className?: string }

const COLUMNS: Column[] = [
  { key: 'date', label: 'วันที่', sortable: true },
  { key: 'time', label: 'เวลา', sortable: true },
  { key: 'camera', label: 'กล้อง', sortable: true },
  { key: 'zone', label: 'โซน', sortable: true },
  { key: 'hardhat', label: 'สวมหมวก', sortable: true, align: 'center' },
  { key: 'no_hardhat', label: 'ไม่สวมหมวก', sortable: true, align: 'center' },
  { key: 'violation', label: 'สถานะ', sortable: true },
  { key: 'max_conf', label: 'ความมั่นใจ', sortable: true },
]

function SortIcon({ active, order }: { active: boolean; order: EventQuery['order'] }) {
  if (!active) return <ArrowUpDown className="size-3 opacity-0 transition group-hover:opacity-50" />
  return order === 'asc' ? <ArrowUp className="size-3 text-primary" /> : <ArrowDown className="size-3 text-primary" />
}

export function EventsTable({
  items,
  loading,
  query,
  onSort,
  onSelect,
  selectedId,
  onClear,
}: {
  items: Event[] | undefined
  loading: boolean
  query: EventQuery
  onSort: (key: string) => void
  onSelect: (e: Event) => void
  selectedId: string | null
  onClear: () => void
}) {
  // sort by 'datetime' shows as sorted by date
  const activeSort = query.sort === 'datetime' ? 'date' : query.sort
  return (
    <div className="scrollbar-thin overflow-x-auto">
      <table className="w-full min-w-[860px] text-sm">
        <thead>
          <tr className="border-b bg-slate-50/80 text-left text-xs font-medium text-slate-500">
            <th className="w-20 py-3 pl-5 font-medium">ภาพ</th>
            {COLUMNS.map((c) => (
              <th key={c.key} className={cn('px-3 py-3 font-medium', c.align === 'center' && 'text-center')}>
                <button
                  type="button"
                  onClick={() => onSort(c.key === 'date' ? 'datetime' : c.key)}
                  className={cn(
                    'group inline-flex items-center gap-1 transition hover:text-slate-800',
                    activeSort === c.key && 'text-slate-800',
                  )}
                >
                  {c.label}
                  <SortIcon active={activeSort === c.key} order={query.order} />
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading && !items
            ? Array.from({ length: 8 }, (_, i) => (
                <tr key={i} className="border-b border-slate-100">
                  <td className="py-2.5 pl-5">
                    <Skeleton className="h-9 w-14 rounded-md" />
                  </td>
                  {COLUMNS.map((c) => (
                    <td key={c.key} className="px-3 py-2.5">
                      <Skeleton className="h-4 w-16" />
                    </td>
                  ))}
                </tr>
              ))
            : items?.map((e, i) => (
                <tr
                  key={e.event_id}
                  onClick={() => onSelect(e)}
                  style={{ animationDelay: `${i * 20}ms` }}
                  className={cn(
                    'animate-fade-in cursor-pointer border-b border-slate-100 transition-colors hover:bg-orange-50/40',
                    selectedId === e.event_id && 'bg-orange-50/70',
                    loading && 'opacity-60',
                  )}
                >
                  <td className="py-2 pl-5">
                    <FrameImage src={e.frame_url} alt={e.event_id} compact className="h-9 w-14 rounded-md" />
                  </td>
                  <td className="px-3 py-2">
                    <div className="font-medium text-slate-800">{formatThaiDate(e.date)}</div>
                    <div className="text-[11px] text-slate-400">{e.event_id}</div>
                  </td>
                  <td className="px-3 py-2 text-slate-600 tabular-nums">{e.time}</td>
                  <td className="px-3 py-2 text-slate-600">{cameraLabel(e.camera)}</td>
                  <td className="px-3 py-2 text-slate-700">{zoneLabel(e.zone)}</td>
                  <td className="px-3 py-2 text-center text-slate-600 tabular-nums">{e.hardhat}</td>
                  <td
                    className={cn(
                      'px-3 py-2 text-center tabular-nums',
                      e.no_hardhat > 0 ? 'font-semibold text-rose-600' : 'text-slate-400',
                    )}
                  >
                    {e.no_hardhat}
                  </td>
                  <td className="px-3 py-2">
                    <ViolationBadge violation={e.violation} />
                  </td>
                  <td className="px-3 py-2">
                    <ConfidenceBar value={e.max_conf} />
                  </td>
                </tr>
              ))}
        </tbody>
      </table>
      {!loading && items?.length === 0 && (
        <EmptyState
          icon={SearchX}
          title="ไม่พบเหตุการณ์ที่ตรงกับตัวกรอง"
          description="ลองปรับช่วงวันที่ โซน หรือกล้อง"
          action={
            <Button variant="outline" size="sm" onClick={onClear}>
              ล้างตัวกรองทั้งหมด
            </Button>
          }
        />
      )}
    </div>
  )
}
