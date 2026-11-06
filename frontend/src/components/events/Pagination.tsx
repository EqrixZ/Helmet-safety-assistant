import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { formatNumber } from '@/lib/format'
import { cn } from '@/lib/utils'

function pageList(page: number, pages: number): (number | 'gap')[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1)
  const set = new Set([1, pages, page - 1, page, page + 1])
  const sorted = [...set].filter((p) => p >= 1 && p <= pages).sort((a, b) => a - b)
  const out: (number | 'gap')[] = []
  let prev = 0
  for (const p of sorted) {
    if (p - prev > 1) out.push('gap')
    out.push(p)
    prev = p
  }
  return out
}

export function Pagination({
  page,
  pages,
  total,
  size,
  onPage,
}: {
  page: number
  pages: number
  total: number
  size: number
  onPage: (p: number) => void
}) {
  const { t } = useTranslation()
  const start = total === 0 ? 0 : (page - 1) * size + 1
  const end = Math.min(total, page * size)
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t px-5 py-3 sm:flex-row">
      <div className="text-xs text-slate-500">
        <Trans
          i18nKey="events.pagination.showing"
          values={{ start, end, total: formatNumber(total) }}
          components={{ b: <span className="font-medium text-slate-700" /> }}
        />
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon-sm" disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label={t('events.pagination.prev')}>
          <ChevronLeft />
        </Button>
        {pageList(page, pages).map((p, i) =>
          p === 'gap' ? (
            <span key={`g${i}`} className="px-1 text-xs text-slate-400">…</span>
          ) : (
            <button
              key={p}
              type="button"
              onClick={() => onPage(p)}
              className={cn(
                'size-8 rounded-md text-xs font-medium transition',
                p === page ? 'bg-navy text-card' : 'text-slate-600 hover:bg-slate-100',
              )}
            >
              {p}
            </button>
          ),
        )}
        <Button variant="ghost" size="icon-sm" disabled={page >= pages} onClick={() => onPage(page + 1)} aria-label={t('events.pagination.next')}>
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}
