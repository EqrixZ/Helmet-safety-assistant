import { ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { NavLink } from 'react-router-dom'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useAppStatus } from '@/hooks/useAppStatus'
import { cn } from '@/lib/utils'
import { Logo } from './Logo'
import { NAV_ITEMS } from './nav'

export function NavList({ compact, onNavigate }: { compact: boolean; onNavigate?: () => void }) {
  const { t } = useTranslation()
  return (
    <nav className="flex flex-col">
      {NAV_ITEMS.map((item) => {
        const link = (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'group relative flex h-12 items-center gap-3 rounded-lg px-4 text-sm transition-colors',
                compact && 'justify-center px-0',
                isActive ? 'font-semibold text-navy' : 'font-medium text-caption hover:bg-slate-50 hover:text-slate-700',
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className={cn('absolute size-1.5 rounded-full bg-navy', compact ? 'left-2' : 'left-1.5')} />
                )}
                <item.icon className={cn('size-[18px] shrink-0', isActive ? 'text-navy' : 'text-slate-400 group-hover:text-slate-600')} />
                {!compact && <span className="truncate">{t(item.labelKey)}</span>}
              </>
            )}
          </NavLink>
        )
        if (!compact) return link
        return (
          <Tooltip key={item.to}>
            <TooltipTrigger asChild>{link}</TooltipTrigger>
            <TooltipContent side="right">{t(item.labelKey)}</TooltipContent>
          </Tooltip>
        )
      })}
    </nav>
  )
}

export function SidebarBody({ compact = false, onNavigate }: { compact?: boolean; onNavigate?: () => void }) {
  const { health } = useAppStatus()
  const { t } = useTranslation()
  return (
    <div className="flex h-full flex-col bg-card px-4 py-6 shadow-sidebar">
      <div className={cn('px-2 pb-8', compact && 'px-0')}>
        <Logo compact={compact} />
      </div>
      {!compact && <div className="px-4 pb-2 text-[11px] font-medium tracking-wider text-slate-400 uppercase">{t('nav.mainMenu')}</div>}
      <NavList compact={compact} onNavigate={onNavigate} />
      <div className="mt-auto">
        {!compact ? (
          <div className="rounded-xl bg-page p-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-navy">
              <ShieldCheck className="size-4 text-tile-green" />
              {t('sidebar.cardTitle')}
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-caption">
              {t('sidebar.cardBody')}
            </p>
            <div className="mt-2 text-[10px] text-slate-400">{t('sidebar.version', { version: health?.version ?? '1.0.0' })}</div>
          </div>
        ) : (
          <div className="grid place-items-center">
            <ShieldCheck className="size-5 text-tile-green" />
          </div>
        )}
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <>
      <aside className="hidden w-[220px] shrink-0 lg:block">
        <div className="fixed inset-y-0 left-0 z-20 w-[220px]">
          <SidebarBody />
        </div>
      </aside>
      <aside className="hidden w-[72px] shrink-0 md:block lg:hidden">
        <div className="fixed inset-y-0 left-0 z-20 w-[72px]">
          <SidebarBody compact />
        </div>
      </aside>
    </>
  )
}
