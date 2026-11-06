import { Download, FileText, Printer } from 'lucide-react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import type { Report } from '@/api/types'
import { Markdown } from '@/components/common/Markdown'
import { Button } from '@/components/ui/button'
import { formatDateTime } from '@/lib/format'
import { downloadText } from '@/lib/utils'

const PAPER_PROSE =
  'prose-slate dark:prose-invert prose-h1:font-serif prose-h1:text-[26px] prose-h1:leading-snug prose-h1:mb-2 prose-h2:font-serif prose-h2:text-lg prose-h2:mt-8 prose-h2:border-b prose-h2:border-slate-200 prose-h2:pb-2 prose-h2:text-slate-900 prose-p:text-[14px] prose-li:text-[14px] prose-td:text-[13px] prose-th:text-[13px]'

export function ReportPaper({ report, siteName }: { report: Report; siteName: string }) {
  const { t } = useTranslation()
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <FileText className="size-4" />
          <span className="font-mono">{report.name}</span>
          <span className="text-slate-300">•</span>
          <span>{t('reports.createdAt', { date: formatDateTime(report.created_at) })}</span>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => downloadText(report.name, report.markdown)}>
            <Download /> {t('reports.paper.download')}
          </Button>
          <Button variant="dark" size="sm" onClick={() => window.print()}>
            <Printer /> {t('reports.paper.print')}
          </Button>
        </div>
      </div>

      <div className="rounded-sm bg-slate-200/60 p-3 sm:p-6">
        <article className="animate-slide-up mx-auto min-h-[60vh] max-w-[210mm] bg-card px-8 py-10 shadow-[0_1px_3px_rgba(15,23,42,0.08),0_12px_40px_-12px_rgba(15,23,42,0.25)] sm:px-14 sm:py-14">
          <PaperHeader siteName={siteName} />
          <Markdown className={PAPER_PROSE}>{report.markdown}</Markdown>
          <PaperFooter report={report} />
        </article>
      </div>

      {createPortal(
        <div className="print-portal">
          <PaperHeader siteName={siteName} />
          <Markdown className={PAPER_PROSE}>{report.markdown}</Markdown>
          <PaperFooter report={report} />
        </div>,
        document.body,
      )}
    </div>
  )
}

function PaperHeader({ siteName }: { siteName: string }) {
  const { t } = useTranslation()
  return (
    <div className="mb-8 flex items-center justify-between border-b-2 border-primary pb-3 text-[11px] tracking-wide text-slate-500">
      <span className="font-semibold text-slate-700">HELMET SAFETY ASSISTANT</span>
      <span>{siteName || t('common.defaultSiteName')}</span>
    </div>
  )
}

/** Printed with the report, so it follows the report's language rather than the UI language. */
function PaperFooter({ report }: { report: Report }) {
  const { t } = useTranslation()
  return (
    <div className="mt-12 border-t border-slate-200 pt-3 text-center text-[10px] text-slate-400">
      {t('reports.paper.footer', { lng: report.language === 'en' ? 'en' : 'th' })}
    </div>
  )
}
