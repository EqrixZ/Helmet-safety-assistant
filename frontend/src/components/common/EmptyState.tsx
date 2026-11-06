import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  tone = 'default',
}: {
  icon: LucideIcon
  title: string
  description?: ReactNode
  action?: ReactNode
  className?: string
  tone?: 'default' | 'danger'
}) {
  return (
    <div className={cn('animate-fade-in flex flex-col items-center justify-center px-6 py-12 text-center', className)}>
      <div className="relative mb-4">
        <div className={cn('absolute inset-0 scale-150 rounded-full blur-xl', tone === 'danger' ? 'bg-red-soft' : 'bg-blue-soft')} />
        <div
          className={cn(
            'relative grid size-14 place-items-center rounded-2xl border bg-card shadow-sm',
            tone === 'danger' ? 'border-red-soft text-tile-red' : 'border-slate-200 text-slate-400',
          )}
        >
          <Icon className="size-6" />
        </div>
      </div>
      <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
      {description && <div className="mt-1.5 max-w-sm text-sm leading-relaxed text-slate-500">{description}</div>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
