import { ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useAppStatus } from '@/hooks/useAppStatus'
import { cn } from '@/lib/utils'
import { Logo } from './Logo'
import { NAV_ITEMS } from './nav'

function NavList({ compact, onNavigate }: { compact: boolean; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const link = (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                compact && 'justify-center px-0',
                isActive
                  ? 'bg-white/[0.08] text-white'
                  : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-100',
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute top-2 bottom-2 left-0 w-[3px] rounded-r-full bg-primary" />}
                <item.icon
                  className={cn('size-[18px] shrink-0', isActive ? 'text-primary' : 'text-slate-500 group-hover:text-slate-300')}
                />
                {!compact && <span className="truncate">{item.label}</span>}
              </>
            )}
          </NavLink>
        )
        if (!compact) return link
        return (
          <Tooltip key={item.to}>
            <TooltipTrigger asChild>{link}</TooltipTrigger>
            <TooltipContent side="right">{item.label}</TooltipContent>
          </Tooltip>
        )
      })}
    </nav>
  )
}

export function SidebarBody({ compact = false, onNavigate }: { compact?: boolean; onNavigate?: () => void }) {
  const { health } = useAppStatus()
  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-slate-900 to-slate-950 px-3 py-5">
      <div className={cn('px-2 pb-6', compact && 'px-0')}>
        <Logo compact={compact} />
      </div>
      {!compact && <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">เมนูหลัก</div>}
      <NavList compact={compact} onNavigate={onNavigate} />
      <div className="mt-auto">
        {!compact ? (
          <div className="rounded-xl border border-white/5 bg-white/[0.03] p-3.5">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <ShieldCheck className="size-4 text-emerald-400" />
              ระบบตรวจจับหมวกนิรภัย
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400">
              YOLO26s + ผู้ช่วย LLM สำหรับวิเคราะห์ความปลอดภัยในไซต์ก่อสร้าง
            </p>
            <div className="mt-2 text-[10px] text-slate-500">เวอร์ชัน {health?.version ?? '1.0.0'}</div>
          </div>
        ) : (
          <div className="grid place-items-center">
            <ShieldCheck className="size-5 text-emerald-400/80" />
          </div>
        )}
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <>
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="fixed inset-y-0 left-0 w-64">
          <SidebarBody />
        </div>
      </aside>
      <aside className="hidden w-[72px] shrink-0 md:block lg:hidden">
        <div className="fixed inset-y-0 left-0 w-[72px]">
          <SidebarBody compact />
        </div>
      </aside>
    </>
  )
}
