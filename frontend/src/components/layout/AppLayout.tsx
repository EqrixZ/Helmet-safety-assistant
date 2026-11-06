import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

function BackdropGlow() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-page">
      <div className="absolute -top-48 -right-40 size-[560px] rounded-full bg-tile-blue/10 blur-3xl" />
      <div className="absolute -bottom-56 -left-32 size-[520px] rounded-full bg-tile-blue/[0.08] blur-3xl" />
    </div>
  )
}

export function AppLayout() {
  const { i18n } = useTranslation()
  return (
    <div className="relative isolate flex min-h-full">
      <BackdropGlow />
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1">
          {/* Keyed by language so pages (and plain formatter output) re-render on a language switch. */}
          <Outlet key={i18n.resolvedLanguage ?? i18n.language} />
        </main>
      </div>
    </div>
  )
}
