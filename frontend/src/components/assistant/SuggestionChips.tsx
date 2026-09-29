import { Sparkles } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export function SuggestionChips({
  questions,
  loading,
  onPick,
  disabled,
  variant = 'inline',
}: {
  questions: string[]
  loading: boolean
  onPick: (q: string) => void
  disabled?: boolean
  variant?: 'inline' | 'grid'
}) {
  if (loading) {
    return (
      <div className={cn('flex gap-2', variant === 'grid' ? 'grid sm:grid-cols-2' : 'overflow-hidden')}>
        {Array.from({ length: variant === 'grid' ? 4 : 3 }, (_, i) => (
          <Skeleton key={i} className={variant === 'grid' ? 'h-14 rounded-xl' : 'h-8 w-52 shrink-0 rounded-full'} />
        ))}
      </div>
    )
  }
  if (questions.length === 0) return null
  if (variant === 'grid') {
    return (
      <div className="grid gap-2.5 sm:grid-cols-2">
        {questions.map((q, i) => (
          <button
            key={q}
            type="button"
            disabled={disabled}
            onClick={() => onPick(q)}
            style={{ animationDelay: `${i * 60}ms` }}
            className="animate-slide-up group flex items-start gap-2.5 rounded-xl border border-slate-200 bg-white p-3.5 text-left text-sm text-slate-700 shadow-xs transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md disabled:opacity-50"
          >
            <Sparkles className="mt-0.5 size-4 shrink-0 text-primary/70 transition group-hover:text-primary" />
            {q}
          </button>
        ))}
      </div>
    )
  }
  return (
    <div className="scrollbar-thin -mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
      {questions.map((q) => (
        <button
          key={q}
          type="button"
          disabled={disabled}
          onClick={() => onPick(q)}
          className="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 shadow-xs transition hover:border-primary/40 hover:bg-orange-50/60 hover:text-slate-900 disabled:opacity-50"
        >
          {q}
        </button>
      ))}
    </div>
  )
}
