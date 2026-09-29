import { CalendarDays, Loader2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReportType } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { IndeterminateProgress } from '@/components/ui/progress'
import { Segmented } from '@/components/ui/segmented'
import { formatThaiDate, shiftIsoDate } from '@/lib/format'

const STAGES = [
  'กำลังรวบรวมบันทึกเหตุการณ์ในช่วงที่เลือก…',
  'กำลังคำนวณสถิติรายโซนและช่วงเวลา…',
  'กำลังให้ AI วิเคราะห์และเขียนบทสรุป…',
  'กำลังประเมินความเสี่ยงและข้อเสนอแนะ…',
  'กำลังจัดรูปแบบรายงาน…',
]

function useStage(active: boolean): string {
  const [i, setI] = useState(0)
  useEffect(() => {
    if (!active) {
      setI(0)
      return
    }
    const id = window.setInterval(() => setI((x) => Math.min(x + 1, STAGES.length - 1)), 2500)
    return () => window.clearInterval(id)
  }, [active])
  return STAGES[i] ?? ''
}

export function ReportGenerator({
  type,
  date,
  onType,
  onDate,
  onGenerate,
  generating,
  maxDate,
  minDate,
}: {
  type: ReportType
  date: string
  onType: (t: ReportType) => void
  onDate: (d: string) => void
  onGenerate: () => void
  generating: boolean
  maxDate?: string
  minDate?: string
}) {
  const stage = useStage(generating)
  const rangeText =
    date && type === 'weekly' ? `${formatThaiDate(date)} – ${formatThaiDate(shiftIsoDate(date, 6))}` : formatThaiDate(date)

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>สร้างรายงานใหม่</CardTitle>
          <CardDescription>AI จะสรุปข้อมูลและเขียนรายงานภาษาไทยให้อัตโนมัติ</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Label>ประเภทรายงาน</Label>
          <Segmented<ReportType>
            className="flex w-full [&>button]:flex-1"
            value={type}
            onChange={onType}
            options={[
              { value: 'daily', label: 'รายวัน' },
              { value: 'weekly', label: 'รายสัปดาห์ (7 วัน)' },
            ]}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="report-date">{type === 'daily' ? 'วันที่' : 'วันเริ่มต้นสัปดาห์'}</Label>
          <Input id="report-date" type="date" value={date} min={minDate} max={maxDate} onChange={(e) => onDate(e.target.value)} />
          {date && (
            <p className="flex items-center gap-1.5 text-xs text-slate-500">
              <CalendarDays className="size-3.5" /> ช่วงข้อมูล: {rangeText}
            </p>
          )}
        </div>
        <Button className="w-full" size="lg" onClick={onGenerate} disabled={generating || !date}>
          {generating ? <Loader2 className="animate-spin" /> : <Sparkles />}
          {generating ? 'กำลังสร้างรายงาน…' : 'สร้างรายงาน'}
        </Button>
        {generating && (
          <div className="animate-fade-in space-y-2 rounded-lg bg-orange-50/60 p-3">
            <IndeterminateProgress />
            <p key={stage} className="animate-fade-in text-xs text-slate-600">
              {stage}
            </p>
            <p className="text-[11px] text-slate-400">อาจใช้เวลา 10–60 วินาที ขึ้นอยู่กับโมเดล LLM</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
