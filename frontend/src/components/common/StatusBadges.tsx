import { Database, FlaskConical, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { DataSource } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function ViolationBadge({ violation }: { violation: boolean }) {
  return violation ? (
    <Badge variant="danger">
      <ShieldAlert /> ไม่สวมหมวก
    </Badge>
  ) : (
    <Badge variant="success">
      <ShieldCheck /> ปลอดภัย
    </Badge>
  )
}

export function DataSourceBadge({ source }: { source: DataSource | undefined }) {
  if (!source) return null
  const real = source === 'real'
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span>
          <Badge variant={real ? 'success' : 'warning'} className="cursor-default">
            {real ? <Database /> : <FlaskConical />}
            {real ? 'ข้อมูลจริง' : 'ข้อมูลตัวอย่าง'}
          </Badge>
        </span>
      </TooltipTrigger>
      <TooltipContent>
        {real
          ? 'ข้อมูลจาก events.csv ที่ได้จากการรันตรวจจับคลิปจริง'
          : 'ยังไม่มี events.csv — ระบบกำลังแสดง events_sample.csv (อัปโหลดคลิปและรันการตรวจจับในหน้าตั้งค่า)'}
      </TooltipContent>
    </Tooltip>
  )
}
