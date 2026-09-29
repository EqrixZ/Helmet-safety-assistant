import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { cn } from '@/lib/utils'

export function ChartCard({
  title,
  description,
  icon: Icon,
  loading,
  error,
  onRetry,
  empty,
  emptyIcon,
  height = 260,
  className,
  legend,
  children,
}: {
  title: string
  description?: string
  icon?: LucideIcon
  loading: boolean
  error?: unknown
  onRetry?: () => void
  empty?: boolean
  emptyIcon: LucideIcon
  height?: number
  className?: string
  legend?: ReactNode
  children: ReactNode
}) {
  return (
    <Card className={cn('card-hover', className)}>
      <CardHeader>
        <div className="flex items-start gap-3">
          {Icon && (
            <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500">
              <Icon className="size-4" />
            </div>
          )}
          <div>
            <CardTitle>{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
        </div>
        {legend}
      </CardHeader>
      <CardContent>
        <div style={{ height }} className="relative">
          {loading && !error ? (
            <div className="flex h-full items-end gap-2 pt-6">
              {Array.from({ length: 12 }, (_, i) => (
                <Skeleton key={i} className="flex-1" style={{ height: `${30 + ((i * 37) % 60)}%` }} />
              ))}
            </div>
          ) : error ? (
            <ErrorState error={error} onRetry={onRetry} className="h-full py-4" />
          ) : empty ? (
            <EmptyState icon={emptyIcon} title="ไม่มีข้อมูลในช่วงเวลานี้" description="ลองเลือกช่วงวันที่อื่น" className="h-full py-4" />
          ) : (
            children
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-slate-500">
      <span className="size-2.5 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  )
}
