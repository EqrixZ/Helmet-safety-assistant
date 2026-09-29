import { Bot, FileText, LayoutDashboard, type LucideIcon, MapPinned, ScrollText, Settings } from 'lucide-react'

export type NavItem = { to: string; label: string; description: string; icon: LucideIcon }

export const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'แดชบอร์ด', description: 'ภาพรวมความปลอดภัย', icon: LayoutDashboard },
  { to: '/events', label: 'บันทึกเหตุการณ์', description: 'ตรวจสอบทุกเหตุการณ์', icon: ScrollText },
  { to: '/assistant', label: 'ผู้ช่วย AI', description: 'ถาม-ตอบจากข้อมูลจริง', icon: Bot },
  { to: '/reports', label: 'รายงาน', description: 'สร้างรายงานอัตโนมัติ', icon: FileText },
  { to: '/zones', label: 'โซนพื้นที่', description: 'ความเสี่ยงรายโซน', icon: MapPinned },
  { to: '/settings', label: 'ตั้งค่า', description: 'ข้อมูล โมเดล และเอกสาร', icon: Settings },
]
