import { Cpu } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '@/api/endpoints'
import type { DetectionKind } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAppStatus } from '@/hooks/useAppStatus'
import { useAsync } from '@/hooks/useAsync'
import { formatPercent } from '@/lib/format'
import { InfoRow, SectionCard } from './SectionCard'

const KIND_KEYS: Record<DetectionKind, string> = {
  hardhat: 'settings.detector.kindHardhat',
  no_hardhat: 'settings.detector.kindNoHardhat',
}

function ModelRows() {
  const { t } = useTranslation()
  const { data: info, loading, error } = useAsync((signal) => api.modelInfo(signal), [])
  if (loading && !info) return <Skeleton className="h-24 w-full" />
  if (error || !info) {
    return (
      <InfoRow
        label={t('settings.detector.model')}
        value={<span className="text-red-ink">{t('settings.detector.loadFailed')}</span>}
      />
    )
  }
  return (
    <>
      <InfoRow label={t('settings.detector.model')} value={info.family ?? '—'} mono />
      <InfoRow label="Threshold: Helmet / Head" value={`${info.thresholds.hardhat} / ${info.thresholds.no_hardhat}`} />
      <InfoRow
        label={t('settings.detector.voteRule')}
        value={t('settings.detector.voteValue', { ratio: formatPercent(info.violation_frame_ratio, 0) })}
      />
      <InfoRow
        label={t('settings.detector.weights')}
        value={
          info.source === 'local'
            ? 'backend/models/best.pt'
            : t('settings.detector.downloadedFrom', { repo: info.fallback_repo })
        }
        mono
      />
      <div className="flex items-start justify-between gap-4 border-b border-dashed border-slate-100 py-2.5">
        <span className="text-xs text-slate-500">{t('settings.detector.classMapping')}</span>
        <div className="flex flex-wrap justify-end gap-1.5">
          {info.class_names.map((name) => {
            const kind = info.class_mapping[name]
            return (
              <Badge key={name} variant="outline" className="font-mono text-[11px]">
                {name} → {kind ? t(KIND_KEYS[kind]) : t('settings.detector.unused')}
              </Badge>
            )
          })}
        </div>
      </div>
    </>
  )
}

export function DetectorCard() {
  const { health } = useAppStatus()
  const { t } = useTranslation()
  return (
    <SectionCard icon={Cpu} title={t('settings.detector.title')} description={t('settings.detector.description')}>
      <ModelRows />
      <InfoRow label={t('settings.detector.systemVersion')} value={health?.version ?? '—'} />
      {health && (
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[11px] text-slate-500">
            <span>0</span>
            <span>threshold</span>
            <span>1.0</span>
          </div>
          <div className="relative h-2 rounded-full bg-gradient-to-r from-slate-100 via-blue-soft to-green-soft">
            <div
              className="absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-card bg-primary shadow"
              style={{ left: `${health.conf_threshold * 100}%` }}
            />
          </div>
        </div>
      )}
    </SectionCard>
  )
}
