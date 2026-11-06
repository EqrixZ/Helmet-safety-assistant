import { addDays, differenceInCalendarDays, format, parseISO } from 'date-fns'
import i18n, { currentLang } from '@/i18n'

/** Zone keys known to the UI; display names live in the translation files (`zoneNames`). */
export const ZONE_KEYS = ['entrance', 'crane', 'scaffold', 'floor3', 'warehouse'] as const

/** Intl locale for the active language: Thai uses the Buddhist-era calendar, English uses en-GB. */
function locale(): string {
  return currentLang() === 'th' ? 'th-TH' : 'en-GB'
}

export function zoneLabel(key: string): string {
  if (key === 'unknown') return i18n.t('common.unknownZone')
  return i18n.t(`zoneNames.${key}`, { defaultValue: key })
}

/** Zone name wrapped in the localized "zone" phrase, e.g. "Crane zone". */
export function zoneWithName(key: string): string {
  return i18n.t('common.zoneWithName', { name: zoneLabel(key) })
}

export function cameraLabel(key: string): string {
  if (key === 'unknown') return i18n.t('common.unknownCamera')
  const m = /^cam(\d+)$/i.exec(key)
  return m ? i18n.t('common.camera', { id: m[1] }) : key
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat(locale()).format(n)
}

/** Clock time with the localized suffix (Thai appends the "o'clock" abbreviation). */
export function formatTime(time: string): string {
  return i18n.t('common.time', { time })
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

/** "29 Sep 2026" / Thai short month + Buddhist-era year */
export function formatDate(iso: string | null | undefined, style: 'short' | 'long' = 'short'): string {
  if (!iso) return '—'
  const d = safeParse(iso)
  if (!d) return iso
  return new Intl.DateTimeFormat(locale(), {
    day: 'numeric',
    month: style === 'long' ? 'long' : 'short',
    year: 'numeric',
  }).format(d)
}

/** "Tuesday 29 September 2026" / Thai long form with Buddhist-era year */
export function formatFullDate(d: Date): string {
  return new Intl.DateTimeFormat(locale(), {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(d)
}

/** "29 Sep" for chart axes */
export function formatDayMonth(iso: string): string {
  const d = safeParse(iso)
  if (!d) return iso
  return new Intl.DateTimeFormat(locale(), { day: 'numeric', month: 'short' }).format(d)
}

/** "29 Sep 2026, 14:05" */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = safeParse(iso)
  if (!d) return iso
  return new Intl.DateTimeFormat(locale(), {
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
  const h = String(Number(key)).padStart(2, '0')
  return i18n.t('common.hourRange', { from: `${h}:00`, to: `${h}:59` })
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
  const tone = rate >= 0.4 ? 'high' : rate >= 0.2 ? 'medium' : 'low'
  return { label: i18n.t(`risk.${tone}`), tone }
}
