import { CalendarDays, Loader2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { ReportType } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { IndeterminateProgress } from '@/components/ui/progress'
import { Segmented } from '@/components/ui/segmented'
import { formatDate, shiftIsoDate } from '@/lib/format'

const STAGE_KEYS = [
  'reports.generator.stages.collect',
  'reports.generator.stages.stats',
  'reports.generator.stages.analyse',
  'reports.generator.stages.risk',
  'reports.generator.stages.format',
]

function useStage(active: boolean): string {
  const [i, setI] = useState(0)
  useEffect(() => {
    if (!active) {
      setI(0)
      return
    }
    const id = window.setInterval(() => setI((x) => Math.min(x + 1, STAGE_KEYS.length - 1)), 2500)
    return () => window.clearInterval(id)
  }, [active])
  return STAGE_KEYS[i] ?? ''
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
  const { t } = useTranslation()
  const stage = t(useStage(generating))
  const rangeText =
    date && type === 'weekly' ? `${formatDate(date)} – ${formatDate(shiftIsoDate(date, 6))}` : formatDate(date)

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{t('reports.generator.title')}</CardTitle>
          <CardDescription>{t('reports.generator.description')}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Label>{t('reports.generator.type')}</Label>
          <Segmented<ReportType>
            className="flex w-full [&>button]:flex-1"
            value={type}
            onChange={onType}
            options={[
              { value: 'daily', label: t('reports.daily') },
              { value: 'weekly', label: t('reports.generator.weeklyLong') },
            ]}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="report-date">{type === 'daily' ? t('reports.generator.date') : t('reports.generator.weekStart')}</Label>
          <Input id="report-date" type="date" value={date} min={minDate} max={maxDate} onChange={(e) => onDate(e.target.value)} />
          {date && (
            <p className="flex items-center gap-1.5 text-xs text-slate-500">
              <CalendarDays className="size-3.5" /> {t('reports.generator.range', { range: rangeText })}
            </p>
          )}
        </div>
        <Button className="w-full" size="lg" onClick={onGenerate} disabled={generating || !date}>
          {generating ? <Loader2 className="animate-spin" /> : <Sparkles />}
          {generating ? t('reports.generator.generating') : t('reports.generator.generate')}
        </Button>
        {generating && (
          <div className="animate-fade-in space-y-2 rounded-lg bg-blue-soft p-3">
            <IndeterminateProgress />
            <p key={stage} className="animate-fade-in text-xs text-slate-600">
              {stage}
            </p>
            <p className="text-[11px] text-slate-400">{t('reports.generator.duration')}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
