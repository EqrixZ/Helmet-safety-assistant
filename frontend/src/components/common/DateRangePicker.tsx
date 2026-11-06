import { CalendarRange } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { DateRange } from '@/api/types'
import { daysBetweenInclusive, shiftIsoDate } from '@/lib/format'
import { cn } from '@/lib/utils'

type Bounds = { min: string | null; max: string | null }

export function DateRangePicker({
  value,
  onChange,
  bounds,
  className,
}: {
  value: DateRange
  onChange: (range: DateRange) => void
  bounds: Bounds
  className?: string
}) {
  const { t } = useTranslation()
  const max = bounds.max ?? undefined
  const min = bounds.min ?? undefined
  const presets: { label: string; range: DateRange }[] = max
    ? [
        { label: t('common.range7'), range: { from: shiftIsoDate(max, -6), to: max } },
        { label: t('common.range14'), range: { from: shiftIsoDate(max, -13), to: max } },
        { label: t('common.rangeAll'), range: { from: min, to: max } },
      ]
    : []
  const isActive = (r: DateRange) => r.from === value.from && r.to === value.to

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
        {presets.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => onChange(p.range)}
            className={cn(
              'rounded-md px-2.5 py-1 text-xs font-medium transition-all',
              isActive(p.range) ? 'bg-card text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800',
            )}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-card px-3 text-sm shadow-xs focus-within:border-primary focus-within:ring-[3px] focus-within:ring-primary/20">
        <CalendarRange className="size-4 shrink-0 text-slate-400" />
        <input
          type="date"
          aria-label={t('common.dateFrom')}
          value={value.from ?? ''}
          min={min}
          max={value.to ?? max}
          onChange={(e) => onChange({ ...value, from: e.target.value || undefined })}
          className="w-[8.5rem] bg-transparent text-slate-700 outline-none"
        />
        <span className="text-slate-300">→</span>
        <input
          type="date"
          aria-label={t('common.dateTo')}
          value={value.to ?? ''}
          min={value.from ?? min}
          max={max}
          onChange={(e) => onChange({ ...value, to: e.target.value || undefined })}
          className="w-[8.5rem] bg-transparent text-slate-700 outline-none"
        />
      </div>
      {value.from && value.to && (
        <span className="text-xs text-slate-400">{t('common.days', { count: daysBetweenInclusive(value.from, value.to) })}</span>
      )}
    </div>
  )
}
