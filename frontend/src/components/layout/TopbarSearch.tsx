import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import i18n, { LANGUAGES } from '@/i18n'
import { ZONE_KEYS } from '@/lib/format'

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Localized words in every supported language, e.g. the zone name in Thai and English. */
function allLangs(key: string): string[] {
  return LANGUAGES.map((lng) => i18n.t(key, { lng }).toLowerCase())
}

/** Maps free text to an existing /events filter: event id, zone (key or name in any language) or camera. */
export function searchTarget(text: string): string | null {
  const q = text.trim().toLowerCase()
  if (!q) return null
  const evt = q.match(/evt[\s-]?(\d+)/)
  if (evt?.[1]) return `/events?event=EVT-${evt[1].padStart(4, '0')}`
  const camWords = ['cam', ...allLangs('topbar.searchCameraWord')].map(escapeRegExp).join('|')
  const cam = q.match(new RegExp(`(?:${camWords})\\s*(\\d+)`))
  if (cam?.[1]) return `/events?camera=cam${Number(cam[1])}`
  const zone = ZONE_KEYS.find((key) => q.includes(key) || allLangs(`zoneNames.${key}`).some((name) => q.includes(name)))
  if (zone) return `/events?zone=${zone}`
  return null
}

export function TopbarSearch() {
  const [text, setText] = useState('')
  const navigate = useNavigate()
  const { t } = useTranslation()

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    const target = searchTarget(text)
    if (!target) {
      toast.info(t('topbar.searchHint'))
      return
    }
    navigate(target)
    setText('')
  }

  return (
    <form onSubmit={onSubmit} role="search" className="relative w-full max-w-sm">
      <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-slate-400" />
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t('topbar.searchPlaceholder')}
        aria-label={t('topbar.searchLabel')}
        className="h-11 w-full rounded-full bg-card pr-4 pl-11 text-sm text-navy shadow-soft outline-none placeholder:text-slate-400 focus-visible:ring-[3px] focus-visible:ring-primary/20"
      />
    </form>
  )
}
