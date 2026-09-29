import { FileText, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { ApiError, toErrorMessage } from '@/api/client'
import { api } from '@/api/endpoints'
import type { Report, ReportType } from '@/api/types'
import { EmptyState } from '@/components/common/EmptyState'
import { LlmNotConfiguredCard } from '@/components/common/LlmNotConfiguredCard'
import { PageContainer, PageHeader } from '@/components/common/PageHeader'
import { ReportGenerator } from '@/components/reports/ReportGenerator'
import { ReportHistory } from '@/components/reports/ReportHistory'
import { ReportPaper } from '@/components/reports/ReportPaper'
import { Card } from '@/components/ui/card'
import { useAppStatus } from '@/hooks/useAppStatus'
import { useAsync } from '@/hooks/useAsync'
import { shiftIsoDate } from '@/lib/format'

export function ReportsPage() {
  const { health, siteName } = useAppStatus()
  const maxDate = health?.date_range.max ?? undefined
  const minDate = health?.date_range.min ?? undefined
  const [type, setType] = useState<ReportType>('daily')
  const [date, setDate] = useState('')
  const [generating, setGenerating] = useState(false)
  const [opening, setOpening] = useState(false)
  const [report, setReport] = useState<Report | null>(null)
  const [llmError, setLlmError] = useState<string | null>(null)
  const history = useAsync((s) => api.reports(s), [])

  // Default date: last day of the log (daily) or its last 7 days (weekly).
  useEffect(() => {
    if (!maxDate) return
    setDate(type === 'daily' ? maxDate : shiftIsoDate(maxDate, -6))
  }, [type, maxDate])

  const generate = async () => {
    setGenerating(true)
    setLlmError(null)
    try {
      const r = await api.createReport({ type, date })
      setReport(r)
      history.reload()
      toast.success('สร้างรายงานเรียบร้อย', { description: r.name })
    } catch (err) {
      if (err instanceof ApiError && err.isLlmNotConfigured) setLlmError(err.message)
      else toast.error('สร้างรายงานไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setGenerating(false)
    }
  }

  const open = async (name: string) => {
    setOpening(true)
    try {
      setReport(await api.report(name))
    } catch (err) {
      toast.error('เปิดรายงานไม่สำเร็จ', { description: toErrorMessage(err) })
    } finally {
      setOpening(false)
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="รายงานความปลอดภัย"
        description="สร้างรายงานรายวันหรือรายสัปดาห์ พร้อมบทวิเคราะห์และข้อเสนอแนะจาก AI — ดาวน์โหลดหรือพิมพ์เป็น PDF ได้ทันที"
      />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
        <div className="space-y-4">
          <ReportGenerator
            type={type}
            date={date}
            onType={setType}
            onDate={setDate}
            onGenerate={() => void generate()}
            generating={generating}
            maxDate={maxDate}
            minDate={minDate}
          />
          {(llmError !== null || health?.llm_configured === false) && (
            <LlmNotConfiguredCard message={llmError ?? undefined} />
          )}
          <ReportHistory
            items={history.data}
            loading={history.loading}
            error={history.error}
            onRetry={history.reload}
            activeName={report?.name}
            onOpen={(n) => void open(n)}
          />
        </div>
        <div className="min-w-0">
          {opening ? (
            <Card className="grid min-h-[60vh] place-items-center">
              <Loader2 className="size-6 animate-spin text-slate-400" />
            </Card>
          ) : report ? (
            <ReportPaper key={report.name + report.created_at} report={report} siteName={siteName} />
          ) : (
            <Card className="grid min-h-[60vh] place-items-center border-dashed">
              <EmptyState
                icon={FileText}
                title={generating ? 'กำลังเตรียมรายงาน…' : 'ยังไม่ได้เลือกรายงาน'}
                description="เลือกประเภทและวันที่ แล้วกด “สร้างรายงาน” หรือเปิดรายงานเดิมจากรายการด้านซ้าย"
              />
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
