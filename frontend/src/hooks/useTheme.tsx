import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'hsa-theme'
const FADE_MS = 200

function storedTheme(): Theme | null {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY)
    return v === 'light' || v === 'dark' ? v : null
  } catch {
    return null
  }
}

function systemTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function currentTheme(): Theme {
  // index.html sets data-theme before React mounts; trust it so the first render matches the paint.
  const attr = document.documentElement.getAttribute('data-theme')
  return attr === 'dark' || attr === 'light' ? attr : (storedTheme() ?? systemTheme())
}

type ThemeContextValue = { theme: Theme; toggleTheme: () => void; setTheme: (t: Theme) => void }

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(currentTheme)

  const apply = useCallback((next: Theme, persist: boolean) => {
    const root = document.documentElement
    root.classList.add('theme-transition')
    root.setAttribute('data-theme', next)
    window.setTimeout(() => root.classList.remove('theme-transition'), FADE_MS)
    if (persist) {
      try {
        window.localStorage.setItem(STORAGE_KEY, next)
      } catch {
        /* storage unavailable — theme still applies for this session */
      }
    }
    setThemeState(next)
  }, [])

  // Printed reports always use the light palette (white paper), whatever the screen theme.
  useEffect(() => {
    const root = document.documentElement
    const before = () => root.setAttribute('data-theme', 'light')
    const after = () => root.setAttribute('data-theme', theme)
    window.addEventListener('beforeprint', before)
    window.addEventListener('afterprint', after)
    return () => {
      window.removeEventListener('beforeprint', before)
      window.removeEventListener('afterprint', after)
    }
  }, [theme])

  // Follow the OS setting until the user has picked a theme explicitly.
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!mq) return
    const onChange = () => {
      if (!storedTheme()) apply(mq.matches ? 'dark' : 'light', false)
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [apply])

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      setTheme: (t) => apply(t, true),
      toggleTheme: () => apply(theme === 'dark' ? 'light' : 'dark', true),
    }),
    [theme, apply],
  )
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
