import { MapPinned } from 'lucide-react'
import { api } from '@/api/endpoints'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ZoneCard } from '@/components/zones/ZoneCard'
import { useAsync } from '@/hooks/useAsync'

function RiskLegend() {
  const items = [
    { c: 'bg-rose-500', t: 'สูง ≥ 40%' },
    { c: 'bg-amber-500', t: 'กลาง 20–39%' },
    { c: 'bg-emerald-500', t: 'ต่ำ < 20%' },
  ]
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-xs">
      <span className="font-medium text-slate-500">ระดับความเสี่ยง:</span>
      {items.map((i) => (
        <span key={i.t} className="flex items-center gap-1.5">
          <span className={`size-2 rounded-full ${i.c}`} /> {i.t}
        </span>
      ))}
    </div>
  )
}

export function ZonesPage() {
  const zones = useAsync((s) => api.zones(s), [])
  return (
    <PageContainer>
      <PageHeader
        title="โซนพื้นที่"
        description="ความเสี่ยงของแต่ละโซนจากอัตราการไม่สวมหมวกนิรภัยตลอดช่วงข้อมูล — คลิกการ์ดเพื่อดูเหตุการณ์"
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
          <EmptyState icon={MapPinned} title="ยังไม่มีข้อมูลโซน" description="อัปโหลดคลิปและรันการตรวจจับเพื่อเริ่มเก็บข้อมูล" />
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
