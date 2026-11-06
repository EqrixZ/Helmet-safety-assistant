import { MapPinned } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '@/api/endpoints'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ZoneCard } from '@/components/zones/ZoneCard'
import { useAsync } from '@/hooks/useAsync'

function RiskLegend() {
  const { t } = useTranslation()
  const items = [
    { c: 'bg-tile-red', t: t('zones.legendHigh') },
    { c: 'bg-tile-orange', t: t('zones.legendMedium') },
    { c: 'bg-tile-green', t: t('zones.legendLow') },
  ]
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-card px-3 py-2 text-xs text-slate-600 shadow-xs">
      <span className="font-medium text-slate-500">{t('zones.riskLevel')}</span>
      {items.map((i) => (
        <span key={i.t} className="flex items-center gap-1.5">
          <span className={`size-2 rounded-full ${i.c}`} /> {i.t}
        </span>
      ))}
    </div>
  )
}

export function ZonesPage() {
  const { t } = useTranslation()
  const zones = useAsync((s) => api.zones(s), [])
  return (
    <PageContainer>
      <PageHeader
        title={t('zones.title')}
        description={t('zones.description')}
        actions={<RiskLegend />}
      />
      {zones.loading && !zones.data ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Card key={i} className="space-y-4 p-5">
              <Skeleton className="h-10 w-2/3" />
              <Skeleton className="h-12" />
              <Skeleton className="h-14" />
            </Card>
          ))}
        </div>
      ) : zones.error ? (
        <ErrorState error={zones.error} onRetry={zones.reload} />
      ) : !zones.data || zones.data.length === 0 ? (
        <Card>
          <EmptyState icon={MapPinned} title={t('zones.emptyTitle')} description={t('zones.emptyDescription')} />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {zones.data.map((z, i) => (
            <ZoneCard key={z.key} zone={z} index={i} />
          ))}
        </div>
      )}
    </PageContainer>
  )
}
