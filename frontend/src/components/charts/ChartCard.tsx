import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { cn } from '@/lib/utils'

export function ChartCard({
  title,
  description,
  viewAllTo,
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
  /** Route for the outlined "View all" button in the header. */
  viewAllTo?: string
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
  const { t } = useTranslation()
  return (
    <Card className={cn('card-hover', className)}>
      <CardHeader>
        <div className="min-w-0">
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
          {legend && <div className="mt-2.5">{legend}</div>}
        </div>
        {viewAllTo && (
          <Button asChild variant="outline" size="sm" className="shrink-0">
            <Link to={viewAllTo}>{t('common.viewAll')}</Link>
          </Button>
        )}
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
            <EmptyState icon={emptyIcon} title={t('common.noDataInRange')}
              description={t('common.tryOtherRange')} className="h-full py-4" />
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
    <span className="flex items-center gap-1.5 text-xs text-caption">
      <span className="size-2 rounded-full" style={{ background: color }} />
      {label}
    </span>
  )
}
