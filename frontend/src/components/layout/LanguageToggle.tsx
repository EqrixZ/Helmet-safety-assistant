import { useTranslation } from 'react-i18next'
import { type Language, LANGUAGES, setLanguage, useLang } from '@/i18n'
import { cn } from '@/lib/utils'

const NAME_KEYS: Record<Language, string> = { th: 'topbar.languageTh', en: 'topbar.languageEn' }

/** "TH | EN" pill for the top bar. */
export function LanguageToggle() {
  const { t } = useTranslation()
  const lang = useLang()
  return (
    <div role="group" aria-label={t('topbar.language')} className="flex h-11 items-center rounded-full bg-card p-1 shadow-soft">
      {LANGUAGES.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLanguage(l)}
          aria-pressed={lang === l}
          aria-label={t(NAME_KEYS[l])}
          title={t(NAME_KEYS[l])}
          lang={l}
          className={cn(
            'grid h-9 min-w-9 place-items-center rounded-full px-2.5 text-xs font-semibold transition',
            lang === l ? 'bg-blue-soft text-blue-ink' : 'text-slate-500 hover:text-navy',
          )}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  )
}
