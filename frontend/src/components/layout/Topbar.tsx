import { Building2, CalendarDays, Menu } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { useAppStatus } from '@/hooks/useAppStatus'
import { formatThaiFullDate } from '@/lib/format'
import { SidebarBody } from './Sidebar'
import { StatusDot, type DotTone } from './StatusDot'
import { NAV_ITEMS } from './nav'

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
  const { pathname } = useLocation()
  const current = NAV_ITEMS.find((n) => pathname.startsWith(n.to))

  const backendTone: DotTone = !healthChecked ? 'pending' : backendOnline ? 'ok' : 'down'
  const provider = health?.llm_provider ?? null
  const onFallback = provider?.name === 'fallback'
  const llmTone: DotTone =
    !healthChecked || !health ? 'pending' : !backendOnline ? 'down' : !health.llm_configured || onFallback ? 'warn' : 'ok'

  const backendTip = !healthChecked
    ? 'กำลังตรวจสอบการเชื่อมต่อ…'
    : backendOnline
      ? `เชื่อมต่อ Backend แล้ว · ${health?.events_count ?? 0} เหตุการณ์ในบันทึก`
      : 'ไม่สามารถเชื่อมต่อ Backend ได้ (ตรวจสอบซ้ำทุก 30 วินาที)'
  const llmTip = !health
    ? 'ยังไม่ทราบสถานะ LLM'
    : !health.llm_configured
      ? 'ยังไม่ได้ตั้งค่า LLM_API_KEY — ผู้ช่วยและรายงานจะยังใช้งานไม่ได้'
      : [
          onFallback
            ? `ใช้ผู้ให้บริการสำรอง: ${provider.model} (${hostOf(provider.base_url)}) — ตัวหลักติดโควตาหรือไม่พร้อม`
            : `LLM พร้อมใช้งาน · ${provider?.model ?? health.llm_model} (${hostOf(provider?.base_url ?? health.llm_base_url)})`,
          health.llm_rpm > 0 ? `จำกัด ${health.llm_rpm} คำขอ/นาที` : null,
          health.llm_fallback_configured && !onFallback ? 'มีผู้ให้บริการสำรองพร้อมใช้' : null,
        ]
          .filter(Boolean)
          .join(' · ')

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6">
        <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMenuOpen(true)} aria-label="เปิดเมนู">
            <Menu className="size-5" />
          </Button>
          <SheetContent side="left" className="w-72 border-0 bg-slate-950 p-0 [&>button]:text-slate-400">
            <SheetTitle className="sr-only">เมนู</SheetTitle>
            <SidebarBody onNavigate={() => setMenuOpen(false)} />
          </SheetContent>
        </Sheet>

        <div className="flex min-w-0 flex-1 items-center gap-3">
          <div className="hidden size-9 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-600 sm:grid">
            <Building2 className="size-[18px]" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-slate-900">{siteName}</div>
            <div className="flex items-center gap-1.5 truncate text-xs text-slate-500">
              <span className="hidden sm:inline">{current?.label ?? 'Helmet Safety Assistant'}</span>
              <span className="hidden sm:inline text-slate-300">•</span>
              <CalendarDays className="size-3.5 shrink-0" />
              <span className="truncate">{formatThaiFullDate(today)}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StatusDot label="Backend" tone={backendTone} tooltip={backendTip} />
          <StatusDot label={onFallback ? 'LLM (สำรอง)' : 'LLM'} tone={llmTone} tooltip={llmTip} />
        </div>
      </div>
    </header>
  )
}
