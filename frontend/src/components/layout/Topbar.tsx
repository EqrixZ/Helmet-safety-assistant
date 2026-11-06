import { Bell, ChevronDown, Menu, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { useAppStatus } from '@/hooks/useAppStatus'
import { formatFullDate } from '@/lib/format'
import { LanguageToggle } from './LanguageToggle'
import { SidebarBody } from './Sidebar'
import { StatusDot, type DotTone } from './StatusDot'
import { ThemeToggle } from './ThemeToggle'
import { TopbarSearch } from './TopbarSearch'

function hostOf(url: string): string {
  try {
    return new URL(url).host
  } catch {
    return url
  }
}

function useToday(): Date {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000)
    return () => window.clearInterval(id)
  }, [])
  return now
}

export function Topbar() {
  const { health, healthChecked, backendOnline, siteName } = useAppStatus()
  const [menuOpen, setMenuOpen] = useState(false)
  const today = useToday()
  const { t } = useTranslation()

  const backendTone: DotTone = !healthChecked ? 'pending' : backendOnline ? 'ok' : 'down'
  const provider = health?.llm_provider ?? null
  const onFallback = provider?.name === 'fallback'
  const llmTone: DotTone =
    !healthChecked || !health ? 'pending' : !backendOnline ? 'down' : !health.llm_configured || onFallback ? 'warn' : 'ok'

  const backendTip = !healthChecked
    ? t('topbar.checking')
    : backendOnline
      ? t('topbar.backendOnline', { count: health?.events_count ?? 0 })
      : t('topbar.backendOffline')
  const llmTip = !health
    ? t('topbar.llmUnknown')
    : !health.llm_configured
      ? t('topbar.llmNotConfigured')
      : [
          onFallback
            ? t('topbar.llmFallback', { model: provider.model, host: hostOf(provider.base_url) })
            : t('topbar.llmReady', {
                model: provider?.model ?? health.llm_model,
                host: hostOf(provider?.base_url ?? health.llm_base_url),
              }),
          health.llm_rpm > 0 ? t('topbar.llmRpm', { rpm: health.llm_rpm }) : null,
          health.llm_fallback_configured && !onFallback ? t('topbar.llmFallbackAvailable') : null,
        ]
          .filter(Boolean)
          .join(' · ')

  return (
    <header className="sticky top-0 z-10">
      <div className="flex h-20 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
          <Button variant="outline" size="icon" className="rounded-full border-0 shadow-soft md:hidden" onClick={() => setMenuOpen(true)} aria-label={t('nav.openMenu')}>
            <Menu className="size-5" />
          </Button>
          <SheetContent side="left" className="w-72 border-0 bg-card p-0">
            <SheetTitle className="sr-only">{t('nav.menu')}</SheetTitle>
            <SidebarBody onNavigate={() => setMenuOpen(false)} />
          </SheetContent>
        </Sheet>

        <div className="flex min-w-0 flex-1 items-center">
          <TopbarSearch />
        </div>

        <div className="flex items-center gap-2.5">
          <span className="hidden text-xs text-caption xl:inline">{formatFullDate(today)}</span>
          <div className="hidden items-center gap-1 rounded-full bg-card p-1 shadow-soft sm:flex">
            <StatusDot label="Backend" tone={backendTone} tooltip={backendTip} />
            <StatusDot label={onFallback ? t('topbar.llmFallbackLabel') : 'LLM'} tone={llmTone} tooltip={llmTip} />
          </div>
          <LanguageToggle />
          <ThemeToggle />
          <Link
            to="/events?violation=true"
            aria-label={t('topbar.recentViolations')}
            title={t('topbar.recentViolations')}
            className="grid size-11 place-items-center rounded-full bg-card text-slate-500 shadow-soft transition hover:text-navy"
          >
            <Bell className="size-[18px]" />
          </Link>
          <Link
            to="/settings"
            title={t('nav.settings.label')}
            className="flex h-11 items-center gap-2.5 rounded-full bg-card py-1 pr-3 pl-1 shadow-soft transition hover:shadow-card"
          >
            <span className="grid size-9 place-items-center rounded-full bg-blue-soft text-blue-ink">
              <UserRound className="size-[18px]" />
            </span>
            <span className="hidden min-w-0 leading-tight md:block">
              <span className="block text-[13px] font-semibold text-navy">{t('topbar.userRole')}</span>
              <span className="block max-w-40 truncate text-[11px] text-caption">{siteName || t('common.defaultSiteName')}</span>
            </span>
            <ChevronDown className="size-4 text-slate-400" />
          </Link>
        </div>
      </div>
    </header>
  )
}
