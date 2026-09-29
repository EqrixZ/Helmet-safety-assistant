import { Cpu } from 'lucide-react'
import { api } from '@/api/endpoints'
import type { DetectionKind } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAppStatus } from '@/hooks/useAppStatus'
import { useAsync } from '@/hooks/useAsync'
import { formatPercent } from '@/lib/format'
import { InfoRow, SectionCard } from './SectionCard'

const KIND_LABEL: Record<DetectionKind, string> = { hardhat: 'สวมหมวก', no_hardhat: 'ไม่สวมหมวก' }

function ModelRows() {
  const { data: info, loading, error } = useAsync((signal) => api.modelInfo(signal), [])
  if (loading && !info) return <Skeleton className="h-24 w-full" />
  if (error || !info) return <InfoRow label="โมเดล" value={<span className="text-rose-600">โหลดข้อมูลโมเดลไม่สำเร็จ</span>} />
  return (
    <>
      <InfoRow label="โมเดล" value={info.family ?? '—'} mono />
      <InfoRow label="Threshold: Helmet / Head" value={`${info.thresholds.hardhat} / ${info.thresholds.no_hardhat}`} />
      <InfoRow label="เกณฑ์โหวตการละเมิด" value={`พบ Head ≥ ${formatPercent(info.violation_frame_ratio, 0)} ของเฟรม`} />
      <InfoRow label="ไฟล์ weights" value={info.source === 'local' ? 'backend/models/best.pt' : `ดาวน์โหลดจาก ${info.fallback_repo}`} mono />
      <div className="flex items-start justify-between gap-4 border-b border-dashed border-slate-100 py-2.5">
        <span className="text-xs text-slate-500">คลาส → การนับ</span>
        <div className="flex flex-wrap justify-end gap-1.5">
          {info.class_names.map((name) => {
            const kind = info.class_mapping[name]
            return (
              <Badge key={name} variant="outline" className="font-mono text-[11px]">
                {name} → {kind ? KIND_LABEL[kind] : 'ไม่ใช้'}
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
  return (
    <SectionCard icon={Cpu} title="ตัวตรวจจับ (Detector)" description="โมเดล, threshold แยกตามคลาส และเกณฑ์โหวต (ตั้งค่าใน .env — อ่านอย่างเดียว)">
      <ModelRows />
      <InfoRow label="เวอร์ชันระบบ" value={health?.version ?? '—'} />
      {health && (
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[11px] text-slate-500">
            <span>0</span>
            <span>threshold</span>
            <span>1.0</span>
          </div>
          <div className="relative h-2 rounded-full bg-gradient-to-r from-slate-100 via-orange-100 to-emerald-100">
            <div
              className="absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-primary shadow"
              style={{ left: `${health.conf_threshold * 100}%` }}
            />
          </div>
        </div>
      )}
    </SectionCard>
  )
}
