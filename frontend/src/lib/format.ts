import { addDays, differenceInCalendarDays, format, parseISO } from 'date-fns'

export const ZONE_LABELS: Record<string, string> = {
  entrance: 'ทางเข้า',
  crane: 'เครน',
  scaffold: 'นั่งร้าน',
  floor3: 'ชั้น 3',
  warehouse: 'คลังวัสดุ',
}

export function zoneLabel(key: string): string {
  if (key === 'unknown') return 'ไม่ทราบโซน'
  return ZONE_LABELS[key] ?? key
}

export function cameraLabel(key: string): string {
  if (key === 'unknown') return 'ไม่ทราบกล้อง'
  const m = /^cam(\d+)$/i.exec(key)
  return m ? `กล้อง ${m[1]}` : key
}

const nf = new Intl.NumberFormat('th-TH')
export function formatNumber(n: number): string {
  return nf.format(n)
}

export function formatPercent(ratio: number, digits = 1): string {
  return `${(ratio * 100).toFixed(digits)}%`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let v = bytes / 1024
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${units[i] ?? 'GB'}`
}

function safeParse(iso: string): Date | null {
  const d = parseISO(iso)
  return Number.isNaN(d.getTime()) ? null : d
}

/** "29 ก.ย. 2569" */
export function formatThaiDate(iso: string | null | undefined, style: 'short' | 'long' = 'short'): string {
  if (!iso) return '—'
  const d = safeParse(iso)
  if (!d) return iso
  return new Intl.DateTimeFormat('th-TH', {
    day: 'numeric',
    month: style === 'long' ? 'long' : 'short',
    year: 'numeric',
  }).format(d)
}

/** "จันทร์ที่ 29 กันยายน 2569" */
export function formatThaiFullDate(d: Date): string {
  return new Intl.DateTimeFormat('th-TH', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(d)
}

/** "29 ก.ย." for chart axes */
export function formatThaiDayMonth(iso: string): string {
  const d = safeParse(iso)
  if (!d) return iso
  return new Intl.DateTimeFormat('th-TH', { day: 'numeric', month: 'short' }).format(d)
}

/** "29 ก.ย. 2569 14:05" */
export function formatThaiDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = safeParse(iso)
  if (!d) return iso
  return new Intl.DateTimeFormat('th-TH', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}

export function formatHourKey(key: string): string {
  return `${key.padStart(2, '0')}:00`
}

export function formatHourRange(key: string): string {
  const h = Number(key)
  return `${String(h).padStart(2, '0')}:00–${String(h).padStart(2, '0')}:59 น.`
}

export function toIsoDate(d: Date): string {
  return format(d, 'yyyy-MM-dd')
}

export function shiftIsoDate(iso: string, days: number): string {
  const d = safeParse(iso)
  return d ? toIsoDate(addDays(d, days)) : iso
}

export function daysBetweenInclusive(from: string, to: string): number {
  const a = safeParse(from)
  const b = safeParse(to)
  if (!a || !b) return 0
  return differenceInCalendarDays(b, a) + 1
}

export function riskLevel(rate: number): { label: string; tone: 'high' | 'medium' | 'low' } {
  if (rate >= 0.4) return { label: 'สูง', tone: 'high' }
  if (rate >= 0.2) return { label: 'กลาง', tone: 'medium' }
  return { label: 'ต่ำ', tone: 'low' }
}
