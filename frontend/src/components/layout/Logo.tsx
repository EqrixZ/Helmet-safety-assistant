import { HardHat } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className={cn('flex items-center gap-3', compact && 'justify-center')}>
      <div className="relative grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-[#F7A34B] to-[#E0761A] shadow-lg shadow-primary/25 ring-1 ring-white/10">
        <HardHat className="size-5.5 text-white" strokeWidth={2.2} />
      </div>
      {!compact && (
        <div className="min-w-0 leading-tight">
          <div className="truncate text-[15px] font-bold tracking-tight text-white">Helmet Safety</div>
          <div className="truncate text-[11px] font-medium tracking-wide text-slate-400">Assistant · AI Monitoring</div>
        </div>
      )}
    </div>
  )
}
