import { Bot, FileText, LayoutDashboard, type LucideIcon, MapPinned, ScrollText, Settings } from 'lucide-react'

/** Labels are translation keys, resolved with t() at render time. */
export type NavItem = { to: string; labelKey: string; descriptionKey: string; icon: LucideIcon }

export const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', labelKey: 'nav.dashboard.label', descriptionKey: 'nav.dashboard.description', icon: LayoutDashboard },
  { to: '/events', labelKey: 'nav.events.label', descriptionKey: 'nav.events.description', icon: ScrollText },
  { to: '/assistant', labelKey: 'nav.assistant.label', descriptionKey: 'nav.assistant.description', icon: Bot },
  { to: '/reports', labelKey: 'nav.reports.label', descriptionKey: 'nav.reports.description', icon: FileText },
  { to: '/zones', labelKey: 'nav.zones.label', descriptionKey: 'nav.zones.description', icon: MapPinned },
  { to: '/settings', labelKey: 'nav.settings.label', descriptionKey: 'nav.settings.description', icon: Settings },
]
