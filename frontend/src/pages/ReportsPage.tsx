import { FileText, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { ApiError, describeError, toErrorMessage } from '@/api/client'
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
import { useLang } from '@/i18n'
import { shiftIsoDate } from '@/lib/format'

export function ReportsPage() {
  const { t } = useTranslation()
  const lang = useLang()
  const { health, siteName } = useAppStatus()
  const maxDate = health?.date_range.max ?? undefined
  const minDate = health?.date_range.min ?? undefined
  const [type, setType] = useState<ReportType>('daily')
  const [date, setDate] = useState('')
  const [generating, setGenerating] = useState(false)
  const [opening, setOpening] = useState(false)
  const [report, setReport] = useState<Report | null>(null)
  const [llmError, setLlmError] = useState<ApiError | null>(null)
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
      const r = await api.createReport({ type, date, language: lang })
      setReport(r)
      history.reload()
      toast.success(t('reports.generated'), { description: r.name })
    } catch (err) {
      if (err instanceof ApiError && err.isLlmNotConfigured) setLlmError(err)
      else toast.error(t('reports.generateFailed'), { description: toErrorMessage(err) })
    } finally {
      setGenerating(false)
    }
  }

  const open = async (name: string) => {
    setOpening(true)
    try {
      setReport(await api.report(name))
    } catch (err) {
      toast.error(t('reports.openFailed'), { description: toErrorMessage(err) })
    } finally {
      setOpening(false)
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title={t('reports.title')}
        description={t('reports.description')}
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
            <LlmNotConfiguredCard detail={llmError ? describeError(llmError).detail : null} />
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
                title={generating ? t('reports.preparing') : t('reports.noneSelected')}
                description={t('reports.emptyHint')}
              />
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
