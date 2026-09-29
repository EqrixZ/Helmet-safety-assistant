import { Activity, BarChart3, Camera, Clock, MapPin, Percent, ShieldAlert, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '@/api/endpoints'
import type { DateRange } from '@/api/types'
import { CameraDonutChart } from '@/components/charts/CameraDonutChart'
import { ChartCard, LegendItem } from '@/components/charts/ChartCard'
import { DailyViolationsChart } from '@/components/charts/DailyViolationsChart'
import { HourBarChart } from '@/components/charts/HourBarChart'
import { ZoneBarChart } from '@/components/charts/ZoneBarChart'
import { CHART } from '@/components/charts/palette'
import { DateRangePicker } from '@/components/common/DateRangePicker'
import { ErrorState } from '@/components/common/ErrorState'
import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { DataSourceBadge } from '@/components/common/StatusBadges'
import { KpiCard } from '@/components/dashboard/KpiCard'
import { RecentViolations } from '@/components/dashboard/RecentViolations'
import { useAppStatus } from '@/hooks/useAppStatus'
import { useAsync } from '@/hooks/useAsync'
import { formatHourRange, formatNumber, formatPercent, formatThaiDate, shiftIsoDate, zoneLabel } from '@/lib/format'

const Legend2 = (
  <div className="flex items-center gap-3">
    <LegendItem color={CHART.violation} label="ละเมิด" />
    <LegendItem color={CHART.totalSoft} label="ทั้งหมด" />
  </div>
)

export function DashboardPage() {
  const { health, healthChecked } = useAppStatus()
  const bounds = health?.date_range ?? { min: null, max: null }
  const [range, setRange] = useState<DateRange>({})

  // Default to the full log range once health is known.
  useEffect(() => {
    if (!range.from && !range.to && bounds.min && bounds.max) {
      // Default to the last 7 days so KPI trends compare against the week before.
      const weekStart = shiftIsoDate(bounds.max, -6)
      setRange({ from: weekStart > bounds.min ? weekStart : bounds.min, to: bounds.max })
    }
  }, [bounds.min, bounds.max, range.from, range.to])

  const ready = healthChecked && (Boolean(range.from) || !bounds.min)
  const deps = [range.from, range.to]
  const stats = useAsync((s) => api.stats(range, s), deps, { enabled: ready })
  const byDay = useAsync((s) => api.aggregates('day', range, s), deps, { enabled: ready })
  const byZone = useAsync((s) => api.aggregates('zone', range, s), deps, { enabled: ready })
  const byHour = useAsync((s) => api.aggregates('hour', range, s), deps, { enabled: ready })
  const byCamera = useAsync((s) => api.aggregates('camera', range, s), deps, { enabled: ready })

  const st = stats.data
  const kpiLoading = stats.loading && !st

  return (
    <PageContainer>
      <PageHeader
        title="แดชบอร์ดความปลอดภัย"
        description={
          <span className="flex flex-wrap items-center gap-2">
            ภาพรวมการสวมหมวกนิรภัย
            {st?.from && st.to && (
              <span className="text-slate-400">
                ({formatThaiDate(st.from)} – {formatThaiDate(st.to)})
              </span>
            )}
            <DataSourceBadge source={st?.data_source ?? health?.data_source} />
          </span>
        }
        actions={<DateRangePicker value={range} onChange={setRange} bounds={bounds} />}
      />

      {stats.error ? (
        <ErrorState error={stats.error} onRetry={stats.reload} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="เหตุการณ์ทั้งหมด"
            icon={Activity}
            accent="slate"
            loading={kpiLoading}
            value={formatNumber(st?.total_events ?? 0)}
            trend={st?.trend.events}
          />
          <KpiCard
            label="การละเมิด (ไม่สวมหมวก)"
            icon={ShieldAlert}
            accent="rose"
            loading={kpiLoading}
            value={formatNumber(st?.total_violations ?? 0)}
            trend={st?.trend.violations}
            polarity="up-bad"
            delay={60}
          />
          <KpiCard
            label="อัตราการละเมิด"
            icon={Percent}
            accent="orange"
            loading={kpiLoading}
            value={formatPercent(st?.violation_rate ?? 0)}
            trend={st?.trend.violation_rate}
            polarity="up-bad"
            delay={120}
          />
          <KpiCard
            label="โซนที่ละเมิดมากที่สุด"
            icon={MapPin}
            accent="amber"
            loading={kpiLoading}
            value={st?.top_zone ? zoneLabel(st.top_zone.key) : '—'}
            sub={
              st?.top_zone
                ? `${st.top_zone.violations} ครั้ง${st.top_hour ? ` · ช่วงเสี่ยง ${formatHourRange(st.top_hour.key)}` : ''}`
                : 'ไม่พบการละเมิด'
            }
            delay={180}
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard
          className="xl:col-span-2"
          title="แนวโน้มการละเมิดรายวัน"
          description="จำนวนครั้งที่ตรวจพบผู้ไม่สวมหมวก เทียบกับเหตุการณ์ทั้งหมด"
          icon={TrendingUp}
          loading={byDay.loading && !byDay.data}
          error={byDay.error}
          onRetry={byDay.reload}
          empty={byDay.data?.length === 0}
          emptyIcon={TrendingUp}
          height={280}
          legend={Legend2}
        >
          <DailyViolationsChart data={byDay.data ?? []} />
        </ChartCard>
        <ChartCard
          title="สัดส่วนการละเมิดตามกล้อง"
          icon={Camera}
          loading={byCamera.loading && !byCamera.data}
          error={byCamera.error}
          onRetry={byCamera.reload}
          empty={(byCamera.data ?? []).every((r) => r.violations === 0)}
          emptyIcon={Camera}
          height={280}
        >
          <CameraDonutChart data={byCamera.data ?? []} />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard
          title="การละเมิดตามโซน"
          icon={BarChart3}
          loading={byZone.loading && !byZone.data}
          error={byZone.error}
          onRetry={byZone.reload}
          empty={byZone.data?.length === 0}
          emptyIcon={BarChart3}
          height={340}
          legend={Legend2}
        >
          <ZoneBarChart data={byZone.data ?? []} />
        </ChartCard>
        <ChartCard
          title="การละเมิดตามช่วงเวลา"
          icon={Clock}
          loading={byHour.loading && !byHour.data}
          error={byHour.error}
          onRetry={byHour.reload}
          empty={byHour.data?.length === 0}
          emptyIcon={Clock}
          height={340}
          legend={Legend2}
        >
          <HourBarChart data={byHour.data ?? []} />
        </ChartCard>
        <RecentViolations range={range} />
      </div>

    </PageContainer>
  )
}
