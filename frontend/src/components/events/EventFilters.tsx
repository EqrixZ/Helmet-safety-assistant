import { FilterX } from 'lucide-react'
import { api } from '@/api/endpoints'
import type { EventQuery } from '@/api/types'
import { DateRangePicker } from '@/components/common/DateRangePicker'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAppStatus } from '@/hooks/useAppStatus'
import { useAsync } from '@/hooks/useAsync'
import { cameraLabel, zoneLabel } from '@/lib/format'

const ALL = '__all__'

export function EventFilters({
  query,
  onChange,
  onClear,
  activeCount,
}: {
  query: EventQuery
  onChange: (patch: Record<string, string | undefined>) => void
  onClear: () => void
  activeCount: number
}) {
  const { health } = useAppStatus()
  const zones = useAsync((s) => api.zones(s), [])
  const cameras = useAsync((s) => api.cameras(s), [])
  const zoneKeys = new Set((zones.data ?? []).map((z) => z.key))
  if (query.zone) zoneKeys.add(query.zone)
  const cameraKeys = new Set((cameras.data ?? []).map((c) => c.key))
  if (query.camera) cameraKeys.add(query.camera)
  const violationValue = query.violation === undefined ? ALL : String(query.violation)

  return (
    <div className="flex flex-wrap items-center gap-2">
      <DateRangePicker
        value={{ from: query.from, to: query.to }}
        onChange={(r) => onChange({ from: r.from, to: r.to })}
        bounds={health?.date_range ?? { min: null, max: null }}
      />
      <Select value={query.zone ?? ALL} onValueChange={(v) => onChange({ zone: v === ALL ? undefined : v })}>
        <SelectTrigger className="w-40" aria-label="โซน">
          <SelectValue placeholder="ทุกโซน" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>ทุกโซน</SelectItem>
          {[...zoneKeys].sort().map((k) => (
            <SelectItem key={k} value={k}>
              {zoneLabel(k)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={query.camera ?? ALL} onValueChange={(v) => onChange({ camera: v === ALL ? undefined : v })}>
        <SelectTrigger className="w-36" aria-label="กล้อง">
          <SelectValue placeholder="ทุกกล้อง" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>ทุกกล้อง</SelectItem>
          {[...cameraKeys].sort().map((k) => (
            <SelectItem key={k} value={k}>
              {cameraLabel(k)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={violationValue} onValueChange={(v) => onChange({ violation: v === ALL ? undefined : v })}>
        <SelectTrigger className="w-40" aria-label="สถานะ">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>ทุกสถานะ</SelectItem>
          <SelectItem value="true">ไม่สวมหมวก</SelectItem>
          <SelectItem value="false">ปลอดภัย</SelectItem>
        </SelectContent>
      </Select>
      {activeCount > 0 && (
        <Button variant="ghost" size="sm" onClick={onClear} className="text-slate-500">
          <FilterX /> ล้างตัวกรอง ({activeCount})
        </Button>
      )}
    </div>
  )
}
