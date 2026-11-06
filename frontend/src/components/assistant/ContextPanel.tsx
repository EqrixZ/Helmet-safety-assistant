import { CalendarRange, Coins, Database, FileText, Info, ScrollText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ContextSources } from '@/api/types'
import { DataSourceBadge } from '@/components/common/StatusBadges'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate, formatNumber } from '@/lib/format'

export function ContextPanel({ sources, loading }: { sources: ContextSources | undefined; loading: boolean }) {
  const { t } = useTranslation()
  return (
    <div className="flex h-full flex-col gap-5 p-5">
      <div>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Database className="size-4 text-primary" /> {t('assistant.sourcesTitle')}
        </h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">{t('assistant.context.description')}</p>
      </div>

      {loading && !sources ? (
        <div className="space-y-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-24" />
        </div>
      ) : sources ? (
        <>
          <section className="space-y-2.5 rounded-xl border border-slate-200 bg-card p-3.5">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                <ScrollText className="size-3.5" /> {t('assistant.context.eventLog')}
              </span>
              <DataSourceBadge source={sources.data_source} />
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-slate-50 p-2">
                <div className="text-slate-500">{t('assistant.context.eventCount')}</div>
                <div className="mt-0.5 text-base font-bold text-slate-900 tabular-nums">{formatNumber(sources.events_count)}</div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2">
                <div className="text-slate-500">{t('assistant.context.sentToContext')}</div>
                <div className="mt-0.5 text-sm font-semibold text-slate-800">
                  {t('assistant.context.statsPlusRows', { count: sources.log_rows, rows: formatNumber(sources.log_rows) })}
                </div>
              </div>
            </div>
            {sources.log_filter && <p className="text-[11px] leading-relaxed text-slate-500">{sources.log_filter}</p>}
            <div className="flex items-center gap-1.5 text-xs text-slate-600">
              <CalendarRange className="size-3.5 text-slate-400" />
              {formatDate(sources.log_range.min)} – {formatDate(sources.log_range.max)}
            </div>
          </section>

          <section className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-1.5">
                <FileText className="size-3.5" /> {t('assistant.context.regulations')}
              </span>
              <span className="text-slate-400">
                {t('assistant.context.paragraphs', {
                  shown: sources.regulation_paragraphs.length,
                  total: sources.regulation_paragraphs_total,
                })}
              </span>
            </div>
            {sources.regulation_paragraphs.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-200 p-3 text-xs text-slate-500">
                {t('assistant.context.noDocs')}
              </div>
            ) : (
              <ul className="space-y-1.5">
                {sources.regulation_paragraphs.map((p, i) => (
                  <li key={`${i}-${p}`} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-card px-2.5 py-2 text-xs text-slate-700">
                    <FileText className="size-3.5 shrink-0 text-primary/70" />
                    <span className="truncate" title={p}>
                      {p}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-card px-3 py-2 text-xs">
            <span className="flex items-center gap-1.5 font-semibold text-slate-700">
              <Coins className="size-3.5" /> {t('assistant.context.size')}
            </span>
            <span className="font-mono tabular-nums text-slate-800" title={t('assistant.context.sizeTip')}>
              {t('assistant.context.tokens', { value: formatNumber(sources.token_estimate) })}
            </span>
          </div>
        </>
      ) : (
        <div className="text-xs text-slate-500">{t('assistant.context.loadFailed')}</div>
      )}

      <div className="mt-auto flex gap-2 rounded-lg bg-slate-100/80 p-3 text-[11px] leading-relaxed text-slate-500">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        {t('assistant.context.disclaimer')}
      </div>
    </div>
  )
}
