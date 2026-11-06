import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next, useTranslation } from 'react-i18next'
import type { Language } from '@/api/types'
import en from './en.json'
import th from './th.json'

export type { Language }

export const LANGUAGES: readonly Language[] = ['th', 'en']
export const LANG_STORAGE_KEY = 'hsa-lang'

/** Any `th*` tag → 'th', everything else → 'en' (mirrors the inline script in index.html). */
export function normalizeLang(value: string | null | undefined): Language {
  return (value ?? '').toLowerCase().startsWith('th') ? 'th' : 'en'
}

function syncHtmlLang(lng: string | undefined): void {
  if (typeof document !== 'undefined') document.documentElement.lang = normalizeLang(lng)
}

i18n.on('languageChanged', syncHtmlLang)

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { th: { translation: th }, en: { translation: en } },
    supportedLngs: [...LANGUAGES],
    nonExplicitSupportedLngs: true,
    load: 'languageOnly',
    fallbackLng: 'en',
    initAsync: false,
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: LANG_STORAGE_KEY,
      caches: ['localStorage'],
      convertDetectedLanguage: (lng: string) => normalizeLang(lng),
    },
  })

syncHtmlLang(i18n.resolvedLanguage ?? i18n.language)

/** The active UI language, outside React (formatters, API calls). */
export function currentLang(): Language {
  return normalizeLang(i18n.resolvedLanguage ?? i18n.language)
}

export function setLanguage(lang: Language): void {
  void i18n.changeLanguage(lang)
}

/** The active UI language; re-renders the caller when it changes. */
export function useLang(): Language {
  const { i18n: instance } = useTranslation()
  return normalizeLang(instance.resolvedLanguage ?? instance.language)
}

export default i18n
