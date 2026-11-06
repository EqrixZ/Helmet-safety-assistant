import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

export type DotTone = 'ok' | 'warn' | 'down' | 'pending'

const TONES: Record<DotTone, { dot: string; ping: string }> = {
  ok: { dot: 'bg-tile-green', ping: 'bg-tile-green' },
  warn: { dot: 'bg-tile-orange', ping: 'bg-tile-orange' },
  down: { dot: 'bg-tile-red', ping: 'bg-tile-red' },
  pending: { dot: 'bg-slate-300', ping: 'bg-slate-300' },
}

export function PulseDot({ tone, className }: { tone: DotTone; className?: string }) {
  const t = TONES[tone]
  return (
    <span className={cn('relative flex size-2.5', className)}>
      {tone !== 'pending' && (
        <span className={cn('absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', t.ping)} />
      )}
      <span className={cn('relative inline-flex size-2.5 rounded-full', t.dot)} />
    </span>
  )
}

export function StatusDot({ label, tone, tooltip }: { label: string; tone: DotTone; tooltip: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className="flex h-9 items-center gap-2 rounded-full px-3 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
        >
          <PulseDot tone={tone} />
          {label}
        </button>
      </TooltipTrigger>
      <TooltipContent side="bottom">{tooltip}</TooltipContent>
    </Tooltip>
  )
}
